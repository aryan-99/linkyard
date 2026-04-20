# How Linkyard Works — Technical Overview

A conceptual guide to the design choices behind Linkyard. Read this to understand *why* the system is built the way it is. For *what* it does (endpoints, columns, layer layout), see `API_SPEC.md`, `DATA_MODEL.md`, and `ARCHITECTURE.md`.

---

## The core problem

Traditional bookmarks and browser history are keyword-searchable — you can find a link if you remember a word from its title or URL. But human memory doesn't work that way. You remember *what an article was about*, not its exact title. Linkyard solves this by searching links by **meaning**, not by string matching.

---

## How semantic search works

Every link is converted into a fixed-length vector of floating-point numbers (an **embedding**) that encodes its meaning. Semantically similar content — even if worded differently — ends up as nearby vectors in this high-dimensional space.

When you search, your query text is embedded the same way, then the database returns the stored links whose vectors are closest to the query vector. "Closest" is measured by **cosine similarity** — the angle between two vectors. A score of 1.0 means identical direction (same meaning); 0.0 means orthogonal (unrelated).

```
"async python tutorial"  →  [0.12, -0.84, 0.33, ...]  ←── query vector
                                         ↕ cosine distance
"concurrency in Python"  →  [0.14, -0.81, 0.31, ...]  ←── stored link (close → high score)
"chocolate cake recipe"  →  [-0.72, 0.41, -0.18, ...]  ←── stored link (far → low score)
```

This is why two links about the same topic surface together even if they share no words.

---

## The ingest pipeline

When a link is saved, five things happen in order:

1. **URL normalization** — scheme and host are lowercased, trailing slashes stripped. This prevents `https://Example.com/` and `https://example.com` from being treated as different links.

2. **Metadata enrichment** *(Stage 2, not yet)* — if title or snippet are missing, `httpx` fetches the page and scrapes `<title>` and `<meta name="description">`. This improves embedding quality for bare URLs.

3. **Text assembly** — title, snippet, and URL are concatenated into a single string to embed. More context → better vector.

4. **Embedding** — the assembled text is passed to the `EmbeddingProvider`, which returns a vector of length `EMBEDDING_DIM`. The vector is stored alongside the other link fields.

5. **Persistence** — one row is written to the `links` table. The embedding is stored as a `VECTOR(N)` column, a type added to Postgres by the pgvector extension.

Embedding happens **at save time**, not at search time. This means search is fast (one embedding computation + one indexed vector scan) regardless of how many links are stored.

---

## The pluggable embedding provider

The embedding dimension and quality depend on the model. We want to be able to swap providers without rewriting any business logic:

| Provider | Dim | Use case |
|---|---|---|
| `StubProvider` | 384 | Dev and tests. Deterministic hash → unit-vector. No model needed. |
| `LocalProvider` *(future)* | 384 | Sentence-transformers MiniLM running in-process. No API key, works offline. |
| `OpenAIProvider` *(future)* | 1536 | `text-embedding-3-small`. Best quality, requires API key and network. |

The provider is selected by `EMBEDDING_PROVIDER` env var. All callers depend on the `EmbeddingProvider` ABC — they call `provider.embed(text)` and get back a `list[float]`. The concrete provider is never imported outside its own module.

**Gotcha:** changing providers requires a migration to change the vector column dimension, plus re-embedding all existing rows. This is a breaking change — plan for it.

---

## Why pgvector instead of a dedicated vector DB

Dedicated vector databases (Pinecone, Qdrant, Weaviate) are optimized for pure vector search at massive scale. For Linkyard — a personal tool with thousands to low-millions of links — Postgres + pgvector is the right call:

- **One less service to operate.** No sync between a relational DB and a vector store.
- **Transactional writes.** The link row and its embedding are written atomically. No partial state where metadata exists but the embedding is missing.
- **Standard SQL filtering.** Vector search can be pre-filtered with normal `WHERE` clauses (future: filter by tag, date, source).
- **pgvector's IVFFlat index** handles millions of vectors efficiently for our latency targets. We add it in a later migration once enough rows exist (the index needs data to train on).

---

## Why async everywhere on the backend

Each request may do two slow things: a database query and (for ingest) an HTTP fetch to scrape metadata. In a synchronous server, each of those blocks the thread — meaning concurrent requests queue up behind each other.

FastAPI with async SQLAlchemy (via `asyncpg`) and `httpx` lets both operations yield control while waiting on I/O, so many requests can be in-flight simultaneously on a small number of threads. This matters especially for the ingest endpoint, which will eventually call an external embedding API.

The tradeoff: async code is harder to reason about, and Alembic (the migration tool) is synchronous — it uses a separate sync `DATABASE_URL_SYNC` connection string. No sync SQLAlchemy is permitted inside `backend/app/` outside of Alembic's env.py.

---

## Why routers stay thin

Routers validate HTTP input and return HTTP output. Nothing more. Business logic lives in `services/`. This means:

- **Services are testable without HTTP.** You can call `ingest_link(session, data)` directly in a test without spinning up FastAPI.
- **Logic isn't duplicated.** The extension, the web UI, and a future CLI all call the same service layer through the same endpoints.
- **Schemas are stable contracts.** ORM objects are never returned directly — only Pydantic schemas. If the DB model changes internally, the API contract stays stable as long as the schema doesn't change.

---

## How the browser extension fits in

The extension runs entirely in the browser. Its only job is to collect metadata about the current tab (URL, page title, meta description) and POST it to the backend. There is no business logic in the extension.

MV3 service workers (background scripts) are ephemeral — they terminate when idle and restart on demand. This means the extension cannot hold long-lived state in memory. Configuration (backend URL, auth token) is stored in `chrome.storage` and read on demand.

The content script runs in the page context and can read the DOM. The popup communicates with the content script via `chrome.tabs.sendMessage` to request metadata before POSTing to the backend.

---

## Data flow: saving a link end-to-end

```
User clicks "Save" in popup
    │
    ▼
content.js reads document.title, document.querySelector('meta[name=description]')
    │
    ▼
popup.js POSTs { url, title, snippet, source: "extension" } to POST /links
    │
    ▼
FastAPI router validates input via LinkCreate schema
    │
    ▼
ingest_link() normalizes URL → assembles text → calls StubProvider.embed()
    │
    ▼
Link row written to Postgres (url, title, snippet, embedding, ...)
    │
    ▼
201 LinkDetailResponse returned to popup → popup shows "Saved"
```

---

## Data flow: searching end-to-end *(Stage 2)*

```
User types query in search box
    │
    ▼
Frontend POSTs to GET /search?q=...&k=10
    │
    ▼
Backend embeds query text via EmbeddingProvider
    │
    ▼
SELECT ... FROM links ORDER BY embedding <=> :query_vec LIMIT 10
    │
    ▼
Postgres uses IVFFlat index to find approximate nearest neighbors
    │
    ▼
Results returned with cosine similarity scores, ranked best-first
    │
    ▼
Frontend renders results list
```

---

## What's not in scope (yet)

- **Authentication.** The app is single-user for now. The `url` uniqueness constraint is per-user in the data model notes — that constraint is deferred until auth lands.
- **Tags.** The schema reserves room for a tags join table but it's not implemented.
- **Re-embedding.** When you switch providers, existing links have the wrong vector dimension. A migration + batch re-embed job is needed.
- **Metadata fetch.** The ingest pipeline currently uses only client-supplied title/snippet. The `httpx` fetch step is planned for Stage 2.

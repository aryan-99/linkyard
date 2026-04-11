# Linkyard Architecture

## Goal
Save links from anywhere (browser extension, web UI, API). Search them by meaning, not just keywords.

## High-level shape

```
[Browser extension] ──┐
[Web UI (React)]  ────┼──► [FastAPI backend] ──► [Postgres + pgvector]
[Direct API use]  ────┘           │
                                  └──► [Embedding provider]
                                       (local model | OpenAI | stub)
```

## Backend (FastAPI)

Layered:

- **routers/** — thin HTTP layer. Validates input, calls services, returns schemas.
- **services/** — business logic. Ingest pipeline, embedding, search ranking.
- **models/** — SQLAlchemy ORM. Single source of truth for DB schema.
- **schemas/** — Pydantic request/response types. Never leak ORM objects.
- **db.py** — async engine + session factory.
- **config.py** — Pydantic settings loaded from env.

Async SQLAlchemy throughout. Alembic for migrations. pgvector extension enabled via migration.

### Ingest pipeline
1. Client posts `{url, title?, snippet?}`.
2. Service normalizes URL, fetches metadata if missing (`httpx`).
3. Service computes embedding via pluggable `EmbeddingProvider`.
4. Row written to `links` with `embedding VECTOR(N)`.

### Search
- Query text → embedding → `ORDER BY embedding <=> :q LIMIT k`.
- Optional keyword prefilter on `title || snippet`.

## Frontend (React + Vite + TS)

- `src/api/` — fetch wrappers, one per resource.
- `src/components/` — presentational.
- `src/pages/` — route-level.
- Week 3 goal: search input + results list.

## Extension (MV3)

- `background.js` — service worker. Handles messages from popup/content.
- `content.js` — scrapes current tab metadata on demand.
- `popup/` — save button + status feedback.
- Posts to backend via `fetch`. API base URL lives in extension storage.

## Embedding provider
Abstracted so we can swap:
- `StubProvider` — deterministic hash → vector, for tests and local dev without a model.
- `LocalProvider` — sentence-transformers via a sidecar or in-process.
- `OpenAIProvider` — `text-embedding-3-small`.

Selected via `EMBEDDING_PROVIDER` env var.

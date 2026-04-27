<div align="center">

# Linkyard

**Save links from anywhere. Find them by meaning.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-semantic_search-blueviolet?style=flat-square)](https://github.com/pgvector/pgvector)
[![MV3](https://img.shields.io/badge/Extension-Manifest_V3-4285F4?style=flat-square&logo=googlechrome&logoColor=white)](https://developer.chrome.com/docs/extensions/mv3/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

</div>

---

Linkyard is a personal link-bookmarking app with **semantic search** — powered by pgvector embeddings. Instead of remembering exact titles or keywords, you can search by meaning: *"that article about async Python performance"* finds the right link even if those words aren't in it.

## Features

- **One-click save** from any tab via the browser extension
- **Semantic search** — find links by meaning, not just keywords
- **Match scores** — see how closely each result fits your query
- **Web UI** — browse, add, and delete links without leaving the browser
- **Dark mode** — respects your OS preference automatically
- **Clean API** — fully documented REST API for scripting or integrations

## Architecture

```
┌─────────────────────────┐     ┌────────────────────────────┐
│   Browser Extension     │     │        Web Frontend         │
│  (MV3 · plain JS)       │     │   (React 18 · Vite · TS)   │
│                         │     │                             │
│  popup → background.js  │     │  /links   →  LinksPage      │
│  saves current tab URL  │     │  /search  →  SearchPage     │
└──────────┬──────────────┘     └────────────┬───────────────┘
           │  POST /links                     │  GET /links, /search
           └──────────────┬───────────────────┘
                          ▼
             ┌────────────────────────┐
             │      FastAPI Backend   │
             │                        │
             │  /links  CRUD router   │
             │  /links/search         │
             │  EmbeddingProvider ──┐ │
             └──────────────────┬───┘ │
                                │     │ embed on ingest
                          ┌─────▼─────▼──────────────┐
                          │  PostgreSQL 16 + pgvector  │
                          │  cosine distance search    │
                          └────────────────────────────┘
```

## Quick Start

**Prerequisites:** Docker, Python 3.11+, Node 18+

```bash
# 1. Start Postgres
docker compose -f docker-compose.dev.yml up -d

# 2. Backend
cd backend
pip install -r requirements.txt
alembic upgrade head          # run migrations
uvicorn app.main:app --reload # http://localhost:8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173

# 4. Extension
# Chrome: chrome://extensions → Enable Developer mode → Load unpacked → select extension/
```

API docs auto-generated at `http://localhost:8000/docs`.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2 async, Pydantic v2, Alembic |
| Database | PostgreSQL 16, pgvector |
| Frontend | React 18, Vite, TypeScript |
| Extension | Chrome MV3, plain ES modules |
| Dev infra | Docker Compose |

## Project Layout

```
backend/app/
  main.py          FastAPI entrypoint + CORS config
  config.py        Pydantic settings (env-driven)
  db.py            Async engine + session factory
  models/          SQLAlchemy ORM models
  schemas/         Pydantic request/response schemas
  routers/         HTTP endpoints (one file per resource)
  services/        Business logic — ingest, embedding, search

frontend/src/
  api/             Typed fetch wrappers (links.ts, search.ts)
  components/      Shared UI components
  pages/           LinksPage, SearchPage

extension/
  background.js    Service worker — handles SAVE_LINK message
  popup/           popup.html + popup.js
  manifest.json    MV3 manifest
```

## Embedding Providers

Search quality depends on the active embedding provider, selected via the `EMBEDDING_PROVIDER` env var:

| Provider | `EMBEDDING_PROVIDER` value | Notes |
|---|---|---|
| **Stub** *(default)* | `stub` | Hash-based unit vectors. Zero deps, but search isn't semantically meaningful. |
| **Local** *(planned)* | `local` | `sentence-transformers` — offline, good quality. |
| **OpenAI** *(planned)* | `openai` | `text-embedding-3-small` — best quality, requires API key. |

Switching providers requires a re-embed of existing links and an Alembic migration if the embedding dimension changes.

## Roadmap

- [x] Links CRUD (create, list, delete)
- [x] Semantic search with match scores
- [x] Browser extension (MV3, one-click save)
- [x] Dark mode UI
- [x] Integration test suite
- [ ] Real embedding provider (LocalProvider / OpenAI)
- [ ] Extension options page (configurable API URL)
- [ ] Tagging and collections
- [ ] Auth / multi-user support

## Development Notes

- All backend routes and services are `async def` — no sync DB access anywhere in `backend/app/`
- Alembic uses a separate sync `DATABASE_URL_SYNC` env var (psycopg driver) since Alembic itself isn't async
- CORS is locked to `chrome-extension://` origins by regex (`CORS_ORIGIN_REGEX` env var) — pin to your published extension ID in production
- Tests require a live Postgres instance (`pytest-asyncio`, `asyncpg`). Run from `backend/` with `pytest`

---

<div align="center">
<sub>Built with FastAPI · pgvector · React · Chrome MV3</sub>
</div>

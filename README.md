# Linkyard

A semantic link-bookmarking app. Save links from anywhere, search them by meaning.

## Components

- **backend/** — FastAPI + SQLAlchemy, Postgres with pgvector for semantic search
- **frontend/** — React + Vite + TypeScript
- **extension/** — MV3 browser extension for one-click saves
- **docs/** — architecture, API spec, data model

## Quick start

```bash
docker compose -f docker-compose.dev.yml up -d   # start Postgres
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

See `docs/ARCHITECTURE.md` for the full picture.

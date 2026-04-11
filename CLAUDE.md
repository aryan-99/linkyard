# Linkyard — Claude context

> **Read first every session:** `docs/JOURNAL.md` — compact shared history (current state + ADRs + recent log). It's the cheapest way to get oriented across sessions; use it before re-reading other docs or exploring the codebase.

## What this is
Semantic link-bookmarking app. Save URLs via browser extension or web UI; search them by meaning using pgvector embeddings.

## Stack
- **Backend:** FastAPI, SQLAlchemy 2.x async, Postgres 16 + pgvector, Alembic, Pydantic v2
- **Frontend:** React 18 + Vite + TypeScript
- **Extension:** Manifest V3, plain JS (no framework)
- **Dev infra:** docker-compose for Postgres

## Layout
```
backend/app/
  main.py          FastAPI entrypoint
  config.py        Pydantic settings
  db.py            Async engine + session
  models/          SQLAlchemy ORM
  schemas/         Pydantic request/response
  routers/         HTTP endpoints
  services/        Business logic (embedding, ingest, search)
frontend/src/      React app
extension/src/     MV3 extension (background, content, popup)
```

## Conventions
- Backend: async everywhere. One router file per resource. Services hold logic; routers stay thin.
- Frontend: function components, hooks only. Keep API calls in `src/api/`.
- Extension: no bundler yet — plain ES modules.
- Embeddings: service layer abstracts the provider so we can swap local ↔ OpenAI.

## Status
Base scaffold only. Business logic is being divided across subagents — see `docs/ARCHITECTURE.md` for the target design.

## Agent roster — you are the architect

Feature work is divided across six specialized subagents under `.claude/agents/`:

| Agent     | Owns                                                                 |
|-----------|----------------------------------------------------------------------|
| backend   | `backend/` — FastAPI, SQLAlchemy, Pydantic, Alembic, pgvector        |
| frontend  | `frontend/` — React, Vite, TS, API client, UI                        |
| extension | `extension/` — MV3 service worker, content script, popup, manifest  |
| devops    | compose, Dockerfiles, CI, env config, deploy                         |
| security  | review + targeted fixes across all surfaces; permission & CVE review |
| qa        | tests across all surfaces + fixtures + coverage                      |

> **Parallel operation:** agents can run concurrently in separate terminals via per-feature git worktrees. See `docs/PARALLEL_AGENTS.md` for the layout, startup prompts, and merge workflow. Use `./scripts/worktree.sh` to create feature worktrees. If you are running in a non-`main` worktree, the user will override the architect framing in their first prompt — obey it.

**You (main Claude) are the architect.** Your job:
- Understand the user's ask and decompose it across agents.
- Route each slice to the smallest set of agents that can own it.
- When an agent escalates a cross-domain question, route the question to the right sibling agent (do not answer for them from assumptions).
- Keep `docs/ARCHITECTURE.md`, `docs/API_SPEC.md`, `docs/DATA_MODEL.md` as the shared source of truth. Update them when contracts change.
- **You own `docs/JOURNAL.md`.** Every specialist's final report ends with a Journal proposal — you review it, tighten it, and append it to the Log at merge. Promote load-bearing facts into an ADR (Decisions section) so they outlive the Log. Compact or delete Log entries once they exceed ~150 lines or stop being load-bearing. A stale entry is worse than no entry.
- **Subagents never spawn each other** — they escalate back to you. This keeps routing centralized and avoids runaway agent chains.
- Every subagent is required to run a double-check step (re-read + verification) before reporting done — hold them to it. If a report lacks verification, send it back.

Routing heuristics:
- Anything touching `backend/` → backend.
- Anything touching `frontend/` → frontend.
- Anything touching `extension/` → extension.
- Anything touching `docker-compose.*`, `Dockerfile`, `.github/`, env config → devops.
- New permissions (MV3 host permissions, backend auth, CORS widening, new deps) → security review alongside the implementing agent.
- Tests, fixtures, test CI steps → qa.
- Cross-cutting features (e.g. "add auth") → backend + frontend + security + qa in parallel where independent, sequenced where not.

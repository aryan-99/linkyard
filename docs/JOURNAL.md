# Linkyard Journal

> **Why this file exists.** Compact shared memory for every agent — the architect and every specialist in every worktree. Read this at session start instead of re-reading every doc or re-exploring the codebase. Cross-session history lives here so we don't burn tokens re-deriving it each time.

## How to use this file

**Reading (every agent, every session start):**
Read the top three sections — **Current state**, **Decisions**, and the top of the **Log** — before doing anything else. That's usually enough orientation. Only drop into `ARCHITECTURE.md` / `API_SPEC.md` / `DATA_MODEL.md` or the code itself when you need detail the journal doesn't carry.

**Writing (architect only):**
Specialist agents running in feature worktrees do **not** edit this file directly — it's shared, so concurrent edits would conflict. Instead, every specialist's final report includes a **Journal proposal**: a one-entry draft the architect reviews and appends at merge time. Example:

> **Journal proposal:** `2026-04-11 — links-crud (backend): Added POST /links and GET /links with URL normalization via urllib. Alembic migration 0001 enables pgvector and creates links table. Gotcha: HttpUrl rejects schemeless URLs — frontend must normalize before posting.`

If a change is load-bearing enough to shape future work (API contract, stack choice, naming convention, security boundary), the architect also adds or amends an **ADR** in the Decisions section.

**Compaction (architect responsibility):**
When the Log exceeds ~150 lines, summarize or delete older entries. Promote anything still load-bearing into an ADR. A stale entry is worse than no entry — it misleads future sessions.

---

## Current state

- **Phase:** Base scaffold. No business logic shipped. No migrations yet. No real tests.
- **Runnable:** Backend boots `/healthz`, frontend renders a placeholder page, extension can be sideloaded but has no backend endpoint to save to.
- **In flight:** None — no feature worktrees created yet.
- **Next logical slice:** backend `POST /links` + `GET /links` + Alembic initial migration (enables pgvector, creates `links` table), then frontend API client + list page, then extension wiring.

---

## Decisions

High-level "why" for choices that shape the codebase. Newest first. An ADR is stable once written — supersede by adding a new one; don't edit historical ADRs.

### ADR-003 (2026-04-10): Worktree-per-feature-per-agent parallel layout
**Context:** Multiple terminals running specialized agents must work without stomping on each other's files.
**Decision:** One git worktree per feature per agent. Branches named `<agent>/<feature>`. Helper script at `scripts/worktree.sh`. See `docs/PARALLEL_AGENTS.md` for full operating model.
**Consequences:** Shared files (docs, root configs, `docker-compose.dev.yml`, `.github/`, this journal) are **architect-only**. Specialists propose changes to shared files in their final reports; the architect applies them at merge. Subagents never spawn each other — all cross-domain routing goes through the architect.

### ADR-002 (2026-04-10): Pluggable embedding provider
**Context:** We want to ship with a fake embedder (no model required) and swap to a local sentence-transformers model or OpenAI later without touching routers or services that use embeddings.
**Decision:** `EmbeddingProvider` interface in `backend/app/services/embedding/` (TBD). Implementations: `StubProvider` (deterministic hash → vector, for tests and dev), `LocalProvider` (sentence-transformers), `OpenAIProvider` (`text-embedding-3-small`). Selection via `EMBEDDING_PROVIDER` env var.
**Consequences:** Embedding dimension (`EMBEDDING_DIM`) must match the provider; changing provider means a migration + re-embed. Routers and search services depend on the interface, not a concrete provider — never `import openai` outside the `openai` provider module.

### ADR-001 (2026-04-10): Async SQLAlchemy everywhere on the backend
**Context:** pgvector queries plus `httpx` metadata fetches both benefit from concurrency. Mixing sync and async sessions is a well-known footgun.
**Decision:** SQLAlchemy 2.x async throughout. All routes and services are `async def`. `asyncpg` driver.
**Consequences:** Alembic itself isn't async — it uses `DATABASE_URL_SYNC` via the `psycopg` driver. Test fixtures must use `pytest-asyncio`. No sync DB access is permitted anywhere in `backend/app/`.

---

## Log

Newest first. Each entry ≤10 lines. Older than ~2 weeks or no longer load-bearing: compact or delete. Promote anything that should outlive the Log into an ADR.

### 2026-04-10 — Project rebuilt from scratch (architect)
Prior Linkyard session was lost to technical issues; rebuilt fresh in this directory. Created scaffold: backend (FastAPI skeleton, `main.py`/`config.py`/`db.py`, empty `models`/`schemas`/`routers`/`services` packages, `requirements.txt`, `.env.example`), frontend (React/Vite/TS skeleton with placeholder `App.tsx`), extension (MV3 skeleton with `background.js`/`content.js`/popup), `docker-compose.dev.yml` for Postgres 16 + pgvector, six agent configs under `.claude/agents/`, per-feature worktree tooling at `scripts/worktree.sh`, `docs/PARALLEL_AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/API_SPEC.md`, `docs/DATA_MODEL.md`, and this journal.
**No business logic yet** — no models, no routers beyond `/healthz`, no migrations, no embedding provider implementation, no real tests.
**Gotchas:** `.claude/settings.local.json` must stay gitignored (user-local). Git identity is not pre-configured — first contributor sets it per-repo with `git config user.email / user.name` (no `--global`). The architect (main Claude in the main worktree) is the only writer for this journal and other shared files.

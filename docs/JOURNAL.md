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

- **Phase:** Stage 5 in progress. Live test done. Search embedding quality improved.
- **Runnable:** Backend serves `/links` CRUD + `GET /links/search?q=` + `GET/PUT /settings` + `POST /settings/reembed` + `/healthz`. Settings endpoints require `Authorization: Bearer <token>` when `ADMIN_TOKEN` is set in `.env`. Frontend has Links, Search, and Settings tabs; Settings page has Admin Token section at top. Extension popup saves current tab; gear icon opens options page to configure backend URL. DB needs `docker compose -f docker-compose.dev.yml up -d` then `alembic upgrade head` (from `backend/`) before first use. Load extension via `chrome://extensions > Load unpacked > extension/`. Run `pip install -r requirements.txt` to install `sentence-transformers` for local semantic search.
- **Docs:** `HOW_IT_WORKS.md` added — conceptual design guide.
- **In flight:** QoL pass (search threshold + meta_description in embeddings + HNSW index), then OpenAI provider, then Docker packaging + public release.
- **Next logical slice:** QoL pass — see deferred search improvements in log entry below. Then OpenAI path (1536-dim migration + OpenAIProvider unlock). Encrypt API key at rest remains a pre-prod blocker.

---

## Decisions

High-level "why" for choices that shape the codebase. Newest first. An ADR is stable once written — supersede by adding a new one; don't edit historical ADRs.

### ADR-003 (2026-04-10): Worktree-per-feature-per-agent parallel layout
**Context:** Multiple terminals running specialized agents must work without stomping on each other's files.
**Decision:** One git worktree per feature per agent. Branches named `<agent>/<feature>`. Helper script at `scripts/worktree.sh`. See `docs/PARALLEL_AGENTS.md` for full operating model.
**Consequences:** Shared files (docs, root configs, `docker-compose.dev.yml`, `.github/`, this journal) are **architect-only**. Specialists propose changes to shared files in their final reports; the architect applies them at merge. Subagents never spawn each other — all cross-domain routing goes through the architect.

### ADR-002 (2026-04-10): Pluggable embedding provider
**Context:** We want to ship with a fake embedder (no model required) and swap to a local sentence-transformers model or OpenAI later without touching routers or services that use embeddings.
**Decision:** `EmbeddingProvider` interface in `backend/app/services/embedding/base.py`. Implementations: `StubProvider` (deterministic hash → unit-vector, shipped), `LocalProvider` (sentence-transformers, future), `OpenAIProvider` (`text-embedding-3-small`, future). Factory in `factory.py`. Selection via `EMBEDDING_PROVIDER` env var.
**Consequences:** Embedding dimension (`EMBEDDING_DIM`) must match the provider; changing provider means a migration + re-embed. Routers and search services depend on the interface, not a concrete provider — never `import openai` outside the `openai` provider module.

### ADR-001 (2026-04-10): Async SQLAlchemy everywhere on the backend
**Context:** pgvector queries plus `httpx` metadata fetches both benefit from concurrency. Mixing sync and async sessions is a well-known footgun.
**Decision:** SQLAlchemy 2.x async throughout. All routes and services are `async def`. `asyncpg` driver.
**Consequences:** Alembic itself isn't async — it uses `DATABASE_URL_SYNC` via the `psycopg` driver. Test fixtures must use `pytest-asyncio`. No sync DB access is permitted anywhere in `backend/app/`.

---

## Log

Newest first. Each entry ≤10 lines. Older than ~2 weeks or no longer load-bearing: compact or delete. Promote anything that should outlive the Log into an ADR.

### 2026-04-29 — Live test + search embedding improvements (architect)
Live test completed. Two search fixes shipped: (1) negative match % clamped to 0 in `SearchPage.tsx` (cosine distance can exceed 1 for non-orthogonal vectors); (2) embedding model swapped from `all-MiniLM-L6-v2` → `multi-qa-MiniLM-L6-cos-v1` (retrieval-trained, same 384-dim, no migration); (3) URL removed from `text_for_embedding` — was adding noise with no semantic value. After restart, re-embed all links via Settings.
**Deferred search improvements (QoL pass):** (a) add `meta_description` to `text_for_embedding` as fallback when snippet is empty; (b) score threshold ~0.30 to suppress weak matches; (c) HNSW index on `embedding` column via Alembic migration. None are blocking — save for QoL pass.
**Release checklist (in order):** QoL pass → OpenAI provider (1536-dim migration) → encrypt API key at rest → CORS pin → Docker packaging → README → secrets audit → tag + push.

### 2026-04-29 — Static bearer-token auth on settings endpoints (backend + frontend + qa)
`ADMIN_TOKEN` env var added to `config.py` (str | None, default None — auth disabled when unset). `AdminTokenDep` in `deps.py` uses `HTTPBearer(auto_error=False)`: pass-through when token unset, HTTP 401 on wrong/missing token when set. Applied via `dependencies=[AdminTokenDep]` to all three settings routes (`GET/PUT /settings`, `POST /settings/reembed`). `/links` and `/healthz` unprotected by design. Frontend: `setAuthToken()` added to `client.ts`; `request<T>` sends `Authorization: Bearer` header only when token is non-null. Settings page gains "Admin Token" section at top — password input, Save token button, persisted to `localStorage` under `linkyard_admin_token`. `main.tsx` bootstraps token from localStorage before first render. QA: `test_settings.py` updated with `patch_admin_token` autouse fixture + auth headers on all 12 existing tests + 2 new 401 tests (14 total). Pre-prod: set `ADMIN_TOKEN` to a random secret in `.env`.

### 2026-04-28 — Simplify pass (architect)
Dedup: `request<T>` + `BASE` extracted to `frontend/src/api/client.ts`; `SessionDep` centralised in `deps.py`; `text_for_embedding()` extracted to `ingest.py` and shared with `settings.py`. Efficiency: reembed N+1 eliminated (single `select(Link)`), embed calls parallelised with `asyncio.gather`, `httpx.AsyncClient` moved to `OpenAIProvider.__init__`. Bug: `asyncio.get_event_loop()` → `get_running_loop()` (deprecated in 3.10+). Extension: `showStatus()` helper added to `popup.js`; URL protocol check in `options.js` collapsed into `new URL()` try/catch. 26 tests still passing.

### 2026-04-28 — Extension options page (extension agent)
Added `src/options/options.html` + `options.js` for configuring backend API base URL via `chrome.storage.sync`. Gear button (⚙) in popup header opens options via `chrome.runtime.openOptionsPage()`. URL validated (must be http/https, trailing slash stripped). `host_permissions` expanded from `localhost:8000` only to all `localhost/*` and `127.0.0.1/*` ports (http + https) to support arbitrary local ports. `manifest.json` gains `options_ui` declaration. No new Chrome API permissions.

### 2026-04-28 — Settings + provider switching (backend + frontend + qa + security)
Backend: `AppSettings` table (migration 0002, always id=1 row) stores active provider + OpenAI API key. `GET/PUT /settings` + `POST /settings/reembed` endpoints. `SettingsResponse` exposes `has_openai_key: bool` only — key never leaves the DB. `OpenAIProvider` implemented but locked out via `SettingsUpdate` validator (422 until 1536-dim migration). `ingest_link` / `search_links` now take provider as a parameter; `get_active_provider` dep reads DB row, falls back to "local". Config default changed "stub" → "local". Frontend: `SettingsPage` with provider dropdown (OpenAI disabled/"coming soon"), masked API key field with clear button, re-embed section with result feedback; Settings tab added to nav.
QA: 12 integration tests in `tests/test_settings.py` (CRUD, key never-leaked in GET+PUT, clear-by-empty-string, null=no-change, reembed count, provider dependency end-to-end). Tests need real Postgres — run `alembic upgrade head` then `pytest`.
Security: 0 critical/high, 3 medium accepted or deferred (no-auth on settings — OK for local; HTTPStatusError key leak in OpenAIProvider — **fixed now**; reembed no-cap — warning log added). 1 low fixed (max_length=200 on API key). Pre-prod blockers: add auth, encrypt key at rest. `sentence-transformers` pinned to `3.*`.

### 2026-04-28 — LocalProvider: local semantic embeddings (backend agent)
Added `LocalProvider` in `backend/app/services/embedding/local.py` using `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim, no API key). Lazy-loads model on first `embed()` call; blocking `encode()` dispatched via `run_in_executor` so the async loop is never stalled. `factory.py` updated with `"local"` branch (lazy import). `config.py` gains `local_embedding_model` setting. `requirements.txt` adds `sentence-transformers`. Stub path unchanged. **To activate:** set `EMBEDDING_PROVIDER=local` in `.env` and restart — no migration needed since dim stays 384. First request downloads the model (~90 MB).

### 2026-04-27 — Extension wiring + security hardening (architect)
MV3 popup implemented: popup.js reads tab.url/tab.title via `chrome.tabs.query`, displays both, sends `SAVE_LINK` to background.js which POSTs `{url, title, source:"extension"}` to `POST /links`. Swapped `scripting` permission for `tabs` — reduced permission footprint. Guards against non-http(s) schemes via positive allowlist. Backend: `allow_origin_regex` added to CORSMiddleware for `chrome-extension://[a-p]{32}` (tightened from `.*` during security review); configurable via `CORS_ORIGIN_REGEX` env var — pin to specific extension ID in prod. Security review: 2 medium findings fixed (popup scheme guard, CORS regex precision); no XSS surface (textContent only throughout popup).
**Devops note:** Set `CORS_ORIGIN_REGEX=chrome-extension://<published-id>` in prod environment before go-live.

### 2026-04-19 — UI polish + dark mode (frontend agent)
Added `index.css` with CSS custom property token set (light + dark via `prefers-color-scheme`). Replaced all hardcoded hex colours across `App`, `LinksPage`, `SearchPage`, `AddLinkForm` with `var(--color-*)` references. Nav refactored to slim top-bar with underline tab indicator. Link/search rows gain hover highlight; delete button hidden until hover. Score badge is now an accent-tint pill. Focus rings via global CSS. No new deps; `tsc --noEmit` clean.

### 2026-04-19 — QA: integration test suite (qa agent)
14 tests in `backend/tests/test_links.py` + `conftest.py` covering full CRUD, URL validation, embedding persistence, and search (empty DB, score range, missing/empty `q`). All pass against real Postgres. `pytest.ini` added with `asyncio_mode=auto`. Infrastructure note: pytest-asyncio 0.24 requires all async fixtures to be function-scoped when asyncpg is involved — cross-scope loop mismatch; fixed via `asyncio_default_fixture_loop_scope=function`.

### 2026-04-19 — Stage 2: semantic search (architect)
Backend: `services/search.py` — embeds query via provider, cosine distance (`<=>`) pgvector query, returns ranked `(Link, score)` pairs. `GET /links/search?q=` endpoint added to links router **before** `/{link_id}` to avoid path collision. New schemas: `SearchResultItem` (LinkResponse + score float), `SearchResultsResponse`.
Frontend: `api/search.ts` client, `SearchPage.tsx` (debounced 300ms live search, match % badge, loading/empty states), `App.tsx` updated with Links/Search tab nav.
**Note:** Search ranks by cosine similarity against the StubProvider's hash-based embeddings — results will be semantically meaningful only once a real embedding provider is wired in.

### 2026-04-17 — Stage 1: links CRUD + frontend (architect)
Backend: `Link` ORM model, Pydantic schemas (`LinkCreate/Update/Response/Detail/List`), Alembic setup + migration `0001_initial` (enables `pgvector`, creates `links` table + `idx_links_created_at`), `StubProvider` embedding service, `ingest_link` service (URL normalization via `urllib.parse`), full CRUD router wired into `main.py`.
Frontend: `src/api/links.ts` client (fetch wrapper), `AddLinkForm` component, `LinksPage` (list + paginate + delete), `App.tsx` updated.
**Gotcha:** No Python package manager in the dev shell — Alembic files were written manually rather than via `alembic init` / `alembic revision`. Run `alembic upgrade head` from `backend/` inside a venv or Docker container where deps are installed.
**Gotcha:** Subagents lacked Write/Bash permissions — architect implemented directly.

### 2026-04-10 — Project rebuilt from scratch (architect)
Prior Linkyard session was lost to technical issues; rebuilt fresh in this directory. Created scaffold: backend (FastAPI skeleton, `main.py`/`config.py`/`db.py`, empty `models`/`schemas`/`routers`/`services` packages, `requirements.txt`, `.env.example`), frontend (React/Vite/TS skeleton with placeholder `App.tsx`), extension (MV3 skeleton with `background.js`/`content.js`/popup), `docker-compose.dev.yml` for Postgres 16 + pgvector, six agent configs under `.claude/agents/`, per-feature worktree tooling at `scripts/worktree.sh`, `docs/PARALLEL_AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/API_SPEC.md`, `docs/DATA_MODEL.md`, and this journal.
**No business logic yet** — no models, no routers beyond `/healthz`, no migrations, no embedding provider implementation, no real tests.
**Gotchas:** `.claude/settings.local.json` must stay gitignored (user-local). Git identity is not pre-configured — first contributor sets it per-repo with `git config user.email / user.name` (no `--global`). The architect (main Claude in the main worktree) is the only writer for this journal and other shared files.

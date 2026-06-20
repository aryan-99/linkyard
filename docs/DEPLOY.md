# Linkyard — Deploy Guide

> **Status: TODO — hosting platform not yet chosen.**
>
> The previous Fly.io deploy path was removed: Fly discontinued its permanent
> free tier for new accounts (now pay-as-you-go, ~$5–15/mo for this 3-piece
> stack), so it's no longer worth it for a portfolio demo.

## Target architecture

Linkyard is three deployable surfaces:

| Surface  | What it is                          | Needs                          |
|----------|-------------------------------------|--------------------------------|
| Backend  | FastAPI app (`backend/`)            | Python 3.12 runtime, stateless |
| Frontend | Vite/React SPA (`frontend/`)        | Static file host (built bundle)|
| Database | Postgres 16 **with pgvector**       | Persistent, pgvector extension |

The build artifacts already exist: `backend/Dockerfile` packages the API, and
the frontend builds to static files via `npm run build` (`VITE_API_BASE_URL`
is baked in at build time).

## Candidate free platforms (verified June 2026)

Research on genuinely-free options (no credit card, permanent — not trial):

- **Database — [Neon](https://neon.com/pricing):** permanent free tier, no card,
  pgvector supported, 0.5 GB storage, scale-to-zero after 5 min (auto-resumes on
  next query). Strongest free Postgres+pgvector option.
- **Backend — [Render](https://render.com/docs/free) web service:** free, no card,
  750 instance-hrs/mo, spins down after 15 min idle (~1 min cold start).
  ⚠️ Do **not** use Render's own free Postgres — it is deleted 30 days after
  creation. Pair Render compute with Neon for the DB.
- **Frontend — static host:** Render Static Sites, Vercel, Netlify, or
  Cloudflare Pages — all genuinely free for a static SPA.

> Koyeb (permanent free, pgvector, scale-to-zero) is a viable alternative for
> backend+DB but may require a credit card for human verification.

## When a platform is chosen

A full step-by-step walkthrough will be written here. The deploy will need to:

1. Provision Postgres with pgvector; run `CREATE EXTENSION IF NOT EXISTS vector;`.
2. Set backend env: `DATABASE_URL` (asyncpg) + `DATABASE_URL_SYNC` (psycopg),
   `ADMIN_TOKEN`, `CORS_ORIGIN_REGEX`, `EMBEDDING_PROVIDER`, `EMBEDDING_DIM`.
   On platforms without `CAP_NET_ADMIN`, set `EGRESS_FIREWALL=false` (the
   app-level SSRF guards in `backend/app/services/fetch.py` remain the primary
   defence — see that file and `backend/Dockerfile`).
3. Run `alembic upgrade head` against the database.
4. Optionally boot once with `DEMO_SEED=true` to pre-load example links, then
   set it back to `false` so restarts don't re-seed.
5. Build + deploy the frontend with `VITE_API_BASE_URL` pointed at the backend.
6. Pin `CORS_ORIGIN_REGEX` to the deployed frontend URL once known, e.g.
   `https://<frontend-host>|chrome-extension://[a-p]{32}`.

`docker-compose.prod.yml` remains a working self-hosted path independent of any
managed platform.

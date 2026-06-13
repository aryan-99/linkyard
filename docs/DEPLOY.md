# Linkyard — Fly.io Deploy Guide

Step-by-step walkthrough from a clean Fly account to a live demo.
All commands are run from the **repo root** unless noted otherwise.

---

## Prerequisites

- [flyctl](https://fly.io/docs/hands-on/install-flyctl/) installed and on `$PATH`.
- Node 20+ and Python 3.12+ available locally (for building/migrating).
- The repo is cloned and `pip install -r backend/requirements.txt` has been run.

---

## 1. Authenticate

```bash
fly auth login
```

---

## 2. Create the backend app

```bash
fly apps create linkyard-backend --org personal
```

> If `linkyard-backend` is already taken on Fly, choose another name and update
> `fly/backend/fly.toml` (`app = "..."`) to match.

---

## 3. Provision Postgres with pgvector

Fly's managed Postgres image ships without pgvector by default.
Use the pgvector-enabled image instead via a standalone VM:

```bash
fly postgres create \
  --name linkyard-db \
  --region iad \
  --vm-size shared-cpu-1x \
  --volume-size 1 \
  --image-ref ghcr.io/baosystems/postgis:16-3.4
```

> **Note on pgvector:** `ghcr.io/baosystems/postgis` bundles both PostGIS and
> pgvector on pg16.  After attaching (step 4) you still need to run
> `CREATE EXTENSION vector;` manually — see step 6.
>
> Alternative: use the official `pgvector/pgvector:pg16` image by deploying a
> Fly Machine directly, but the managed `fly postgres` path is simpler for a
> portfolio demo.

---

## 4. Attach Postgres to the backend app

```bash
fly postgres attach linkyard-db --app linkyard-backend
```

This injects `DATABASE_URL` (in `postgresql://` format) into the backend app's
secrets automatically.  However, the app needs **two** URL formats:

- `DATABASE_URL` — asyncpg driver (`postgresql+asyncpg://...`) for SQLAlchemy
- `DATABASE_URL_SYNC` — psycopg driver (`postgresql://...`) for Alembic

Fly's auto-injected `DATABASE_URL` uses plain `postgresql://` (which is correct
for Alembic/psycopg).  You need to create the asyncpg variant manually:

```bash
# Copy the value fly printed after attach, then:
fly secrets set \
  DATABASE_URL="postgresql+asyncpg://<user>:<pass>@<host>/<db>?sslmode=require" \
  DATABASE_URL_SYNC="postgresql://<user>:<pass>@<host>/<db>?sslmode=require" \
  --app linkyard-backend
```

> Tip: `fly postgres attach` prints the connection string.  The asyncpg URL
> is identical except the scheme is `postgresql+asyncpg` instead of
> `postgresql`.

---

## 5. Set remaining backend secrets

```bash
fly secrets set \
  ADMIN_TOKEN="$(openssl rand -hex 32)" \
  --app linkyard-backend
```

`CORS_ORIGIN_REGEX` is set as a plain env var (not a secret) in
`fly/backend/fly.toml`.  Leave it as `__PLACEHOLDER__` for now — you will fill
it in after you know the frontend URL (step 10).

---

## 6. Enable pgvector extension

SSH into the Postgres VM and run `CREATE EXTENSION`:

```bash
fly ssh console --app linkyard-db
```

Inside the console:

```bash
# Connect to the linkyard database
psql -U postgres
\c linkyard
CREATE EXTENSION IF NOT EXISTS vector;
\q
exit
```

---

## 7. Deploy the backend

From the **repo root** (the Dockerfile build context uses `../scripts/`):

```bash
fly deploy \
  --config fly/backend/fly.toml \
  --dockerfile backend/Dockerfile
```

Fly will build the image, push it, and start the Machine.
The healthcheck (`GET /healthz`) must return 200 before traffic is routed.

---

## 8. Run Alembic migrations

Once the backend Machine is running:

```bash
fly ssh console --app linkyard-backend
```

Inside:

```bash
cd /app
alembic upgrade head
exit
```

This creates all tables, adds the HNSW index on `links.embedding`, etc.

---

## 9. Create and deploy the frontend

```bash
fly apps create linkyard-frontend --org personal
```

Deploy the Vite SPA (VITE_API_BASE_URL is baked into the bundle at build time):

```bash
fly deploy \
  --config fly/frontend/fly.toml \
  --dockerfile fly/frontend/Dockerfile \
  --build-arg VITE_API_BASE_URL=https://linkyard-backend.fly.dev
```

> If you used a different backend app name in step 2, replace
> `linkyard-backend.fly.dev` with your actual backend hostname.

---

## 10. Pin CORS to the frontend URL

Find the frontend's public URL:

```bash
fly status --app linkyard-frontend
# or:
fly info --app linkyard-frontend
# Hostname will be something like: linkyard-frontend.fly.dev
```

Update the backend's CORS env var so it accepts requests from **both** the
hosted frontend and any load-unpacked extension install (load-unpacked IDs
are derived from each user's directory path, so we use a wildcard rather
than pinning a single ID — see CLAUDE notes for the trade-off):

```bash
fly secrets set \
  CORS_ORIGIN_REGEX="https://linkyard-frontend\\.fly\\.dev|chrome-extension://[a-p]{32}" \
  --app linkyard-backend
```

> Replace `linkyard-frontend` if you used a different app name in step 9.
> Starlette's CORS middleware uses `fullmatch`, so the two alternatives are
> bounded — no anchors needed.

Restart the backend to pick up the new env var:

```bash
fly machines restart --app linkyard-backend
```

---

## 11. Verify end-to-end

1. Open `https://linkyard-frontend.fly.dev` in your browser.
2. Add a link — the backend should accept it and return a card.
3. Run a semantic search — results should appear (stub embeddings or local model).
4. Check backend logs for any errors:

```bash
fly logs --app linkyard-backend
```

---

## 12. Disable demo seed after first boot

The backend boots with `DEMO_SEED=true` (set in `fly/backend/fly.toml`), which
(once the backend agent ships the seed pipeline) pre-populates example links on
first startup.  After the data is seeded, disable it so restarts don't re-seed:

```bash
# Edit fly/backend/fly.toml — change DEMO_SEED = "true" to "false"
# then redeploy:
fly deploy --config fly/backend/fly.toml --dockerfile backend/Dockerfile
```

Alternatively, override it with a secret (secrets take precedence over [env]):

```bash
fly secrets set DEMO_SEED=false --app linkyard-backend
```

---

## CAP_NET_ADMIN note

`backend/Dockerfile` normally runs `scripts/block_egress_private.sh` (iptables
rules that block outbound TCP to RFC-1918 ranges) before starting uvicorn.
This is the production `docker-compose.prod.yml` path, which grants
`cap_add: NET_ADMIN` to the container.

**Fly Machines do not grant CAP_NET_ADMIN.** The script would abort with
`"Operation not permitted"` and the container would exit before uvicorn starts.

Decision: the Dockerfile CMD checks the `EGRESS_FIREWALL` env var.

- `EGRESS_FIREWALL=true` (default) — runs the iptables script.  Used by
  `docker-compose.prod.yml`.
- `EGRESS_FIREWALL=false` — skips iptables entirely.  Set in
  `fly/backend/fly.toml`.

The application-level SSRF guards remain active on Fly regardless:

- IP blocklist check on initial DNS resolve (RFC-1918, loopback, link-local).
- Per-redirect hook reading `Location` header to catch DNS-rebinding.
- 5 MB streaming cap + content-type guard.

These are implemented in `backend/app/services/fetch.py` and are the primary
SSRF defence.  The iptables layer is defence-in-depth — its absence on Fly is
an accepted trade-off for a portfolio demo.  For a security-sensitive production
deployment, use a dedicated egress proxy or Fly's built-in network policies
instead.

---

## docker-compose.prod.yml is unchanged

The Fly deploy is additive.  `docker-compose.prod.yml` continues to work as
before: `EGRESS_FIREWALL` defaults to `true` in the Dockerfile, and
`cap_add: NET_ADMIN` is already set in the compose file.

---

## Quick reference: app names and URLs

| Surface  | Fly app name          | Public URL                              |
|----------|-----------------------|-----------------------------------------|
| Backend  | `linkyard-backend`    | `https://linkyard-backend.fly.dev`      |
| Frontend | `linkyard-frontend`   | `https://linkyard-frontend.fly.dev`     |
| Postgres | `linkyard-db`         | internal only (Fly private network)     |

Adjust app names if the defaults are taken on Fly.

---

## Rollback

```bash
# List recent releases
fly releases --app linkyard-backend

# Roll back to a specific version
fly deploy --image <image-ref> --app linkyard-backend
```

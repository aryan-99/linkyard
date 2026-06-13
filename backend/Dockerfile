# =============================================================================
# backend/Dockerfile — Linkyard backend packaging stub
# =============================================================================
# STATUS: packaging stub — not yet used in docker-compose.dev.yml (which
# mounts source directly for hot-reload).  Intended for production / CI builds.
#
# TODO: set CORS_ORIGIN_REGEX=chrome-extension://<extension-id> in the
#       environment (compose override, k8s secret, or CI env var) before
#       go-live so the CORS allowlist is pinned to the published extension ID.
# =============================================================================

FROM python:3.12-slim

# ── system packages ───────────────────────────────────────────────────────────
# iptables / ip6tables are required by scripts/block_egress_private.sh
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        iptables \
    && rm -rf /var/lib/apt/lists/*

# ── python dependencies ───────────────────────────────────────────────────────
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── application source ────────────────────────────────────────────────────────
COPY backend/app/ ./app/
COPY backend/alembic.ini ./
COPY backend/alembic/ ./alembic/

# ── egress firewall script ────────────────────────────────────────────────────
COPY scripts/block_egress_private.sh /usr/local/bin/block_egress_private.sh
RUN chmod +x /usr/local/bin/block_egress_private.sh

# ── runtime ───────────────────────────────────────────────────────────────────
EXPOSE 8000

# TODO: drop to non-root user after iptables — requires gosu or init container
# pattern.  iptables (called first in CMD) needs root/CAP_NET_ADMIN; uvicorn
# should then exec as an unprivileged user via `gosu app uvicorn ...`.
# Until gosu is added, the process runs as root inside the container.
# CAP_NET_ADMIN is scoped in compose (cap_add) so blast radius is limited.
# EGRESS_FIREWALL controls whether block_egress_private.sh runs at startup.
#
#   EGRESS_FIREWALL=true  (default / docker-compose.prod.yml path)
#     Runs iptables rules before uvicorn.  Requires CAP_NET_ADMIN on the host.
#     docker-compose.prod.yml already sets `cap_add: NET_ADMIN`.
#
#   EGRESS_FIREWALL=false (Fly.io path)
#     Skips iptables entirely — Fly Machines do not grant CAP_NET_ADMIN so
#     the script would abort with "Operation not permitted".
#     Application-level SSRF guards (IP blocklist + redirect hook in
#     backend/app/services/fetch.py) remain active as the primary defence.
#     See docs/DEPLOY.md §CAP_NET_ADMIN note for full rationale.
#
# Default is "true" so existing docker-compose.prod.yml behaviour is unchanged.
ENV EGRESS_FIREWALL=true

CMD ["/bin/sh", "-c", \
  "if [ \"$EGRESS_FIREWALL\" = \"true\" ]; then /usr/local/bin/block_egress_private.sh; fi \
   && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]

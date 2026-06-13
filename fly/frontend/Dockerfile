# =============================================================================
# fly/frontend/Dockerfile — Linkyard frontend (Vite SPA → nginx-alpine)
# =============================================================================
# Multi-stage:
#   Stage 1 (build) — node:20-alpine builds the Vite bundle.
#   Stage 2 (serve) — nginx:1.27-alpine serves the static dist/.
#
# VITE_API_BASE_URL is baked at build time (Vite replaces it at bundle time).
# Pass it as a --build-arg when running fly deploy:
#
#   fly deploy --config fly/frontend/fly.toml \
#     --build-arg VITE_API_BASE_URL=https://linkyard-backend.fly.dev
# =============================================================================

# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS build

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

WORKDIR /app

# Install dependencies first (layer caching)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ── Stage 2: serve ────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS serve

# Remove the default nginx site
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from stage 1
COPY --from=build /app/dist /usr/share/nginx/html

# SPA fallback: all paths serve index.html so React Router handles routing
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    # Health check endpoint for Fly\n\
    location /healthz {\n\
        access_log off;\n\
        return 200 "ok";\n\
        add_header Content-Type text/plain;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

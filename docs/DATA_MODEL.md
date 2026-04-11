# Linkyard Data Model

## `links`
| column            | type          | notes                                    |
|-------------------|---------------|------------------------------------------|
| id                | uuid PK       | `gen_random_uuid()`                      |
| url               | text NOT NULL | normalized, unique per user (future)     |
| title             | text          |                                          |
| snippet           | text          | short user-provided or scraped summary   |
| meta_description  | text          | scraped `<meta name="description">`      |
| source            | text NOT NULL | `extension` \| `web` \| `api`            |
| embedding         | vector(N)     | N matches provider; nullable until ready |
| created_at        | timestamptz   | default now()                            |
| updated_at        | timestamptz   | default now()                            |

Indexes:
- `idx_links_created_at` (btree, DESC)
- `idx_links_embedding` (ivfflat, `vector_cosine_ops`, lists=100) — added once rows exist
- `uniq_links_url` (unique btree on normalized url) — future, once auth lands

## `tags` (future)
Simple join table, deferred until single-user flow works.

## Migrations
Alembic. First migration: enable `pgvector` extension, create `links` table, create btree index on `created_at`. ivfflat index added in a later migration once there's enough data.

## Embedding dimension
Driven by `EMBEDDING_DIM` env var. Default 384 (sentence-transformers MiniLM) or 1536 (OpenAI). Changing dim requires a migration + re-embed.

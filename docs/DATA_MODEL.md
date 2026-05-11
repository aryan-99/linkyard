# Linkyard Data Model

## `links`
| column            | type          | notes                                    |
|-------------------|---------------|------------------------------------------|
| id                | uuid PK       | `gen_random_uuid()`                      |
| url               | text NOT NULL | normalized, unique per user (future)     |
| title             | text          |                                          |
| snippet           | text          | short user-provided or scraped summary   |
| meta_description  | text          | scraped `<meta name="description">`      |
| page_body         | text          | scraped visible body text, ≤500 words    |
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

## `app_settings`
| column             | type          | notes                                        |
|--------------------|---------------|----------------------------------------------|
| id                 | int PK        | always 1 (singleton row)                     |
| embedding_provider | text          | `local` \| `stub` \| `openai`               |
| openai_api_key     | text          | nullable; never returned by API              |
| search_threshold   | float         | default 0.30; post-filter on cosine score    |

## Migrations
| # | File | Change |
|---|------|--------|
| 0001 | `0001_initial.py` | Enable pgvector, create `links` table + `idx_links_created_at` |
| 0002 | `0002_app_settings.py` | Create `app_settings` table (singleton row) |
| 0003 | `0003_add_search_threshold.py` | Add `search_threshold` to `app_settings` |
| 0004 | `0004_add_page_body.py` | Add `page_body TEXT` to `links` |

## Embedding dimension
Driven by `EMBEDDING_DIM` env var. Default 384 (sentence-transformers MiniLM) or 1536 (OpenAI). Changing dim requires a migration + re-embed.

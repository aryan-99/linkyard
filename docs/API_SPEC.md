# Linkyard API Spec

Base URL: `http://localhost:8000`
All request/response bodies are JSON. Timestamps are ISO 8601 UTC.

## Auth

Settings endpoints require `Authorization: Bearer <token>` when `ADMIN_TOKEN` is set in the server's `.env`. If `ADMIN_TOKEN` is unset, the header is ignored. All other endpoints are unauthenticated.

---

## Health

### `GET /healthz`
→ `200 { "status": "ok" }`

---

## Links

### `POST /links`
Save a new link. Backend fetches the URL server-side to extract `page_body` and `meta_description` (non-fatal if fetch fails).

Request body:
```json
{
  "url": "https://example.com/article",
  "title": "Optional title",
  "snippet": "Optional user note",
  "meta_description": "Optional (client-supplied wins over server-fetched)",
  "source": "extension | web | api"
}
```
→ `201 LinkDetailResponse`

### `GET /links`
List links, newest first.

Query params: `limit` (default 20, max 100), `offset` (default 0)

→ `200 LinkListResponse`

### `GET /links/search?q=`
Semantic search. Embeds `q`, cosine similarity against all stored embeddings, post-filters by `search_threshold` (set in settings, default 0.30).

Query params: `q` (required), `limit` (default 20), `offset` (default 0)

→ `200 SearchResultsResponse`

### `GET /links/{id}`
→ `200 LinkDetailResponse` | `404`

### `POST /links/{id}/refetch`
Re-fetch page body from the source URL, update `page_body` and re-embed. Non-fatal if fetch fails (stores `null`).

→ `200 LinkDetailResponse` | `404`

### `PATCH /links/{id}`
Partial update. Body fields optional: `title`, `snippet`.

→ `200 LinkResponse`

### `DELETE /links/{id}`
→ `204`

---

## Settings

All settings endpoints require auth (see Auth section).

### `GET /settings`
→ `200 SettingsResponse`

### `PUT /settings`
Update one or more settings fields. All fields optional.

```json
{
  "embedding_provider": "local | stub | openai",
  "openai_api_key": "sk-... (empty string to clear)",
  "search_threshold": 0.30
}
```
→ `200 SettingsResponse`

### `POST /settings/reembed`
Re-embed all links using stored `page_body`, `snippet`, `title`, and `meta_description`. Uses currently active provider.

→ `200 { "reembedded": 42 }`

### `POST /settings/refetch`
Re-fetch page body from source URLs and re-embed. By default targets only links where `page_body IS NULL`; set `force: true` to re-fetch all.

```json
{ "force": false }
```
→ `200 { "refetched": 17 }`

---

## Schemas

### `LinkResponse`
```json
{
  "id": "uuid",
  "url": "string",
  "title": "string | null",
  "snippet": "string | null",
  "page_body_preview": "string | null (first 150 chars of extracted body)",
  "source": "extension | web | api",
  "created_at": "iso8601",
  "updated_at": "iso8601"
}
```

### `LinkDetailResponse`
Extends `LinkResponse` with:
```json
{
  "meta_description": "string | null"
}
```

### `LinkListResponse`
```json
{
  "items": [LinkResponse],
  "pagination": { "limit": 20, "offset": 0, "total": 123 }
}
```

### `SearchResultItem`
Extends `LinkResponse` with:
```json
{ "score": 0.87 }
```

### `SearchResultsResponse`
```json
{
  "items": [SearchResultItem],
  "pagination": { "limit": 20, "offset": 0, "total": 5 }
}
```

### `SettingsResponse`
```json
{
  "embedding_provider": "local | stub | openai",
  "has_openai_key": true,
  "search_threshold": 0.30
}
```

---

## Errors
Standard FastAPI `{"detail": "..."}` shape. `422` for validation errors, `404` for missing resources, `401` for missing/wrong auth token, `500` for unexpected server errors.

# Linkyard API Spec

Base URL: `http://localhost:8000`
All request/response bodies are JSON. Timestamps are ISO 8601 UTC.

## Health

### `GET /healthz`
→ `200 { "status": "ok" }`

## Links

### `POST /links`
Create a new link.

```json
{
  "url": "https://example.com/article",
  "title": "Optional title",
  "snippet": "Optional short description",
  "meta_description": "Optional scraped meta",
  "source": "extension" | "web" | "api"
}
```
→ `201 LinkResponse`

### `GET /links`
List links, newest first. Query params:
- `limit` (default 20, max 100)
- `offset` (default 0)

→ `200 LinkListResponse`

### `GET /links/{id}`
→ `200 LinkDetailResponse` | `404`

### `PATCH /links/{id}`
Partial update. Body fields optional: `title`, `snippet`, `tags`.
→ `200 LinkResponse`

### `DELETE /links/{id}`
→ `204`

## Search

### `GET /search?q=...&k=10`
Semantic search over stored links.

→ `200 { "results": [{ "link": LinkResponse, "score": 0.87 }, ...] }`

## Schemas

### `LinkResponse`
```json
{
  "id": "uuid",
  "url": "string",
  "title": "string | null",
  "snippet": "string | null",
  "source": "string",
  "created_at": "iso8601",
  "updated_at": "iso8601"
}
```

### `LinkDetailResponse`
Extends `LinkResponse` with `meta_description`, `tags[]`.

### `LinkListResponse`
```json
{
  "items": [LinkResponse],
  "pagination": { "limit": 20, "offset": 0, "total": 123 }
}
```

## Errors
Standard FastAPI `{"detail": "..."}` shape. 422 for validation, 404 for missing, 500 for unexpected.

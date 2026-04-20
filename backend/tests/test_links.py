"""
Integration tests for the /links router.

All tests make real HTTP calls through the FastAPI app to a real Postgres DB.
No mocking.  Each test is independent — the `clean_links` fixture (autouse)
truncates the links table before every test.

Test map
--------
CRUD:
  1. POST /links         — 201 with correct fields; embedding stored (not null)
  2. POST /links         — invalid URL (no scheme) → 422
  3. GET  /links         — paginated list; 3 links → all 3 returned
  4. GET  /links/{id}    — detail for existing link
  5. GET  /links/{id}    — 404 for unknown id
  6. PATCH /links/{id}   — update title and snippet
  7. DELETE /links/{id}  — 204; subsequent GET → 404

Search:
  8. GET /links/search?q=hello  — 0 links → empty list, not an error
  9. GET /links/search?q=hello  — links saved → 200, items with scores 0..1
 10. GET /links/search           — missing q → 422
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# ── helpers ────────────────────────────────────────────────────────────────────

def _link_payload(**overrides) -> dict:
    defaults = {
        "url": "https://example.com/page",
        "title": "Example Page",
        "snippet": "A snippet about the example page.",
        "source": "web",
    }
    return {**defaults, **overrides}


# ── CRUD tests ─────────────────────────────────────────────────────────────────

async def test_create_link_returns_201_with_correct_fields(client: AsyncClient):
    """POST /links creates a link and returns 201 with all expected fields."""
    payload = _link_payload()
    resp = await client.post("/links", json=payload)

    assert resp.status_code == 201, resp.text

    body = resp.json()
    assert body["url"] == "https://example.com/page"
    assert body["title"] == "Example Page"
    assert body["snippet"] == "A snippet about the example page."
    assert body["source"] == "web"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body
    # id must be a valid UUID
    uuid.UUID(body["id"])


async def test_create_link_embedding_is_stored(
    client: AsyncClient, session_factory: async_sessionmaker
):
    """Embedding column must be non-null after ingest."""
    payload = _link_payload(url="https://embedding-check.example.com")
    resp = await client.post("/links", json=payload)
    assert resp.status_code == 201, resp.text

    link_id = resp.json()["id"]

    async with session_factory() as session:
        from app.models.link import Link
        result = await session.execute(
            select(Link).where(Link.id == uuid.UUID(link_id))
        )
        link = result.scalar_one()
        assert link.embedding is not None, "embedding must not be null after ingest"
        assert len(link.embedding) == 384


async def test_create_link_rejects_invalid_url(client: AsyncClient):
    """POST /links with a schemeless URL must return 422."""
    payload = _link_payload(url="not-a-url")
    resp = await client.post("/links", json=payload)
    assert resp.status_code == 422, resp.text


async def test_create_link_rejects_url_without_scheme(client: AsyncClient):
    """POST /links with a domain-only URL (no http/https) must return 422."""
    payload = _link_payload(url="example.com/page")
    resp = await client.post("/links", json=payload)
    assert resp.status_code == 422, resp.text


async def test_list_links_returns_all_saved_links(client: AsyncClient):
    """GET /links returns all saved links in the paginated response."""
    urls = [
        "https://alpha.example.com",
        "https://beta.example.com",
        "https://gamma.example.com",
    ]
    for url in urls:
        r = await client.post("/links", json=_link_payload(url=url))
        assert r.status_code == 201, r.text

    resp = await client.get("/links")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert "items" in body
    assert "pagination" in body
    assert body["pagination"]["total"] == 3
    returned_urls = {item["url"] for item in body["items"]}
    for url in urls:
        assert url in returned_urls


async def test_list_links_empty_when_no_links(client: AsyncClient):
    """GET /links returns an empty list when no links are saved."""
    resp = await client.get("/links")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"] == []
    assert body["pagination"]["total"] == 0


async def test_get_link_returns_detail(client: AsyncClient):
    """GET /links/{id} returns the detail for an existing link."""
    create_resp = await client.post(
        "/links",
        json=_link_payload(
            url="https://detail.example.com",
            meta_description="A meta description.",
        ),
    )
    assert create_resp.status_code == 201, create_resp.text
    link_id = create_resp.json()["id"]

    resp = await client.get(f"/links/{link_id}")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["id"] == link_id
    assert body["url"] == "https://detail.example.com"
    # LinkDetailResponse includes meta_description
    assert "meta_description" in body
    assert body["meta_description"] == "A meta description."


async def test_get_link_404_for_unknown_id(client: AsyncClient):
    """GET /links/{id} returns 404 for a non-existent UUID."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/links/{fake_id}")
    assert resp.status_code == 404, resp.text


async def test_patch_link_updates_title_and_snippet(client: AsyncClient):
    """PATCH /links/{id} updates title and snippet."""
    create_resp = await client.post(
        "/links",
        json=_link_payload(url="https://patch.example.com", title="Old Title", snippet="Old snippet"),
    )
    assert create_resp.status_code == 201, create_resp.text
    link_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/links/{link_id}",
        json={"title": "New Title", "snippet": "New snippet"},
    )
    assert patch_resp.status_code == 200, patch_resp.text

    body = patch_resp.json()
    assert body["title"] == "New Title"
    assert body["snippet"] == "New snippet"
    assert body["id"] == link_id


async def test_delete_link_returns_204_and_subsequent_get_is_404(client: AsyncClient):
    """DELETE /links/{id} returns 204; a subsequent GET returns 404."""
    create_resp = await client.post(
        "/links",
        json=_link_payload(url="https://delete-me.example.com"),
    )
    assert create_resp.status_code == 201, create_resp.text
    link_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/links/{link_id}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"/links/{link_id}")
    assert get_resp.status_code == 404, get_resp.text


# ── Search tests ───────────────────────────────────────────────────────────────

async def test_search_empty_db_returns_empty_list(client: AsyncClient):
    """GET /links/search?q=hello with no links returns 200 with an empty list."""
    resp = await client.get("/links/search", params={"q": "hello"})
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["items"] == []
    assert body["pagination"]["total"] == 0


async def test_search_returns_results_with_valid_scores(client: AsyncClient):
    """GET /links/search?q=hello with saved links returns items with scores in [0, 1]."""
    links_to_create = [
        _link_payload(
            url="https://search-one.example.com",
            title="hello world",
            snippet="A page about greetings.",
        ),
        _link_payload(
            url="https://search-two.example.com",
            title="python programming",
            snippet="Python tips and tricks.",
        ),
        _link_payload(
            url="https://search-three.example.com",
            title="async fastapi",
            snippet="Building async APIs with FastAPI.",
        ),
    ]
    for payload in links_to_create:
        r = await client.post("/links", json=payload)
        assert r.status_code == 201, r.text

    resp = await client.get("/links/search", params={"q": "hello"})
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert "items" in body
    assert len(body["items"]) == 3

    for item in body["items"]:
        # Required fields present
        assert "id" in item
        assert "url" in item
        assert "score" in item
        # Score must be a float between 0 and 1 inclusive
        score = item["score"]
        assert isinstance(score, float), f"score must be float, got {type(score)}: {score}"
        assert 0.0 <= score <= 1.0, f"score {score} is outside [0, 1]"


async def test_search_missing_q_returns_422(client: AsyncClient):
    """GET /links/search without ?q= returns 422 validation error."""
    resp = await client.get("/links/search")
    assert resp.status_code == 422, resp.text


async def test_search_empty_q_returns_422(client: AsyncClient):
    """GET /links/search?q= (empty string) returns 422 — min_length=1."""
    resp = await client.get("/links/search", params={"q": ""})
    assert resp.status_code == 422, resp.text

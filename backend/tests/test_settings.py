"""
Integration tests for the /settings router.

All tests make real HTTP calls through the FastAPI app to a real Postgres DB.
No mocking.  Each test is independent — the `reset_settings` fixture truncates
and re-inserts the canonical id=1 row before every settings test.

Test map
--------
GET /settings:
  1. Returns 200 with default values on a fresh row (provider="local", has_openai_key=False)
  2. Response never includes an "openai_api_key" field

PUT /settings — provider field:
  3. Can update embedding_provider to "stub" — response reflects updated value
  4. Submitting "openai" as provider returns 422 with message containing "migration"
  5. Omitting embedding_provider in body leaves existing provider unchanged

PUT /settings — API key field:
  6. Setting openai_api_key to a non-empty string makes has_openai_key true
  7. Clearing key with openai_api_key="" makes has_openai_key false
  8. Sending openai_api_key=null (None in Python) leaves existing key unchanged
  9. openai_api_key value is never returned in GET or PUT responses

POST /settings/reembed:
 10. With no links returns {"reembedded": 0}
 11. With N links saved, returns {"reembedded": N} and all embeddings are non-null

Provider dependency (integration):
 12. After setting provider to "stub" via PUT /settings, POST /links produces a
     non-null embedding (stub provider is active end-to-end)

Auth behaviour:
 13. GET /settings without a token when admin_token is configured → 401
 14. PUT /settings without a token when admin_token is configured → 401
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app import config as app_config
from app.models.app_settings import AppSettings
from app.models.link import Link

# Token value used in all settings tests that require auth.
_TEST_TOKEN = "testtoken"

# Convenience header dict — pass as `headers=auth_headers` on every settings request.
auth_headers = {"Authorization": f"Bearer {_TEST_TOKEN}"}


# ── helpers ────────────────────────────────────────────────────────────────────

def _link_payload(**overrides) -> dict:
    defaults = {
        "url": "https://example.com/settings-test",
        "title": "Settings Test Page",
        "snippet": "A snippet used during settings tests.",
        "source": "web",
    }
    return {**defaults, **overrides}


# ── fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def patch_admin_token(monkeypatch):
    """
    Set settings.admin_token to the test token value for every settings test.

    Uses monkeypatch.setattr so the original value is restored after each test.
    This means every test in this module runs with auth enforced — callers must
    pass auth_headers on all settings requests, or expect a 401.
    """
    monkeypatch.setattr(app_config.settings, "admin_token", _TEST_TOKEN)


@pytest.fixture(autouse=True)
async def reset_settings(engine):
    """
    Reset the app_settings row to a known state before every test.

    Deletes any existing row and inserts the canonical default (id=1,
    provider='local', no API key) so every test starts from identical DB state
    regardless of what previous tests did.
    """
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM app_settings WHERE id = 1"))
        await conn.execute(
            text(
                "INSERT INTO app_settings (id, embedding_provider, openai_api_key)"
                " VALUES (1, 'local', NULL)"
            )
        )
    yield
    # No teardown needed — next test's setup handles cleanup.


# ── GET /settings ──────────────────────────────────────────────────────────────

async def test_get_settings_returns_defaults_on_fresh_row(client: AsyncClient):
    """GET /settings returns 200 with provider='local' and has_openai_key=False."""
    resp = await client.get("/settings", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["embedding_provider"] == "local"
    assert body["has_openai_key"] is False


async def test_get_settings_never_includes_api_key_field(client: AsyncClient):
    """GET /settings must not expose the raw openai_api_key in the JSON response."""
    resp = await client.get("/settings", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert "openai_api_key" not in body, (
        "openai_api_key must never appear in the settings response"
    )


# ── PUT /settings — provider field ────────────────────────────────────────────

async def test_put_settings_updates_provider_to_stub(client: AsyncClient):
    """PUT /settings with embedding_provider='stub' returns the updated provider."""
    resp = await client.put("/settings", json={"embedding_provider": "stub"}, headers=auth_headers)
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["embedding_provider"] == "stub"


async def test_put_settings_rejects_openai_provider_with_422(client: AsyncClient):
    """PUT /settings with embedding_provider='openai' returns 422 mentioning 'migration'."""
    resp = await client.put("/settings", json={"embedding_provider": "openai"}, headers=auth_headers)
    assert resp.status_code == 422, resp.text

    # The validation message must mention "migration" so callers understand why
    resp_text = resp.text.lower()
    assert "migration" in resp_text, (
        f"Expected 'migration' in 422 error body, got: {resp.text}"
    )


async def test_put_settings_omitting_provider_leaves_it_unchanged(client: AsyncClient):
    """PUT /settings without embedding_provider field keeps the existing provider value."""
    # First set provider to "stub"
    set_resp = await client.put("/settings", json={"embedding_provider": "stub"}, headers=auth_headers)
    assert set_resp.status_code == 200, set_resp.text
    assert set_resp.json()["embedding_provider"] == "stub"

    # Now PUT with only the API key field — provider must remain "stub"
    patch_resp = await client.put("/settings", json={"openai_api_key": "some-key"}, headers=auth_headers)
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["embedding_provider"] == "stub", (
        "embedding_provider must not change when omitted from the request body"
    )


# ── PUT /settings — API key field ─────────────────────────────────────────────

async def test_put_settings_setting_api_key_makes_has_openai_key_true(client: AsyncClient):
    """PUT /settings with a non-empty openai_api_key sets has_openai_key=True."""
    resp = await client.put("/settings", json={"openai_api_key": "sk-test-1234"}, headers=auth_headers)
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["has_openai_key"] is True


async def test_put_settings_clearing_api_key_makes_has_openai_key_false(client: AsyncClient):
    """PUT /settings with openai_api_key='' clears the key; has_openai_key becomes False."""
    # Set a key first
    set_resp = await client.put("/settings", json={"openai_api_key": "sk-test-abc"}, headers=auth_headers)
    assert set_resp.status_code == 200, set_resp.text
    assert set_resp.json()["has_openai_key"] is True

    # Clear it with an empty string
    clear_resp = await client.put("/settings", json={"openai_api_key": ""}, headers=auth_headers)
    assert clear_resp.status_code == 200, clear_resp.text
    assert clear_resp.json()["has_openai_key"] is False


async def test_put_settings_null_api_key_leaves_existing_key_unchanged(
    client: AsyncClient, session_factory: async_sessionmaker
):
    """PUT /settings with openai_api_key=null (None) does NOT clear an existing key."""
    # Set a known key directly in the DB so we have a baseline
    async with session_factory() as session:
        result = await session.execute(select(AppSettings).where(AppSettings.id == 1))
        row = result.scalar_one()
        row.openai_api_key = "sk-do-not-clear-me"
        await session.commit()

    # Confirm key is set via GET
    get_resp = await client.get("/settings", headers=auth_headers)
    assert get_resp.json()["has_openai_key"] is True

    # PUT with null for the key — must be a no-op for the key field
    put_resp = await client.put("/settings", json={"openai_api_key": None}, headers=auth_headers)
    assert put_resp.status_code == 200, put_resp.text
    assert put_resp.json()["has_openai_key"] is True, (
        "Sending openai_api_key=null must not clear an existing key"
    )

    # Verify via a fresh GET as well
    get_after = await client.get("/settings", headers=auth_headers)
    assert get_after.json()["has_openai_key"] is True


async def test_put_settings_api_key_never_returned_in_response(client: AsyncClient):
    """PUT /settings and GET /settings must never return the raw openai_api_key value."""
    put_resp = await client.put("/settings", json={"openai_api_key": "sk-secret-key"}, headers=auth_headers)
    assert put_resp.status_code == 200, put_resp.text
    assert "openai_api_key" not in put_resp.json(), (
        "PUT response must not expose openai_api_key"
    )

    get_resp = await client.get("/settings", headers=auth_headers)
    assert get_resp.status_code == 200, get_resp.text
    assert "openai_api_key" not in get_resp.json(), (
        "GET response must not expose openai_api_key"
    )


# ── POST /settings/reembed ────────────────────────────────────────────────────

async def test_reembed_with_no_links_returns_zero(client: AsyncClient):
    """POST /settings/reembed with an empty links table returns {"reembedded": 0}."""
    resp = await client.post("/settings/reembed", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body == {"reembedded": 0}


async def test_reembed_with_links_updates_all_embeddings(
    client: AsyncClient, session_factory: async_sessionmaker
):
    """POST /settings/reembed with N links returns {"reembedded": N} and all embeddings are non-null."""
    # Use stub provider so this test runs without sentence-transformers installed.
    await client.put("/settings", json={"embedding_provider": "stub"}, headers=auth_headers)

    n = 3
    urls = [f"https://reembed-{i}.example.com" for i in range(n)]
    for url in urls:
        r = await client.post("/links", json=_link_payload(url=url))
        assert r.status_code == 201, r.text

    # Null out embeddings directly so we can confirm reembed actually writes them
    async with session_factory() as session:
        for url in urls:
            result = await session.execute(select(Link).where(Link.url == url))
            link = result.scalar_one()
            link.embedding = None
        await session.commit()

    resp = await client.post("/settings/reembed", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body == {"reembedded": n}, f"Expected reembedded={n}, got {body}"

    # Verify embeddings are non-null in the DB after the reembed
    async with session_factory() as session:
        for url in urls:
            result = await session.execute(select(Link).where(Link.url == url))
            link = result.scalar_one()
            assert link.embedding is not None, (
                f"embedding for {url} must not be null after reembed"
            )
            assert len(link.embedding) > 0, (
                f"embedding for {url} must have non-zero length after reembed"
            )


# ── Provider dependency integration ───────────────────────────────────────────

async def test_post_links_uses_stub_provider_after_settings_update(
    client: AsyncClient, session_factory: async_sessionmaker
):
    """After switching provider to 'stub' via PUT /settings, POST /links produces a non-null embedding."""
    # Switch to stub provider
    put_resp = await client.put("/settings", json={"embedding_provider": "stub"}, headers=auth_headers)
    assert put_resp.status_code == 200, put_resp.text
    assert put_resp.json()["embedding_provider"] == "stub"

    # Create a link — stub provider must be used (no model download needed)
    create_resp = await client.post(
        "/links",
        json=_link_payload(url="https://stub-provider-check.example.com"),
    )
    assert create_resp.status_code == 201, create_resp.text
    link_id = create_resp.json()["id"]

    # Confirm the embedding is stored and non-null
    async with session_factory() as session:
        result = await session.execute(
            select(Link).where(Link.id == uuid.UUID(link_id))
        )
        link = result.scalar_one()
        assert link.embedding is not None, (
            "embedding must not be null when stub provider is active"
        )
        assert len(link.embedding) > 0, (
            "embedding must have non-zero length when stub provider is active"
        )


# ── Auth behaviour ────────────────────────────────────────────────────────────

async def test_settings_get_unauthorized(client: AsyncClient):
    """GET /settings without a Bearer token returns 401 when admin_token is configured.

    The patch_admin_token fixture sets admin_token=_TEST_TOKEN for this test,
    so the absence of any Authorization header must produce a 401.
    """
    # Arrange: no auth header — rely on patch_admin_token autouse fixture
    # Act
    resp = await client.get("/settings")
    # Assert
    assert resp.status_code == 401, (
        f"Expected 401 when no token is provided, got {resp.status_code}: {resp.text}"
    )


async def test_settings_put_unauthorized(client: AsyncClient):
    """PUT /settings without a Bearer token returns 401 when admin_token is configured.

    The patch_admin_token fixture sets admin_token=_TEST_TOKEN for this test,
    so the absence of any Authorization header must produce a 401.
    """
    # Arrange: no auth header — rely on patch_admin_token autouse fixture
    # Act
    resp = await client.put("/settings", json={"embedding_provider": "stub"})
    # Assert
    assert resp.status_code == 401, (
        f"Expected 401 when no token is provided, got {resp.status_code}: {resp.text}"
    )

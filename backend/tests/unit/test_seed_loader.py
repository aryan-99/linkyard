"""Unit tests for backend/app/seed/load.py.

No database or network required — everything is mocked.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.seed.load import seed_demo_links


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session(row_count: int) -> MagicMock:
    """Return a mock AsyncSession whose SELECT count returns *row_count*."""
    scalar_result = MagicMock()
    scalar_result.scalar_one.return_value = row_count

    execute_result = MagicMock()
    execute_result.scalar_one.return_value = row_count

    session = MagicMock()
    session.execute = AsyncMock(return_value=execute_result)
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


def _make_provider(embedding: list[float] | None = None) -> MagicMock:
    """Return a mock EmbeddingProvider whose embed() returns a stub vector."""
    provider = MagicMock()
    provider.embed = AsyncMock(return_value=embedding or [0.1] * 384)
    return provider


_MINIMAL_ENTRIES = [
    {
        "url": "https://example.com/a",
        "title": "Entry A",
        "snippet": None,
        "page_body": "Some body text about entry A.",
        "meta_description": "Meta A",
    },
    {
        "url": "https://example.com/b",
        "title": "Entry B",
        "snippet": "A short note",
        "page_body": "Body text for B.",
        "meta_description": None,
    },
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_seed_skips_when_table_nonempty():
    """seed_demo_links must be a no-op when links table already has rows."""
    session = _make_session(row_count=5)
    provider = _make_provider()

    await seed_demo_links(session, provider)

    # Should never try to insert anything
    session.add.assert_not_called()
    session.commit.assert_not_called()
    provider.embed.assert_not_called()


@pytest.mark.asyncio
async def test_seed_inserts_when_table_empty(tmp_path: Path):
    """seed_demo_links inserts all entries from the JSON when table is empty."""
    seed_file = tmp_path / "demo_links.json"
    seed_file.write_text(json.dumps(_MINIMAL_ENTRIES), encoding="utf-8")

    session = _make_session(row_count=0)
    provider = _make_provider()

    with patch("app.seed.load._SEED_FILE", seed_file):
        await seed_demo_links(session, provider)

    # One add() per entry
    assert session.add.call_count == len(_MINIMAL_ENTRIES)
    # Exactly one commit at the end
    session.commit.assert_awaited_once()
    # One embed() call per entry
    assert provider.embed.await_count == len(_MINIMAL_ENTRIES)


@pytest.mark.asyncio
async def test_seed_sets_source_field(tmp_path: Path):
    """Each inserted Link must have source='seed'."""
    seed_file = tmp_path / "demo_links.json"
    seed_file.write_text(json.dumps(_MINIMAL_ENTRIES[:1]), encoding="utf-8")

    session = _make_session(row_count=0)
    provider = _make_provider()

    with patch("app.seed.load._SEED_FILE", seed_file):
        await seed_demo_links(session, provider)

    added_link = session.add.call_args[0][0]
    assert added_link.source == "seed"


@pytest.mark.asyncio
async def test_seed_idempotent_called_twice(tmp_path: Path):
    """Calling seed_demo_links twice on a non-empty table is always a no-op on the second call."""
    seed_file = tmp_path / "demo_links.json"
    seed_file.write_text(json.dumps(_MINIMAL_ENTRIES), encoding="utf-8")

    # First call: table is empty, seed runs
    session_first = _make_session(row_count=0)
    provider = _make_provider()
    with patch("app.seed.load._SEED_FILE", seed_file):
        await seed_demo_links(session_first, provider)
    assert session_first.add.call_count == len(_MINIMAL_ENTRIES)

    # Second call: table now has rows (simulate post-first-seed state)
    session_second = _make_session(row_count=len(_MINIMAL_ENTRIES))
    provider2 = _make_provider()
    with patch("app.seed.load._SEED_FILE", seed_file):
        await seed_demo_links(session_second, provider2)
    session_second.add.assert_not_called()
    provider2.embed.assert_not_called()

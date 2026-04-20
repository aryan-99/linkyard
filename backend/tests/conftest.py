"""
Pytest fixtures for Linkyard backend integration tests.

Design notes:
- Tests hit a real Postgres (same DB as dev — linkyard/linkyard).
- All async fixtures are function-scoped to avoid asyncpg cross-loop errors
  that occur when a session-scoped engine is reused across different event loops.
- Base.metadata.create_all is called once per test (cheap — tables already exist).
- The links table is TRUNCATED before each test (autouse) for isolation.
- The FastAPI dependency `get_session` is overridden per test to use a session
  built from the test engine so HTTP requests and direct DB queries share the same DB.
- asyncio_mode = "auto" is set in pytest.ini so all async test functions/fixtures
  run automatically.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base, get_session
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://linkyard:linkyard@localhost:5432/linkyard"


@pytest.fixture
async def engine():
    """
    Function-scoped async engine.

    Function scope avoids asyncpg futures being attached to the wrong event
    loop when fixtures at different scopes share the same engine.
    """
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest.fixture
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(autouse=True)
async def clean_links(engine):
    """Truncate links table before every test for isolation."""
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE links RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
async def client(session_factory):
    """
    httpx.AsyncClient wired to the FastAPI app via ASGITransport.

    The get_session dependency is overridden so every HTTP request in the test
    uses a session from the test engine — same DB, no separate connection pool.
    """
    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

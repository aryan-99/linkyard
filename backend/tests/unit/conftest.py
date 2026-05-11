# Unit-test conftest: override DB-dependent autouse fixtures from the parent
# conftest so that pure unit tests run without a Postgres connection.
import pytest


@pytest.fixture(autouse=True)
def clean_links():
    """No-op override: unit tests have no DB to truncate."""
    yield


@pytest.fixture(autouse=True)
async def suppress_page_fetch():
    """No-op override: unit tests don't call ingest, so no HTTP to suppress."""
    yield

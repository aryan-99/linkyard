"""Demo seed loader.

Called at startup when DEMO_SEED=true.  Inserts pre-fetched demo links so that
the live demo has meaningful semantic-search content without any manual step.

Design constraints:
- No outbound HTTP here — page_body is already baked into demo_links.json.
- Idempotent: if the links table already has rows, returns immediately.
- Embeddings are generated at seed time via the live provider so they match
  whatever provider the deployment uses.
"""

import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.services.embedding.base import EmbeddingProvider
from app.services.ingest import text_for_embedding

logger = logging.getLogger(__name__)

_SEED_FILE = Path(__file__).parent / "demo_links.json"
_SEED_SOURCE = "seed"


async def seed_demo_links(session: AsyncSession, provider: EmbeddingProvider) -> None:
    """Insert demo links if the links table is empty.

    Args:
        session: An open async SQLAlchemy session (caller manages commit/close).
        provider: The active embedding provider to use for generating embeddings.
    """
    # Idempotency guard: skip if any links already exist.
    result = await session.execute(select(func.count()).select_from(Link))
    count = result.scalar_one()
    if count > 0:
        logger.info("seed_demo_links: links table has %d rows — skipping seed", count)
        return

    with open(_SEED_FILE, encoding="utf-8") as f:
        entries: list[dict] = json.load(f)

    logger.info("seed_demo_links: seeding %d demo links…", len(entries))

    # Generate all embeddings in parallel for speed.
    texts = [
        text_for_embedding(
            e.get("title"),
            e.get("snippet"),
            e.get("page_body"),
            e.get("meta_description"),
        )
        for e in entries
    ]
    embeddings = await asyncio.gather(*[provider.embed(t) for t in texts])

    for entry, embedding in zip(entries, embeddings):
        link = Link(
            url=entry["url"],
            title=entry.get("title"),
            snippet=entry.get("snippet"),
            meta_description=entry.get("meta_description"),
            page_body=entry.get("page_body"),
            source=_SEED_SOURCE,
            embedding=embedding,
        )
        session.add(link)

    await session.commit()
    logger.info("seed_demo_links: inserted %d demo links", len(entries))

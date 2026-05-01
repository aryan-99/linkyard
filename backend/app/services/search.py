from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.services.embedding.base import EmbeddingProvider


async def search_links(
    session: AsyncSession,
    query: str,
    provider: EmbeddingProvider,
    limit: int = 20,
    offset: int = 0,
    threshold: float = 0.3,
) -> tuple[list[tuple[Link, float]], int]:
    query_embedding = await provider.embed(query)

    distance = Link.embedding.cosine_distance(query_embedding)
    score = (1 - distance).label("score")

    base = (
        select(Link, score)
        .where(Link.embedding.is_not(None))
        .order_by(distance)
    )

    total_result = await session.execute(
        select(func.count()).select_from(
            select(Link).where(Link.embedding.is_not(None)).subquery()
        )
    )
    total = total_result.scalar_one()

    result = await session.execute(base.limit(limit).offset(offset))
    rows = result.all()

    # Filter out results below the configured cosine similarity threshold.
    # score is 1 - cosine_distance; higher is better. Weak matches are dropped
    # here (post-fetch) rather than in SQL to keep the offset/limit semantics
    # simple — for typical collection sizes this is fine.
    return [
        (row[0], float(row[1])) for row in rows if float(row[1]) >= threshold
    ], total

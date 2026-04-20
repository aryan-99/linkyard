from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.services.embedding import get_embedding_provider


async def search_links(
    session: AsyncSession,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[tuple[Link, float]], int]:
    provider = get_embedding_provider()
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

    return [(row[0], float(row[1])) for row in rows], total

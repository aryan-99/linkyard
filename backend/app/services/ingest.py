from urllib.parse import urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.schemas.link import LinkCreate
from app.services.embedding.base import EmbeddingProvider


def text_for_embedding(title: str | None, snippet: str | None, url: str) -> str:
    return " ".join(filter(None, [title, snippet]))


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=parsed.path.rstrip("/") if parsed.path != "/" else parsed.path,
    )
    return urlunparse(normalized)


async def ingest_link(
    session: AsyncSession, data: LinkCreate, provider: EmbeddingProvider
) -> Link:
    url = _normalize_url(data.url)

    embedding = await provider.embed(text_for_embedding(data.title, data.snippet, url))

    link = Link(
        url=url,
        title=data.title,
        snippet=data.snippet,
        meta_description=data.meta_description,
        source=data.source,
        embedding=embedding,
    )
    session.add(link)
    await session.flush()
    await session.refresh(link)
    return link

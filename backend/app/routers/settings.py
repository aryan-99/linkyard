import asyncio
import logging

from fastapi import APIRouter
from sqlalchemy import select

from app.deps import ProviderDep, SessionDep
from app.models.app_settings import AppSettings
from app.models.link import Link
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services.ingest import text_for_embedding

logger = logging.getLogger(__name__)
router = APIRouter()


def _row_to_response(row: AppSettings) -> SettingsResponse:
    return SettingsResponse(
        embedding_provider=row.embedding_provider,
        has_openai_key=bool(row.openai_api_key),
    )


@router.get("", response_model=SettingsResponse)
async def get_settings(session: SessionDep) -> SettingsResponse:
    result = await session.execute(select(AppSettings).where(AppSettings.id == 1))
    row = result.scalar_one_or_none()
    if row is None:
        # Row missing (pre-migration dev env): return defaults, never leak key
        return SettingsResponse(embedding_provider="local", has_openai_key=False)
    return _row_to_response(row)


@router.put("", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate, session: SessionDep
) -> SettingsResponse:
    result = await session.execute(select(AppSettings).where(AppSettings.id == 1))
    row = result.scalar_one_or_none()
    if row is None:
        row = AppSettings(id=1)
        session.add(row)

    if data.embedding_provider is not None:
        row.embedding_provider = data.embedding_provider

    if data.openai_api_key is not None:
        # Empty string means "clear the key"; non-empty means "set it"
        row.openai_api_key = None if data.openai_api_key == "" else data.openai_api_key

    await session.commit()
    await session.refresh(row)
    return _row_to_response(row)


@router.post("/reembed", response_model=dict)
async def reembed_links(session: SessionDep, provider: ProviderDep) -> dict:
    """Re-embed all links using the currently active provider.

    Fetches link content without loading existing embeddings (wasteful).
    Returns the count of links updated.
    """
    result = await session.execute(select(Link))
    links = list(result.scalars().all())
    logger.warning("reembed: starting re-embed of %d links", len(links))

    embeddings = await asyncio.gather(
        *[provider.embed(text_for_embedding(link.title, link.snippet, link.url)) for link in links]
    )
    for link, embedding in zip(links, embeddings):
        link.embedding = embedding

    await session.commit()
    return {"reembedded": len(links)}

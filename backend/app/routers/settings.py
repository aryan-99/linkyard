import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.db import get_session
from app.deps import ProviderDep
from app.models.app_settings import AppSettings
from app.models.link import Link
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


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
        # Safety net: create the row if somehow missing
        row = AppSettings(id=1, embedding_provider="local", openai_api_key=None)
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
    result = await session.execute(
        select(Link.id, Link.url, Link.title, Link.snippet)
    )
    rows = result.all()
    logger.warning("reembed: starting re-embed of %d links", len(rows))

    count = 0
    for row in rows:
        link_id, url, title, snippet = row
        text = " ".join(filter(None, [title, snippet, url]))
        embedding = await provider.embed(text)

        # Fetch the ORM object to update it
        link_result = await session.execute(select(Link).where(Link.id == link_id))
        link = link_result.scalar_one()
        link.embedding = embedding
        count += 1

    await session.commit()
    return {"reembedded": count}

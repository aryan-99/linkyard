import asyncio
import logging

from fastapi import APIRouter
from sqlalchemy import select

from app.deps import AdminTokenDep, ProviderDep, SessionDep
from app.models.app_settings import AppSettings
from app.models.link import Link
from app.schemas.settings import SettingsResponse, SettingsUpdate
from pydantic import BaseModel

from app.services.ingest import _fetch_page_body, text_for_embedding

logger = logging.getLogger(__name__)
router = APIRouter()


def _row_to_response(row: AppSettings) -> SettingsResponse:
    return SettingsResponse(
        embedding_provider=row.embedding_provider,
        has_openai_key=bool(row.openai_api_key),
        search_threshold=row.search_threshold,
    )


@router.get("", response_model=SettingsResponse, dependencies=[AdminTokenDep])
async def get_settings(session: SessionDep) -> SettingsResponse:
    result = await session.execute(select(AppSettings).where(AppSettings.id == 1))
    row = result.scalar_one_or_none()
    if row is None:
        # Row missing (pre-migration dev env): return defaults, never leak key
        return SettingsResponse(embedding_provider="local", has_openai_key=False, search_threshold=0.3)
    return _row_to_response(row)


@router.put("", response_model=SettingsResponse, dependencies=[AdminTokenDep])
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

    if data.search_threshold is not None:
        row.search_threshold = data.search_threshold

    await session.commit()
    await session.refresh(row)
    return _row_to_response(row)


class RefetchRequest(BaseModel):
    force: bool = False


@router.post("/refetch", response_model=dict, dependencies=[AdminTokenDep])
async def refetch_links(body: RefetchRequest, session: SessionDep, provider: ProviderDep) -> dict:
    if body.force:
        result = await session.execute(select(Link))
    else:
        result = await session.execute(select(Link).where(Link.page_body.is_(None)))
    links = list(result.scalars().all())
    logger.warning("refetch: starting re-fetch of %d links (force=%s)", len(links), body.force)
    fetch_results = await asyncio.gather(*[_fetch_page_body(str(link.url)) for link in links])
    embeddings = await asyncio.gather(*[
        provider.embed(text_for_embedding(
            link.title, link.snippet,
            page_body, link.meta_description or fetched_meta,
        ))
        for link, (page_body, fetched_meta) in zip(links, fetch_results)
    ])
    for link, (page_body, fetched_meta), embedding in zip(links, fetch_results, embeddings):
        link.page_body = page_body
        link.meta_description = link.meta_description or fetched_meta
        link.embedding = embedding
    await session.commit()
    return {"refetched": len(links)}


@router.post("/reembed", response_model=dict, dependencies=[AdminTokenDep])
async def reembed_links(session: SessionDep, provider: ProviderDep) -> dict:
    """Re-embed all links using the currently active provider.

    Fetches link content without loading existing embeddings (wasteful).
    Returns the count of links updated.
    """
    result = await session.execute(select(Link))
    links = list(result.scalars().all())
    logger.warning("reembed: starting re-embed of %d links", len(links))

    embeddings = await asyncio.gather(
        *[provider.embed(text_for_embedding(link.title, link.snippet, link.page_body, link.meta_description)) for link in links]
    )
    for link, embedding in zip(links, embeddings):
        link.embedding = embedding

    await session.commit()
    return {"reembedded": len(links)}

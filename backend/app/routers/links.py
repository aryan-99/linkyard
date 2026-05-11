import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.deps import AdminTokenDep, ProviderDep, SearchThresholdDep, SessionDep
from app.models.link import Link
from app.schemas.link import (
    LinkCreate,
    LinkDetailResponse,
    LinkListResponse,
    LinkResponse,
    LinkUpdate,
    SearchResultItem,
    SearchResultsResponse,
)
from app.services.ingest import _fetch_page_body, ingest_link, text_for_embedding
from app.services.search import search_links

router = APIRouter()


@router.post("", response_model=LinkDetailResponse, status_code=201)
async def create_link(
    data: LinkCreate, session: SessionDep, provider: ProviderDep
) -> LinkDetailResponse:
    link = await ingest_link(session, data, provider)
    await session.commit()
    await session.refresh(link)
    return LinkDetailResponse.model_validate(link)


@router.get("", response_model=LinkListResponse)
async def list_links(
    session: SessionDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LinkListResponse:
    total_result = await session.execute(select(func.count()).select_from(Link))
    total = total_result.scalar_one()

    result = await session.execute(
        select(Link).order_by(Link.created_at.desc()).limit(limit).offset(offset)
    )
    items = result.scalars().all()

    return LinkListResponse(
        items=[LinkResponse.model_validate(item) for item in items],
        pagination={"limit": limit, "offset": offset, "total": total},
    )


@router.get("/search", response_model=SearchResultsResponse)
async def search_links_endpoint(
    session: SessionDep,
    provider: ProviderDep,
    threshold: SearchThresholdDep,
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SearchResultsResponse:
    results, total = await search_links(session, q, provider, limit, offset, threshold)
    return SearchResultsResponse(
        items=[
            SearchResultItem(**LinkResponse.model_validate(link).model_dump(), score=score)
            for link, score in results
        ],
        pagination={"limit": limit, "offset": offset, "total": total},
    )


@router.get("/{link_id}", response_model=LinkDetailResponse)
async def get_link(link_id: uuid.UUID, session: SessionDep) -> LinkDetailResponse:
    result = await session.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return LinkDetailResponse.model_validate(link)


@router.post("/{link_id}/refetch", response_model=LinkDetailResponse, dependencies=[AdminTokenDep])
async def refetch_link(link_id: uuid.UUID, session: SessionDep, provider: ProviderDep) -> LinkDetailResponse:
    result = await session.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    page_body, fetched_meta = await _fetch_page_body(str(link.url))
    effective_meta = link.meta_description or fetched_meta
    link.page_body = page_body
    link.meta_description = effective_meta
    link.embedding = await provider.embed(
        text_for_embedding(link.title, link.snippet, page_body, effective_meta)
    )
    await session.commit()
    await session.refresh(link)
    return LinkDetailResponse.model_validate(link)


@router.patch("/{link_id}", response_model=LinkResponse)
async def update_link(
    link_id: uuid.UUID, data: LinkUpdate, session: SessionDep
) -> LinkResponse:
    result = await session.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")

    if data.title is not None:
        link.title = data.title
    if data.snippet is not None:
        link.snippet = data.snippet

    await session.commit()
    await session.refresh(link)
    return LinkResponse.model_validate(link)


@router.delete("/{link_id}", status_code=204)
async def delete_link(link_id: uuid.UUID, session: SessionDep) -> None:
    result = await session.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    await session.delete(link)
    await session.commit()

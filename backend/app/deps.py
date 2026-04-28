from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.app_settings import AppSettings
from app.services.embedding.base import EmbeddingProvider
from app.services.embedding.factory import get_embedding_provider_for

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_active_provider(
    session: AsyncSession = Depends(get_session),
) -> EmbeddingProvider:
    """FastAPI dependency that returns the currently configured embedding provider.

    Reads the active provider name from the app_settings DB row (id=1).
    Falls back to "local" if the row is missing (e.g. pre-migration).
    """
    result = await session.execute(select(AppSettings).where(AppSettings.id == 1))
    row = result.scalar_one_or_none()
    provider_name = row.embedding_provider if row else "local"
    api_key = row.openai_api_key if row else None
    return get_embedding_provider_for(provider_name, api_key)


ProviderDep = Annotated[EmbeddingProvider, Depends(get_active_provider)]

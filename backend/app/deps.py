from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.models.app_settings import AppSettings
from app.services.embedding.base import EmbeddingProvider
from app.services.embedding.factory import get_embedding_provider_for

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# ---------------------------------------------------------------------------
# Admin bearer-token auth
# ---------------------------------------------------------------------------
# HTTPBearer extracts the token from the "Authorization: Bearer <token>"
# header.  auto_error=False means FastAPI will NOT automatically reject
# requests with no/malformed header — we handle that logic ourselves so we
# can pass through when admin_token is not configured.
_bearer_scheme = HTTPBearer(auto_error=False)


async def _verify_admin_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> None:
    """Dependency that enforces the static admin bearer token.

    Behaviour:
    - If ``settings.admin_token`` is None or empty string → no-op (pass through).
    - Otherwise the request must carry ``Authorization: Bearer <token>`` with
      the exact configured value.  Any mismatch or missing header → HTTP 401.
    """
    configured = settings.admin_token
    if not configured:
        # Auth disabled — local dev convenience.
        return

    if credentials is None or credentials.credentials != configured:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Use as a route dependency: dependencies=[AdminTokenDep]
# or inject directly as a parameter annotated with this type.
AdminTokenDep = Depends(_verify_admin_token)


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

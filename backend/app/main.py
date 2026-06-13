import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import links
from app.routers import settings as settings_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.demo_seed:
        try:
            from app.db import SessionLocal
            from app.deps import get_active_provider
            from app.seed.load import seed_demo_links

            async with SessionLocal() as session:
                provider = await get_active_provider(session)
                await seed_demo_links(session, provider)
        except Exception:
            logger.exception(
                "demo seed failed — app will still serve requests normally"
            )
    yield


app = FastAPI(title="Linkyard", debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # allow_origins=["*"] only covers http/https; chrome-extension:// origins
    # require an explicit regex. In dev this permits any extension ID.
    # In production, set CORS_ORIGIN_REGEX to a specific extension ID:
    #   chrome-extension://abcdefghijklmnopabcdefghijklmnop
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(links.router, prefix="/links", tags=["links"])
app.include_router(settings_router.router, prefix="/settings", tags=["settings"])

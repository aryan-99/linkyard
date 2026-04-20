from app.config import settings
from app.services.embedding.base import EmbeddingProvider
from app.services.embedding.stub import StubProvider


def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "stub":
        return StubProvider(dim=settings.embedding_dim)
    raise ValueError(f"Unknown embedding provider: {settings.embedding_provider!r}")

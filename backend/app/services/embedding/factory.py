from app.config import settings
from app.services.embedding.base import EmbeddingProvider
from app.services.embedding.stub import StubProvider


def get_embedding_provider_for(
    name: str, api_key: str | None = None
) -> EmbeddingProvider:
    """Build a provider by name.

    "stub"  — hash-based deterministic provider (no model needed).
    "local" — sentence-transformers local model (no API key needed).
    "openai" — NOT yet activatable via API (requires 1536-dim migration).
               Raises ValueError to enforce the guard.
    """
    if name == "stub":
        return StubProvider(dim=settings.embedding_dim)
    if name == "local":
        from app.services.embedding.local import LocalProvider  # noqa: PLC0415
        return LocalProvider(model_name=settings.local_embedding_model)
    raise ValueError(f"Unknown embedding provider: {name!r}")


def get_embedding_provider() -> EmbeddingProvider:
    """Build a provider from the environment/config settings (legacy path)."""
    return get_embedding_provider_for(
        settings.embedding_provider,
        api_key=settings.openai_api_key,
    )

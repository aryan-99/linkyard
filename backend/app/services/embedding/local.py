import asyncio
from typing import Optional

from app.services.embedding.base import EmbeddingProvider

_FALLBACK_DIM = 384


class LocalProvider(EmbeddingProvider):
    """Runs sentence-transformers locally — no API key required.

    The SentenceTransformer model is lazy-loaded on the first embed() call so
    that importing this module (or switching to stub) doesn't pay the model
    load cost at startup.

    encode() is CPU-bound and blocking; it is dispatched to a thread-pool
    executor so it never stalls the async event loop.
    """

    def __init__(self, model_name: str = "multi-qa-MiniLM-L6-cos-v1") -> None:
        self._model_name = model_name
        self._model: Optional[object] = None

    def _load_model(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415
            self._model = SentenceTransformer(self._model_name)

    @property
    def dim(self) -> int:
        if self._model is None:
            return _FALLBACK_DIM
        return self._model.get_sentence_embedding_dimension()

    async def embed(self, text: str) -> list[float]:
        loop = asyncio.get_running_loop()

        def _encode() -> list[float]:
            self._load_model()
            vector = self._model.encode(text, normalize_embeddings=True)
            return vector.tolist()

        return await loop.run_in_executor(None, _encode)

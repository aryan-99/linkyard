import hashlib
import math

from app.services.embedding.base import EmbeddingProvider


class StubProvider(EmbeddingProvider):
    def __init__(self, dim: int = 384) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    async def embed(self, text: str) -> list[float]:
        seed = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        raw = [(seed >> i & 0xFF) / 127.5 - 1.0 for i in range(self._dim)]
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]

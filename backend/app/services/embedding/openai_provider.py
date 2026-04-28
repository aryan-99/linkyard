import httpx

from app.services.embedding.base import EmbeddingProvider


class OpenAIProvider(EmbeddingProvider):
    """OpenAI text-embedding-3-small provider.

    Produces 1536-dimensional vectors. The current DB schema stores Vector(384),
    so this provider CANNOT be activated via the settings API until a migration
    widens the column to 1536. The class is implemented here for future use;
    the settings router rejects "openai" with a 422 until that migration lands.
    """

    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient()

    @property
    def dim(self) -> int:
        return 1536

    async def embed(self, text: str) -> list[float]:
        response = await self._client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._model, "input": text},
            timeout=30.0,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # Raise without chaining to avoid leaking the response body
            # (which may contain a partial API key) into logs/tracebacks.
            raise RuntimeError(
                f"OpenAI embeddings request failed with status {exc.response.status_code}"
            ) from None
        data = response.json()
        return data["data"][0]["embedding"]

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://linkyard:linkyard@localhost:5432/linkyard"
    database_url_sync: str = "postgresql://linkyard:linkyard@localhost:5432/linkyard"

    debug: bool = False

    embedding_provider: str = "stub"
    embedding_dim: int = 384

    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"

    cors_origins_raw: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://linkyard:linkyard@localhost:5432/linkyard"
    database_url_sync: str = "postgresql://linkyard:linkyard@localhost:5432/linkyard"

    debug: bool = False

    embedding_provider: str = "local"
    embedding_dim: int = 384

    local_embedding_model: str = "multi-qa-MiniLM-L6-cos-v1"

    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"

    cors_origins_raw: str = "http://localhost:5173"

    # Regex applied in addition to cors_origins. In dev we allow any
    # chrome-extension:// origin because the extension ID is generated and
    # varies per browser/install. The pattern requires the extension ID to be
    # exactly 32 lowercase a-p characters (Chrome's CRX ID format) so that the
    # scheme prefix cannot be abused with arbitrary suffixes or other schemes.
    # In production, scope this to a known ID via the env var, e.g.:
    #   CORS_ORIGIN_REGEX=chrome-extension://abcdefghijklmnopabcdefghijklmnop
    cors_origin_regex: str = r"chrome-extension://[a-p]{32}"

    # Static bearer token for settings endpoints.
    # Leave unset (or empty) to disable auth — safe for local dev.
    # Set ADMIN_TOKEN=<secret> in .env to require Bearer auth on /settings routes.
    admin_token: str | None = None

    # Demo seed: when True, insert pre-fetched demo links at startup (no-op if
    # the links table already has rows).  Default False — never affects dev envs.
    demo_seed: bool = False

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]


settings = Settings()

from pydantic import BaseModel, Field, model_validator


class SettingsResponse(BaseModel):
    embedding_provider: str
    has_openai_key: bool  # True if openai_api_key is set and non-empty
    search_threshold: float


class SettingsUpdate(BaseModel):
    embedding_provider: str | None = None
    # None = no change; "" = clear the key; max_length guards against
    # oversized payloads being persisted (real OpenAI keys are ~51 chars).
    openai_api_key: str | None = Field(default=None, max_length=200)
    # None = no change; valid range is 0.0–1.0 (cosine similarity).
    search_threshold: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_provider(self) -> "SettingsUpdate":
        if self.embedding_provider not in (None, "local", "stub"):
            raise ValueError(
                "OpenAI provider requires a schema migration to 1536-dim; not yet supported via UI"
            )
        return self

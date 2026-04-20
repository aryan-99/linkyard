import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator


class LinkCreate(BaseModel):
    url: str
    title: str | None = None
    snippet: str | None = None
    meta_description: str | None = None
    source: Literal["extension", "web", "api"] = "web"

    @field_validator("url")
    @classmethod
    def url_must_have_scheme(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class LinkUpdate(BaseModel):
    title: str | None = None
    snippet: str | None = None


class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    title: str | None
    snippet: str | None
    source: str
    created_at: datetime
    updated_at: datetime


class LinkDetailResponse(LinkResponse):
    meta_description: str | None


class LinkListResponse(BaseModel):
    items: list[LinkResponse]
    pagination: dict


class SearchResultItem(LinkResponse):
    score: float


class SearchResultsResponse(BaseModel):
    items: list[SearchResultItem]
    pagination: dict

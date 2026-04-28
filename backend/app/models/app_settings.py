from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    embedding_provider: Mapped[str] = mapped_column(Text, nullable=False, default="local")
    openai_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)

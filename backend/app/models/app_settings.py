from sqlalchemy import Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    embedding_provider: Mapped[str] = mapped_column(Text, nullable=False, default="local")
    openai_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_threshold: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.3, server_default="0.3"
    )

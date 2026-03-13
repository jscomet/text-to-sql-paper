"""API key model."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class APIKey(Base):
    """API key model for storing user's LLM API keys."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    # Provider configuration
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # Provider: openai, dashscope, deepseek, etc.
    key_encrypted: Mapped[str] = mapped_column(nullable=False)  # Encrypted API key
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Custom base URL
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Model name
    format_type: Mapped[str] = mapped_column(String(20), nullable=False, default="openai")  # Response format: openai, anthropic, vllm

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    # Indexes
    __table_args__ = (
        Index("ix_api_keys_user_id", "user_id"),
        Index("ix_api_keys_provider", "provider"),
        Index("ix_api_keys_is_default", "is_default"),
        Index("ix_api_keys_user_default", "user_id", "is_default"),
        Index("ix_api_keys_format_type", "format_type"),
    )

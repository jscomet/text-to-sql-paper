"""Database connection model."""
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import String, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.query_history import QueryHistory


class DBConnection(Base):
    """Database connection configuration model."""

    __tablename__ = "db_connections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    db_type: Mapped[str] = mapped_column(String(20), nullable=False)
    host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(nullable=True)
    database: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    password_encrypted: Mapped[Optional[str]] = mapped_column(nullable=True)
    schema_cache: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="db_connections")
    query_history: Mapped[List["QueryHistory"]] = relationship(
        "QueryHistory",
        back_populates="connection"
    )

    # Indexes
    __table_args__ = (
        Index("ix_db_connections_user_id", "user_id"),
        Index("ix_db_connections_db_type", "db_type"),
    )

    def is_active(self) -> bool:
        """Check if connection is active."""
        return self.status == "active"

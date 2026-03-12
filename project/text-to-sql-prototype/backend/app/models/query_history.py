"""Query history model."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Index, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.db_connection import DBConnection
    from app.models.query_result import QueryResult


class QueryHistory(Base):
    """Query history model for storing natural language queries."""

    __tablename__ = "query_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    connection_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("db_connections.id", ondelete="SET NULL"),
        nullable=True
    )
    nl_question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending"
    )
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="query_history")
    connection: Mapped[Optional["DBConnection"]] = relationship(
        "DBConnection",
        back_populates="query_history"
    )
    result: Mapped[Optional["QueryResult"]] = relationship(
        "QueryResult",
        back_populates="query",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_query_history_user_id", "user_id"),
        Index("ix_query_history_connection_id", "connection_id"),
        Index("ix_query_history_created_at", "created_at"),
        Index("ix_query_history_is_favorite", "is_favorite"),
        Index("ix_query_history_user_created", "user_id", "created_at"),
    )

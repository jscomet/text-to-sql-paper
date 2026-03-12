"""User model."""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.db_connection import DBConnection
    from app.models.query_history import QueryHistory
    from app.models.eval_task import EvalTask
    from app.models.api_key import APIKey


class User(Base):
    """User model for storing user information."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    db_connections: Mapped[List["DBConnection"]] = relationship(
        "DBConnection",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    query_history: Mapped[List["QueryHistory"]] = relationship(
        "QueryHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    eval_tasks: Mapped[List["EvalTask"]] = relationship(
        "EvalTask",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_users_status", "status"),
    )

    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == "active"

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == "admin"

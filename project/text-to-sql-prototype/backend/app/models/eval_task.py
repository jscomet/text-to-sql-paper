"""Evaluation task model."""
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import String, ForeignKey, Index, Integer, Float, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.eval_result import EvalResult


class EvalTask(Base):
    """Evaluation task model for model evaluation."""

    __tablename__ = "eval_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    model_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    eval_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="greedy_search"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_questions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processed_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    log_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="eval_tasks")
    results: Mapped[List["EvalResult"]] = relationship(
        "EvalResult",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_eval_tasks_user_id", "user_id"),
        Index("ix_eval_tasks_status", "status"),
        Index("ix_eval_tasks_dataset_type", "dataset_type"),
        Index("ix_eval_tasks_created_at", "created_at"),
    )

    def is_pending(self) -> bool:
        """Check if task is pending."""
        return self.status == "pending"

    def is_running(self) -> bool:
        """Check if task is running."""
        return self.status == "running"

    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if task is failed."""
        return self.status == "failed"

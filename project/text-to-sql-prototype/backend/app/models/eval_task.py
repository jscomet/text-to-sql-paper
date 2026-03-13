"""Evaluation task model."""
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import String, ForeignKey, Index, Integer, Float, JSON, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.eval_result import EvalResult
    from app.models.db_connection import DBConnection


class EvalTask(Base):
    """Evaluation task model for model evaluation."""

    __tablename__ = "eval_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Parent-child relationship fields
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("eval_tasks.id", ondelete="CASCADE"),
        nullable=True
    )
    task_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="single"
    )  # 'single', 'parent', 'child'
    db_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    connection_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("db_connections.id", ondelete="SET NULL"),
        nullable=True
    )
    child_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_children: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    model_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    eval_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="greedy_search"
    )
    max_iterations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3
    )
    sampling_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )
    correction_strategy: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
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
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="eval_tasks")
    connection: Mapped[Optional["DBConnection"]] = relationship("DBConnection")
    parent: Mapped[Optional["EvalTask"]] = relationship(
        "EvalTask",
        remote_side="EvalTask.id",
        back_populates="children"
    )
    children: Mapped[List["EvalTask"]] = relationship(
        "EvalTask",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
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
        Index("ix_eval_tasks_parent_id", "parent_id"),
        Index("ix_eval_tasks_task_type", "task_type"),
        Index("ix_eval_tasks_db_id", "db_id"),
        Index("ix_eval_tasks_parent_status", "parent_id", "status"),
        Index("ix_eval_tasks_user_type", "user_id", "task_type"),
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

    def is_parent(self) -> bool:
        """Check if this is a parent task."""
        return self.task_type == "parent"

    def is_child(self) -> bool:
        """Check if this is a child task."""
        return self.task_type == "child"

    def is_single(self) -> bool:
        """Check if this is a single (standalone) task."""
        return self.task_type == "single"

    def update_parent_stats(self) -> None:
        """Update parent task statistics from children."""
        if not self.is_parent() or not self.children:
            return

        total = sum(c.total_questions or 0 for c in self.children)
        correct = sum(c.correct_count or 0 for c in self.children)
        completed = sum(1 for c in self.children if c.status == "completed")

        self.total_questions = total
        self.correct_count = correct
        self.accuracy = correct / total if total > 0 else 0.0
        self.completed_children = completed

        # Auto-update parent status
        if completed == self.child_count:
            self.status = "completed"
        elif completed > 0:
            self.status = "running"

"""Evaluation result model."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Index, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.eval_task import EvalTask


class EvalResult(Base):
    """Evaluation result model for storing evaluation results."""

    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("eval_tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    question_id: Mapped[str] = mapped_column(String(100), nullable=False)
    nl_question: Mapped[str] = mapped_column(Text, nullable=False)
    db_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gold_sql: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    # Relationships
    task: Mapped["EvalTask"] = relationship("EvalTask", back_populates="results")

    # Indexes
    __table_args__ = (
        Index("ix_eval_results_task_id", "task_id"),
        Index("ix_eval_results_is_correct", "is_correct"),
        Index("ix_eval_results_error_type", "error_type"),
        Index("ix_eval_results_task_correct", "task_id", "is_correct"),
    )

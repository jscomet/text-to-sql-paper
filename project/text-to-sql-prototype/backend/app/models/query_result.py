"""Query result model."""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import ForeignKey, Float, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class QueryResult(Base):
    """Query result model for storing query execution results."""

    __tablename__ = "query_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    query_id: Mapped[int] = mapped_column(
        ForeignKey("query_history.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    # Relationships
    query: Mapped["QueryHistory"] = relationship("QueryHistory", back_populates="result")

"""Base model class for SQLAlchemy 2.0 declarative models."""
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map = {
        datetime: DateTime(timezone=False),
    }

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """String representation of the model."""
        columns = [f"{col.name}={getattr(self, col.name)!r}" for col in self.__table__.columns]
        return f"{self.__class__.__name__}({', '.join(columns)})"

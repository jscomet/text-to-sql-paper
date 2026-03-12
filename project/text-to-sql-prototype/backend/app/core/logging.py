"""Logging configuration using loguru."""
import sys
from typing import Any, Dict

from loguru import logger

from app.core.config import settings


def configure_logging() -> None:
    """Configure loguru logging."""
    # Remove default handler
    logger.remove()

    # Add console handler with custom format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=settings.is_development,
        diagnose=settings.is_development,
    )

    # Add file handler for production
    if settings.is_production:
        logger.add(
            "logs/app.log",
            rotation="00:00",  # Rotate at midnight
            retention="30 days",
            compression="zip",
            format=log_format,
            level="INFO",
        )


def get_logger(name: str) -> Any:
    """Get a logger instance with bound context."""
    return logger.bind(name=name)

"""Structured application logging configuration."""

import logging
import sys
from logging import Logger
from typing import Literal

from app.config.settings import Settings

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LevelFilter(logging.Filter):
    """Allow log records that match an exact severity level."""

    def __init__(self, level: int) -> None:
        super().__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self.level


def _build_formatter(settings: Settings) -> logging.Formatter:
    """Create a formatter suitable for the active environment."""
    if settings.is_development:
        return logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    return logging.Formatter(
        fmt=(
            '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","message":"%(message)s"}'
        ),
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def setup_logging(settings: Settings) -> None:
    """Configure root logging and dedicated severity handlers."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.LOG_LEVEL)

    formatter = _build_formatter(settings)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    root_logger.addHandler(console_handler)

    logs_directory = "logs"
    if not settings.is_development:
        from pathlib import Path

        Path(logs_directory).mkdir(parents=True, exist_ok=True)

        for level_name in ("INFO", "WARNING", "ERROR"):
            file_handler = logging.FileHandler(
                f"{logs_directory}/{level_name.lower()}.log",
                encoding="utf-8",
            )
            file_handler.setLevel(getattr(logging, level_name))
            file_handler.addFilter(LevelFilter(getattr(logging, level_name)))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )


def get_logger(name: str) -> Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)

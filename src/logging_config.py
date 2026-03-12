"""Logging configuration for Wiggum Report.

Provides centralized logging setup with console and rotating file handlers.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from src.config.settings import Settings


def setup_logging(
    settings: Optional[Settings] = None,
    log_level: str = "INFO",
    log_dir: str = "./logs",
    log_file: str = "wiggum.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure comprehensive logging for the Wiggum Report application.

    Args:
        settings: Optional Settings instance for configuration
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        log_file: Log filename
        max_bytes: Maximum size of each log file before rotation (bytes)
        backup_count: Number of backup log files to keep
        console_output: Whether to output logs to console

    Returns:
        Root logger configured with handlers
    """
    # Override defaults from settings if provided
    if settings:
        log_level = os.getenv("LOG_LEVEL", log_level)
        log_dir = os.getenv("LOG_DIR", log_dir)
        log_file = os.getenv("LOG_FILE", log_file)
        max_bytes = (
            int(os.getenv("LOG_MAX_SIZE_MB", str(max_bytes // (1024 * 1024))))
            * 1024
            * 1024
        )
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", str(backup_count)))

    # Convert log level string to numeric level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    # Create logger
    logger = logging.getLogger("wiggum")
    logger.setLevel(numeric_level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, log_file)

        file_handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(
            f"Logging configured: level={log_level}, file={log_path}, max_size={max_bytes // (1024 * 1024)}MB, backups={backup_count}"
        )
    except Exception as e:
        logger.warning(
            f"Failed to configure file logging: {e}. Continuing with console only."
        )

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (usually module name like __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"wiggum.{name}")


class LoggerMixin:
    """Mixin class to add logging capability to any class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(
            self.__class__.__module__ + "." + self.__class__.__name__
        )

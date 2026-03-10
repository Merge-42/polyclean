import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import Logger


def setup_logging(
    log_level: str = "INFO",
    log_file: Path | str | None = None,
) -> None:
    """Configure Loguru for the application.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, only stdout is used.
                  Supports rotation keywords: "500 MB", "1 week", etc.

    """
    logger.remove()

    # Console: stdout with colored output
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File: optional, with rotation and compression
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_path),
            level=log_level,
            rotation="500 MB",
            retention="7 days",
            compression="zip",
            enqueue=True,
            serialize=False,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        )


def get_logger() -> "Logger":
    """Return the configured logger instance."""
    return logger

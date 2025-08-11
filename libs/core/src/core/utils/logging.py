"""
Logging utilities for core and application-wide use.

Provides a standardized logger configuration that can be imported and used
across all Python-based applications and libraries in the project.
"""

import logging
import sys
from typing import Optional


def get_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    stream: Optional[object] = None,
    fmt: Optional[str] = None,
) -> logging.Logger:
    """Return a configured logger instance.

    Args:
        name: Logger name. If None, use root logger.
        level: Logging level (default: logging.INFO).
        stream: Stream to log to (default: sys.stdout).
        fmt: Log message format string.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler_stream = stream if stream is not None else sys.stdout
        handler = logging.StreamHandler(handler_stream)
        formatter = logging.Formatter(
            fmt or "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    return logger


def set_global_logging_level(level: int) -> None:
    """Set the logging level for all loggers.
        NOTSET = 0
        DEBUG = 10
        INFO = 20
        WARNING = 30
        ERROR = 40
        CRITICAL = 50
    Args:
        level: Logging level (e.g., logging.DEBUG).
    """
    logging.basicConfig(level=level)
    for logger_name in logging.root.manager.loggerDict:
        logging.getLogger(logger_name).setLevel(level)


# Provide a default logger for convenience
logger = get_logger("core")

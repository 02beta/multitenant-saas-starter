"""
Logging utilities for core and application-wide use.

Provides a standardized logger configuration that can be imported and used
across all Python-based applications and libraries in the project.

Includes optional integration with Axiom for centralized log aggregation.
"""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

try:  # Prefer a soft import so core works without axiom installed
    import axiom  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    axiom = None  # type: ignore


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


class CoreAxiomHandler(logging.Handler):
    """Logging handler that forwards records to Axiom.

    This handler is intentionally minimal and synchronous to keep the initial
    integration simple. It can be replaced with a more advanced/batched
    implementation later if needed.
    """

    def __init__(
        self,
        dataset: str,
        *,
        token: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> None:
        """Initialize the handler with dataset and credentials.

        Args:
            dataset: Target Axiom dataset name.
            token: Axiom API token. Defaults to ``AXIOM_TOKEN`` env var.
            org_id: Axiom organization ID. Defaults to ``AXIOM_ORG_ID`` env var.
        """
        super().__init__()
        if axiom is None:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "axiom-py is not installed. Add it to your environment to use "
                "Axiom logging."
            )

        resolved_token = token or os.getenv("AXIOM_TOKEN", "")
        resolved_org_id = org_id or os.getenv("AXIOM_ORG_ID", "")
        if not resolved_token or not resolved_org_id:
            raise RuntimeError(
                "AXIOM_TOKEN and AXIOM_ORG_ID must be set to use Axiom logging."
            )

        # axiom.Client(token=..., org_id=...)
        self._client = axiom.Client(
            token=resolved_token, org_id=resolved_org_id
        )
        self._dataset = dataset

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        """Emit a single logging record to Axiom."""
        try:
            # Prefer formatted message so custom formatters are respected
            message = self.format(record)
            event = {
                "_time": datetime.fromtimestamp(
                    record.created, tz=timezone.utc
                ).isoformat(),
                "message": message,
                "level": record.levelname,
                "logger": record.name,
                "pathname": record.pathname,
                "lineno": record.lineno,
                "function": record.funcName,
                "process": record.process,
                "thread": record.thread,
            }
            if record.exc_info:
                try:
                    event["exc_info"] = self.formatException(record.exc_info)
                except Exception:
                    event["exc_info"] = "<unavailable>"

            # Synchronous ingest of a single event. Keep minimal for now.
            self._client.ingest(self._dataset, [event])
        except Exception:
            # Never raise from logging handlers
            self.handleError(record)


def setup_logging(
    *,
    environment_name: Optional[str] = None,
    token: Optional[str] = None,
    org_id: Optional[str] = None,
    level: int = logging.INFO,
) -> None:
    """Configure root logging to forward records to Axiom.

    Args:
        environment_name: Environment label used to build the dataset name as
            ``api-<ENVIRONMENT>``. If not provided, falls back to the
            ``ENVIRONMENT`` or ``APP_ENV`` env vars, defaulting to
            ``development``.
        token: Axiom API token. Defaults to ``AXIOM_TOKEN`` env var.
        org_id: Axiom organization ID. Defaults to ``AXIOM_ORG_ID`` env var.
        level: Root logger level. Defaults to ``logging.INFO``.
    """
    env = (
        environment_name
        or os.getenv("ENVIRONMENT")
        or os.getenv("APP_ENV")
        or "development"
    )
    dataset = f"api-{env}"

    handler = CoreAxiomHandler(dataset=dataset, token=token, org_id=org_id)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


# Provide a default logger for convenience
logger = get_logger("core")

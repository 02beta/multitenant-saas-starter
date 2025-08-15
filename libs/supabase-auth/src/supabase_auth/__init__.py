"""Supabase authentication provider.

This module initializes logging for the Supabase auth provider.
If the `axiom-py` client is available and the required environment
variables are set, logs will also be shipped to Axiom.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from core.domains.auth.factory import AuthProviderRegistry

from .config import SupabaseConfig
from .provider import SupabaseAuthProvider

logger = logging.getLogger("supabase_auth")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# Optional: Axiom logging if axiom-py is available and configured
try:  # Try to import axiom client
    from axiom import Client as _AxiomClient  # type: ignore

    _AXIOM_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _AXIOM_AVAILABLE = False


def _maybe_attach_axiom_handler() -> None:
    """Attach an Axiom logging handler if environment is configured.

    Requires AXIOM_TOKEN and AXIOM_ORG_ID (or AXIOM_ORG). Dataset defaults to
    "supabase-auth" and can be overridden with AXIOM_DATASET.
    """

    if not _AXIOM_AVAILABLE:
        logger.info(
            "Axiom logging not configured. Install 'axiom-py' and set "
            "AXIOM_TOKEN/AXIOM_ORG_ID to aggregate logs."
        )
        return

    token = os.getenv("AXIOM_TOKEN")
    org_id = os.getenv("AXIOM_ORG_ID") or os.getenv("AXIOM_ORG")
    dataset = os.getenv("AXIOM_DATASET", "supabase-auth")

    if not token or not org_id:
        logger.info(
            "Axiom client available but missing AXIOM_TOKEN/AXIOM_ORG_ID. "
            "Set these env vars to enable centralized log aggregation."
        )
        return

    class _AxiomHandler(logging.Handler):
        """Minimal Axiom logging handler using axiom-py client."""

        def __init__(self, axiom_client: Any, axiom_dataset: str) -> None:
            super().__init__()
            self._client = axiom_client
            self._dataset = axiom_dataset

        def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
            try:
                message = self.format(record)
                event = {
                    "message": message,
                    "level": record.levelname,
                    "logger": record.name,
                    "module": record.module,
                    "function": record.funcName,
                    "time": datetime.now(timezone.utc).isoformat(),
                }
                self._client.ingest(self._dataset, [event])
            except Exception:
                # Never let logging raise
                pass

    try:
        axiom_client = _AxiomClient(token, org_id)
        axiom_handler = _AxiomHandler(axiom_client, dataset)
        axiom_handler.setLevel(logging.INFO)
        axiom_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
        )

        logger.addHandler(axiom_handler)
        logger.info(
            "Axiom logging enabled for dataset '%s' (org: %s)", dataset, org_id
        )
    except Exception:
        logger.info(
            "Failed to initialize Axiom logging. Ensure 'axiom-py' is "
            "installed and AXIOM_TOKEN/AXIOM_ORG_ID are set."
        )


_maybe_attach_axiom_handler()


def create_supabase_provider(config: dict) -> SupabaseAuthProvider:
    """Factory function for Supabase provider."""
    supabase_config = SupabaseConfig(**config)
    return SupabaseAuthProvider(supabase_config)


# Auto-register the provider when this package is imported
AuthProviderRegistry.register_provider("supabase", create_supabase_provider)

__all__ = [
    "SupabaseAuthProvider",
    "SupabaseConfig",
    "create_supabase_provider",
]

"""main backend-core exports"""

from .config import settings
from .database import (
    DatabaseManager,
    create_tables,
    create_tables_async,
    db_manager,
    get_async_session,
    get_session,
)
from .utils import (
    get_logger,
    set_global_logging_level,
    setup_logging,
)
from .utils import (
    logger as core_logger,
)

__all__ = [
    "settings",
    "core_logger",
    "get_logger",
    "set_global_logging_level",
    "setup_logging",
    "core_logger",
    "DatabaseManager",
    "create_tables",
    "create_tables_async",
    "db_manager",
    "get_async_session",
    "get_session",
]

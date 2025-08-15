"""
Enhanced database connection and session management using PostgreSQL as the backend.
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from ..config import settings
from ..utils import get_logger
from .exceptions import (
    AsyncNotConfiguredError,
    MissingDatabaseURLError,
    TableCreationError,
    TableDropError,
    TransactionCommitError,
    TransactionRollbackError,
)

__all__ = [
    "DatabaseManager",
    "db_manager",
    "create_schemas",
    "create_schemas_async",
    "create_tables",
    "create_tables_async",
    "get_session",
    "get_async_session",
]

logger = get_logger(__name__)

# Database URLs from settings
DATABASE_URL = settings.database_url
ASYNC_DATABASE_URL = settings.database_async_url

if not DATABASE_URL:
    raise MissingDatabaseURLError("DATABASE_URL")

if not ASYNC_DATABASE_URL:
    raise MissingDatabaseURLError("DATABASE_ASYNC_URL")

# Create engines
engine = create_engine(DATABASE_URL, echo=False)
async_engine = (
    create_async_engine(ASYNC_DATABASE_URL, echo=False)
    if ASYNC_DATABASE_URL
    else None
)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = (
    async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    if async_engine
    else None
)


class DatabaseManager:
    """Database session manager with both sync and async support."""

    def __init__(self):
        self.engine = engine
        self.async_engine = async_engine
        self.SessionLocal = SessionLocal
        self.AsyncSessionLocal = AsyncSessionLocal

    def get_sync_session(self) -> Session:
        """Get a synchronous database session."""
        return self.SessionLocal()

    @contextmanager
    def get_sync_session_context(self) -> Generator[Session, None, None]:
        """Get a synchronous database session with context management."""
        session = self.get_sync_session()
        try:
            yield session
            try:
                session.commit()
            except Exception as e:
                raise TransactionCommitError(str(e))
        except Exception as e:
            try:
                session.rollback()
            except Exception as rollback_error:
                raise TransactionRollbackError(rollback_error) from e
            raise
        finally:
            session.close()

    async def get_async_session(self) -> AsyncSession:
        """Get an asynchronous database session."""
        if not self.AsyncSessionLocal:
            raise AsyncNotConfiguredError("get_async_session")
        return self.AsyncSessionLocal()

    @asynccontextmanager
    async def get_async_session_context(
        self,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get an asynchronous database session with context management."""
        if not self.AsyncSessionLocal:
            raise AsyncNotConfiguredError("get_async_session_context")

        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                try:
                    await session.commit()
                except Exception as e:
                    raise TransactionCommitError(str(e))
            except Exception as e:
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    raise TransactionRollbackError(rollback_error) from e
                raise

    def get_schema_names(self, models: list | None = None):
        """Get all schema names from the models."""
        schema_names = set()
        if models is not None:
            target_models = models
        else:
            target_models = [m for m in SQLModel.metadata.tables.values()]

        for model in target_models:
            schema_names.add(model.schema)
        return schema_names

    def create_schemas(self, models: list | None = None):
        """Create all database schemas.

        Extracts schema names from the models' __table_args__ property and
        creates them in the database if they do not already exist.
        """
        if not self.engine:
            logger.error("Database engine not configured")
            return

        schema_names = self.get_schema_names(models)

        if schema_names:
            with self.engine.connect() as conn:
                for schema in schema_names:
                    logger.info(f"Creating schema: {schema}")
                    conn.execute(
                        text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
                    )
                conn.commit()
            logger.info(f"Schemas created: {schema_names}")

    async def create_schemas_async(self, models: list | None = None):
        """Create all database schemas asynchronously."""
        if not self.async_engine:
            raise AsyncNotConfiguredError("create_schemas_async")

        schema_names = self.get_schema_names(models)

        if schema_names:
            async with self.async_engine.connect() as conn:
                for schema in schema_names:
                    logger.info(f"Creating schema (async): {schema}")
                    await conn.execute(
                        text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
                    )
                await conn.commit()
            logger.info(f"Schemas created: {schema_names}")

    def create_tables(self, models: list | None = None):
        """Create all database tables.

        Args:
            models: list of SQLModel classes to create tables for, or None to
                create all tables from SQLModel.metadata.
        """
        try:
            if models:
                # Create tables for specific models
                for model in models:
                    try:
                        logger.info(
                            f"Creating tables for model: "
                            f"{getattr(model, '__tablename__', model.__name__)}"
                        )
                        model.metadata.create_all(self.engine)
                    except Exception as e:
                        table_name = getattr(
                            model, "__tablename__", model.__name__
                        )
                        raise TableCreationError(table_name, str(e))
            else:
                logger.info("Creating all tables from SQLModel.metadata")
                SQLModel.metadata.create_all(self.engine)
        except TableCreationError:
            raise
        except Exception as e:
            raise TableCreationError("all tables", str(e))

    async def create_tables_async(self, models: list | None = None):
        """Create all database tables asynchronously.

        Args:
            models: list of SQLModel classes to create tables for, or None to
                create all tables from SQLModel.metadata.
        """
        if not self.async_engine:
            raise AsyncNotConfiguredError("create_tables_async")

        try:
            if models:
                # Create tables for specific models
                for model in models:
                    try:
                        logger.info(
                            f"Creating tables for model (async): "
                            f"{getattr(model, '__tablename__', model.__name__)}"
                        )
                        async with self.async_engine.begin() as conn:
                            await conn.run_sync(model.metadata.create_all)
                    except Exception as e:
                        table_name = getattr(
                            model, "__tablename__", model.__name__
                        )
                        raise TableCreationError(table_name, str(e))
            else:
                logger.info(
                    "Creating all tables from SQLModel.metadata (async)"
                )
                async with self.async_engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all)
        except TableCreationError:
            raise
        except Exception as e:
            raise TableCreationError("all tables", str(e))

    def drop_tables(self, models: list | None = None):
        """Drop all database tables.

        Args:
            models: list of SQLModel classes to drop tables for, or None to
                drop all tables from SQLModel.metadata.
        """
        try:
            if models:
                # Drop tables for specific models
                for model in models:
                    try:
                        logger.info(
                            f"Dropping tables for model: "
                            f"{getattr(model, '__tablename__', model.__name__)}"
                        )
                        model.metadata.drop_all(self.engine)
                    except Exception as e:
                        table_name = getattr(
                            model, "__tablename__", model.__name__
                        )
                        raise TableDropError(table_name, str(e))
            else:
                logger.info("Dropping all tables from SQLModel.metadata")
                SQLModel.metadata.drop_all(self.engine)
        except TableDropError:
            raise
        except Exception as e:
            raise TableDropError("all tables", str(e))

    async def drop_tables_async(self, models: list | None = None):
        """Drop all database tables asynchronously.

        Args:
            models: list of SQLModel classes to drop tables for, or None to
                drop all tables from SQLModel.metadata.
        """
        if not self.async_engine:
            raise AsyncNotConfiguredError("drop_tables_async")

        try:
            if models:
                # Drop tables for specific models
                for model in models:
                    try:
                        logger.info(
                            f"Dropping tables for model (async): "
                            f"{getattr(model, '__tablename__', model.__name__)}"
                        )
                        async with self.async_engine.begin() as conn:
                            await conn.run_sync(model.metadata.drop_all)
                    except Exception as e:
                        table_name = getattr(
                            model, "__tablename__", model.__name__
                        )
                        raise TableDropError(table_name, str(e))
            else:
                logger.info(
                    "Dropping all tables from SQLModel.metadata (async)"
                )
                async with self.async_engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.drop_all)
        except TableDropError:
            raise
        except Exception as e:
            raise TableDropError("all tables", str(e))


# Global database manager instance
db_manager = DatabaseManager()


def create_schemas(models: list | None = None):
    """Create all database schemas."""
    logger.info("Creating database schemas")
    db_manager.create_schemas(models)


async def create_schemas_async(models: list | None = None):
    """Create all database schemas."""
    logger.info("Creating database schemas asynchronously")
    await db_manager.create_schemas_async(models)


def create_tables(models: list | None = None):
    """Create all database tables."""
    logger.info("Creating database tables")
    db_manager.create_tables(models)


async def create_tables_async(models: list | None = None):
    """Create all database tables asynchronously."""
    logger.info("Creating database tables asynchronously")
    await db_manager.create_tables_async(models)


def get_session() -> Generator[Session, None, None]:
    """Get database session with proper context management."""
    logger.info("Getting database session")
    with db_manager.get_sync_session_context() as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session with proper context management."""
    async with db_manager.get_async_session_context() as session:
        yield session

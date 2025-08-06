"""Core library exceptions for database and general operations."""

from typing import Any, Dict, Optional

__all__ = [
    "CoreException",
    "DatabaseConfigurationError",
    "MissingDatabaseURLError",
    "InvalidDatabaseURLError",
    "AsyncNotConfiguredError",
    "DatabaseConnectionError",
    "ConnectionPoolExhaustedError",
    "DatabaseUnavailableError",
    "SessionError",
    "SessionNotActiveError",
    "SessionAlreadyClosedError",
    "TransactionError",
    "TransactionRollbackError",
    "TransactionCommitError",
    "DeadlockError",
    "SchemaError",
    "TableCreationError",
    "TableDropError",
    "SchemaValidationError",
    "QueryError",
    "QueryTimeoutError",
    "InvalidQueryError",
    "DataIntegrityError",
    "UniqueConstraintViolationError",
    "ForeignKeyViolationError",
    "CheckConstraintViolationError",
]


class CoreException(Exception):
    """Base exception for all core library exceptions."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize core exception.

        Args:
            message: Error message
            error_code: Optional error code for categorization
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


# Database Configuration Exceptions
class DatabaseConfigurationError(CoreException):
    """Base exception for database configuration errors."""

    pass


class MissingDatabaseURLError(DatabaseConfigurationError):
    """Raised when required database URL is not configured."""

    def __init__(self, env_var: str = "SUPABASE_DB_URL"):
        """
        Initialize missing database URL error.

        Args:
            env_var: Name of the missing environment variable
        """
        super().__init__(
            message=f"{env_var} environment variable is required",
            error_code="MISSING_DB_URL",
            details={"env_var": env_var},
        )


class InvalidDatabaseURLError(DatabaseConfigurationError):
    """Raised when database URL format is invalid."""

    def __init__(self, url: str, reason: str):
        """
        Initialize invalid database URL error.

        Args:
            url: The invalid URL
            reason: Reason why the URL is invalid
        """
        super().__init__(
            message=f"Invalid database URL: {reason}",
            error_code="INVALID_DB_URL",
            details={"url": url, "reason": reason},
        )


class AsyncNotConfiguredError(DatabaseConfigurationError):
    """Raised when async operations are attempted without async configuration."""

    def __init__(self, operation: str):
        """
        Initialize async not configured error.

        Args:
            operation: The operation that requires async configuration
        """
        super().__init__(
            message=f"Async database not configured. Set SUPABASE_DB_URL_ASYNC environment variable to use {operation}",
            error_code="ASYNC_NOT_CONFIGURED",
            details={"operation": operation},
        )


# Database Connection Exceptions
class DatabaseConnectionError(CoreException):
    """Base exception for database connection errors."""

    pass


class ConnectionPoolExhaustedError(DatabaseConnectionError):
    """Raised when database connection pool is exhausted."""

    def __init__(self, pool_size: int, timeout: float):
        """
        Initialize connection pool exhausted error.

        Args:
            pool_size: Current pool size
            timeout: Timeout value in seconds
        """
        super().__init__(
            message=f"Connection pool exhausted (size: {pool_size}, timeout: {timeout}s)",
            error_code="POOL_EXHAUSTED",
            details={"pool_size": pool_size, "timeout": timeout},
        )


class DatabaseUnavailableError(DatabaseConnectionError):
    """Raised when database is unavailable or unreachable."""

    def __init__(self, host: str, port: int, reason: Optional[str] = None):
        """
        Initialize database unavailable error.

        Args:
            host: Database host
            port: Database port
            reason: Additional reason for unavailability
        """
        message = f"Database at {host}:{port} is unavailable"
        if reason:
            message += f": {reason}"

        super().__init__(
            message=message,
            error_code="DB_UNAVAILABLE",
            details={"host": host, "port": port, "reason": reason},
        )


# Session Management Exceptions
class SessionError(CoreException):
    """Base exception for session-related errors."""

    pass


class SessionNotActiveError(SessionError):
    """Raised when operations are attempted on an inactive session."""

    def __init__(self, operation: str):
        """
        Initialize session not active error.

        Args:
            operation: Operation that was attempted
        """
        super().__init__(
            message=f"Cannot perform {operation} on inactive session",
            error_code="SESSION_NOT_ACTIVE",
            details={"operation": operation},
        )


class SessionAlreadyClosedError(SessionError):
    """Raised when operations are attempted on a closed session."""

    def __init__(self):
        """Initialize session already closed error."""
        super().__init__(
            message="Session has already been closed",
            error_code="SESSION_CLOSED",
        )


# Transaction Exceptions
class TransactionError(CoreException):
    """Base exception for transaction-related errors."""

    pass


class TransactionRollbackError(TransactionError):
    """Raised when transaction rollback fails."""

    def __init__(self, original_error: Exception):
        """
        Initialize transaction rollback error.

        Args:
            original_error: The original error that caused the rollback
        """
        super().__init__(
            message=f"Failed to rollback transaction: {str(original_error)}",
            error_code="ROLLBACK_FAILED",
            details={"original_error": str(original_error)},
        )


class TransactionCommitError(TransactionError):
    """Raised when transaction commit fails."""

    def __init__(self, reason: str):
        """
        Initialize transaction commit error.

        Args:
            reason: Reason for commit failure
        """
        super().__init__(
            message=f"Failed to commit transaction: {reason}",
            error_code="COMMIT_FAILED",
            details={"reason": reason},
        )


class DeadlockError(TransactionError):
    """Raised when a database deadlock is detected."""

    def __init__(self, resources: Optional[str] = None):
        """
        Initialize deadlock error.

        Args:
            resources: Description of resources involved in deadlock
        """
        message = "Database deadlock detected"
        if resources:
            message += f" involving: {resources}"

        super().__init__(
            message=message,
            error_code="DEADLOCK",
            details={"resources": resources},
        )


# Schema/Migration Exceptions
class SchemaError(CoreException):
    """Base exception for schema-related errors."""

    pass


class TableCreationError(SchemaError):
    """Raised when table creation fails."""

    def __init__(self, table_name: str, reason: str):
        """
        Initialize table creation error.

        Args:
            table_name: Name of the table
            reason: Reason for creation failure
        """
        super().__init__(
            message=f"Failed to create table '{table_name}': {reason}",
            error_code="TABLE_CREATE_FAILED",
            details={"table_name": table_name, "reason": reason},
        )


class TableDropError(SchemaError):
    """Raised when table drop operation fails."""

    def __init__(self, table_name: str, reason: str):
        """
        Initialize table drop error.

        Args:
            table_name: Name of the table
            reason: Reason for drop failure
        """
        super().__init__(
            message=f"Failed to drop table '{table_name}': {reason}",
            error_code="TABLE_DROP_FAILED",
            details={"table_name": table_name, "reason": reason},
        )


class SchemaValidationError(SchemaError):
    """Raised when schema validation fails."""

    def __init__(self, model_name: str, issues: list[str]):
        """
        Initialize schema validation error.

        Args:
            model_name: Name of the model
            issues: List of validation issues
        """
        super().__init__(
            message=f"Schema validation failed for model '{model_name}'",
            error_code="SCHEMA_VALIDATION_FAILED",
            details={"model_name": model_name, "issues": issues},
        )


# Query Exceptions
class QueryError(CoreException):
    """Base exception for query-related errors."""

    pass


class QueryTimeoutError(QueryError):
    """Raised when a query exceeds the timeout limit."""

    def __init__(self, query: str, timeout: float):
        """
        Initialize query timeout error.

        Args:
            query: The query that timed out (truncated)
            timeout: Timeout value in seconds
        """
        truncated_query = query[:100] + "..." if len(query) > 100 else query
        super().__init__(
            message=f"Query exceeded timeout of {timeout}s",
            error_code="QUERY_TIMEOUT",
            details={"query": truncated_query, "timeout": timeout},
        )


class InvalidQueryError(QueryError):
    """Raised when a query is invalid or malformed."""

    def __init__(self, query: str, reason: str):
        """
        Initialize invalid query error.

        Args:
            query: The invalid query (truncated)
            reason: Reason why query is invalid
        """
        truncated_query = query[:100] + "..." if len(query) > 100 else query
        super().__init__(
            message=f"Invalid query: {reason}",
            error_code="INVALID_QUERY",
            details={"query": truncated_query, "reason": reason},
        )


# Data Integrity Exceptions
class DataIntegrityError(CoreException):
    """Base exception for data integrity violations."""

    pass


class UniqueConstraintViolationError(DataIntegrityError):
    """Raised when a unique constraint is violated."""

    def __init__(self, table: str, column: str, value: Any):
        """
        Initialize unique constraint violation error.

        Args:
            table: Table name
            column: Column name
            value: The duplicate value
        """
        super().__init__(
            message=f"Unique constraint violated: {column}='{value}' already exists in {table}",
            error_code="UNIQUE_VIOLATION",
            details={"table": table, "column": column, "value": str(value)},
        )


class ForeignKeyViolationError(DataIntegrityError):
    """Raised when a foreign key constraint is violated."""

    def __init__(self, table: str, column: str, referenced_table: str):
        """
        Initialize foreign key violation error.

        Args:
            table: Table name
            column: Column with foreign key
            referenced_table: Referenced table name
        """
        super().__init__(
            message=f"Foreign key constraint violated: {table}.{column} references "
            f"non-existent record in {referenced_table}",
            error_code="FK_VIOLATION",
            details={
                "table": table,
                "column": column,
                "referenced_table": referenced_table,
            },
        )


class CheckConstraintViolationError(DataIntegrityError):
    """Raised when a check constraint is violated."""

    def __init__(self, table: str, constraint_name: str, value: Any):
        """
        Initialize check constraint violation error.

        Args:
            table: Table name
            constraint_name: Name of the constraint
            value: The value that violated the constraint
        """
        super().__init__(
            message=f"Check constraint '{constraint_name}' violated in table '{table}'",
            error_code="CHECK_VIOLATION",
            details={
                "table": table,
                "constraint_name": constraint_name,
                "value": str(value),
            },
        )

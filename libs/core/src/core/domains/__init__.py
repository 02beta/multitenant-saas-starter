"""Core package for the workspace."""

# Explicit imports for better IDE support
from .memberships import (
    # Exceptions
    InsufficientPermissionsError,
    InvitationAlreadyAcceptedError,
    InvitationNotFoundError,
    LastOwnerRemovalError,
    # Models and schemas
    Membership,
    MembershipCreate,
    MembershipNotFoundError,
    MembershipPublic,
    # Repository and service
    MembershipRepository,
    # Enums
    MembershipRole,
    MembershipService,
    MembershipStatus,
    MembershipUpdate,
    NotOrganizationMemberError,
    UserAlreadyInvitedError,
    UserAlreadyMemberError,
)
from .organizations import (
    Organization,
    OrganizationCreate,
    OrganizationPublic,
    OrganizationRepository,
    OrganizationService,
    OrganizationUpdate,
)
from .users import (
    PasswordService,
    User,
    UserCreate,
    UserPublic,
    UserRepository,
    UserService,
    UserUpdate,
)

# Re-export all public names from database, exceptions, organizations, memberships, and users

__all__ = [
    # Database
    "DatabaseManager",
    "create_tables",
    "create_tables_async",
    "db_manager",
    "get_async_session",
    "get_session",
    # Exceptions
    "AsyncNotConfiguredError",
    "CheckConstraintViolationError",
    "ConnectionPoolExhaustedError",
    "CoreException",
    "DatabaseConfigurationError",
    "DatabaseConnectionError",
    "DatabaseUnavailableError",
    "DataIntegrityError",
    "DeadlockError",
    "ForeignKeyViolationError",
    "InsufficientPermissionsError",
    "InvalidDatabaseURLError",
    "InvalidQueryError",
    "InvitationAlreadyAcceptedError",
    "InvitationNotFoundError",
    "LastOwnerRemovalError",
    "MissingDatabaseURLError",
    "NotOrganizationMemberError",
    "QueryError",
    "QueryTimeoutError",
    "SchemaError",
    "SchemaValidationError",
    "SessionAlreadyClosedError",
    "SessionError",
    "SessionNotActiveError",
    "TableCreationError",
    "TableDropError",
    "MembershipNotFoundError",
    "TransactionCommitError",
    "TransactionError",
    "TransactionRollbackError",
    "UniqueConstraintViolationError",
    "UserAlreadyInvitedError",
    "UserAlreadyMemberError",
    # Models and schemas
    "PasswordService",
    "Organization",
    "OrganizationCreate",
    "OrganizationPublic",
    "OrganizationUpdate",
    "Membership",
    "MembershipCreate",
    "MembershipPublic",
    "MembershipUpdate",
    "User",
    "UserCreate",
    "UserPublic",
    "UserUpdate",
    # Enums
    "MembershipRole",
    "MembershipStatus",
    # Repository and service
    "OrganizationRepository",
    "OrganizationService",
    "MembershipRepository",
    "MembershipService",
    "UserRepository",
    "UserService",
]

# Backend Core

The `backend-core` workspace is a Python library that provides the foundational infrastructure for backend applications. It contains core functionality including database connection management, domain models, data validation, exception handling, and shared utilities. This workspace serves as the central hub for business logic and data access patterns across the application.

Key features:

- **Database Management**: PostgreSQL connection handling with both sync and async support
- **Domain Models**: SQLModel-based data models with audit trails and soft delete capabilities
- **Configuration**: Centralized settings management using Pydantic
- **Exception Handling**: Comprehensive error handling with domain-specific exceptions
- **Common Utilities**: Shared mixins, protocols, and base classes for consistent development patterns

## Workspace Structure

```sh
# ./libs/backend-core/src/core/
├── config/
│   ├── __init__.py
│   └── settings.py
├── domains/
│   ├── __init__.py
│   ├── users/
│   ├── organizations/
│   └── memberships/
├── common/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── mixins.py
│   └── protocols.py
├── database/
│   ├── __init__.py
│   └── database.py
│   └── exceptions.py
├── __init__.py
```

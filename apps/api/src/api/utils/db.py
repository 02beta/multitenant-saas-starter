"""Environment utilities for the API."""


def is_development_environment() -> bool:
    """Return True if the API is running in a development environment.

    This checks common environment variables to determine if the current
    environment is development (not CI, not production, not staging).
    """
    import os

    env = os.getenv("ENV", "").lower()
    ci = os.getenv("CI", "").lower() == "true"
    node_env = os.getenv("NODE_ENV", "").lower()
    fastapi_env = os.getenv("FASTAPI_ENV", "").lower()

    if ci:
        return False

    # Check for explicit development indicators
    if (
        env == "development"
        or node_env == "development"
        or fastapi_env == "development"
    ):
        return True

    # Check for explicit production or staging indicators
    if (
        env in ("production", "prod", "staging")
        or node_env in ("production", "prod", "staging")
        or fastapi_env in ("production", "prod", "staging")
    ):
        return False

    return True


async def create_schemas() -> bool:
    """Create database schemas defined in a string array.

    This function creates schemas in the database for each schema name
    specified in the internal list, using an async database session.
    """
    from core.database import async_get_session

    schema_names = [
        "usr",
        "org",
        "auth",
    ]

    async with async_get_session() as session:
        for schema in schema_names:
            await session.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}";')
        await session.commit()

    return True

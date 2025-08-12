"""FastAPI application with domain-driven routes."""

from contextlib import asynccontextmanager

from core.common.exceptions import DomainException
from core.database import create_tables
from fastapi import FastAPI

from .config import settings
from .routes import (
    auth_router,
    memberships_router,
    organizations_router,
    users_router,
)
from .utils import handle_domain_exception


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    print("Starting up API...")

    # Minimal logging setup (dataset: api-<ENVIRONMENT>)
    try:
        from core import core_logger, setup_logging

        setup_logging()
        core_logger.info("Logging initialized")
    except Exception as ax_err:  # Soft-fail if not configured
        core_logger.warning("logging not initialized: %s", ax_err)

    create_tables()
    print("Database tables created successfully")
    yield
    print("Shutting down API...")


app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    cors_origins=settings.api_cors_origins,
    version=settings.api_version,
    lifespan=lifespan,
    debug=settings.debug,
)

# Include domain endpoint routers
app.include_router(auth_router, prefix="/v1")
app.include_router(users_router, prefix="/v1")
app.include_router(organizations_router, prefix="/v1")
app.include_router(memberships_router, prefix="/v1")


# Exception handling
@app.exception_handler(DomainException)
async def domain_exception_handler(request, exc: DomainException):
    return handle_domain_exception(exc)


# Root routes
@app.get("/")
async def root():
    return {"message": "Multi-tenant SaaS API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

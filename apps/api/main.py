"""FastAPI application with domain-driven routes."""

from contextlib import asynccontextmanager

from core.common.exceptions import DomainException
from core.database import create_tables
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .middleware.csrf import CSRFMiddleware
from .middleware.rate_limit import RateLimitMiddleware
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
    version=settings.api_version,
    lifespan=lifespan,
    debug=settings.debug,
)

# Add Rate Limiting middleware (must be before other middleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,  # General rate limit
    requests_per_hour=1000,
    auth_endpoints_per_minute=10,  # Stricter for auth endpoints
    ban_duration_seconds=300,  # 5 minute ban for violations
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-CSRF-Token",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
)

# Add CSRF protection middleware
app.add_middleware(
    CSRFMiddleware,
    cookie_secure=not settings.debug,  # Use secure cookies in production
    exempt_paths=[
        "/v1/auth/login",
        "/v1/auth/signup",
        "/v1/auth/forgot-password",
        "/docs",
        "/openapi.json",
        "/health",
        "/",
    ],
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

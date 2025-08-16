"""CSRF Protection Middleware for FastAPI."""

import secrets
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection using Double Submit Cookie pattern.

    This middleware:
    1. Generates a CSRF token and sets it as a cookie
    2. Validates the token on state-changing requests (POST, PUT, DELETE, PATCH)
    3. Exempts read-only operations (GET, HEAD, OPTIONS)
    """

    def __init__(
        self,
        app: ASGIApp,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        cookie_secure: bool = True,
        cookie_httponly: bool = False,  # Must be False for JS to read it
        cookie_samesite: str = "strict",
        exempt_paths: list[str] = None,
    ):
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        # Default exempt paths for auth endpoints that need to work without existing session
        self.exempt_paths = exempt_paths or [
            "/auth/login",
            "/auth/signup",
            "/auth/forgot-password",
            "/docs",
            "/openapi.json",
            "/health",
        ]

    async def dispatch(self, request: Request, call_next):
        # Check if path is exempt
        if any(
            request.url.path.startswith(path) for path in self.exempt_paths
        ):
            return await call_next(request)

        # Get or generate CSRF token
        csrf_cookie = request.cookies.get(self.cookie_name)

        # For safe methods, just ensure cookie exists
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)

            # Set CSRF cookie if it doesn't exist
            if not csrf_cookie:
                csrf_token = secrets.token_urlsafe(32)
                response.set_cookie(
                    key=self.cookie_name,
                    value=csrf_token,
                    secure=self.cookie_secure,
                    httponly=self.cookie_httponly,
                    samesite=self.cookie_samesite,
                    max_age=3600,  # 1 hour
                )

            return response

        # For state-changing methods, validate CSRF token
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            # Get token from header
            csrf_header = request.headers.get(self.header_name)

            # Validate tokens match
            if not csrf_cookie or not csrf_header:
                logger.warning(
                    f"CSRF token missing - Cookie: {bool(csrf_cookie)}, "
                    f"Header: {bool(csrf_header)}, Path: {request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token missing",
                )

            if csrf_cookie != csrf_header:
                logger.warning(
                    f"CSRF token mismatch - Path: {request.url.path}, "
                    f"Method: {request.method}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token invalid",
                )

            # Tokens valid, proceed with request
            response = await call_next(request)

            # Rotate token for extra security (optional)
            # Commented out to avoid breaking concurrent requests
            # new_token = secrets.token_urlsafe(32)
            # response.set_cookie(
            #     key=self.cookie_name,
            #     value=new_token,
            #     secure=self.cookie_secure,
            #     httponly=self.cookie_httponly,
            #     samesite=self.cookie_samesite,
            #     max_age=3600
            # )

            return response

        # For other methods, just pass through
        return await call_next(request)


def get_csrf_token(request: Request) -> Optional[str]:
    """Helper function to get CSRF token from request cookies."""
    return request.cookies.get("csrf_token")

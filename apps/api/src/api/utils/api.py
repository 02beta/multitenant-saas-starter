"""API utilities for handling domain exceptions."""

from typing import Any, Dict

from core.common.exceptions import DomainException
from fastapi import HTTPException
from fastapi.responses import JSONResponse

__all__ = ["handle_domain_exception", "domain_exception_to_response"]


def handle_domain_exception(exc: DomainException) -> HTTPException:
    """
    Convert a domain exception to a FastAPI HTTPException.

    Args:
        exc: Domain exception

    Returns:
        HTTPException with appropriate status code and detail
    """
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.message,
        headers={"X-Error-Type": exc.__class__.__name__},
    )


def domain_exception_to_response(exc: DomainException) -> JSONResponse:
    """
    Convert a domain exception to a JSON response.

    Args:
        exc: Domain exception

    Returns:
        JSONResponse with error details
    """
    content: Dict[str, Any] = {
        "error": {
            "message": exc.message,
            "type": exc.__class__.__name__,
        }
    }

    if exc.details:
        content["error"]["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers={"X-Error-Type": exc.__class__.__name__},
    )

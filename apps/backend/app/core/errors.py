import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class IronMindException(Exception):
    """Base exception for all IronMind domain errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ResourceNotFoundError(IronMindException):
    def __init__(self, message: str = "Requested resource was not found.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, details=details)


class ModelInferenceError(IronMindException):
    def __init__(self, message: str = "Local model inference failure.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, details=details)


class AirgapBreachAttemptError(IronMindException):
    def __init__(self, message: str = "External network call blocked by Sovereign Air-gap enforcement.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, details=details)


def register_error_handlers(app: FastAPI) -> None:
    """Register centralized custom exception handlers for FastAPI application."""

    @app.exception_handler(IronMindException)
    async def ironmind_exception_handler(request: Request, exc: IronMindException):
        logger.error("IronMind Error: %s | Status: %s | Details: %s", exc.message, exc.status_code, exc.details)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                    "details": exc.details,
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation Error on %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "type": "RequestValidationError",
                    "message": "Invalid request payload or query parameter format.",
                    "details": exc.errors(),
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled Server Exception on %s: %s", request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "type": "InternalServerError",
                    "message": "An unexpected internal server error occurred in local workbench.",
                    "details": str(exc),
                }
            }
        )

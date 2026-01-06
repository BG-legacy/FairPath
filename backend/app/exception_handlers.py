"""
Global exception handlers for safe error responses
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils.security import sanitize_error_message
from app.config import settings
import asyncio
import logging
from openai import APITimeoutError, APIError


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with sanitized error messages and specific error codes
    """
    # Don't sanitize if it's already a formatted error response
    if isinstance(exc.detail, dict) and "success" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # Sanitize the detail message
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    sanitized_detail = sanitize_error_message(detail)
    
    # Map status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        413: "PAYLOAD_TOO_LARGE",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": sanitized_detail,
            "error": error_code,
            "status_code": exc.status_code
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors with sanitized messages and detailed field errors
    """
    errors = exc.errors()
    sanitized_errors = []
    
    for error in errors:
        # Extract field name and message
        field = ".".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        error_type = error.get("type", "validation_error")
        sanitized_msg = sanitize_error_message(msg)
        
        sanitized_errors.append({
            "field": field,
            "message": sanitized_msg,
            "type": error_type
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error: Please check your input",
            "error": "VALIDATION_ERROR",
            "status_code": 422,
            "details": sanitized_errors
        }
    )


async def timeout_exception_handler(request: Request, exc: asyncio.TimeoutError) -> JSONResponse:
    """
    Handle timeout exceptions, especially for OpenAI endpoints
    """
    # Check if this is an OpenAI-related timeout
    is_openai_endpoint = any(
        path in request.url.path for path in ['/openai', '/coach', '/paths', '/resume']
    )
    
    error_message = (
        "The request timed out. This may be due to high server load or a slow external service. "
        "Please try again in a moment."
        if is_openai_endpoint
        else "The request took too long to complete. Please try again."
    )
    
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "success": False,
            "message": error_message,
            "error": "TIMEOUT_ERROR",
            "status_code": 504
        }
    )


async def openai_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle OpenAI-specific exceptions (timeout, API errors)
    """
    if isinstance(exc, APITimeoutError) or isinstance(exc, asyncio.TimeoutError):
        return await timeout_exception_handler(request, exc)
    
    if isinstance(exc, APIError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "success": False,
                "message": "External service error. Please try again in a moment.",
                "error": "EXTERNAL_SERVICE_ERROR",
                "status_code": 502
            }
        )
    
    # Fall through to general handler
    return await general_exception_handler(request, exc)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions with safe error messages
    Prevents leaking sensitive information like stack traces, file paths, etc.
    """
    # Check for timeout errors
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return await timeout_exception_handler(request, exc)
    
    # Check for OpenAI errors
    if isinstance(exc, (APITimeoutError, APIError)):
        return await openai_exception_handler(request, exc)
    
    # Log the full error server-side (in production, use proper logging)
    if settings.ENV_MODE == "development":
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {type(exc).__name__}", exc_info=exc)
    else:
        # In production, log to proper logging system (implement as needed)
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    
    # Return safe error message to client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred. Please try again later.",
            "error": "INTERNAL_SERVER_ERROR",
            "status_code": 500
        }
    )



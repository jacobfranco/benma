"""FastAPI application factory."""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from benma_api import __version__
from benma_api.api.routes import dev_router, router
from benma_api.config import Settings, get_settings
from benma_api.errors import BenmaError
from benma_api.logging import configure_logging
from benma_api.schemas import ErrorResponse

logger = logging.getLogger("benma_api.requests")


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging()
    app = FastAPI(
        title="Benma API",
        version=__version__,
        description="Truth-preserving Mandarin speech evidence API",
        responses={
            401: {"model": ErrorResponse, "description": "Authentication failed"},
            404: {"model": ErrorResponse, "description": "Resource unavailable to account"},
            422: {"model": ErrorResponse, "description": "Invalid request or audio"},
            500: {"model": ErrorResponse, "description": "Internal failure"},
            502: {"model": ErrorResponse, "description": "Provider rejected or malformed"},
            503: {"model": ErrorResponse, "description": "Provider unavailable"},
            504: {"model": ErrorResponse, "description": "Provider timeout"},
        },
    )
    app.state.settings = resolved
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.effective_cors_origins,
        allow_credentials=False,  # The client sends an explicit bearer token, not cookies.
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Server-Timing"] if resolved.environment == "development" else [],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request completed",
            extra={"request_id": request_id, "status_code": response.status_code},
        )
        return response

    @app.exception_handler(BenmaError)
    async def benma_error_handler(request: Request, exc: BenmaError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "retryable": exc.retryable,
                    "request_id": request_id,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "request validation failed",
                    "retryable": False,
                    "request_id": request_id,
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "not_found" if exc.status_code == 404 else "request_error",
                    "message": "resource not found"
                    if exc.status_code == 404
                    else "request could not be completed",
                    "retryable": False,
                    "request_id": request_id,
                }
            },
        )

    @app.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception(
            "unhandled request failure",
            exc_info=exc,
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_failure",
                    "message": "an internal failure occurred",
                    "retryable": False,
                    "request_id": request_id,
                }
            },
        )

    app.include_router(router)
    if resolved.dev_auth_enabled:
        app.include_router(dev_router)
    return app


app = create_app()

"""FastAPI application entry point."""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import create_db_and_tables
from .exceptions import APIException
from .health import router as health_router
from .middleware import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from .rate_limit import RateLimitMiddleware
from .routes import posts_router, profile_router, users_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Blog API application")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API Version: {settings.api_version}")

    # Create database tables
    create_db_and_tables()

    yield

    # Shutdown
    logger.info("Shutting down Blog API application")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url=f"/{settings.api_version}/docs",
    redoc_url=f"/{settings.api_version}/redoc",
    openapi_url=f"/{settings.api_version}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware (order matters - last added is executed first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# Add rate limiting (configure per environment)
if settings.environment == "production":
    app.add_middleware(RateLimitMiddleware, default_rate=100, default_per=60)
else:
    # More lenient for development
    app.add_middleware(RateLimitMiddleware, default_rate=1000, default_per=60)


# Exception handlers
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions.

    Args:
        request: Incoming request
        exc: API exception

    Returns:
        JSON error response
    """
    logger.warning(f"API exception: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle request validation errors.

    Args:
        request: Incoming request
        exc: Validation error

    Returns:
        JSON error response
    """
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: Incoming request
        exc: Exception

    Returns:
        JSON error response
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "details": {} if settings.is_production else {"message": str(exc)},
        },
    )


# Health check endpoint (simple, for backward compatibility)
@app.get("/health", tags=["Health"])
async def health_check_simple() -> dict[str, str]:
    """Simple health check endpoint (backward compatible).

    Returns:
        Health status
    """
    return {"status": "healthy", "version": settings.api_version}


# Register routers
app.include_router(health_router)  # Detailed health checks
api_prefix = f"/{settings.api_version}"
app.include_router(profile_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(posts_router, prefix=api_prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
        log_level=settings.log_level.lower(),
    )

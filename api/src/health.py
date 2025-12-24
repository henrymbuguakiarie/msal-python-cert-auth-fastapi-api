"""Health check endpoints for monitoring and observability."""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlmodel import Session, text

from .config import Settings, get_settings
from .database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


class HealthStatus(BaseModel):
    """Health status response model."""

    status: str
    timestamp: datetime
    version: str
    environment: str
    checks: dict[str, dict[str, Any]]


class HealthCheck:
    """Health check service for monitoring system components."""

    def __init__(self, settings: Settings, session: Session | None = None) -> None:
        """Initialize health check service.

        Args:
            settings: Application settings
            session: Database session (optional)
        """
        self.settings = settings
        self.session = session

    async def check_database(self) -> dict[str, Any]:
        """Check database connectivity.

        Returns:
            Database health status
        """
        try:
            if self.session:
                # Execute simple query
                self.session.exec(text("SELECT 1"))
                return {
                    "status": "healthy",
                    "message": "Database is accessible",
                    "database_url": self.settings.database_url.split("@")[-1],  # Hide credentials
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "message": f"Database error: {str(e)}"}

        return {"status": "unknown", "message": "Database session not available"}

    async def check_jwks_endpoint(self) -> dict[str, Any]:
        """Check JWKS endpoint connectivity.

        Returns:
            JWKS endpoint health status
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.settings.jwks_endpoint)
                response.raise_for_status()

                return {
                    "status": "healthy",
                    "message": "JWKS endpoint is accessible",
                    "endpoint": self.settings.jwks_endpoint,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                }
        except Exception as e:
            logger.error(f"JWKS health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"JWKS endpoint error: {str(e)}",
                "endpoint": self.settings.jwks_endpoint,
            }

    async def get_full_status(self) -> HealthStatus:
        """Get comprehensive health status.

        Returns:
            Full health status with all checks
        """
        # Run all health checks
        checks = {
            "database": await self.check_database(),
            "jwks": await self.check_jwks_endpoint(),
        }

        # Determine overall status
        overall_status = "healthy"
        if any(check.get("status") == "unhealthy" for check in checks.values()):
            overall_status = "unhealthy"
        elif any(check.get("status") == "unknown" for check in checks.values()):
            overall_status = "degraded"

        return HealthStatus(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            version=self.settings.api_version,
            environment=self.settings.environment,
            checks=checks,
        )


@router.get(
    "",
    response_model=HealthStatus,
    summary="Comprehensive health check",
    description="Returns detailed health status of all system components",
)
async def health_check_detailed(
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> HealthStatus:
    """Detailed health check endpoint.

    Args:
        settings: Application settings
        session: Database session

    Returns:
        Comprehensive health status
    """
    health_checker = HealthCheck(settings, session)
    return await health_checker.get_full_status()


@router.get(
    "/live",
    summary="Liveness probe",
    description="Simple liveness check for Kubernetes/container orchestration",
    status_code=status.HTTP_200_OK,
)
async def liveness() -> dict[str, str]:
    """Liveness probe endpoint.

    Returns:
        Simple status indicating service is alive
    """
    return {"status": "alive"}


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Readiness check for Kubernetes/container orchestration",
    status_code=status.HTTP_200_OK,
)
async def readiness(
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Readiness probe endpoint.

    Checks if the service is ready to accept traffic.

    Args:
        settings: Application settings
        session: Database session

    Returns:
        Readiness status
    """
    health_checker = HealthCheck(settings, session)

    # Check critical dependencies
    db_status = await health_checker.check_database()

    if db_status.get("status") == "healthy":
        return {"status": "ready"}

    return {"status": "not ready", "reason": "database unavailable"}

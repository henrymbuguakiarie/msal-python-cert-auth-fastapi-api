"""Standard API response models for consistent response structure."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    field: str | None = Field(
        None, description="Field that caused the error (if applicable)"
    )
    details: dict[str, Any] | None = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """Standard error response format.

    Provides consistent error structure across all API endpoints.
    """

    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error description")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When error occurred"
    )
    path: str | None = Field(None, description="Request path that caused error")
    correlation_id: str | None = Field(
        None, description="Request correlation ID for tracing"
    )
    errors: list[ErrorDetail] | None = Field(
        None, description="Detailed error list (for validation errors)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid request data",
                "status_code": 422,
                "timestamp": "2024-12-24T12:00:00Z",
                "path": "/v1/posts",
                "correlation_id": "abc123",
                "errors": [
                    {
                        "code": "VALUE_ERROR",
                        "message": "Title must be between 1 and 200 characters",
                        "field": "title",
                    }
                ],
            }
        }


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response wrapper.

    Wraps successful responses with metadata for consistency.
    """

    success: bool = Field(True, description="Indicates successful operation")
    data: T = Field(..., description="Response data")
    message: str | None = Field(None, description="Optional success message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": 1, "title": "Example Post"},
                "message": "Post created successfully",
                "timestamp": "2024-12-24T12:00:00Z",
            }
        }


class ListResponse(BaseModel, Generic[T]):
    """Standard list response with metadata.

    Provides consistent structure for list endpoints with pagination info.
    """

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items available")
    count: int = Field(..., description="Number of items in current response")
    skip: int = Field(0, description="Number of items skipped")
    limit: int = Field(100, description="Maximum items per response")
    has_next: bool = Field(..., description="Whether more items are available")
    has_prev: bool = Field(..., description="Whether previous items exist")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        skip: int = 0,
        limit: int = 100,
    ) -> "ListResponse[T]":
        """Create list response with calculated metadata.

        Args:
            items: List of items for current page
            total: Total number of items available
            skip: Number of items skipped
            limit: Maximum items per page

        Returns:
            List response with metadata
        """
        count = len(items)
        has_next = (skip + count) < total
        has_prev = skip > 0

        return cls(
            items=items,
            total=total,
            count=count,
            skip=skip,
            limit=limit,
            has_next=has_next,
            has_prev=has_prev,
        )

    class Config:
        json_schema_extra = {
            "example": {
                "items": [{"id": 1, "title": "Post 1"}, {"id": 2, "title": "Post 2"}],
                "total": 100,
                "count": 2,
                "skip": 0,
                "limit": 2,
                "has_next": True,
                "has_prev": False,
            }
        }


class CreatedResponse(BaseModel, Generic[T]):
    """Response for resource creation (HTTP 201).

    Includes location information for newly created resource.
    """

    success: bool = Field(True, description="Creation successful")
    data: T = Field(..., description="Created resource")
    location: str | None = Field(None, description="URI of created resource")
    message: str = Field("Resource created successfully", description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": 42, "title": "New Post"},
                "location": "/v1/posts/42",
                "message": "Post created successfully",
            }
        }


class DeletedResponse(BaseModel):
    """Response for successful deletion (HTTP 200/204).

    Simple confirmation of deletion operation.
    """

    success: bool = Field(True, description="Deletion successful")
    message: str = Field("Resource deleted successfully", description="Success message")
    deleted_id: int | str | None = Field(None, description="ID of deleted resource")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Post deleted successfully",
                "deleted_id": 42,
            }
        }


class UpdatedResponse(BaseModel, Generic[T]):
    """Response for successful update operation.

    Returns updated resource with metadata.
    """

    success: bool = Field(True, description="Update successful")
    data: T = Field(..., description="Updated resource")
    message: str = Field("Resource updated successfully", description="Success message")
    changes: list[str] | None = Field(
        None, description="List of fields that were modified"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": 42, "title": "Updated Post"},
                "message": "Post updated successfully",
                "changes": ["title", "content"],
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str = Field(
        ..., description="Overall health status (healthy/degraded/unhealthy)"
    )
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )
    environment: str = Field(..., description="Current environment")
    checks: dict[str, dict[str, Any]] = Field(
        ..., description="Component-specific health checks"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "v1",
                "timestamp": "2024-12-24T12:00:00Z",
                "environment": "production",
                "checks": {
                    "database": {
                        "status": "healthy",
                        "message": "Database is accessible",
                    },
                    "jwks": {
                        "status": "healthy",
                        "message": "JWKS endpoint is accessible",
                    },
                },
            }
        }

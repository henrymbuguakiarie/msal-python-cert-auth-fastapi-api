"""Pagination utilities for API responses."""
from typing import Any, Generic, TypeVar
from urllib.parse import urlencode

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum items to return")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")
    has_next: bool = Field(..., description="Whether there are more items")
    has_prev: bool = Field(..., description="Whether there are previous items")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.
    
    Provides consistent pagination structure across all list endpoints.
    """
    
    items: list[T] = Field(..., description="List of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        skip: int = 0,
        limit: int = 100,
    ) -> "PaginatedResponse[T]":
        """Create paginated response with metadata.
        
        Args:
            items: List of items for current page
            total: Total number of items available
            skip: Number of items skipped
            limit: Maximum items per page
            
        Returns:
            Paginated response with metadata
        """
        has_next = (skip + limit) < total
        has_prev = skip > 0
        
        meta = PaginationMeta(
            total=total,
            skip=skip,
            limit=limit,
            has_next=has_next,
            has_prev=has_prev,
        )
        
        return cls(items=items, meta=meta)


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters for large datasets."""
    
    cursor: str | None = Field(None, description="Cursor for next page")
    limit: int = Field(100, ge=1, le=1000, description="Maximum items to return")


class CursorPaginationMeta(BaseModel):
    """Cursor-based pagination metadata."""
    
    next_cursor: str | None = Field(None, description="Cursor for next page")
    prev_cursor: str | None = Field(None, description="Cursor for previous page")
    has_next: bool = Field(..., description="Whether there are more items")
    limit: int = Field(..., description="Maximum items per page")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Generic cursor-based paginated response.
    
    More efficient for large datasets than offset pagination.
    """
    
    items: list[T] = Field(..., description="List of items")
    meta: CursorPaginationMeta = Field(..., description="Pagination metadata")

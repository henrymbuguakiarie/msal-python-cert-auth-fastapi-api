"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base user model."""

    display_name: str | None = None


class UserResponse(UserBase):
    """User response model."""

    id: int
    oid: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileResponse(BaseModel):
    """Profile response model from /profile endpoint."""

    oid: str = Field(..., description="Microsoft Entra ID object ID")
    name: str | None = Field(None, description="User name from token")
    email: str | None = Field(None, description="User email from token")
    preferred_username: str | None = Field(None, description="Preferred username")


class BlogPostBase(BaseModel):
    """Base blog post model."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class BlogPostCreate(BlogPostBase):
    """Blog post creation request."""

    pass


class BlogPostUpdate(BlogPostBase):
    """Blog post update request."""

    pass


class BlogPostResponse(BlogPostBase):
    """Blog post response model."""

    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BlogPostWithAuthor(BlogPostResponse):
    """Blog post with author information."""

    author: UserResponse | None = None


class PaginatedBlogPosts(BaseModel):
    """Paginated blog posts response."""

    posts: list[BlogPostWithAuthor]
    total: int
    skip: int
    limit: int

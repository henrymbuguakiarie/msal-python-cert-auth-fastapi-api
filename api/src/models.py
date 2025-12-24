"""Database models and schemas."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Field as SQLField
from sqlmodel import Relationship, SQLModel

if TYPE_CHECKING:
    pass


# Database Models (SQLModel)
class User(SQLModel, table=True):
    """User model representing authenticated Microsoft Entra ID users.
    
    Attributes:
        id: Internal database primary key
        oid: Microsoft Entra ID object ID (unique identifier)
        display_name: Optional display name from Entra ID
        created_at: Timestamp of user creation
        updated_at: Timestamp of last update
    """
    
    __tablename__ = "users"
    
    id: int | None = SQLField(default=None, primary_key=True)
    oid: str = SQLField(index=True, unique=True, nullable=False)
    display_name: str | None = SQLField(default=None)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class BlogPost(SQLModel, table=True):
    """Blog post model.
    
    Attributes:
        id: Primary key
        title: Post title (required)
        content: Post content (required)
        author_id: Foreign key to User
        created_at: Timestamp of post creation
        updated_at: Timestamp of last update
    """
    
    __tablename__ = "blog_posts"
    
    id: int | None = SQLField(default=None, primary_key=True)
    title: str = SQLField(nullable=False, index=True)
    content: str = SQLField(nullable=False)
    author_id: int = SQLField(foreign_key="users.id", nullable=False)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


# Define relationships after both models are defined
User.posts = Relationship(back_populates="author", sa_relationship_kwargs={"lazy": "select"})
BlogPost.author = Relationship(back_populates="posts", sa_relationship_kwargs={"lazy": "select"})


# API Schemas (Pydantic)
class UserBase(BaseModel):
    """Base user schema."""
    
    display_name: str | None = Field(None, description="User display name")


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    oid: str = Field(..., description="Microsoft Entra ID object ID")


class UserResponse(UserBase):
    """Schema for user responses."""
    
    id: int = Field(..., description="Internal user ID")
    oid: str = Field(..., description="Microsoft Entra ID object ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = {"from_attributes": True}


class BlogPostBase(BaseModel):
    """Base blog post schema."""
    
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    content: str = Field(..., min_length=1, description="Post content")


class BlogPostCreate(BlogPostBase):
    """Schema for creating a blog post."""
    
    pass


class BlogPostUpdate(BaseModel):
    """Schema for updating a blog post."""
    
    title: str | None = Field(None, min_length=1, max_length=200, description="Post title")
    content: str | None = Field(None, min_length=1, description="Post content")


class BlogPostResponse(BlogPostBase):
    """Schema for blog post responses."""
    
    id: int = Field(..., description="Post ID")
    author_id: int = Field(..., description="Author user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = {"from_attributes": True}


class BlogPostDetailResponse(BlogPostResponse):
    """Schema for detailed blog post responses including author info."""
    
    author: UserResponse = Field(..., description="Post author information")
    
    model_config = {"from_attributes": True}


class ProfileResponse(BaseModel):
    """Schema for user profile responses."""
    
    oid: str = Field(..., description="Microsoft Entra ID object ID")
    name: str | None = Field(None, description="User name from token")
    email: str | None = Field(None, description="User email from token")
    preferred_username: str | None = Field(None, description="Preferred username")

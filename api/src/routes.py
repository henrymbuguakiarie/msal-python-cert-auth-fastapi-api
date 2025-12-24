"""API route handlers."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from .auth import get_current_user, get_user_oid
from .database import get_session
from .exceptions import APIException, AuthorizationError, ResourceNotFoundError
from .models import (
    BlogPostCreate,
    BlogPostDetailResponse,
    BlogPostResponse,
    BlogPostUpdate,
    ProfileResponse,
    UserResponse,
)
from .services import BlogPostService, UserService

logger = logging.getLogger(__name__)

# Create routers
profile_router = APIRouter(prefix="/profile", tags=["Profile"])
users_router = APIRouter(prefix="/users", tags=["Users"])
posts_router = APIRouter(prefix="/posts", tags=["Blog Posts"])


# Profile endpoints
@profile_router.get(
    "",
    response_model=ProfileResponse,
    summary="Get current user profile",
    description="Retrieve profile information from the access token claims",
)
async def get_profile(
    claims: dict[str, Any] = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ProfileResponse:
    """Get current user's profile from token claims.

    Args:
        claims: JWT token claims
        session: Database session

    Returns:
        User profile information
    """
    service = UserService(session)
    return service.get_profile_from_claims(claims)


# User endpoints
@users_router.post(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register current user",
    description="Create or retrieve user record for the authenticated user",
)
async def register_user(
    user_oid: str = Depends(get_user_oid),
    claims: dict[str, Any] = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserResponse:
    """Register or retrieve current user.

    Args:
        user_oid: User's Microsoft Entra ID object ID
        claims: JWT token claims
        session: Database session

    Returns:
        User information
    """
    service = UserService(session)
    display_name = claims.get("name")
    user, created = service.get_or_create_user(user_oid, display_name)

    if created:
        logger.info(f"Registered new user: {user_oid}")

    return UserResponse.model_validate(user)


# Blog post endpoints
@posts_router.post(
    "",
    response_model=BlogPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a blog post",
    description="Create a new blog post for the authenticated user",
)
async def create_post(
    post_data: BlogPostCreate,
    user_oid: str = Depends(get_user_oid),
    session: Session = Depends(get_session),
) -> BlogPostResponse:
    """Create a new blog post.

    Args:
        post_data: Blog post creation data
        user_oid: Current user's object ID
        session: Database session

    Returns:
        Created blog post
    """
    try:
        service = BlogPostService(session)
        post = service.create_post(post_data, user_oid)
        return BlogPostResponse.model_validate(post)
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create post",
        ) from e


@posts_router.get(
    "",
    response_model=list[BlogPostDetailResponse],
    summary="List all blog posts",
    description="Retrieve a paginated list of all blog posts",
)
async def list_posts(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    _: dict[str, Any] = Depends(get_current_user),  # Require authentication
) -> list[BlogPostDetailResponse]:
    """List all blog posts.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        session: Database session

    Returns:
        List of blog posts with author information
    """
    from .repositories import UserRepository

    service = BlogPostService(session)
    posts = service.list_posts(skip=skip, limit=limit)

    # Manually construct response with author information
    user_repo = UserRepository(session)
    result = []
    for post in posts:
        author = user_repo.get_by_id(post.author_id)
        if author:
            result.append(
                BlogPostDetailResponse(
                    id=post.id,
                    title=post.title,
                    content=post.content,
                    author_id=post.author_id,
                    created_at=post.created_at,
                    updated_at=post.updated_at,
                    author=UserResponse(
                        id=author.id,
                        oid=author.oid,
                        display_name=author.display_name,
                        created_at=author.created_at,
                        updated_at=author.updated_at,
                    ),
                )
            )
    return result


@posts_router.get(
    "/{post_id}",
    response_model=BlogPostDetailResponse,
    summary="Get a blog post",
    description="Retrieve a specific blog post by ID",
)
async def get_post(
    post_id: int,
    session: Session = Depends(get_session),
    _: dict[str, Any] = Depends(get_current_user),  # Require authentication
) -> BlogPostDetailResponse:
    """Get a specific blog post.

    Args:
        post_id: Post ID
        session: Database session

    Returns:
        Blog post with author information

    Raises:
        HTTPException: If post not found
    """
    from .repositories import UserRepository

    try:
        service = BlogPostService(session)
        post = service.get_post(post_id)

        # Manually construct response with author information
        user_repo = UserRepository(session)
        author = user_repo.get_by_id(post.author_id)

        if author:
            return BlogPostDetailResponse(
                id=post.id,
                title=post.title,
                content=post.content,
                author_id=post.author_id,
                created_at=post.created_at,
                updated_at=post.updated_at,
                author=UserResponse(
                    id=author.id,
                    oid=author.oid,
                    display_name=author.display_name,
                    created_at=author.created_at,
                    updated_at=author.updated_at,
                ),
            )
        else:
            raise ResourceNotFoundError("Author", post.author_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e


@posts_router.put(
    "/{post_id}",
    response_model=BlogPostResponse,
    summary="Update a blog post",
    description="Update a blog post (only the author can update)",
)
async def update_post(
    post_id: int,
    post_data: BlogPostUpdate,
    user_oid: str = Depends(get_user_oid),
    session: Session = Depends(get_session),
) -> BlogPostResponse:
    """Update a blog post.

    Args:
        post_id: Post ID
        post_data: Update data
        user_oid: Current user's object ID
        session: Database session

    Returns:
        Updated blog post

    Raises:
        HTTPException: If post not found or user lacks permission
    """
    try:
        service = BlogPostService(session)
        post = service.update_post(post_id, post_data, user_oid)
        return BlogPostResponse.model_validate(post)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e


@posts_router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a blog post",
    description="Delete a blog post (only the author can delete)",
)
async def delete_post(
    post_id: int,
    user_oid: str = Depends(get_user_oid),
    session: Session = Depends(get_session),
) -> None:
    """Delete a blog post.

    Args:
        post_id: Post ID
        user_oid: Current user's object ID
        session: Database session

    Raises:
        HTTPException: If post not found or user lacks permission
    """
    try:
        service = BlogPostService(session)
        service.delete_post(post_id, user_oid)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message) from e
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message) from e

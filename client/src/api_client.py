"""API client for calling the downstream FastAPI.

This module provides a service layer for interacting with the blog API,
including automatic Bearer token injection and error handling.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from .config import Settings
from .exceptions import (
    APIClientError,
    APIServerError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from .models import (
    BlogPostCreate,
    BlogPostResponse,
    BlogPostUpdate,
    BlogPostWithAuthor,
    PaginatedBlogPosts,
    ProfileResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)


class APIClient:
    """Client for calling the downstream FastAPI.

    This class handles:
    - Bearer token injection
    - Request/response serialization
    - Error handling and logging
    - Type-safe API calls

    Attributes:
        settings: Application settings
        base_url: Base URL of the API
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the API client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.base_url = settings.api_base_url.rstrip("/")

    def _get_headers(self, access_token: str) -> dict[str, str]:
        """Build HTTP headers with Bearer token.

        Args:
            access_token: JWT access token

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Returns:
            Response JSON data

        Raises:
            UnauthorizedError: For 401 responses
            ForbiddenError: For 403 responses
            NotFoundError: For 404 responses
            BadRequestError: For 400 responses
            APIServerError: For 5xx responses
            APIClientError: For other error responses
        """
        try:
            response_data = response.json()
        except Exception:
            response_data = {"detail": response.text}

        if response.status_code == 401:
            logger.error(f"Unauthorized: {response_data}")
            raise UnauthorizedError(
                response_data.get("detail", "Authentication required")
            )
        elif response.status_code == 403:
            logger.error(f"Forbidden: {response_data}")
            raise ForbiddenError(
                response_data.get("detail", "Insufficient permissions")
            )
        elif response.status_code == 404:
            logger.error(f"Not found: {response_data}")
            raise NotFoundError(response_data.get("detail", "Resource not found"))
        elif response.status_code == 400:
            logger.error(f"Bad request: {response_data}")
            raise BadRequestError(response_data.get("detail", "Invalid request"))
        elif response.status_code >= 500:
            logger.error(f"Server error: {response_data}")
            raise APIServerError(response_data.get("detail", "Internal server error"))
        elif not response.ok:
            logger.error(f"API error: {response.status_code} - {response_data}")
            raise APIClientError(
                response_data.get("detail", f"API error: {response.status_code}")
            )

        return response_data

    def get_profile(self, access_token: str) -> ProfileResponse:
        """Get current user profile.

        Args:
            access_token: Bearer token

        Returns:
            User profile data

        Raises:
            APIClientError: If the request fails
        """
        url = f"{self.base_url}/v1/profile"
        headers = self._get_headers(access_token)

        logger.info("Fetching user profile")
        response = requests.get(url, headers=headers, timeout=10)
        data = self._handle_response(response)

        return ProfileResponse(**data)

    def list_posts(
        self,
        access_token: str,
        skip: int = 0,
        limit: int = 10,
    ) -> PaginatedBlogPosts:
        """List blog posts with pagination.

        Args:
            access_token: JWT access token
            skip: Number of posts to skip
            limit: Maximum number of posts to return

        Returns:
            Paginated blog posts

        Raises:
            APIClientError: If the request fails
        """
        url = f"{self.base_url}/v1/posts"
        headers = self._get_headers(access_token)
        params = {"skip": skip, "limit": limit}

        logger.info(f"Fetching posts (skip={skip}, limit={limit})")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = self._handle_response(response)

        # API returns a list, wrap it in pagination structure
        if isinstance(data, list):
            return PaginatedBlogPosts(
                posts=data, total=len(data), skip=skip, limit=limit
            )
        return PaginatedBlogPosts(**data)

    def get_post(self, access_token: str, post_id: int) -> BlogPostWithAuthor:
        """Get a single blog post by ID.

        Args:
            access_token: JWT access token
            post_id: Blog post ID

        Returns:
            Blog post with author information

        Raises:
            NotFoundError: If post doesn't exist
            APIClientError: If the request fails
        """
        url = f"{self.base_url}/v1/posts/{post_id}"
        headers = self._get_headers(access_token)

        logger.info(f"Fetching post {post_id}")
        response = requests.get(url, headers=headers, timeout=10)
        data = self._handle_response(response)

        return BlogPostWithAuthor(**data)

    def create_post(
        self,
        access_token: str,
        post_data: BlogPostCreate,
    ) -> BlogPostResponse:
        """Create a new blog post.

        Args:
            access_token: JWT access token
            post_data: Blog post creation data

        Returns:
            Created blog post

        Raises:
            BadRequestError: If validation fails
            APIClientError: If the request fails
        """
        url = f"{self.base_url}/v1/posts"
        headers = self._get_headers(access_token)
        payload = post_data.model_dump()

        logger.info(f"Creating post: {post_data.title}")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = self._handle_response(response)

        return BlogPostResponse(**data)

    def update_post(
        self,
        access_token: str,
        post_id: int,
        post_data: BlogPostUpdate,
    ) -> BlogPostResponse:
        """Update an existing blog post.

        Args:
            access_token: JWT access token
            post_id: Blog post ID
            post_data: Updated blog post data

        Returns:
            Updated blog post

        Raises:
            NotFoundError: If post doesn't exist
            ForbiddenError: If user doesn't own the post
            BadRequestError: If validation fails
            APIClientError: If the request fails
        """
        url = f"{self.base_url}/v1/posts/{post_id}"
        headers = self._get_headers(access_token)
        payload = post_data.model_dump()

        logger.info(f"Updating post {post_id}")
        response = requests.put(url, headers=headers, json=payload, timeout=10)
        data = self._handle_response(response)

        return BlogPostResponse(**data)

    def delete_post(self, access_token: str, post_id: int) -> dict[str, str]:
        """Delete a blog post.

        Args:
            access_token: JWT access token
            post_id: Blog post ID

        Returns:
            Success message dictionary

        Raises:
            NotFoundError: If post doesn't exist
            ForbiddenError: If user doesn't own the post
            APIClientError: If the request fails
        """
        url = f"{self.base_url}/v1/posts/{post_id}"
        headers = self._get_headers(access_token)

        logger.info(f"Deleting post {post_id}")
        response = requests.delete(url, headers=headers, timeout=10)
        data = self._handle_response(response)

        return data

"""Unit tests for API client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.api_client import APIClient
from src.config import Settings
from src.exceptions import (
    APIServerError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from src.models import BlogPostCreate, BlogPostUpdate


class TestAPIClient:
    """Tests for APIClient class."""

    def test_initialization(self, mock_settings: Settings) -> None:
        """Test API client initialization."""
        # Arrange & Act
        client = APIClient(mock_settings)

        # Assert
        assert client.settings == mock_settings
        assert client.base_url == "http://localhost:8000"

    def test_get_headers(self, mock_settings: Settings) -> None:
        """Test building HTTP headers with Bearer token."""
        # Arrange
        client = APIClient(mock_settings)
        token = "test_access_token"

        # Act
        headers = client._get_headers(token)

        # Assert
        assert headers["Authorization"] == f"Bearer {token}"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    @patch("src.api_client.requests.get")
    def test_get_profile_success(
        self,
        mock_get: MagicMock,
        mock_settings: Settings,
        sample_user_response: dict,
    ) -> None:
        """Test successful profile retrieval."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = sample_user_response
        mock_get.return_value = mock_response

        client = APIClient(mock_settings)

        # Act
        profile = client.get_profile("test_token")

        # Assert
        assert profile.id == 1
        assert profile.oid == "12345678-1234-1234-1234-123456789012"
        assert profile.display_name == "Test User"
        mock_get.assert_called_once()

    @patch("src.api_client.requests.get")
    def test_get_profile_unauthorized(
        self,
        mock_get: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test profile retrieval with unauthorized error."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        mock_get.return_value = mock_response

        client = APIClient(mock_settings)

        # Act & Assert
        with pytest.raises(UnauthorizedError) as exc_info:
            client.get_profile("invalid_token")

        assert "Invalid token" in str(exc_info.value)

    @patch("src.api_client.requests.get")
    def test_list_posts_success(
        self,
        mock_get: MagicMock,
        mock_settings: Settings,
        sample_posts_list: dict,
    ) -> None:
        """Test successful posts listing."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = sample_posts_list
        mock_get.return_value = mock_response

        client = APIClient(mock_settings)

        # Act
        posts = client.list_posts("test_token", skip=0, limit=10)

        # Assert
        assert posts.total == 2
        assert len(posts.posts) == 2
        assert posts.posts[0].title == "First Post"
        assert posts.skip == 0
        assert posts.limit == 10
        mock_get.assert_called_once()

    @patch("src.api_client.requests.get")
    def test_get_post_success(
        self,
        mock_get: MagicMock,
        mock_settings: Settings,
        sample_post_response: dict,
    ) -> None:
        """Test successful single post retrieval."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        post_with_author = {
            **sample_post_response,
            "author": {
                "id": 1,
                "oid": "user-oid",
                "display_name": "Test User",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            },
        }
        mock_response.json.return_value = post_with_author
        mock_get.return_value = mock_response

        client = APIClient(mock_settings)

        # Act
        post = client.get_post("test_token", 1)

        # Assert
        assert post.id == 1
        assert post.title == "Test Post"
        assert post.author is not None
        assert post.author.display_name == "Test User"

    @patch("src.api_client.requests.get")
    def test_get_post_not_found(
        self,
        mock_get: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test getting non-existent post returns 404."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Post not found"}
        mock_get.return_value = mock_response

        client = APIClient(mock_settings)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            client.get_post("test_token", 999)

        assert "Post not found" in str(exc_info.value)

    @patch("src.api_client.requests.post")
    def test_create_post_success(
        self,
        mock_post: MagicMock,
        mock_settings: Settings,
        sample_post_response: dict,
    ) -> None:
        """Test successful post creation."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 201
        mock_response.json.return_value = sample_post_response
        mock_post.return_value = mock_response

        client = APIClient(mock_settings)
        post_data = BlogPostCreate(
            title="New Post",
            content="This is new content",
        )

        # Act
        created_post = client.create_post("test_token", post_data)

        # Assert
        assert created_post.id == 1
        assert created_post.title == "Test Post"
        mock_post.assert_called_once()

    @patch("src.api_client.requests.post")
    def test_create_post_bad_request(
        self,
        mock_post: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test post creation with validation error."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Title is required"}
        mock_post.return_value = mock_response

        client = APIClient(mock_settings)
        # Use valid data but API returns 400
        post_data = BlogPostCreate(title="Valid Title", content="Content")

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            client.create_post("test_token", post_data)

        assert "Title is required" in str(exc_info.value)

    @patch("src.api_client.requests.put")
    def test_update_post_success(
        self,
        mock_put: MagicMock,
        mock_settings: Settings,
        sample_post_response: dict,
    ) -> None:
        """Test successful post update."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        updated_response = {**sample_post_response, "title": "Updated Title"}
        mock_response.json.return_value = updated_response
        mock_put.return_value = mock_response

        client = APIClient(mock_settings)
        post_data = BlogPostUpdate(
            title="Updated Title",
            content="Updated content",
        )

        # Act
        updated_post = client.update_post("test_token", 1, post_data)

        # Assert
        assert updated_post.id == 1
        assert updated_post.title == "Updated Title"
        mock_put.assert_called_once()

    @patch("src.api_client.requests.put")
    def test_update_post_forbidden(
        self,
        mock_put: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test updating post without permission."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 403
        mock_response.json.return_value = {"detail": "Not the post author"}
        mock_put.return_value = mock_response

        client = APIClient(mock_settings)
        post_data = BlogPostUpdate(title="Title", content="Content")

        # Act & Assert
        with pytest.raises(ForbiddenError) as exc_info:
            client.update_post("test_token", 1, post_data)

        assert "Not the post author" in str(exc_info.value)

    @patch("src.api_client.requests.delete")
    def test_delete_post_success(
        self,
        mock_delete: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test successful post deletion."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Post deleted"}
        mock_delete.return_value = mock_response

        client = APIClient(mock_settings)

        # Act
        result = client.delete_post("test_token", 1)

        # Assert
        assert result["message"] == "Post deleted"
        mock_delete.assert_called_once()

    @patch("src.api_client.requests.delete")
    def test_delete_post_not_found(
        self,
        mock_delete: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test deleting non-existent post."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Post not found"}
        mock_delete.return_value = mock_response

        client = APIClient(mock_settings)

        # Act & Assert
        with pytest.raises(NotFoundError):
            client.delete_post("test_token", 999)

    @patch("src.api_client.requests.get")
    def test_handle_response_server_error(
        self,
        mock_get: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test handling 500 server error."""
        # Arrange
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_get.return_value = mock_response

        client = APIClient(mock_settings)

        # Act & Assert
        with pytest.raises(APIServerError) as exc_info:
            client.get_profile("test_token")

        assert "Internal server error" in str(exc_info.value)

    def test_base_url_trailing_slash_stripped(self, mock_settings: Settings) -> None:
        """Test that trailing slash is removed from base URL."""
        # Arrange
        mock_settings.api_base_url = "http://localhost:8000/"

        # Act
        client = APIClient(mock_settings)

        # Assert
        assert client.base_url == "http://localhost:8000"

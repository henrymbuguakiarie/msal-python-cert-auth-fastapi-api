"""Integration tests for API endpoints."""

from unittest.mock import patch

import pytest
from fastapi import status

from src.models import BlogPost


@pytest.fixture(autouse=True)
def mock_jwt_validation(mock_jwt_claims):
    """Auto-mock JWT validation for all integration tests."""
    with patch("src.auth.JWTValidator.validate_token", return_value=mock_jwt_claims):
        yield


class TestHealthEndpoint:
    """Test suite for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestProfileEndpoints:
    """Test suite for profile endpoints."""

    def test_get_profile(self, client, auth_headers, mock_jwt_claims):
        """Test getting user profile."""
        response = client.get("/v1/profile", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["oid"] == mock_jwt_claims["oid"]
        assert data["name"] == mock_jwt_claims["name"]
        assert data["email"] == mock_jwt_claims["email"]

    def test_get_profile_without_auth(self, client):
        """Test profile endpoint requires authentication."""
        response = client.get("/v1/profile")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserEndpoints:
    """Test suite for user endpoints."""

    def test_register_user(self, client, auth_headers):
        """Test user registration."""
        response = client.post("/v1/users/me", headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["oid"] == "test-oid-123"
        assert "id" in data
        assert "created_at" in data

    def test_register_user_idempotent(self, client, auth_headers):
        """Test that registering same user twice returns same user."""
        # First registration
        response1 = client.post("/v1/users/me", headers=auth_headers)
        user1 = response1.json()

        # Second registration
        response2 = client.post("/v1/users/me", headers=auth_headers)
        user2 = response2.json()

        assert user1["id"] == user2["id"]
        assert user1["oid"] == user2["oid"]


class TestBlogPostEndpoints:
    """Test suite for blog post endpoints."""

    def test_create_post(self, client, auth_headers):
        """Test creating a blog post."""
        post_data = {
            "title": "My First Post",
            "content": "This is the content of my first post.",
        }

        response = client.post("/v1/posts", json=post_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == post_data["title"]
        assert data["content"] == post_data["content"]
        assert "id" in data
        assert "author_id" in data
        assert "created_at" in data

    def test_create_post_validation_error(self, client, auth_headers):
        """Test post creation with invalid data."""
        post_data = {"title": ""}  # Empty title and missing content

        response = client.post("/v1/posts", json=post_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_posts(self, client, auth_headers, test_post):
        """Test listing all posts."""
        response = client.get("/v1/posts", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Verify author information is included
        assert "author" in data[0]
        assert "oid" in data[0]["author"]

    def test_list_posts_pagination(self, client, auth_headers, session, test_user):
        """Test post listing with pagination."""
        # Create multiple posts
        for i in range(5):
            post = BlogPost(title=f"Post {i}", content=f"Content {i}", author_id=test_user.id)
            session.add(post)
        session.commit()

        response = client.get("/v1/posts?skip=2&limit=2", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_get_post(self, client, auth_headers, test_post):
        """Test getting a specific post."""
        response = client.get(f"/v1/posts/{test_post.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_post.id
        assert data["title"] == test_post.title
        assert "author" in data

    def test_get_post_not_found(self, client, auth_headers):
        """Test getting non-existent post returns 404."""
        response = client.get("/v1/posts/999", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_post(self, client, auth_headers, test_post):
        """Test updating a post as the owner."""
        update_data = {"title": "Updated Title", "content": "Updated Content"}

        response = client.put(f"/v1/posts/{test_post.id}", json=update_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["content"] == update_data["content"]

    def test_update_post_partial(self, client, auth_headers, test_post):
        """Test partial update of a post."""
        update_data = {"title": "Only Title Changed"}

        response = client.put(f"/v1/posts/{test_post.id}", json=update_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == update_data["title"]
        # Content should remain unchanged
        assert data["content"] == test_post.content

    def test_update_post_unauthorized(self, client, auth_headers, session, another_user):
        """Test updating post by non-owner returns 403."""
        # Create post owned by another user
        post = BlogPost(title="Another User's Post", content="Content", author_id=another_user.id)
        session.add(post)
        session.commit()
        session.refresh(post)

        update_data = {"title": "Unauthorized Update"}

        response = client.put(f"/v1/posts/{post.id}", json=update_data, headers=auth_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_post(self, client, auth_headers, test_post):
        """Test deleting a post as the owner."""
        response = client.delete(f"/v1/posts/{test_post.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify post is deleted
        get_response = client.get(f"/v1/posts/{test_post.id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_post_unauthorized(self, client, auth_headers, session, another_user):
        """Test deleting post by non-owner returns 403."""
        # Create post owned by another user
        post = BlogPost(title="Another User's Post", content="Content", author_id=another_user.id)
        session.add(post)
        session.commit()
        session.refresh(post)

        response = client.delete(f"/v1/posts/{post.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_post_not_found(self, client, auth_headers):
        """Test deleting non-existent post returns 404."""
        response = client.delete("/v1/posts/999", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAuthenticationRequired:
    """Test suite for authentication requirement."""

    @pytest.mark.parametrize(
        "endpoint,method",
        [
            ("/v1/profile", "GET"),
            ("/v1/users/me", "POST"),
            ("/v1/posts", "GET"),
            ("/v1/posts", "POST"),
            ("/v1/posts/1", "GET"),
            ("/v1/posts/1", "PUT"),
            ("/v1/posts/1", "DELETE"),
        ],
    )
    def test_endpoints_require_authentication(self, client, endpoint, method):
        """Test that all protected endpoints require authentication."""
        response = client.request(method, endpoint)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

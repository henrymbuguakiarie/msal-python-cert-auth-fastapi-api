"""Unit tests for service layer."""

import pytest

from src.exceptions import AuthorizationError, ResourceNotFoundError
from src.models import BlogPostCreate, BlogPostUpdate, User
from src.repositories import UserRepository
from src.services import BlogPostService, UserService


class TestUserService:
    """Test suite for UserService."""

    def test_get_or_create_user_creates_new_user(self, session):
        """Test creating a new user when none exists."""
        service = UserService(session)

        user, created = service.get_or_create_user(oid="new-user-oid", display_name="New User")

        assert created is True
        assert user.oid == "new-user-oid"
        assert user.display_name == "New User"

    def test_get_or_create_user_returns_existing_user(self, session, test_user):
        """Test returning existing user instead of creating duplicate."""
        service = UserService(session)

        user, created = service.get_or_create_user(oid=test_user.oid, display_name="Different Name")

        assert created is False
        assert user.id == test_user.id
        assert user.oid == test_user.oid
        # Display name should remain unchanged
        assert user.display_name == test_user.display_name

    def test_get_profile_from_claims(self, session):
        """Test profile extraction from JWT claims."""
        service = UserService(session)

        claims = {
            "oid": "user-oid-123",
            "name": "John Doe",
            "email": "john@example.com",
            "preferred_username": "john.doe@example.com",
        }

        profile = service.get_profile_from_claims(claims)

        assert profile.oid == "user-oid-123"
        assert profile.name == "John Doe"
        assert profile.email == "john@example.com"
        assert profile.preferred_username == "john.doe@example.com"


class TestBlogPostService:
    """Test suite for BlogPostService."""

    def test_create_post(self, session, test_user):
        """Test creating a blog post."""
        service = BlogPostService(session)

        post_data = BlogPostCreate(title="Test Post", content="Test content")

        post = service.create_post(post_data, test_user.oid)

        assert post.title == "Test Post"
        assert post.content == "Test content"
        assert post.author_id == test_user.id

    def test_create_post_creates_user_if_not_exists(self, session):
        """Test that create_post creates user if it doesn't exist."""
        service = BlogPostService(session)
        user_repo = UserRepository(session)

        post_data = BlogPostCreate(title="First Post", content="First content")

        post = service.create_post(post_data, "new-user-oid")

        assert post.title == "First Post"
        # Manually fetch the author to verify
        author = user_repo.get_by_id(post.author_id)
        assert author is not None
        assert author.oid == "new-user-oid"

    def test_list_posts(self, session, test_post):
        """Test listing all posts."""
        service = BlogPostService(session)

        posts = service.list_posts()

        assert len(posts) == 1
        assert posts[0].id == test_post.id

    def test_list_posts_with_pagination(self, session, test_user):
        """Test post listing with pagination."""
        service = BlogPostService(session)

        # Create multiple posts
        for i in range(5):
            service.create_post(
                BlogPostCreate(title=f"Post {i}", content=f"Content {i}"), test_user.oid
            )

        # Test skip and limit
        posts = service.list_posts(skip=2, limit=2)

        assert len(posts) == 2

    def test_get_post(self, session, test_post):
        """Test getting a specific post."""
        service = BlogPostService(session)

        post = service.get_post(test_post.id)

        assert post.id == test_post.id
        assert post.title == test_post.title

    def test_get_post_raises_not_found(self, session):
        """Test that get_post raises exception for non-existent post."""
        service = BlogPostService(session)

        with pytest.raises(ResourceNotFoundError) as exc_info:
            service.get_post(999)

        assert "BlogPost" in str(exc_info.value)
        assert "999" in str(exc_info.value)

    def test_update_post(self, session, test_post, test_user):
        """Test updating a post as the owner."""
        service = BlogPostService(session)

        update_data = BlogPostUpdate(title="Updated Title", content="Updated Content")

        updated_post = service.update_post(test_post.id, update_data, test_user.oid)

        assert updated_post.title == "Updated Title"
        assert updated_post.content == "Updated Content"

    def test_update_post_partial(self, session, test_post, test_user):
        """Test partial update of a post."""
        service = BlogPostService(session)

        update_data = BlogPostUpdate(title="New Title Only")

        updated_post = service.update_post(test_post.id, update_data, test_user.oid)

        assert updated_post.title == "New Title Only"
        # Content should remain unchanged
        assert updated_post.content == test_post.content

    def test_update_post_raises_authorization_error(self, session, test_post, another_user):
        """Test that update_post raises authorization error for non-owner."""
        service = BlogPostService(session)

        update_data = BlogPostUpdate(title="Unauthorized Update")

        with pytest.raises(AuthorizationError) as exc_info:
            service.update_post(test_post.id, update_data, another_user.oid)

        assert "permission" in str(exc_info.value).lower()

    def test_delete_post(self, session, test_post, test_user):
        """Test deleting a post as the owner."""
        service = BlogPostService(session)

        service.delete_post(test_post.id, test_user.oid)

        # Verify post is deleted
        with pytest.raises(ResourceNotFoundError):
            service.get_post(test_post.id)

    def test_delete_post_raises_authorization_error(self, session, test_post, another_user):
        """Test that delete_post raises authorization error for non-owner."""
        service = BlogPostService(session)

        with pytest.raises(AuthorizationError) as exc_info:
            service.delete_post(test_post.id, another_user.oid)

        assert "permission" in str(exc_info.value).lower()

    def test_validate_ownership_success(self, session, test_post, test_user):
        """Test ownership validation for owner."""
        service = BlogPostService(session)

        # Should not raise exception
        service._validate_ownership(test_post, test_user.oid)

    def test_validate_ownership_fails(self, session, test_post, another_user):
        """Test ownership validation fails for non-owner."""
        service = BlogPostService(session)

        with pytest.raises(AuthorizationError):
            service._validate_ownership(test_post, another_user.oid)

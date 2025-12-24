"""Unit tests for repository layer."""

import time

import pytest

from src.exceptions import ResourceNotFoundError
from src.models import BlogPost, User
from src.repositories import BlogPostRepository, UserRepository


class TestUserRepository:
    """Test suite for UserRepository."""

    def test_get_by_id(self, session, test_user):
        """Test retrieving user by ID."""
        repo = UserRepository(session)

        user = repo.get_by_id(test_user.id)

        assert user is not None
        assert user.id == test_user.id
        assert user.oid == test_user.oid

    def test_get_by_id_returns_none(self, session):
        """Test get_by_id returns None for non-existent user."""
        repo = UserRepository(session)

        user = repo.get_by_id(999)

        assert user is None

    def test_get_by_oid(self, session, test_user):
        """Test retrieving user by OID."""
        repo = UserRepository(session)

        user = repo.get_by_oid(test_user.oid)

        assert user is not None
        assert user.oid == test_user.oid
        assert user.id == test_user.id

    def test_get_by_oid_returns_none(self, session):
        """Test get_by_oid returns None for non-existent OID."""
        repo = UserRepository(session)

        user = repo.get_by_oid("non-existent-oid")

        assert user is None

    def test_create(self, session):
        """Test creating a new user."""
        repo = UserRepository(session)

        user = repo.create(oid="new-oid", display_name="New User")

        assert user.id is not None
        assert user.oid == "new-oid"
        assert user.display_name == "New User"
        assert user.created_at is not None

    def test_get_or_create_creates_new_user(self, session):
        """Test get_or_create creates new user when not exists."""
        repo = UserRepository(session)

        user, created = repo.get_or_create(oid="new-oid", display_name="New User")

        assert created is True
        assert user.oid == "new-oid"

    def test_get_or_create_returns_existing_user(self, session, test_user):
        """Test get_or_create returns existing user."""
        repo = UserRepository(session)

        user, created = repo.get_or_create(oid=test_user.oid)

        assert created is False
        assert user.id == test_user.id


class TestBlogPostRepository:
    """Test suite for BlogPostRepository."""

    def test_get_by_id(self, session, test_post):
        """Test retrieving post by ID."""
        repo = BlogPostRepository(session)

        post = repo.get_by_id(test_post.id)

        assert post is not None
        assert post.id == test_post.id
        assert post.title == test_post.title

    def test_get_by_id_returns_none(self, session):
        """Test get_by_id returns None for non-existent post."""
        repo = BlogPostRepository(session)

        post = repo.get_by_id(999)

        assert post is None

    def test_get_by_id_or_raise(self, session, test_post):
        """Test get_by_id_or_raise returns post."""
        repo = BlogPostRepository(session)

        post = repo.get_by_id_or_raise(test_post.id)

        assert post.id == test_post.id

    def test_get_by_id_or_raise_raises_exception(self, session):
        """Test get_by_id_or_raise raises exception for non-existent post."""
        repo = BlogPostRepository(session)

        with pytest.raises(ResourceNotFoundError) as exc_info:
            repo.get_by_id_or_raise(999)

        assert exc_info.value.status_code == 404

    def test_list_all(self, session, test_user):
        """Test listing all posts."""
        repo = BlogPostRepository(session)

        # Create multiple posts
        for i in range(3):
            repo.create(
                title=f"Post {i}", content=f"Content {i}", author_id=test_user.id
            )

        posts = repo.list_all()

        assert len(posts) == 3

    def test_list_all_with_pagination(self, session, test_user):
        """Test list_all with skip and limit."""
        repo = BlogPostRepository(session)

        # Create 5 posts
        for i in range(5):
            repo.create(
                title=f"Post {i}", content=f"Content {i}", author_id=test_user.id
            )

        posts = repo.list_all(skip=2, limit=2)

        assert len(posts) == 2

    def test_list_by_author(self, session, test_user, another_user):
        """Test listing posts by specific author."""
        repo = BlogPostRepository(session)

        # Create posts for test_user
        for i in range(2):
            repo.create(
                title=f"User1 Post {i}", content=f"Content {i}", author_id=test_user.id
            )

        # Create post for another_user
        repo.create(title="User2 Post", content="Content", author_id=another_user.id)

        posts = repo.list_by_author(test_user.id)

        assert len(posts) == 2
        assert all(post.author_id == test_user.id for post in posts)

    def test_create(self, session, test_user):
        """Test creating a blog post."""
        repo = BlogPostRepository(session)

        post = repo.create(
            title="New Post", content="New Content", author_id=test_user.id
        )

        assert post.id is not None
        assert post.title == "New Post"
        assert post.content == "New Content"
        assert post.author_id == test_user.id
        assert post.created_at is not None

    def test_update(self, session, test_post):
        """Test updating a blog post."""
        repo = BlogPostRepository(session)
        original_updated_at = test_post.updated_at

        # Add small delay to ensure timestamp difference
        time.sleep(0.01)

        updated_post = repo.update(
            post_id=test_post.id, title="Updated Title", content="Updated Content"
        )

        assert updated_post.title == "Updated Title"
        assert updated_post.content == "Updated Content"
        assert updated_post.updated_at > original_updated_at

    def test_update_partial(self, session, test_post):
        """Test partial update of blog post."""
        repo = BlogPostRepository(session)
        original_content = test_post.content

        updated_post = repo.update(post_id=test_post.id, title="New Title")

        assert updated_post.title == "New Title"
        assert updated_post.content == original_content

    def test_update_raises_not_found(self, session):
        """Test update raises exception for non-existent post."""
        repo = BlogPostRepository(session)

        with pytest.raises(ResourceNotFoundError):
            repo.update(post_id=999, title="Should Fail")

    def test_delete(self, session, test_post):
        """Test deleting a blog post."""
        repo = BlogPostRepository(session)
        post_id = test_post.id

        repo.delete(post_id)

        # Verify post is deleted
        deleted_post = repo.get_by_id(post_id)
        assert deleted_post is None

    def test_delete_raises_not_found(self, session):
        """Test delete raises exception for non-existent post."""
        repo = BlogPostRepository(session)

        with pytest.raises(ResourceNotFoundError):
            repo.delete(999)

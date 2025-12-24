"""Service layer for business logic.

Services coordinate between repositories and API routes,
implementing business rules and authorization logic.
"""

import logging

from sqlmodel import Session

from .exceptions import AuthorizationError
from .models import (
    BlogPost,
    BlogPostCreate,
    BlogPostUpdate,
    ProfileResponse,
    User,
    UserCreate,
)
from .repositories import BlogPostRepository, UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related business logic."""

    def __init__(self, session: Session) -> None:
        """Initialize user service.

        Args:
            session: Database session
        """
        self.session = session
        self.repository = UserRepository(session)

    def get_or_create_user(
        self,
        oid: str,
        display_name: str | None = None,
    ) -> tuple[User, bool]:
        """Get existing user or create new one.

        Args:
            oid: Microsoft Entra ID object ID
            display_name: Optional display name

        Returns:
            Tuple of (user, created) where created is True if user was just created
        """
        user, created = self.repository.get_or_create(oid, display_name)

        if created:
            logger.info(f"Created new user with oid: {oid}")
        else:
            logger.debug(f"Found existing user with oid: {oid}")

        return user, created

    def get_profile_from_claims(self, claims: dict[str, any]) -> ProfileResponse:
        """Extract profile information from token claims.

        Args:
            claims: JWT token claims

        Returns:
            User profile response
        """
        return ProfileResponse(
            oid=claims.get("oid", ""),
            name=claims.get("name"),
            email=claims.get("email"),
            preferred_username=claims.get("preferred_username"),
        )


class BlogPostService:
    """Service for blog post-related business logic."""

    def __init__(self, session: Session) -> None:
        """Initialize blog post service.

        Args:
            session: Database session
        """
        self.session = session
        self.repository = BlogPostRepository(session)
        self.user_repository = UserRepository(session)

    def create_post(
        self,
        post_data: BlogPostCreate,
        author_oid: str,
    ) -> BlogPost:
        """Create a new blog post.

        Args:
            post_data: Blog post creation data
            author_oid: Author's Microsoft Entra ID object ID

        Returns:
            Created blog post
        """
        # Ensure user exists in database
        user, _ = self.user_repository.get_or_create(author_oid)

        post = self.repository.create(
            title=post_data.title,
            content=post_data.content,
            author_id=user.id,
        )

        logger.info(f"User {author_oid} created post {post.id}")
        return post

    def list_posts(self, skip: int = 0, limit: int = 100) -> list[BlogPost]:
        """List all blog posts with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of blog posts
        """
        return self.repository.list_all(skip=skip, limit=limit)

    def get_post(self, post_id: int) -> BlogPost:
        """Get a blog post by ID.

        Args:
            post_id: Post ID

        Returns:
            Blog post

        Raises:
            ResourceNotFoundError: If post not found
        """
        return self.repository.get_by_id_or_raise(post_id)

    def update_post(
        self,
        post_id: int,
        post_data: BlogPostUpdate,
        user_oid: str,
    ) -> BlogPost:
        """Update a blog post.

        Enforces ownership validation - only the author can update their posts.

        Args:
            post_id: Post ID
            post_data: Update data
            user_oid: Current user's Microsoft Entra ID object ID

        Returns:
            Updated blog post

        Raises:
            ResourceNotFoundError: If post not found
            AuthorizationError: If user is not the post author
        """
        post = self.repository.get_by_id_or_raise(post_id)

        # Validate ownership
        self._validate_ownership(post, user_oid)

        # Update only provided fields
        updated_post = self.repository.update(
            post_id=post_id,
            title=post_data.title,
            content=post_data.content,
        )

        logger.info(f"User {user_oid} updated post {post_id}")
        return updated_post

    def delete_post(self, post_id: int, user_oid: str) -> None:
        """Delete a blog post.

        Enforces ownership validation - only the author can delete their posts.

        Args:
            post_id: Post ID
            user_oid: Current user's Microsoft Entra ID object ID

        Raises:
            ResourceNotFoundError: If post not found
            AuthorizationError: If user is not the post author
        """
        post = self.repository.get_by_id_or_raise(post_id)

        # Validate ownership
        self._validate_ownership(post, user_oid)

        self.repository.delete(post_id)
        logger.info(f"User {user_oid} deleted post {post_id}")

    def _validate_ownership(self, post: BlogPost, user_oid: str) -> None:
        """Validate that user owns the post.

        Args:
            post: Blog post to check
            user_oid: User's Microsoft Entra ID object ID

        Raises:
            AuthorizationError: If user is not the post author
        """
        author = self.user_repository.get_by_id(post.author_id)
        if not author or author.oid != user_oid:
            logger.warning(
                f"User {user_oid} attempted to access post {post.id} "
                f"owned by {author.oid if author else 'unknown'}"
            )
            raise AuthorizationError("You do not have permission to modify this post")

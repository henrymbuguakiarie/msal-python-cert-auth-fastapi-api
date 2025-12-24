"""Repository pattern for data access abstraction.

Repositories provide a clean interface for database operations,
isolating business logic from data access details.
"""
from datetime import datetime

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from .exceptions import ResourceNotFoundError
from .models import BlogPost, User


class UserRepository:
    """Repository for User data access operations."""
    
    def __init__(self, session: Session) -> None:
        """Initialize user repository.
        
        Args:
            session: Database session
        """
        self.session = session
    
    def get_by_id(self, user_id: int) -> User | None:
        """Get user by internal ID.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            User if found, None otherwise
        """
        return self.session.get(User, user_id)
    
    def get_by_oid(self, oid: str) -> User | None:
        """Get user by Microsoft Entra ID object ID.
        
        Args:
            oid: Microsoft Entra ID object ID
            
        Returns:
            User if found, None otherwise
        """
        statement = select(User).where(User.oid == oid)
        return self.session.exec(statement).first()
    
    def create(self, oid: str, display_name: str | None = None) -> User:
        """Create a new user.
        
        Args:
            oid: Microsoft Entra ID object ID
            display_name: Optional display name
            
        Returns:
            Created user
        """
        user = User(oid=oid, display_name=display_name)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def get_or_create(self, oid: str, display_name: str | None = None) -> tuple[User, bool]:
        """Get existing user or create new one.
        
        Args:
            oid: Microsoft Entra ID object ID
            display_name: Optional display name
            
        Returns:
            Tuple of (user, created) where created is True if user was just created
        """
        existing_user = self.get_by_oid(oid)
        if existing_user:
            return existing_user, False
        
        new_user = self.create(oid, display_name)
        return new_user, True


class BlogPostRepository:
    """Repository for BlogPost data access operations."""
    
    def __init__(self, session: Session) -> None:
        """Initialize blog post repository.
        
        Args:
            session: Database session
        """
        self.session = session
    
    def get_by_id(self, post_id: int) -> BlogPost | None:
        """Get blog post by ID.
        
        Args:
            post_id: Post ID
            
        Returns:
            Blog post if found, None otherwise
        """
        return self.session.get(BlogPost, post_id)
    
    def get_by_id_or_raise(self, post_id: int) -> BlogPost:
        """Get blog post by ID or raise exception.
        
        Args:
            post_id: Post ID
            
        Returns:
            Blog post
            
        Raises:
            ResourceNotFoundError: If post not found
        """
        post = self.get_by_id(post_id)
        if not post:
            raise ResourceNotFoundError("BlogPost", post_id)
        return post
    
    def list_all(self, skip: int = 0, limit: int = 100) -> list[BlogPost]:
        """List all blog posts with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of blog posts
        """
        statement = select(BlogPost).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())
    
    def list_by_author(self, author_id: int, skip: int = 0, limit: int = 100) -> list[BlogPost]:
        """List blog posts by author with pagination.
        
        Args:
            author_id: Author's user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of blog posts
        """
        statement = (
            select(BlogPost)
            .where(BlogPost.author_id == author_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
    
    def create(self, title: str, content: str, author_id: int) -> BlogPost:
        """Create a new blog post.
        
        Args:
            title: Post title
            content: Post content
            author_id: Author's user ID
            
        Returns:
            Created blog post
        """
        post = BlogPost(title=title, content=content, author_id=author_id)
        self.session.add(post)
        self.session.commit()
        self.session.refresh(post)
        return post
    
    def update(
        self,
        post_id: int,
        title: str | None = None,
        content: str | None = None,
    ) -> BlogPost:
        """Update an existing blog post.
        
        Args:
            post_id: Post ID
            title: Optional new title
            content: Optional new content
            
        Returns:
            Updated blog post
            
        Raises:
            ResourceNotFoundError: If post not found
        """
        post = self.get_by_id_or_raise(post_id)
        
        if title is not None:
            post.title = title
        if content is not None:
            post.content = content
        
        post.updated_at = datetime.utcnow()
        
        self.session.add(post)
        self.session.commit()
        self.session.refresh(post)
        return post
    
    def delete(self, post_id: int) -> None:
        """Delete a blog post.
        
        Args:
            post_id: Post ID
            
        Raises:
            ResourceNotFoundError: If post not found
        """
        post = self.get_by_id_or_raise(post_id)
        self.session.delete(post)
        self.session.commit()

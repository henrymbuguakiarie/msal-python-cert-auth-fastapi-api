"""Database connection and session management."""

import logging
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Create engine with appropriate settings
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
engine = create_engine(
    settings.database_url,
    echo=not settings.is_production,
    connect_args=connect_args,
)


def create_db_and_tables() -> None:
    """Create all database tables.

    Should be called at application startup.
    """
    logger.info("Creating database tables")
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.

    Yields:
        Database session with automatic cleanup
    """
    with Session(engine) as session:
        yield session

"""Pytest configuration and shared fixtures."""

import os
from typing import Any, Generator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.database import get_session
from src.main import app
from src.models import BlogPost, User


@pytest.fixture(name="test_engine")
def test_engine_fixture():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(test_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """Create test client with database session override."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(session: Session) -> User:
    """Create a test user."""
    user = User(
        oid="test-oid-123",
        display_name="Test User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def another_user(session: Session) -> User:
    """Create another test user."""
    user = User(
        oid="test-oid-456",
        display_name="Another User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def test_post(session: Session, test_user: User) -> BlogPost:
    """Create a test blog post."""
    post = BlogPost(
        title="Test Post",
        content="This is test content",
        author_id=test_user.id,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


@pytest.fixture
def mock_jwt_claims() -> dict[str, Any]:
    """Mock JWT token claims."""
    return {
        "oid": "test-oid-123",
        "name": "Test User",
        "email": "test@example.com",
        "preferred_username": "testuser@example.com",
        "scp": "access_as_user",
    }


@pytest.fixture
def mock_jwt_validator(mocker, mock_jwt_claims):
    """Mock JWT validator."""
    mock_validator = mocker.patch("src.auth.JWTValidator")
    mock_validator.return_value.validate_token.return_value = mock_jwt_claims
    return mock_validator


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Create authentication headers with mock token."""
    return {"Authorization": "Bearer mock_token"}


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    # Store original env vars
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ.update(
        {
            "TENANT_ID": "test-tenant-id-123e4567-e89b-12d3-a456-426614174000",
            "API_APP_ID_URI": "api://test-api-client-id",
            "REQUIRED_SCOPE": "access_as_user",
            "DATABASE_URL": "sqlite:///:memory:",
            "ENVIRONMENT": "development",
        }
    )

    yield

    # Restore original env vars
    os.environ.clear()
    os.environ.update(original_env)

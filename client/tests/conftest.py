"""Test configuration and fixtures for client tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.auth import MSALAuthClient
from src.config import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing.
    
    Returns:
        Settings instance with test values
    """
    # Create a mock certificate file temporarily
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".pem", delete=False
    ) as cert_file:
        cert_file.write("-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----")
        cert_path = cert_file.name

    settings = Settings(
        tenant_id="12345678-1234-1234-1234-123456789012",
        client_id="87654321-4321-4321-4321-210987654321",
        client_cert_path=cert_path,
        client_cert_thumbprint="1234567890abcdef1234567890abcdef12345678",
        redirect_uri="http://localhost:5000/callback",
        api_scope="api://test-api-id/access_as_user",
        api_base_url="http://localhost:8000",
        flask_secret_key="test-secret",
        flask_port=5000,
        debug=True,
    )

    yield settings

    # Cleanup
    Path(cert_path).unlink(missing_ok=True)


@pytest.fixture
def mock_msal_app() -> MagicMock:
    """Create a mock MSAL application.
    
    Returns:
        Mock MSAL ConfidentialClientApplication
    """
    mock = MagicMock()
    mock.get_authorization_request_url.return_value = (
        "https://login.microsoftonline.com/authorize"
    )
    mock.acquire_token_by_authorization_code.return_value = {
        "access_token": "test_access_token",
        "id_token": "test_id_token",
        "id_token_claims": {
            "name": "Test User",
            "preferred_username": "test@example.com",
            "oid": "user-oid-123",
        },
    }
    mock.acquire_token_silent.return_value = {
        "access_token": "test_access_token_silent",
    }
    mock.get_accounts.return_value = [
        {"username": "test@example.com", "oid": "user-oid-123"}
    ]
    return mock


@pytest.fixture
def sample_token_response() -> dict:
    """Sample token response from MSAL.
    
    Returns:
        Dictionary with token response data
    """
    return {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.test",
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.id_token",
        "id_token_claims": {
            "aud": "client-id",
            "iss": "https://login.microsoftonline.com/tenant-id/v2.0",
            "iat": 1234567890,
            "nbf": 1234567890,
            "exp": 1234571490,
            "name": "Test User",
            "preferred_username": "test@example.com",
            "oid": "12345678-1234-1234-1234-123456789012",
            "tid": "tenant-id",
        },
    }


@pytest.fixture
def sample_user_response() -> dict:
    """Sample user profile response from API.
    
    Returns:
        Dictionary with user data
    """
    return {
        "id": 1,
        "oid": "12345678-1234-1234-1234-123456789012",
        "display_name": "Test User",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def sample_post_response() -> dict:
    """Sample blog post response from API.
    
    Returns:
        Dictionary with blog post data
    """
    return {
        "id": 1,
        "title": "Test Post",
        "content": "This is a test post content.",
        "author_id": 1,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def sample_posts_list() -> dict:
    """Sample paginated posts response from API.
    
    Returns:
        Dictionary with paginated posts data
    """
    return {
        "posts": [
            {
                "id": 1,
                "title": "First Post",
                "content": "Content 1",
                "author_id": 1,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "author": {
                    "id": 1,
                    "oid": "user-oid-1",
                    "display_name": "User One",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                },
            },
            {
                "id": 2,
                "title": "Second Post",
                "content": "Content 2",
                "author_id": 2,
                "created_at": "2024-01-02T00:00:00",
                "updated_at": "2024-01-02T00:00:00",
                "author": {
                    "id": 2,
                    "oid": "user-oid-2",
                    "display_name": "User Two",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                },
            },
        ],
        "total": 2,
        "skip": 0,
        "limit": 10,
    }

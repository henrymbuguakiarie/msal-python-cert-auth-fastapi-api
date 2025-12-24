"""Unit tests for configuration management."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings


class TestSettings:
    """Tests for Settings class."""

    def test_settings_with_valid_env_vars(self, mock_settings: Settings) -> None:
        """Test settings initialization with valid environment variables."""
        # Arrange & Act - using fixture
        settings = mock_settings

        # Assert
        assert settings.tenant_id == "12345678-1234-1234-1234-123456789012"
        assert settings.client_id == "87654321-4321-4321-4321-210987654321"
        assert settings.client_cert_thumbprint == "1234567890abcdef1234567890abcdef12345678"
        assert settings.redirect_uri == "http://localhost:5000/callback"
        assert settings.api_scope == "api://test-api-id/access_as_user"
        assert settings.api_base_url == "http://localhost:8000"
        assert settings.flask_port == 5000
        assert settings.debug is True

    def test_authority_property(self, mock_settings: Settings) -> None:
        """Test authority URL generation."""
        # Arrange
        settings = mock_settings

        # Act
        authority = settings.authority

        # Assert
        assert authority == "https://login.microsoftonline.com/12345678-1234-1234-1234-123456789012"

    def test_scope_list_property(self, mock_settings: Settings) -> None:
        """Test scope list generation."""
        # Arrange
        settings = mock_settings

        # Act
        scope_list = settings.scope_list

        # Assert
        assert isinstance(scope_list, list)
        assert len(scope_list) == 1
        assert scope_list[0] == "api://test-api-id/access_as_user"

    def test_invalid_tenant_id_length(self) -> None:
        """Test validation fails for invalid tenant ID length."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write("test")
            cert_path = f.name

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                tenant_id="invalid-short",
                client_id="87654321-4321-4321-4321-210987654321",
                client_cert_path=cert_path,
                client_cert_thumbprint="1234567890abcdef1234567890abcdef12345678",
                api_scope="api://test/access_as_user",
            )

        assert "tenant_id" in str(exc_info.value)
        Path(cert_path).unlink()

    def test_certificate_path_not_exists(self) -> None:
        """Test validation fails when certificate path doesn't exist."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                tenant_id="12345678-1234-1234-1234-123456789012",
                client_id="87654321-4321-4321-4321-210987654321",
                client_cert_path="/nonexistent/path/cert.pem",
                client_cert_thumbprint="1234567890abcdef1234567890abcdef12345678",
                api_scope="api://test/access_as_user",
            )

        assert "Certificate file not found" in str(exc_info.value)

    def test_api_scope_validation_without_prefix(self) -> None:
        """Test validation fails when API scope doesn't have api:// prefix."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write("test")
            cert_path = f.name

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                tenant_id="12345678-1234-1234-1234-123456789012",
                client_id="87654321-4321-4321-4321-210987654321",
                client_cert_path=cert_path,
                client_cert_thumbprint="1234567890abcdef1234567890abcdef12345678",
                api_scope="invalid-scope",
            )

        assert "must start with 'api://'" in str(exc_info.value)
        Path(cert_path).unlink()

    def test_api_scope_validation_without_access_as_user(self) -> None:
        """Test validation fails when API scope doesn't include access_as_user."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write("test")
            cert_path = f.name

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                tenant_id="12345678-1234-1234-1234-123456789012",
                client_id="87654321-4321-4321-4321-210987654321",
                client_cert_path=cert_path,
                client_cert_thumbprint="1234567890abcdef1234567890abcdef12345678",
                api_scope="api://test-api/wrong_scope",
            )

        assert "access_as_user" in str(exc_info.value)
        Path(cert_path).unlink()

    def test_redirect_uri_validation(self) -> None:
        """Test validation fails for invalid redirect URI format."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write("test")
            cert_path = f.name

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                tenant_id="12345678-1234-1234-1234-123456789012",
                client_id="87654321-4321-4321-4321-210987654321",
                client_cert_path=cert_path,
                client_cert_thumbprint="1234567890abcdef1234567890abcdef12345678",
                api_scope="api://test/access_as_user",
                redirect_uri="invalid-uri-without-protocol",
            )

        assert "must start with http://" in str(exc_info.value)
        Path(cert_path).unlink()

    def test_flask_port_range_validation(self) -> None:
        """Test validation for Flask port range."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write("test")
            cert_path = f.name

        # Act & Assert
        with pytest.raises(ValidationError):
            Settings(
                tenant_id="12345678-1234-1234-1234-123456789012",
                client_id="87654321-4321-4321-4321-210987654321",
                client_cert_path=cert_path,
                client_cert_thumbprint="1234567890abcdef1234567890abcdef12345678",
                api_scope="api://test/access_as_user",
                flask_port=99999,  # Out of valid range
            )

        Path(cert_path).unlink()


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_singleton(self, mock_settings: Settings) -> None:
        """Test that get_settings is cached."""
        # Arrange & Act
        # Clear the cache first
        get_settings.cache_clear()
        
        # Verify the function is an lru_cache
        assert hasattr(get_settings, "cache_info")
        
        # Get cache info
        info_before = get_settings.cache_info()
        
        # Assert - lru_cache default maxsize is 128 (not unlimited)
        assert info_before.maxsize == 128
        assert info_before.currsize == 0  # No calls yet

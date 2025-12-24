"""Unit tests for configuration module."""

import os

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings


class TestSettings:
    """Test suite for Settings configuration."""

    def test_settings_with_valid_env_vars(self):
        """Test settings initialization with valid environment variables."""
        settings = Settings(
            tenant_id="12345678-1234-1234-1234-123456789012",
            api_app_id_uri="api://test-api-client-id",
            required_scope="access_as_user",
        )

        assert settings.tenant_id == "12345678-1234-1234-1234-123456789012"
        assert settings.api_app_id_uri == "api://test-api-client-id"
        assert settings.required_scope == "access_as_user"

    def test_tenant_id_validation_fails_with_short_string(self):
        """Test tenant ID validation fails with invalid format."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                tenant_id="short",
                api_app_id_uri="api://test-client-id",
            )

        assert "TENANT_ID must be a valid GUID" in str(exc_info.value)

    def test_app_id_uri_validation_fails_without_prefix(self, monkeypatch):
        """Test API App ID URI validation fails without 'api://' prefix."""
        # Directly set an invalid value to the env var to test validation
        monkeypatch.setenv("API_APP_ID_URI", "invalid-uri-without-prefix")

        with pytest.raises(ValidationError) as exc_info:
            Settings(
                tenant_id="12345678-1234-1234-1234-123456789012",
            )

        assert "API_APP_ID_URI must start with 'api://'" in str(exc_info.value)

    def test_jwks_endpoint_property(self):
        """Test JWKS endpoint construction."""
        settings = Settings(
            tenant_id="12345678-1234-1234-1234-123456789012",
            api_app_id_uri="api://test-client-id",
        )

        expected_jwks_uri = (
            "https://login.microsoftonline.com/"
            "12345678-1234-1234-1234-123456789012/discovery/v2.0/keys"
        )
        assert settings.jwks_endpoint == expected_jwks_uri

    def test_jwks_endpoint_property_with_override(self):
        """Test JWKS endpoint with manual override."""
        custom_jwks = "https://custom.jwks.endpoint/keys"
        settings = Settings(
            tenant_id="12345678-1234-1234-1234-123456789012",
            api_app_id_uri="api://test-client-id",
            jwks_uri=custom_jwks,
        )

        assert settings.jwks_endpoint == custom_jwks

    def test_token_issuer_property(self):
        """Test token issuer construction."""
        settings = Settings(
            tenant_id="12345678-1234-1234-1234-123456789012",
            api_app_id_uri="api://test-client-id",
        )

        expected_issuer = (
            "https://login.microsoftonline.com/"
            "12345678-1234-1234-1234-123456789012/v2.0"
        )
        assert settings.token_issuer == expected_issuer

    def test_is_production_property(self):
        """Test production environment detection."""
        dev_settings = Settings(
            tenant_id="12345678-1234-1234-1234-123456789012",
            api_app_id_uri="api://test-client-id",
            environment="development",
        )
        assert dev_settings.is_production is False

        prod_settings = Settings(
            tenant_id="12345678-1234-1234-1234-123456789012",
            api_app_id_uri="api://test-client-id",
            environment="production",
        )
        assert prod_settings.is_production is True

    def test_default_values(self):
        """Test default configuration values."""
        settings = Settings(
            tenant_id="12345678-1234-1234-1234-123456789012",
            api_app_id_uri="api://test-client-id",
        )

        assert settings.required_scope == "access_as_user"
        assert settings.api_version == "v1"
        assert settings.environment == "development"
        assert settings.log_level == "INFO"

    def test_get_settings_caching(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

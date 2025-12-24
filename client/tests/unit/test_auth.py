"""Unit tests for MSAL authentication client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.auth import MSALAuthClient
from src.config import Settings
from src.exceptions import (
    AuthenticationError,
    CertificateError,
    TokenAcquisitionError,
)


class TestMSALAuthClient:
    """Tests for MSALAuthClient class."""

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_initialization_success(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test successful initialization of MSAL client."""
        # Arrange
        mock_app = MagicMock()
        mock_msal_class.return_value = mock_app

        # Act
        client = MSALAuthClient(mock_settings)

        # Assert
        assert client.settings == mock_settings
        assert client._msal_app == mock_app
        assert isinstance(client._token_cache, dict)
        mock_msal_class.assert_called_once()

    def test_certificate_loading_pem_format(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test loading PEM certificate file."""
        # Arrange & Act
        with patch("src.auth.msal.ConfidentialClientApplication"):
            client = MSALAuthClient(mock_settings)
            cert_dict = client._load_certificate()

        # Assert
        assert "private_key" in cert_dict
        assert "thumbprint" in cert_dict
        assert cert_dict["thumbprint"] == mock_settings.client_cert_thumbprint

    def test_certificate_loading_file_not_found(
        self,
        mock_settings: Settings,
    ) -> None:
        """Test certificate loading fails when file doesn't exist."""
        # Arrange
        mock_settings.client_cert_path = "/nonexistent/path/cert.pem"

        # Act & Assert
        with pytest.raises(CertificateError) as exc_info:
            with patch("src.auth.msal.ConfidentialClientApplication"):
                client = MSALAuthClient(mock_settings)

        assert "Certificate file not found" in str(exc_info.value)

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_get_authorization_url(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test authorization URL generation."""
        # Arrange
        mock_app = MagicMock()
        expected_url = "https://login.microsoftonline.com/authorize?client_id=test"
        mock_app.get_authorization_request_url.return_value = expected_url
        mock_msal_class.return_value = mock_app

        client = MSALAuthClient(mock_settings)

        # Act
        auth_url, state = client.get_authorization_url(state="test-state")

        # Assert
        assert auth_url == expected_url
        assert state == "test-state"
        mock_app.get_authorization_request_url.assert_called_once_with(
            scopes=mock_settings.scope_list,
            state="test-state",
            redirect_uri=mock_settings.redirect_uri,
        )

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_acquire_token_by_authorization_code_success(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
        sample_token_response: dict,
    ) -> None:
        """Test successful token acquisition by authorization code."""
        # Arrange
        mock_app = MagicMock()
        mock_app.acquire_token_by_authorization_code.return_value = sample_token_response
        mock_msal_class.return_value = mock_app

        client = MSALAuthClient(mock_settings)

        # Act
        result = client.acquire_token_by_authorization_code("test-code")

        # Assert
        assert result == sample_token_response
        assert "access_token" in result
        assert client._token_cache["current_token"] == sample_token_response
        mock_app.acquire_token_by_authorization_code.assert_called_once_with(
            code="test-code",
            scopes=mock_settings.scope_list,
            redirect_uri=mock_settings.redirect_uri,
        )

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_acquire_token_by_authorization_code_error(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test token acquisition fails with error response."""
        # Arrange
        mock_app = MagicMock()
        error_response = {
            "error": "invalid_grant",
            "error_description": "Authorization code has expired",
        }
        mock_app.acquire_token_by_authorization_code.return_value = error_response
        mock_msal_class.return_value = mock_app

        client = MSALAuthClient(mock_settings)

        # Act & Assert
        with pytest.raises(TokenAcquisitionError) as exc_info:
            client.acquire_token_by_authorization_code("expired-code")

        assert "Authorization code has expired" in str(exc_info.value)

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_acquire_token_silent_with_accounts(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
        sample_token_response: dict,
    ) -> None:
        """Test silent token acquisition with accounts in cache."""
        # Arrange
        mock_app = MagicMock()
        mock_account = {"username": "test@example.com"}
        mock_app.get_accounts.return_value = [mock_account]
        mock_app.acquire_token_silent.return_value = sample_token_response
        mock_msal_class.return_value = mock_app

        client = MSALAuthClient(mock_settings)

        # Act
        result = client.acquire_token_silent()

        # Assert
        assert result == sample_token_response
        assert client._token_cache["current_token"] == sample_token_response
        mock_app.acquire_token_silent.assert_called_once_with(
            scopes=mock_settings.scope_list,
            account=mock_account,
        )

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_acquire_token_silent_no_accounts(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test silent token acquisition returns None when no accounts."""
        # Arrange
        mock_app = MagicMock()
        mock_app.get_accounts.return_value = []
        mock_msal_class.return_value = mock_app

        client = MSALAuthClient(mock_settings)

        # Act
        result = client.acquire_token_silent()

        # Assert
        assert result is None
        mock_app.acquire_token_silent.assert_not_called()

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_get_cached_token(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
        sample_token_response: dict,
    ) -> None:
        """Test retrieving cached token."""
        # Arrange
        mock_app = MagicMock()
        mock_msal_class.return_value = mock_app

        client = MSALAuthClient(mock_settings)
        client._cache_token(sample_token_response)

        # Act
        cached_token = client.get_cached_token()

        # Assert
        assert cached_token == sample_token_response

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_get_accounts(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test getting accounts from MSAL cache."""
        # Arrange
        mock_app = MagicMock()
        mock_accounts = [
            {"username": "user1@example.com"},
            {"username": "user2@example.com"},
        ]
        mock_app.get_accounts.return_value = mock_accounts
        mock_msal_class.return_value = mock_app

        client = MSALAuthClient(mock_settings)

        # Act
        accounts = client.get_accounts()

        # Assert
        assert accounts == mock_accounts
        assert len(accounts) == 2

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_clear_cache(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
        sample_token_response: dict,
    ) -> None:
        """Test clearing token cache."""
        # Arrange
        mock_app = MagicMock()
        mock_msal_class.return_value = mock_app

        client = MSALAuthClient(mock_settings)
        client._cache_token(sample_token_response)

        # Act
        client.clear_cache()

        # Assert
        assert client.get_cached_token() is None
        assert len(client._token_cache) == 0

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_get_id_token_claims(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
        sample_token_response: dict,
    ) -> None:
        """Test extracting ID token claims."""
        # Arrange
        mock_app = MagicMock()
        mock_msal_class.return_value = mock_app

        client = MSALAuthClient(mock_settings)
        client._cache_token(sample_token_response)

        # Act
        claims = client.get_id_token_claims()

        # Assert
        assert claims is not None
        assert "name" in claims
        assert claims["name"] == "Test User"
        assert claims["oid"] == "12345678-1234-1234-1234-123456789012"

    @patch("src.auth.msal.ConfidentialClientApplication")
    def test_get_id_token_claims_no_token(
        self,
        mock_msal_class: MagicMock,
        mock_settings: Settings,
    ) -> None:
        """Test getting ID token claims when no token is cached."""
        # Arrange
        mock_app = MagicMock()
        mock_msal_class.return_value = mock_app

        client = MSALAuthClient(mock_settings)

        # Act
        claims = client.get_id_token_claims()

        # Assert
        assert claims is None

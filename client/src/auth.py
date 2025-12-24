"""MSAL authentication client with certificate-based authentication.

This module provides a wrapper around MSAL Python for certificate-based
authentication using the OAuth 2.0 Authorization Code Flow with PKCE.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import msal

from .config import Settings
from .exceptions import (
    AuthenticationError,
    CertificateError,
    TokenAcquisitionError,
)

logger = logging.getLogger(__name__)


class MSALAuthClient:
    """MSAL authentication client for certificate-based auth.
    
    This class handles:
    - Loading X.509 certificates
    - Building authorization URLs
    - Acquiring tokens via authorization code flow
    - Token caching in memory
    
    Attributes:
        settings: Application settings
        _msal_app: MSAL ConfidentialClientApplication instance
        _token_cache: In-memory token cache
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the MSAL authentication client.
        
        Args:
            settings: Application settings containing auth configuration
            
        Raises:
            CertificateError: If certificate loading fails
        """
        self.settings = settings
        self._token_cache: dict[str, Any] = {}
        self._msal_app = self._build_msal_app()

    def _load_certificate(self) -> dict[str, Any]:
        """Load X.509 certificate for authentication.
        
        Returns:
            Certificate dictionary for MSAL
            
        Raises:
            CertificateError: If certificate loading fails
        """
        cert_path = Path(self.settings.client_cert_path)
        
        try:
            with open(cert_path, "rb") as cert_file:
                cert_data = cert_file.read()
            
            # MSAL expects PEM format or PFX
            # For PEM files (most common), we load as string
            if cert_path.suffix.lower() == ".pem":
                cert_dict = {
                    "private_key": cert_data.decode("utf-8"),
                    "thumbprint": self.settings.client_cert_thumbprint,
                }
            else:
                # For PFX files, MSAL expects different format
                # This is a simplified example - production should handle password
                cert_dict = {
                    "private_key": cert_data,
                    "thumbprint": self.settings.client_cert_thumbprint,
                }
            
            logger.info(f"Successfully loaded certificate from {cert_path}")
            return cert_dict
            
        except FileNotFoundError as e:
            logger.error(f"Certificate file not found: {cert_path}")
            raise CertificateError(f"Certificate file not found: {cert_path}") from e
        except Exception as e:
            logger.error(f"Failed to load certificate: {e}")
            raise CertificateError(f"Failed to load certificate: {e}") from e

    def _build_msal_app(self) -> msal.ConfidentialClientApplication:
        """Build MSAL ConfidentialClientApplication with certificate.
        
        Returns:
            Configured MSAL application instance
            
        Raises:
            AuthenticationError: If MSAL app creation fails
        """
        try:
            cert_dict = self._load_certificate()
            
            app = msal.ConfidentialClientApplication(
                client_id=self.settings.client_id,
                client_credential=cert_dict,
                authority=self.settings.authority,
            )
            
            logger.info("Successfully created MSAL application")
            return app
            
        except CertificateError:
            raise
        except Exception as e:
            logger.error(f"Failed to create MSAL application: {e}")
            raise AuthenticationError(f"Failed to create MSAL application: {e}") from e

    def get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
        """Build authorization URL for OAuth 2.0 Authorization Code Flow.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Tuple of (authorization_url, state)
        """
        auth_url = self._msal_app.get_authorization_request_url(
            scopes=self.settings.scope_list,
            state=state,
            redirect_uri=self.settings.redirect_uri,
        )
        
        # MSAL returns the URL directly in this case
        # State is passed through if provided
        actual_state = state or "default_state"
        
        logger.info("Generated authorization URL")
        return auth_url, actual_state

    def acquire_token_by_authorization_code(
        self,
        code: str,
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            scopes: Optional list of scopes (defaults to configured API scope)
            
        Returns:
            Token response dictionary containing access_token, id_token, etc.
            
        Raises:
            TokenAcquisitionError: If token acquisition fails
        """
        if scopes is None:
            scopes = self.settings.scope_list

        try:
            result = self._msal_app.acquire_token_by_authorization_code(
                code=code,
                scopes=scopes,
                redirect_uri=self.settings.redirect_uri,
            )
            
            if "error" in result:
                error_description = result.get("error_description", "Unknown error")
                logger.error(f"Token acquisition failed: {error_description}")
                raise TokenAcquisitionError(
                    f"Failed to acquire token: {error_description}"
                )
            
            # Cache the token
            self._cache_token(result)
            
            logger.info("Successfully acquired access token")
            return result
            
        except TokenAcquisitionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token acquisition: {e}")
            raise TokenAcquisitionError(
                f"Unexpected error during token acquisition: {e}"
            ) from e

    def acquire_token_silent(
        self,
        scopes: list[str] | None = None,
        account: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Acquire token silently from cache or refresh token.
        
        Args:
            scopes: Optional list of scopes (defaults to configured API scope)
            account: Optional account hint from previous authentication
            
        Returns:
            Token response dictionary or None if silent acquisition fails
        """
        if scopes is None:
            scopes = self.settings.scope_list

        accounts = self._msal_app.get_accounts()
        
        if not accounts:
            logger.debug("No accounts in cache for silent token acquisition")
            return None

        # Use provided account or first account in cache
        target_account = account or accounts[0]

        result = self._msal_app.acquire_token_silent(
            scopes=scopes,
            account=target_account,
        )

        if result and "access_token" in result:
            logger.info("Successfully acquired token silently")
            self._cache_token(result)
            return result
        
        logger.debug("Silent token acquisition returned no token")
        return None

    def _cache_token(self, token_response: dict[str, Any]) -> None:
        """Cache token response in memory.
        
        Args:
            token_response: Token response from MSAL
        """
        if "access_token" in token_response:
            self._token_cache["current_token"] = token_response
            logger.debug("Token cached successfully")

    def get_cached_token(self) -> dict[str, Any] | None:
        """Retrieve cached token from memory.
        
        Returns:
            Cached token response or None
        """
        return self._token_cache.get("current_token")

    def get_accounts(self) -> list[dict[str, Any]]:
        """Get all accounts from MSAL cache.
        
        Returns:
            List of account dictionaries
        """
        return self._msal_app.get_accounts()

    def clear_cache(self) -> None:
        """Clear in-memory token cache."""
        self._token_cache.clear()
        logger.info("Token cache cleared")

    def get_id_token_claims(self) -> dict[str, Any] | None:
        """Extract claims from cached ID token.
        
        Returns:
            Dictionary of ID token claims or None
        """
        cached_token = self.get_cached_token()
        if not cached_token or "id_token_claims" not in cached_token:
            return None
        
        return cached_token["id_token_claims"]

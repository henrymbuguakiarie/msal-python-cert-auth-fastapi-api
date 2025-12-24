"""JWT token validation and authentication."""

import logging
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode

from .config import Settings, get_settings
from .exceptions import AuthenticationError, TokenValidationError

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


class JWTValidator:
    """JWT token validator with JWKS support.

    Validates Microsoft Entra ID access tokens by:
    - Verifying signature using JWKS
    - Validating issuer, audience, and expiration
    - Checking required scopes
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize JWT validator.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._jwks_cache: dict[str, Any] | None = None
        self._http_client = httpx.Client(timeout=10.0)

    def __del__(self) -> None:
        """Clean up HTTP client."""
        if hasattr(self, "_http_client"):
            self._http_client.close()

    async def _fetch_jwks(self) -> dict[str, Any]:
        """Fetch JSON Web Key Set from Microsoft.

        Returns:
            JWKS containing public keys for signature verification

        Raises:
            TokenValidationError: If JWKS fetch fails
        """
        if self._jwks_cache:
            return self._jwks_cache

        try:
            response = self._http_client.get(self.settings.jwks_endpoint)
            response.raise_for_status()
            self._jwks_cache = response.json()
            logger.info("Successfully fetched JWKS from Microsoft")
            return self._jwks_cache
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise TokenValidationError(f"Unable to fetch JWKS: {e}")

    def _get_signing_key(self, token: str, jwks: dict[str, Any]) -> dict[str, Any]:
        """Extract signing key from JWKS based on token header.

        Args:
            token: JWT token
            jwks: JSON Web Key Set

        Returns:
            Signing key matching token's kid

        Raises:
            TokenValidationError: If signing key not found
        """
        try:
            # Decode header without verification to get kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise TokenValidationError("Token header missing 'kid' claim")

            # Find matching key in JWKS
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    return key

            raise TokenValidationError(f"Signing key with kid '{kid}' not found in JWKS")

        except JWTError as e:
            logger.error(f"Error extracting signing key: {e}")
            raise TokenValidationError(f"Invalid token header: {e}")

    async def validate_token(self, token: str) -> dict[str, Any]:
        """Validate JWT token and extract claims.

        Args:
            token: JWT access token from Authorization header

        Returns:
            Decoded token claims

        Raises:
            TokenValidationError: If token validation fails
        """
        try:
            # Fetch JWKS
            jwks = await self._fetch_jwks()

            # Get signing key
            signing_key = self._get_signing_key(token, jwks)

            # Ensure algorithm is set for RSA keys
            if "alg" not in signing_key:
                signing_key["alg"] = "RS256"

            # Construct RSA public key
            public_key = jwk.construct(signing_key, algorithm="RS256")

            # Decode and verify signature
            message, encoded_signature = token.rsplit(".", 1)
            decoded_signature = base64url_decode(encoded_signature.encode())

            if not public_key.verify(message.encode(), decoded_signature):
                raise TokenValidationError("Invalid token signature")

            # Decode claims WITHOUT issuer validation first to check actual issuer
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.settings.api_app_id_uri,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": False,  # We'll validate issuer manually
                },
            )

            # Manually validate issuer - accept both v1.0 and v2.0 endpoints
            token_issuer = claims.get("iss", "")
            expected_issuers = [
                f"https://login.microsoftonline.com/{self.settings.tenant_id}/v2.0",
                f"https://sts.windows.net/{self.settings.tenant_id}/",
            ]

            if not any(token_issuer == issuer for issuer in expected_issuers):
                raise TokenValidationError(
                    f"Invalid issuer. Expected one of {expected_issuers}, got {token_issuer}"
                )

            # Validate required scope
            scopes = claims.get("scp", "").split() or claims.get("roles", [])
            if self.settings.required_scope not in scopes:
                raise TokenValidationError(
                    f"Token missing required scope: {self.settings.required_scope}"
                )

            logger.info(f"Successfully validated token for user: {claims.get('oid')}")
            return claims

        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise TokenValidationError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            raise TokenValidationError(f"Token validation error: {e}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """FastAPI dependency to extract and validate current user from token.

    Args:
        credentials: HTTP Bearer token credentials
        settings: Application settings

    Returns:
        Token claims containing user information

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        validator = JWTValidator(settings)
        claims = await validator.validate_token(credentials.credentials)
        return claims
    except TokenValidationError as e:
        raise HTTPException(
            status_code=401,
            detail=e.message,
            headers={"WWW-Authenticate": f'Bearer error="{e.details.get("reason")}"'},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_oid(claims: dict[str, Any] = Depends(get_current_user)) -> str:
    """Extract user's object ID from token claims.

    Args:
        claims: Token claims from get_current_user

    Returns:
        User's Microsoft Entra ID object ID

    Raises:
        HTTPException: If oid claim is missing
    """
    oid = claims.get("oid")
    if not oid:
        raise HTTPException(status_code=401, detail="Token missing required 'oid' claim")
    return oid

"""Configuration management for the client application.

This module provides environment-based configuration using Pydantic Settings.
All sensitive values are loaded from environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        tenant_id: Microsoft Entra ID tenant ID
        client_id: Application (client) ID from app registration
        client_cert_path: Path to X.509 certificate file (.pem or .pfx)
        client_cert_thumbprint: Certificate thumbprint (SHA-1)
        redirect_uri: OAuth redirect URI for authorization code flow
        api_scope: Delegated permission scope (e.g., api://api-app-id/access_as_user)
        api_base_url: Base URL of the downstream FastAPI
        flask_secret_key: Flask session secret key
        flask_port: Port for Flask application
        debug: Enable debug mode
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Microsoft Entra ID Configuration
    tenant_id: str = Field(..., min_length=36, max_length=36)
    client_id: str = Field(..., min_length=36, max_length=36)

    # Certificate Configuration
    client_cert_path: str = Field(...)
    client_cert_thumbprint: str = Field(..., min_length=40, max_length=40)

    # OAuth Configuration
    redirect_uri: str = Field(default="http://localhost:5000/callback")
    api_scope: str = Field(...)

    # API Configuration
    api_base_url: str = Field(default="http://localhost:8000")

    # Flask Configuration
    flask_secret_key: str = Field(default="dev-secret-key-change-in-production")
    flask_port: int = Field(default=5000, ge=1, le=65535)
    debug: bool = Field(default=False)

    @field_validator("client_cert_path")
    @classmethod
    def validate_cert_path(cls, v: str) -> str:
        """Validate that certificate path exists."""
        cert_path = Path(v)
        if not cert_path.exists():
            raise ValueError(f"Certificate file not found: {v}")
        if not cert_path.is_file():
            raise ValueError(f"Certificate path is not a file: {v}")
        return v

    @field_validator("api_scope")
    @classmethod
    def validate_api_scope(cls, v: str) -> str:
        """Validate that API scope follows the correct format."""
        if not v.startswith("api://"):
            raise ValueError(
                "API scope must start with 'api://' "
                "(e.g., api://your-api-app-id/access_as_user)"
            )
        if "/access_as_user" not in v:
            raise ValueError("API scope must include '/access_as_user'")
        return v

    @field_validator("redirect_uri")
    @classmethod
    def validate_redirect_uri(cls, v: str) -> str:
        """Validate redirect URI format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Redirect URI must start with http:// or https://")
        return v

    @property
    def authority(self) -> str:
        """Get the Microsoft identity platform authority URL."""
        return f"https://login.microsoftonline.com/{self.tenant_id}"

    @property
    def scope_list(self) -> list[str]:
        """Get API scope as a list."""
        return [self.api_scope]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Singleton Settings instance
    """
    return Settings()

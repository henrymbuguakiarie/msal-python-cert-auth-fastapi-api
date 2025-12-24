"""Configuration management using Pydantic Settings."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    Example: TENANT_ID=xxx python main.py
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Microsoft Entra ID Configuration
    tenant_id: str = Field(..., description="Microsoft Entra ID tenant ID")
    api_app_id_uri: str = Field(
        ...,
        description="API Application ID URI (e.g., api://client-id)",
        alias="API_APP_ID_URI"
    )
    required_scope: str = Field(
        default="access_as_user",
        description="Required OAuth2 scope for API access"
    )
    
    # JWKS Configuration
    jwks_uri: str | None = Field(
        default=None,
        description="Override JWKS URI (auto-constructed if not provided)"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./blog_api.db",
        description="Database connection string"
    )
    
    # API Configuration
    api_version: str = Field(default="v1", description="API version prefix")
    api_title: str = Field(default="Blog API", description="API title")
    api_description: str = Field(
        default="FastAPI downstream API with Microsoft Entra ID authentication",
        description="API description"
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment"
    )
    
    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    @field_validator("tenant_id")
    @classmethod
    def validate_tenant_id(cls, v: str) -> str:
        """Validate tenant ID format (GUID)."""
        if not v or len(v) < 36:
            raise ValueError("TENANT_ID must be a valid GUID")
        return v
    
    @field_validator("api_app_id_uri", mode="before")
    @classmethod
    def validate_app_id_uri(cls, v: str | None) -> str:
        """Validate Application ID URI format."""
        if v is None or not isinstance(v, str) or not v.startswith("api://"):
            raise ValueError("API_APP_ID_URI must start with 'api://'")
        return v
    
    @property
    def jwks_endpoint(self) -> str:
        """Construct JWKS URI from tenant ID.
        
        Returns:
            JWKS URI for token signature validation
        """
        if self.jwks_uri:
            return self.jwks_uri
        return (
            f"https://login.microsoftonline.com/{self.tenant_id}/"
            "discovery/v2.0/keys"
        )
    
    @property
    def token_issuer(self) -> str:
        """Construct expected token issuer.
        
        Returns:
            Expected issuer claim value
        """
        return f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Singleton Settings instance
    """
    return Settings()

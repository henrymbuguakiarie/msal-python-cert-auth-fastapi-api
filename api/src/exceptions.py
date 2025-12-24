"""Custom exception classes for API error handling."""
from typing import Any


class APIException(Exception):
    """Base exception for all API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize API exception.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(APIException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: dict[str, Any] | None = None) -> None:
        """Initialize authentication error."""
        super().__init__(message=message, status_code=401, details=details)


class AuthorizationError(APIException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions", details: dict[str, Any] | None = None) -> None:
        """Initialize authorization error."""
        super().__init__(message=message, status_code=403, details=details)


class ResourceNotFoundError(APIException):
    """Raised when requested resource doesn't exist."""
    
    def __init__(self, resource: str, identifier: str | int) -> None:
        """Initialize resource not found error."""
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message=message, status_code=404)


class ValidationError(APIException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize validation error."""
        super().__init__(message=message, status_code=422, details=details)


class TokenValidationError(AuthenticationError):
    """Raised when JWT token validation fails."""
    
    def __init__(self, reason: str) -> None:
        """Initialize token validation error."""
        super().__init__(
            message="Token validation failed",
            details={"reason": reason}
        )

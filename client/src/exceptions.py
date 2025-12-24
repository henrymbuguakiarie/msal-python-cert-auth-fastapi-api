"""Custom exceptions for the client application."""


class ClientError(Exception):
    """Base exception for client errors."""

    pass


class AuthenticationError(ClientError):
    """Raised when authentication fails."""

    pass


class TokenAcquisitionError(AuthenticationError):
    """Raised when token acquisition fails."""

    pass


class CertificateError(AuthenticationError):
    """Raised when certificate loading or validation fails."""

    pass


class APIClientError(ClientError):
    """Base exception for API client errors."""

    pass


class UnauthorizedError(APIClientError):
    """Raised when API returns 401 Unauthorized."""

    pass


class ForbiddenError(APIClientError):
    """Raised when API returns 403 Forbidden."""

    pass


class NotFoundError(APIClientError):
    """Raised when API returns 404 Not Found."""

    pass


class BadRequestError(APIClientError):
    """Raised when API returns 400 Bad Request."""

    pass


class APIServerError(APIClientError):
    """Raised when API returns 5xx Server Error."""

    pass

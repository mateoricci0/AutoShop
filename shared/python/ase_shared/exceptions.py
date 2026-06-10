"""ASE exception hierarchy.

All custom exceptions in the platform derive from ASEError so callers
can catch any platform error with a single except clause.
"""

from __future__ import annotations


class ASEError(Exception):
    """Base class for all ASE platform errors."""

    def __init__(self, message: str = "", *args: object) -> None:
        super().__init__(message, *args)
        self.message = message

    def __str__(self) -> str:
        return self.message


class NotFoundError(ASEError):
    """Raised when a requested resource does not exist."""


class ConflictError(ASEError):
    """Raised when an operation would violate a uniqueness constraint."""


class ValidationError(ASEError):
    """Raised when input data fails domain-level validation."""


class ExternalAPIError(ASEError):
    """Raised when a call to an external API (Shopify, DeepSeek, etc.) fails."""

    def __init__(
        self,
        message: str = "",
        *,
        status_code: int | None = None,
        provider: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.provider = provider


class AuthenticationError(ASEError):
    """Raised when authentication fails (invalid credentials, expired session)."""


class EncryptionError(ASEError):
    """Raised when Fernet encryption or decryption fails."""

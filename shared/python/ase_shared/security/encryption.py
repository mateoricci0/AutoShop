"""Fernet symmetric encryption for sensitive values stored in PostgreSQL.

Used primarily to encrypt Shopify API tokens before persisting them.
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    key = os.environ.get("FERNET_KEY")
    if not key:
        raise RuntimeError(
            "FERNET_KEY environment variable is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt(plaintext: str) -> str:
    """Encrypt *plaintext* and return a URL-safe base64 token string."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt *token* and return the original plaintext string.

    Raises:
        cryptography.fernet.InvalidToken: if the token is invalid or tampered.
    """
    return _get_fernet().decrypt(token.encode()).decode()

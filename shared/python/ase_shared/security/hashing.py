"""bcrypt password hashing helpers."""

from __future__ import annotations

import bcrypt


def hash_password(plaintext: str) -> str:
    """Hash *plaintext* with bcrypt and return the hash as a string."""
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()


def verify_password(plaintext: str, hashed: str) -> bool:
    """Return True if *plaintext* matches the bcrypt *hashed* value."""
    return bcrypt.checkpw(plaintext.encode(), hashed.encode())

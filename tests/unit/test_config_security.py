"""
Module: config_security

Purpose:
    Unit tests for config_security.

Responsibilities:
    - Test functionality and edge cases.

Depends on:
    - config_security

Subscribes to:
    None

Publishes:
    None
"""

from config_security import generate_admin_password
from core.security import verify_password


def test_generate_admin_password():
    plain, hashed = generate_admin_password()

    assert len(plain) == 16
    assert isinstance(hashed, str)
    assert hashed.startswith("pbkdf2:sha256:")
    assert verify_password(plain, hashed)

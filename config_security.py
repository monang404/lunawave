"""
Module: config_security

Purpose:
    Handles security configurations, including admin password generation and hashing.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - core.security

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless.
"""

import secrets
import string

from core.security import hash_password


def generate_admin_password() -> tuple[str, str]:
    """Generate password acak + hash-nya. Return (plain, hashed)."""
    alphabet = string.ascii_letters + string.digits
    plain = "".join(secrets.choice(alphabet) for _ in range(16))
    hashed = hash_password(plain)
    return plain, hashed

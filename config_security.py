"""
Module: config_security

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import secrets
import string
from core.security import hash_password

def generate_admin_password() -> tuple[str, str]:
    """Generate password acak + hash-nya. Return (plain, hashed)."""
    alphabet = string.ascii_letters + string.digits
    plain = ''.join(secrets.choice(alphabet) for _ in range(16))
    hashed = hash_password(plain)
    return plain, hashed

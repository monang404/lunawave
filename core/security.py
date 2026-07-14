"""
Module: core.security

Purpose:
    Provide PBKDF2-SHA256 password hashing and constant-time verification.

Responsibilities:
    - Hash a plaintext password with a random 16-byte salt.
    - Verify a plaintext password against a stored pbkdf2 hash string.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless.
"""

import base64
import hashlib
import secrets


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"pbkdf2:sha256:100000${base64.b64encode(salt).decode('utf-8')}${base64.b64encode(key).decode('utf-8')}"


def verify_password(password: str, hashed_password: str) -> bool:
    if not hashed_password.startswith("pbkdf2:sha256:"):
        # TASK-1.1: Tolak semua format non-pbkdf2 — hapus plaintext fallback
        # Plaintext comparison adalah security hole: password mentah tersimpan
        # di env var, log, dan /proc/self/environ.
        return False
    try:
        _, _, iterations, salt_b64, key_b64 = (
            hashed_password.split("$")[0].split(":") + hashed_password.split("$")[1:]
        )
        salt = base64.b64decode(salt_b64)
        expected_key = base64.b64decode(key_b64)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return secrets.compare_digest(key, expected_key)
    except Exception:
        return False

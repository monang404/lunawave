"""
Module: launcher.auth_service

Purpose:
    Non-UI logic for generating, persisting, and verifying the launcher's
    admin password file. Extracted from launcher.gui.auth_panel (T3.2) so
    the auth logic doesn't live inside the Tkinter dialog code.

Responsibilities:
    - Generate new random raw admin passwords.
    - Persist the raw password to instance/admin_password.txt with
      restrictive file permissions.
    - Resolve the password file path and verify stored passwords.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless.
"""

import secrets
import stat
from pathlib import Path


def password_file_path(base_dir) -> Path:
    """Return the on-disk location of the admin password file."""
    return Path(base_dir) / "instance" / "admin_password.txt"


def password_file_exists(base_dir) -> bool:
    """Whether an admin password file already exists (used for first-run check)."""
    return password_file_path(base_dir).exists()


def generate_password() -> str:
    """Generate a new random raw admin password."""
    return secrets.token_urlsafe(12)


def save_password(base_dir, raw_password: str) -> Path:
    """Persist ``raw_password`` to the instance password file.

    NOTE: the file on disk MUST hold the raw plaintext password, not a
    hash. config.py's loader (and config_security.generate_admin_password())
    both read this file as raw plaintext and hash it themselves on every
    startup — writing a pre-hashed string here caused config.py to hash
    an already-hashed value, silently invalidating the password shown
    to the user (PATCH-2026-07-16-001).
    """
    password_file = password_file_path(base_dir)
    password_file.parent.mkdir(parents=True, exist_ok=True)
    with open(password_file, "w", encoding="utf-8") as f:
        f.write(raw_password)
    try:
        password_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return password_file


def verify_password(base_dir, candidate: str) -> bool:
    """Check whether ``candidate`` matches the raw password currently on disk."""
    password_file = password_file_path(base_dir)
    if not password_file.exists():
        return False
    stored = password_file.read_text(encoding="utf-8").strip()
    return secrets.compare_digest(stored, candidate)

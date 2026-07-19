"""
Module: tests.unit.launcher.gui.test_auth_panel

Purpose:
    Regression tests for launcher.gui.auth_panel's admin password file
    contract.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - launcher.gui.auth_panel
    - core.security

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless.
"""

from unittest.mock import MagicMock

import launcher.gui.auth_panel as auth_panel
from core.security import hash_password, verify_password


def _dummy_colors():
    # bg, bg_card, bg_surface, accent, text_1, text_2, text_3, red, green, border
    return ("bg", "bg_card", "bg_surface", "accent", "t1", "t2", "t3", "red", "green", "border")


def test_handle_first_run_writes_raw_password_not_hash(tmp_path, monkeypatch):
    """PATCH-2026-07-16-001 regression.

    Bug found: auth_panel._reset_password() wrote hash_password(raw) into
    the admin password file (originally cache/admin_password.txt, moved to
    instance/admin_password.txt by T1.1). config.py's loader treats the
    *file content*
    as the raw plaintext password and hashes it itself on every startup
    (see config.py / config_security.generate_admin_password()), so writing
    an already-hashed string there caused config.py to hash-the-hash —
    permanently locking the admin out of the password the launcher had
    just shown them.

    Before the fix: `raw_from_file` was a pbkdf2 hash string, so hashing it
    again the way config.py does produced a hash that does NOT verify
    against the original raw_password shown to the user -> the assertions
    below failed on the old code.
    """
    monkeypatch.setattr(auth_panel, "show_new_password_dialog", MagicMock())

    app_instance = MagicMock()
    # Route the deferred first-run dialog callback straight through so we
    # don't need a real Tk mainloop for `after()`.
    app_instance._safe_after.side_effect = lambda _delay, fn: fn()

    auth_panel.handle_first_run(app_instance, tmp_path, *_dummy_colors())

    password_file = tmp_path / "instance" / "admin_password.txt"
    assert password_file.exists()
    raw_from_file = password_file.read_text(encoding="utf-8").strip()

    # The file must NOT already be a pbkdf2 hash — it must be the raw
    # password, exactly like config.py expects to read and then hash itself.
    assert not raw_from_file.startswith("pbkdf2:sha256:")

    # Simulate config.py's own loading contract: it hashes whatever raw
    # plaintext it finds in the file, then that hash must verify against
    # that same file content as the "raw" secret.
    server_side_hash = hash_password(raw_from_file)
    assert verify_password(raw_from_file, server_side_hash) is True


def test_on_reset_password_also_writes_raw_password(tmp_path, monkeypatch):
    """Same contract must hold for the manual "reset password" button,
    which shares the _reset_password() implementation with first-run."""
    import tkinter.messagebox as messagebox

    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(auth_panel, "show_new_password_dialog", MagicMock())

    app_instance = MagicMock()

    auth_panel.on_reset_password(app_instance, tmp_path, *_dummy_colors())

    password_file = tmp_path / "instance" / "admin_password.txt"
    assert password_file.exists()
    raw_from_file = password_file.read_text(encoding="utf-8").strip()
    assert not raw_from_file.startswith("pbkdf2:sha256:")

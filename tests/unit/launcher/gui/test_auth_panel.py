"""
Module: tests.unit.launcher.gui.test_auth_panel

Purpose:
    Regression tests for launcher.gui.auth_panel's "Reset Password"
    contract post-T-B16: the launcher has no auth mechanism of its own
    anymore, it only opens the web portal.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - launcher.gui.auth_panel

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless.
"""

from unittest.mock import MagicMock

import launcher.gui.auth_panel as auth_panel


def test_on_reset_password_opens_web_portal_no_local_file(tmp_path, monkeypatch):
    """T-B16.1/T-B16.2 regression.

    Before the redesign, "Reset Password" generated a raw password and
    wrote it to instance/admin_password.txt (see removed
    launcher.auth_service). Since T-B16, the launcher has no auth
    mechanism of its own at all -- clicking the button must only open the
    web portal (Initial Setup / Login lives entirely in
    server/handlers/setup.py, backed by SQLite admin_account) and must
    never touch the filesystem.
    """
    opened_urls = []
    monkeypatch.setattr(auth_panel.webbrowser, "open", lambda url: opened_urls.append(url))

    app_instance = MagicMock()
    app_instance.server_port = 8765

    auth_panel.on_reset_password(app_instance)

    assert opened_urls == ["http://localhost:8765"]
    # No password file mechanism left to exercise -- instance/ must stay empty.
    assert not (tmp_path / "instance").exists()


def test_on_reset_password_logs_when_write_log_available(monkeypatch):
    monkeypatch.setattr(auth_panel.webbrowser, "open", lambda url: None)

    app_instance = MagicMock()
    app_instance.server_port = 9999

    auth_panel.on_reset_password(app_instance)

    assert app_instance._write_log.called

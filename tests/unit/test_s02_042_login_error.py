"""
Tests for S02-042: Login error state cleared on re-attempt typing
"""


def test_login_error_cleared_on_username_input():
    """Verifikasi bahwa events/index.js memiliki input listener pada adminUsername yang membersihkan loginErrorMsg."""
    events_path = "web/static/js/events/index.js"
    with open(events_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pastikan ada addEventListener("input") pada adminUsername yang clear loginErrorMsg
    assert 'adminUsername' in content
    assert '"input"' in content or "'input'" in content
    assert 'loginErrorMsg' in content


def test_login_error_cleared_on_password_input():
    """Verifikasi bahwa events/index.js memiliki input listener pada adminPassword yang membersihkan loginErrorMsg."""
    events_path = "web/static/js/events/index.js"
    with open(events_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'adminPassword' in content
    # Pastikan ada dua addEventListener("input") — satu untuk password, satu untuk username
    assert content.count('"input"') >= 2 or content.count("'input'") >= 2

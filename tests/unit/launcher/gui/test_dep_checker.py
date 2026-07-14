"""
Module: tests.unit.launcher.gui.test_dep_checker

Purpose:
    Unit tests for the launcher dependency checker.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - launcher.gui.dep_checker

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless.
"""

from launcher.gui.dep_checker import DependencyChecker


def test_check_dependencies(monkeypatch):
    checker = DependencyChecker()

    # Mock importlib.util.find_spec to simulate missing/found packages
    def mock_find_spec(name):
        if name == "missing_pkg":
            return None
        return True

    monkeypatch.setattr("importlib.util.find_spec", mock_find_spec)

    # Temporarily override deps mapping for testing
    monkeypatch.setattr(
        checker.__class__, "check_dependencies", lambda self: (["missing_pkg"], True)
    )

    missing, mpv_ok = checker.check_dependencies()
    assert "missing_pkg" in missing
    assert mpv_ok is True

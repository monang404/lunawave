"""
Module: tests.unit.launcher.gui.test_app_lifecycle

Purpose:
    Regression tests for ServerManager's window-teardown safety: background
    threads (dependency check, status refresh loop, log writer) must not
    raise unhandled exceptions if they try to touch the GUI after the
    window has been destroyed.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - launcher.gui.app

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless (spawns/joins its own threads within each test).
"""

import threading
import time
import tkinter as tk

import pytest

try:
    _root = tk.Tk()
    _root.destroy()
    _HAS_DISPLAY = True
except tk.TclError:
    _HAS_DISPLAY = False

pytestmark = pytest.mark.skipif(not _HAS_DISPLAY, reason="requires a usable X display")


def _make_app(monkeypatch):
    from launcher.gui import app as app_module
    from launcher.gui import auth_panel

    # Keep the first-run password dialog out of the way — irrelevant here.
    # app.py imports handle_first_run locally (inside __init__) from
    # launcher.gui.auth_panel, so that's the name that must be patched.
    monkeypatch.setattr(auth_panel, "handle_first_run", lambda *a, **k: None)
    return app_module.ServerManager()


def test_safe_after_is_a_noop_once_closing(monkeypatch):
    """PATCH-2026-07-16-002 regression (direct check).

    Before the fix, every background-thread call site used raw
    `self.after(...)`/`app.after(...)` with no guard, so a callback firing
    after the window was destroyed raised RuntimeError/TclError in that
    thread. _safe_after must swallow that silently once `_closing` is set.
    """
    app = _make_app(monkeypatch)
    app.update()
    app.destroy()

    # Must not raise, unlike raw self.after() would after destroy.
    app._safe_after(0, lambda: None)


def test_background_thread_after_destroy_does_not_crash(monkeypatch):
    """End-to-end reproduction: spin up the real dependency-check thread
    (which calls back into the GUI via after()), destroy the window while
    it's still relevant, and assert the thread raises nothing.

    Before the fix this reliably reproduced:
        RuntimeError: main thread is not in main loop
    from within the background thread when it called `self.after(...)`
    after `destroy()`.
    """
    errors = []

    def _record_exc(args):
        errors.append(args)

    old_hook = threading.excepthook
    threading.excepthook = _record_exc
    try:
        app = _make_app(monkeypatch)
        app.update()
        app.destroy()
        app.update()
        # Give the daemon dependency-check thread time to finish and try
        # (and, pre-fix, fail) to call back into the destroyed window.
        deadline = time.time() + 3
        while time.time() < deadline:
            time.sleep(0.1)
    finally:
        threading.excepthook = old_hook

    assert errors == [], f"background thread(s) raised after window destroy: {errors}"

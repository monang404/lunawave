"""
Module: tests.unit.launcher.gui.test_app

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
except Exception:
    _HAS_DISPLAY = False

pytestmark = pytest.mark.skipif(not _HAS_DISPLAY, reason="requires a usable X display")


def _make_app(monkeypatch):
    from launcher.gui import app as app_module

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


# ---------------------------------------------------------------------------
# P4-T1c (temuan #9): except/pass di launcher/gui/app.py diklasifikasikan
# "best-effort cleanup" dan diberi logging debug-level (icon load, destroy's
# server-stop cleanup). _safe_after tetap sengaja silent (sudah dicover di
# atas) -- tidak diulang di sini.
# ---------------------------------------------------------------------------


def test_window_icon_load_failure_is_fail_safe_and_logged(monkeypatch):
    from launcher.gui import app as app_module

    calls = []
    monkeypatch.setattr(
        app_module.logger, "debug", lambda event, **kw: calls.append((event, kw))
    )
    monkeypatch.setattr(
        app_module.tk,
        "PhotoImage",
        lambda *a, **kw: (_ for _ in ()).throw(tk.TclError("bad icon")),
    )

    app = _make_app(monkeypatch)  # must not raise even though icon load fails
    app.update()
    app.destroy()

    assert [event for event, _ in calls] == ["window_icon_load_failed"]


def test_destroy_stop_failure_is_fail_safe_and_logged(monkeypatch):
    from launcher.gui import app as app_module

    calls = []
    monkeypatch.setattr(
        app_module.logger, "debug", lambda event, **kw: calls.append((event, kw))
    )

    app = _make_app(monkeypatch)
    app.update()

    monkeypatch.setattr(app, "_is_running", lambda: True)

    def _boom():
        raise RuntimeError("process already reaped")

    app.lifecycle.server_process = type("_P", (), {"stop": staticmethod(_boom)})()

    app.destroy()  # must not raise

    assert [event for event, _ in calls] == ["shutdown_stop_failed"]

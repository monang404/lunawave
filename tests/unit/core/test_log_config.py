"""tests/unit/core/test_log_config.py — mirrors core/log_config.py

Priority: Rendah (wiring). We cover the pure `simple_renderer` function
thoroughly, and treat `setup_logging()` as a smoke test with logging state
restored afterwards so it doesn't leak into other tests.
"""

import logging
import logging.handlers

import pytest

import core.log_config as log_config


def test_simple_renderer_formats_basic_fields():
    result = log_config.simple_renderer(
        None, "info", {"timestamp": "12:00:00", "level": "info", "event": "hello"}
    )
    assert result == "[12:00:00] INFO: hello"


def test_simple_renderer_appends_extra_keys():
    result = log_config.simple_renderer(
        None,
        "info",
        {"timestamp": "12:00:00", "level": "warning", "event": "disk low", "free_mb": 12},
    )
    assert result == "[12:00:00] WARNING: disk low (free_mb=12)"


def test_simple_renderer_ignores_logger_and_exc_info_keys():
    result = log_config.simple_renderer(
        None,
        "info",
        {
            "timestamp": "00:00:01",
            "level": "error",
            "event": "boom",
            "logger": "some.logger",
            "exc_info": True,
        },
    )
    assert result == "[00:00:01] ERROR: boom"


def test_simple_renderer_handles_missing_optional_fields():
    result = log_config.simple_renderer(None, "info", {})
    assert result == "[] : "


@pytest.fixture
def clean_logging_state():
    """setup_logging() mutates the global logging module — snapshot and
    restore root handlers so this test doesn't leak into others."""
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    # logging.basicConfig() is a no-op if the root logger already has
    # handlers (pytest's own log-capture handler, in this case), so we
    # clear them for the duration of the test to let setup_logging() take
    # effect the way it would on a fresh process.
    root.handlers = []
    yield
    root.handlers = original_handlers
    root.setLevel(original_level)


def test_setup_logging_smoke_creates_log_file(tmp_path, monkeypatch, clean_logging_state):
    # pytest's own log-capture plugin keeps a handler on the root logger for
    # the whole test call, which makes logging.basicConfig() (called inside
    # setup_logging()) a legitimate no-op per stdlib semantics — so we don't
    # assert on root.handlers here. What we *can* assert without fighting
    # the test runner's own logging setup is the concrete file-system effect:
    # setup_logging() must create BASE_DIR/lunawave.log via RotatingFileHandler.
    monkeypatch.setattr(log_config, "BASE_DIR", tmp_path)
    log_config.setup_logging()
    assert (tmp_path / "lunawave.log").exists()


def test_setup_logging_wires_a_queue_handler_when_root_has_no_handlers(monkeypatch, tmp_path):
    """Same smoke test, but run in a truly clean logging.basicConfig()
    scenario (as it would run at real app startup) by bypassing pytest's
    log-capture handler for the duration of the call."""
    monkeypatch.setattr(log_config, "BASE_DIR", tmp_path)
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    try:
        root.handlers = []
        log_config.setup_logging()
        assert any(isinstance(h, logging.handlers.QueueHandler) for h in root.handlers)
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)

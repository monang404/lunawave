import pytest
import structlog
from unittest.mock import patch

from core.log_config import _CompactRenderer


def test_compact_renderer_returns_tuple():
    renderer = _CompactRenderer()
    event_dict = {"event": "test event", "level": "info", "timestamp": "12:00:00"}
    
    with patch('sys.stderr.write'):
        result = renderer(None, "info", event_dict)
        
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == ("test event",)
    assert result[1] == {"extra": event_dict}

def test_compact_renderer_drops_noise():
    renderer = _CompactRenderer()

    event_dict = {
        "event": "GET /favicon.ico 200",
        "level": "info"
    }

    import unittest.mock
    with unittest.mock.patch("sys.stderr.write"):
        with pytest.raises(structlog.DropEvent):
            renderer(None, "info", event_dict)

def test_status_bar_worker_exit_condition():
    import threading

    from core.cli_ui import _status_bar_worker, _stop_event, stop_status_bar

    # Reset event just in case
    _stop_event.clear()

    # Start the worker thread explicitly for testing
    t = threading.Thread(target=_status_bar_worker)

    import core.cli_ui
    core.cli_ui._status_bar_active = True

    import unittest.mock
    with unittest.mock.patch("sys.stderr.write"):
        t.start()

        # Stop it
        stop_status_bar()

        # Wait for thread to finish (should be immediate since wait(5) is interrupted)
        t.join(timeout=1.0)

    assert not t.is_alive()
    assert _stop_event.is_set()

def test_summary_worker_exit_condition():
    import threading

    from core.cli_ui import _stop_event, _summary_worker

    _stop_event.clear()

    t = threading.Thread(target=_summary_worker)

    import unittest.mock
    with unittest.mock.patch("sys.stderr.write"):
        t.start()

        _stop_event.set()

        t.join(timeout=1.0)

    assert not t.is_alive()

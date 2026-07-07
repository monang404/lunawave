import pytest
import structlog
from core.log_config import _CompactRenderer

def test_compact_renderer_returns_dict():
    renderer = _CompactRenderer()
    
    event_dict = {
        "event": "Test Event",
        "level": "info",
        "timestamp": "12:00:00",
        "logger": "test"
    }
    
    # We mock sys.stderr so it doesn't print during tests
    import unittest.mock
    with unittest.mock.patch("sys.stderr.write"):
        result = renderer(None, "info", event_dict.copy())
    
    # Harus mengembalikan dict, BUKAN string kosong
    assert isinstance(result, dict)
    assert result["event"] == "Test Event"
    assert result["level"] == "info"

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
    from core.log_config import _stop_event, _status_bar_worker, _status_bar_active, stop_status_bar, start_status_bar
    import threading
    import time
    
    # Reset event just in case
    _stop_event.clear()
    
    # Start the worker thread explicitly for testing
    t = threading.Thread(target=_status_bar_worker)
    
    import core.log_config
    core.log_config._status_bar_active = True
    
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
    from core.log_config import _stop_event, _summary_worker
    import threading
    
    _stop_event.clear()
    
    t = threading.Thread(target=_summary_worker)
    
    import unittest.mock
    with unittest.mock.patch("sys.stderr.write"):
        t.start()
        
        _stop_event.set()
        
        t.join(timeout=1.0)
        
    assert not t.is_alive()

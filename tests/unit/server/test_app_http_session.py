import pytest
from unittest.mock import MagicMock
from server.app import create_app

def test_app_injects_http_session():
    playback_mock = MagicMock()
    ytdlp_mock = MagicMock()
    db_mock = MagicMock()
    manager_mock = MagicMock()
    http_session_mock = MagicMock()
    
    app = create_app(
        playback_mock, 
        ytdlp_mock, 
        db_mock, 
        manager_mock,
        http_session=http_session_mock
    )
    
    assert "http_session" in app
    assert app["http_session"] is http_session_mock

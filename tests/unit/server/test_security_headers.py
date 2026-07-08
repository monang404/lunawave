import pytest
from aiohttp import web
from server.app import create_app
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_playback_controller():
    controller = MagicMock()
    controller.state = MagicMock()
    return controller

@pytest.fixture
def mock_ytdlp():
    return AsyncMock()

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def mock_manager():
    return MagicMock()

@pytest.mark.asyncio
async def test_security_headers_present(aiohttp_client, mock_playback_controller, mock_ytdlp, mock_db, mock_manager):
    app = create_app(mock_playback_controller, mock_ytdlp, mock_db, mock_manager)
    client = await aiohttp_client(app)

    resp = await client.get("/health")
    # Status can be 503 due to mock_db failing health check, but middleware should still inject headers.
    
    assert "Content-Security-Policy" in resp.headers
    assert "X-Frame-Options" in resp.headers
    assert "X-Content-Type-Options" in resp.headers
    assert "Strict-Transport-Security" in resp.headers
    assert "Referrer-Policy" in resp.headers
    
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"

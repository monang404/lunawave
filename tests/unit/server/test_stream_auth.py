from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from server.handlers.http import serve_stream


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.match_info = {"video_id": "dQw4w9WgXcQ"}
    req.headers = {"Origin": "http://localhost:8080"}
    req.host = "localhost:8080"
    req.remote = "192.168.1.5"  # Non-localhost
    req.scheme = "http"
    req.query = {}  # No token

    mock_db = AsyncMock()
    mock_db.verify_session = AsyncMock(return_value=False)

    app = {"db": mock_db}
    req.app = app
    return req

@pytest.mark.asyncio
async def test_serve_stream_requires_token(mock_request):
    response = await serve_stream(mock_request)
    assert response.status == 401
    import json
    data = json.loads(response.text)
    assert data["error"]["code"] == "HTTP_ERROR"
    assert data["error"]["message"] == "Unauthorized token"

@pytest.mark.asyncio
async def test_serve_stream_accepts_valid_token(mock_request):
    mock_request.query = {"token": "valid_token"}
    mock_request.app["db"].verify_session = AsyncMock(return_value=True)
    mock_request.app["db"].get_track = AsyncMock(return_value=None)  # Just to pass beyond auth

    # We mock _try_serve_cache to prevent actual file checks
    with pytest.MonkeyPatch.context() as m:
        m.setattr("server.handlers.http._try_serve_cache", lambda r, v, c: None)
        m.setattr("server.handlers.http._proxy_stream", AsyncMock(return_value=web.Response(text="proxy")))

        mock_request.app["db"].get_track = AsyncMock(return_value=None)
        response = await serve_stream(mock_request)
        # Should reach _proxy_stream because it's authorized
        assert response.text == "proxy"

@pytest.mark.asyncio
async def test_serve_stream_allows_localhost_no_token(mock_request):
    mock_request.remote = "127.0.0.1"  # Localhost
    mock_request.query = {}  # No token

    with pytest.MonkeyPatch.context() as m:
        m.setattr("server.handlers.http._try_serve_cache", lambda r, v, c: None)
        m.setattr("server.handlers.http._proxy_stream", AsyncMock(return_value=web.Response(text="proxy")))

        mock_request.app["db"].get_track = AsyncMock(return_value=None)
        response = await serve_stream(mock_request)
        # Should allow localhost even without token
        assert response.text == "proxy"

"""
Module: server.handlers.http

Purpose:
    Unit tests for server.handlers.http.

Responsibilities:
    - Test functionality and edge cases.

Depends on:
    - server.handlers.http

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import web

from server.handlers.http import health_check, serve_index, serve_metrics, serve_stream


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app = {}
    return req


@pytest.mark.asyncio
async def test_serve_index_returns_file_response(mock_request):
    # Mock STATIC_DIR and FileResponse
    with patch("server.handlers.http.STATIC_DIR", Path("/fake/static")):
        with patch("server.handlers.http.web.FileResponse") as mock_file_response:
            mock_resp = MagicMock()
            mock_resp.headers = {}
            mock_file_response.return_value = mock_resp

            resp = await serve_index(mock_request)

            mock_file_response.assert_called_once_with(Path("/fake/static/index.html"))
            assert resp.headers["Cache-Control"] == "no-cache"


@pytest.mark.asyncio
async def test_health_check_returns_ok_when_connected(mock_request):
    mock_db = MagicMock()
    mock_db.conn = True

    mock_pc = MagicMock()
    mock_pc.mpv.is_connected = True

    mock_request.app["db"] = mock_db
    mock_request.app["playback_controller"] = mock_pc

    with patch("server.handlers.http.web.json_response") as mock_json_resp:
        mock_json_resp.return_value = "response"

        resp = await health_check(mock_request)

        mock_json_resp.assert_called_once_with(
            {"status": "ok", "db": "connected", "mpv": "connected"}
        )
        assert resp == "response"


@pytest.mark.asyncio
async def test_health_check_returns_degraded_when_db_disconnected(mock_request):
    mock_db = MagicMock()
    mock_db.conn = False

    mock_request.app["db"] = mock_db

    with patch("server.handlers.http.web.json_response") as mock_json_resp:
        await health_check(mock_request)
        mock_json_resp.assert_called_once_with(
            {"status": "degraded", "db": "disconnected", "mpv": "not_started"}
        )


@pytest.mark.asyncio
async def test_serve_stream_invalid_video_id(mock_request):
    mock_request.match_info = {"video_id": "invalid!"}

    resp = await serve_stream(mock_request)
    assert isinstance(resp, web.HTTPBadRequest)
    assert resp.text == "Invalid video_id"


@pytest.mark.asyncio
async def test_serve_metrics_allows_localhost(mock_request):
    mock_request.remote = "127.0.0.1"

    with patch("server.handlers.http.get_metrics_content") as mock_get_metrics:
        mock_get_metrics.return_value = (b"metrics", "text/plain; version=0.0.4")

        resp = await serve_metrics(mock_request)

        assert isinstance(resp, web.Response)
        assert resp.body == b"metrics"
        assert resp.content_type == "text/plain"


@pytest.mark.asyncio
async def test_serve_metrics_forbids_external_without_token(mock_request):
    mock_request.remote = "192.168.1.5"
    mock_request.headers = {}

    resp = await serve_metrics(mock_request)

    assert isinstance(resp, web.HTTPForbidden)

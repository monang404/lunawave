"""
Module: server.handlers.http

Purpose:
    Unit tests for server.handlers.http.

Responsibilities:
    - Test functionality and edge cases.

    serve_stream tests moved to
    tests/unit/server/handlers/test_audio_stream_handler.py (T3.4)
    alongside the serve_stream extraction into its own handler module.

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

from server.app import CONN, PLAYBACK_CONTROLLER
from server.handlers.http import health_check, serve_index, serve_metrics


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
    mock_pc = MagicMock()
    mock_pc.mpv.is_connected = True

    mock_request.app[CONN] = True
    mock_request.app[PLAYBACK_CONTROLLER] = mock_pc

    with patch("server.handlers.http.web.json_response") as mock_json_resp:
        mock_json_resp.return_value = "response"

        resp = await health_check(mock_request)

        mock_json_resp.assert_called_once_with(
            {"status": "ok", "db": "connected", "mpv": "connected"}
        )
        assert resp == "response"


@pytest.mark.asyncio
async def test_health_check_returns_degraded_when_db_disconnected(mock_request):
    mock_pc = MagicMock()
    mock_pc.mpv.is_connected = False
    mock_request.app[CONN] = False
    mock_request.app[PLAYBACK_CONTROLLER] = mock_pc

    with patch("server.handlers.http.web.json_response") as mock_json_resp:
        await health_check(mock_request)
        mock_json_resp.assert_called_once_with(
            {"status": "degraded", "db": "disconnected", "mpv": "not_started"}
        )


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


@pytest.mark.asyncio
async def test_serve_metrics_allows_external_with_valid_token(mock_request, monkeypatch):
    """PATCH-2026-07-16-001 regression: token compare pindah ke
    secrets.compare_digest(), pastikan token valid tetap diterima."""
    monkeypatch.setenv("LUNAWAVE_METRICS_TOKEN", "s3cr3t-token")
    mock_request.remote = "192.168.1.5"
    mock_request.headers = {"X-Metrics-Token": "s3cr3t-token"}

    with patch("server.handlers.http.get_metrics_content") as mock_get_metrics:
        mock_get_metrics.return_value = (b"metrics", "text/plain; version=0.0.4")
        resp = await serve_metrics(mock_request)

    assert isinstance(resp, web.Response)
    assert resp.body == b"metrics"


@pytest.mark.asyncio
async def test_serve_metrics_forbids_external_with_wrong_token(mock_request, monkeypatch):
    monkeypatch.setenv("LUNAWAVE_METRICS_TOKEN", "s3cr3t-token")
    mock_request.remote = "192.168.1.5"
    mock_request.headers = {"X-Metrics-Token": "wrong-token"}

    resp = await serve_metrics(mock_request)

    assert isinstance(resp, web.HTTPForbidden)

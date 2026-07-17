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

import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.mark.asyncio
@patch("server.handlers.http._STREAM_ID_RE")
async def test_serve_stream_path_traversal(mock_regex, mock_request):
    mock_regex.match.return_value = True
    mock_request.match_info = {"video_id": "../../../etc/passwd"}

    with patch("server.handlers.http.CACHE_DIR", Path("/fake/cache")):
        resp = await serve_stream(mock_request)
        assert isinstance(resp, web.HTTPForbidden)
        assert resp.text == "Akses ditolak"


@pytest.mark.asyncio
async def test_serve_stream_cache_hit(mock_request):
    mock_request.match_info = {"video_id": "abc123DEF-4"}

    with patch("server.handlers.http.CACHE_DIR") as mock_cache_dir:
        mock_cache_file = MagicMock()
        mock_cache_dir.__truediv__.return_value = mock_cache_file

        mock_cache_file.resolve.return_value.is_relative_to.return_value = True
        mock_cache_file.exists.return_value = True

        with patch("server.handlers.http.web.FileResponse") as mock_file_resp:
            mock_file_resp.return_value = "file_response_mock"
            resp = await serve_stream(mock_request)

            assert resp == "file_response_mock"
            mock_file_resp.assert_called_once_with(
                mock_cache_file, headers={"Access-Control-Allow-Origin": "*"}
            )


@pytest.mark.asyncio
async def test_serve_stream_db_fresh_no_http_session(mock_request):
    mock_request.match_info = {"video_id": "abc123DEF-4"}

    mock_db = AsyncMock()
    mock_row = MagicMock()
    mock_row.stream_url = "https://example.googlevideo.com/videoplayback"
    mock_row.stream_url_ts = time.time() - 10  # Fresh
    mock_db.get_track.return_value = mock_row

    mock_ytdlp = AsyncMock()

    mock_request.app["db"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp

    with patch("server.handlers.http.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.http.STREAM_URL_TTL_SEC", 3600):
            resp = await serve_stream(mock_request)

            assert isinstance(resp, web.HTTPFound)
            assert resp.location == "https://example.googlevideo.com/videoplayback"
            mock_ytdlp.get_stream_url.assert_not_called()


@pytest.mark.asyncio
async def test_serve_stream_db_stale_no_http_session(mock_request):
    mock_request.match_info = {"video_id": "abc123DEF-4"}

    mock_db = AsyncMock()
    mock_row = MagicMock()
    mock_row.stream_url = "https://old.googlevideo.com/videoplayback"
    mock_row.stream_url_ts = time.time() - 8000  # Stale
    mock_db.get_track.return_value = mock_row

    mock_ytdlp = AsyncMock()
    mock_ytdlp.get_stream_url.return_value = "https://new.googlevideo.com/videoplayback"

    mock_request.app["db"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp

    with patch("server.handlers.http.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.http.STREAM_URL_TTL_SEC", 3600):
            resp = await serve_stream(mock_request)

            assert isinstance(resp, web.HTTPFound)
            assert resp.location == "https://new.googlevideo.com/videoplayback"
            mock_ytdlp.get_stream_url.assert_called_once_with("abc123DEF-4")
            mock_db.update_stream_url_only.assert_called_once_with(
                "abc123DEF-4", "https://new.googlevideo.com/videoplayback"
            )


@pytest.mark.asyncio
async def test_serve_stream_redirect_invalid_domain(mock_request):
    mock_request.match_info = {"video_id": "abc123DEF-4"}

    mock_db = AsyncMock()
    mock_row = MagicMock()
    mock_row.stream_url = "https://evil.com/stream"
    mock_row.stream_url_ts = time.time() - 10  # Fresh
    mock_db.get_track.return_value = mock_row

    mock_request.app["db"] = mock_db
    mock_request.app["ytdlp"] = AsyncMock()

    with patch("server.handlers.http.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.http.STREAM_URL_TTL_SEC", 3600):
            resp = await serve_stream(mock_request)

            assert isinstance(resp, web.HTTPForbidden)
            assert resp.text == "URL stream tidak valid"


@pytest.mark.asyncio
async def test_serve_stream_redirect_invalid_scheme(mock_request):
    mock_request.match_info = {"video_id": "abc123DEF-4"}

    mock_db = AsyncMock()
    mock_row = MagicMock()
    mock_row.stream_url = "http://example.googlevideo.com/stream"
    mock_row.stream_url_ts = time.time() - 10  # Fresh
    mock_db.get_track.return_value = mock_row

    mock_request.app["db"] = mock_db
    mock_request.app["ytdlp"] = AsyncMock()

    with patch("server.handlers.http.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.http.STREAM_URL_TTL_SEC", 3600):
            resp = await serve_stream(mock_request)

            assert isinstance(resp, web.HTTPForbidden)
            assert resp.text == "URL stream tidak valid"


@pytest.mark.asyncio
async def test_serve_stream_proxy_retry_fetch_success(mock_request):
    mock_request.match_info = {"video_id": "abc123DEF-4"}
    mock_request.headers = {}

    mock_db = AsyncMock()
    mock_db.get_track.return_value = None

    mock_ytdlp = AsyncMock()
    # First attempt fails, second succeeds
    mock_ytdlp.get_stream_url.side_effect = [
        Exception("Fail"),
        "https://example.googlevideo.com/stream",
    ]

    mock_http_session = MagicMock()
    mock_upstream = MagicMock()
    mock_upstream.status = 200
    mock_upstream.headers = {"Content-Type": "audio/mpeg", "Content-Length": "100"}

    async def mock_chunked(*args, **kwargs):
        yield b"data"

    mock_upstream.content.iter_chunked = mock_chunked

    mock_http_session.get.return_value.__aenter__.return_value = mock_upstream

    mock_request.app["db"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp
    mock_request.app["http_session"] = mock_http_session

    with patch("server.handlers.http.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.http.web.StreamResponse") as mock_stream_response:
            mock_resp_obj = AsyncMock()
            mock_resp_obj.headers = {}
            mock_stream_response.return_value = mock_resp_obj

            resp = await serve_stream(mock_request)

            assert resp == mock_resp_obj
            assert mock_ytdlp.get_stream_url.call_count == 2
            mock_resp_obj.write.assert_called_once_with(b"data")
            mock_resp_obj.write_eof.assert_called_once()


@pytest.mark.asyncio
async def test_serve_stream_proxy_retry_both_fail(mock_request):
    mock_request.match_info = {"video_id": "abc123DEF-4"}

    mock_db = AsyncMock()
    mock_db.get_track.return_value = None

    mock_ytdlp = AsyncMock()
    mock_ytdlp.get_stream_url.side_effect = [Exception("Fail 1"), Exception("Fail 2")]

    mock_http_session = AsyncMock()

    mock_request.app["db"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp
    mock_request.app["http_session"] = mock_http_session

    with patch("server.handlers.http.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        resp = await serve_stream(mock_request)

        assert isinstance(resp, web.HTTPInternalServerError)
        assert "Gagal mencari stream" in resp.text


@pytest.mark.asyncio
async def test_serve_stream_proxy_range_header(mock_request):
    mock_request.match_info = {"video_id": "abc123DEF-4"}
    mock_request.headers = {"Range": "bytes=0-100"}

    mock_db = AsyncMock()
    mock_row = MagicMock()
    mock_row.stream_url = "https://example.googlevideo.com/stream"
    mock_row.stream_url_ts = time.time() - 10  # Fresh
    mock_db.get_track.return_value = mock_row

    mock_ytdlp = AsyncMock()

    mock_http_session = MagicMock()
    mock_upstream = MagicMock()
    mock_upstream.status = 206
    mock_upstream.headers = {"Content-Type": "audio/mpeg", "Content-Range": "bytes 0-100/1000"}

    async def mock_chunked(*args, **kwargs):
        yield b"data"

    mock_upstream.content.iter_chunked = mock_chunked

    mock_http_session.get.return_value.__aenter__.return_value = mock_upstream

    mock_request.app["db"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp
    mock_request.app["http_session"] = mock_http_session

    with patch("server.handlers.http.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.http.STREAM_URL_TTL_SEC", 3600):
            with patch("server.handlers.http.web.StreamResponse") as mock_stream_response:
                mock_resp_obj = AsyncMock()
                mock_resp_obj.headers = {}
                mock_stream_response.return_value = mock_resp_obj

                resp = await serve_stream(mock_request)

                assert resp == mock_resp_obj
                mock_http_session.get.assert_called_once_with(
                    "https://example.googlevideo.com/stream", headers={"Range": "bytes=0-100"}
                )
                assert mock_resp_obj.headers["Content-Range"] == "bytes 0-100/1000"


@pytest.mark.asyncio
async def test_serve_stream_proxy_forbidden_retry(mock_request):
    mock_request.match_info = {"video_id": "abc123DEF-4"}
    mock_request.headers = {}

    mock_db = AsyncMock()
    mock_row = MagicMock()
    mock_row.stream_url = "https://example.googlevideo.com/stream"
    mock_row.stream_url_ts = time.time() - 10  # Fresh
    mock_db.get_track.return_value = mock_row

    mock_ytdlp = AsyncMock()
    mock_ytdlp.get_stream_url.return_value = "https://example.googlevideo.com/newstream"

    mock_http_session = MagicMock()

    # First request returns 403, second returns 200
    mock_upstream_403 = MagicMock()
    mock_upstream_403.status = 403
    mock_upstream_403.headers = {}

    mock_upstream_200 = MagicMock()
    mock_upstream_200.status = 200
    mock_upstream_200.headers = {}
    mock_http_session.get.return_value.__aenter__.side_effect = [
        mock_upstream_403,
        mock_upstream_200,
    ]

    # need to return an async mock for iter_chunked
    async def mock_chunked(*args, **kwargs):
        yield b"data"

    mock_upstream_200.content.iter_chunked = mock_chunked

    mock_request.app["db"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp
    mock_request.app["http_session"] = mock_http_session

    with patch("server.handlers.http.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.http.STREAM_URL_TTL_SEC", 3600):
            with patch("server.handlers.http.web.StreamResponse") as mock_stream_response:
                mock_resp_obj = AsyncMock()
                mock_resp_obj.headers = {}
                mock_stream_response.return_value = mock_resp_obj

                await serve_stream(mock_request)

                assert mock_http_session.get.call_count == 2
                assert mock_ytdlp.get_stream_url.call_count == 1

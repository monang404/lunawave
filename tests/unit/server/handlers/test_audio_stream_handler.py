"""
Module: server.handlers.audio_stream_handler

Purpose:
    Unit tests for server.handlers.audio_stream_handler.serve_stream.
    Moved out of tests/unit/server/handlers/test_http.py (T3.4) alongside
    the serve_stream extraction into its own handler module.

Responsibilities:
    - Test functionality and edge cases: invalid video_id, path
      traversal, cache hit, DB-cached stream URL (fresh/stale), direct
      redirect vs proxy, range-request header forwarding, SSRF/domain
      validation, and retry-on-expired-URL behavior.

Depends on:
    - server.handlers.audio_stream_handler

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

from server.handlers.audio_stream_handler import serve_stream


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app = {}
    return req


@pytest.mark.asyncio
async def test_serve_stream_invalid_video_id(mock_request):
    mock_request.match_info = {"video_id": "invalid!"}

    resp = await serve_stream(mock_request)
    assert isinstance(resp, web.HTTPBadRequest)
    assert resp.text == "Invalid video_id"


@pytest.mark.asyncio
@patch("server.handlers.audio_stream_handler._STREAM_ID_RE")
async def test_serve_stream_path_traversal(mock_regex, mock_request):
    mock_regex.match.return_value = True
    mock_request.match_info = {"video_id": "../../../etc/passwd"}

    with patch("server.handlers.audio_stream_handler.CACHE_DIR", Path("/fake/cache")):
        resp = await serve_stream(mock_request)
        assert isinstance(resp, web.HTTPForbidden)
        assert resp.text == "Akses ditolak"


@pytest.mark.asyncio
async def test_serve_stream_cache_hit(mock_request):
    mock_request.match_info = {"video_id": "abc123DEF-4"}

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
        mock_cache_file = MagicMock()
        mock_cache_dir.__truediv__.return_value = mock_cache_file

        mock_cache_file.resolve.return_value.is_relative_to.return_value = True
        mock_cache_file.exists.return_value = True

        with patch("server.handlers.audio_stream_handler.web.FileResponse") as mock_file_resp:
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

    mock_request.app["tracks"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.audio_stream_handler.STREAM_URL_TTL_SEC", 3600):
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

    mock_request.app["tracks"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.audio_stream_handler.STREAM_URL_TTL_SEC", 3600):
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

    mock_request.app["tracks"] = mock_db
    mock_request.app["ytdlp"] = AsyncMock()

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.audio_stream_handler.STREAM_URL_TTL_SEC", 3600):
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

    mock_request.app["tracks"] = mock_db
    mock_request.app["ytdlp"] = AsyncMock()

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.audio_stream_handler.STREAM_URL_TTL_SEC", 3600):
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

    mock_request.app["tracks"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp
    mock_request.app["http_session"] = mock_http_session

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch(
            "server.handlers.audio_stream_handler.web.StreamResponse"
        ) as mock_stream_response:
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

    mock_request.app["tracks"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp
    mock_request.app["http_session"] = mock_http_session

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
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

    mock_request.app["tracks"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp
    mock_request.app["http_session"] = mock_http_session

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.audio_stream_handler.STREAM_URL_TTL_SEC", 3600):
            with patch(
                "server.handlers.audio_stream_handler.web.StreamResponse"
            ) as mock_stream_response:
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

    mock_request.app["tracks"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp
    mock_request.app["http_session"] = mock_http_session

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch("server.handlers.audio_stream_handler.STREAM_URL_TTL_SEC", 3600):
            with patch(
                "server.handlers.audio_stream_handler.web.StreamResponse"
            ) as mock_stream_response:
                mock_resp_obj = AsyncMock()
                mock_resp_obj.headers = {}
                mock_stream_response.return_value = mock_resp_obj

                await serve_stream(mock_request)

                assert mock_http_session.get.call_count == 2
                assert mock_ytdlp.get_stream_url.call_count == 1


@pytest.mark.asyncio
async def test_serve_stream_client_disconnect_mid_write_no_refetch(mock_request):
    """PATCH-2026-07-20-135 regression.

    Bug found: response.write() raising ConnectionResetError (client tutup
    tab/pindah track/seek di tengah stream) sebelumnya jatuh ke `except
    Exception` generik yang sama dengan error stream-URL asli -> memicu
    refetch yt-dlp yang sia-sia (attempt==0 -> stream_url=None -> continue)
    padahal URL-nya sendiri valid dan sudah sempat mulai ngirim data (upstream
    200). Dibuktikan dulu lewat harness terpisah sebelum ada test ini:
    get_stream_url() terpanggil 2x untuk satu client-disconnect di kode lama.

    Fix: ConnectionResetError/ConnectionAbortedError/BrokenPipeError saat
    menulis ke response ditangkap terpisah -> return langsung tanpa retry,
    tanpa refetch.
    """
    mock_request.match_info = {"video_id": "abc123DEF-4"}
    mock_request.headers = {}

    mock_db = AsyncMock()
    mock_db.get_track.return_value = None

    mock_ytdlp = AsyncMock()
    mock_ytdlp.get_stream_url.return_value = "https://example.googlevideo.com/stream"

    mock_http_session = MagicMock()
    mock_upstream = MagicMock()
    mock_upstream.status = 200
    mock_upstream.headers = {"Content-Type": "audio/mpeg"}

    async def mock_chunked(*args, **kwargs):
        yield b"data"

    mock_upstream.content.iter_chunked = mock_chunked
    mock_http_session.get.return_value.__aenter__.return_value = mock_upstream

    mock_request.app["tracks"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp
    mock_request.app["http_session"] = mock_http_session

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        with patch(
            "server.handlers.audio_stream_handler.web.StreamResponse"
        ) as mock_stream_response:
            mock_resp_obj = AsyncMock()
            mock_resp_obj.headers = {}
            # Simulasikan client memutus koneksi persis di tengah write().
            mock_resp_obj.write.side_effect = ConnectionResetError(
                "Cannot write to closing transport"
            )
            mock_stream_response.return_value = mock_resp_obj

            resp = await serve_stream(mock_request)

            assert resp == mock_resp_obj
            # Inti fix: TIDAK ada refetch kedua ke yt-dlp untuk sekadar
            # client yang sudah pergi.
            assert mock_ytdlp.get_stream_url.call_count == 1
            # response.write_eof() juga tidak perlu dipanggil krn stream
            # sudah putus di tengah jalan.
            mock_resp_obj.write_eof.assert_not_called()


@pytest.mark.asyncio
async def test_serve_stream_genuine_url_error_still_retries(mock_request):
    """Pembanding: error yang BUKAN client-disconnect (mis. koneksi upstream
    ke YouTube gagal total) harus tetap lewat jalur retry/refetch lama --
    fix di atas hanya mengecualikan disconnect, tidak melemahkan retry asli.
    """
    mock_request.match_info = {"video_id": "abc123DEF-4"}
    mock_request.headers = {}

    mock_db = AsyncMock()
    mock_db.get_track.return_value = None

    mock_ytdlp = AsyncMock()
    mock_ytdlp.get_stream_url.return_value = "https://example.googlevideo.com/stream"

    mock_http_session = MagicMock()
    # Upstream request itu sendiri yang gagal (bukan disconnect saat write).
    mock_http_session.get.side_effect = TimeoutError("upstream timeout")

    mock_request.app["tracks"] = mock_db
    mock_request.app["ytdlp"] = mock_ytdlp
    mock_request.app["http_session"] = mock_http_session

    with patch("server.handlers.audio_stream_handler.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value.resolve.return_value.is_relative_to.return_value = (
            True
        )
        mock_cache_dir.__truediv__.return_value.exists.return_value = False

        resp = await serve_stream(mock_request)

        # Tetap retry seperti semula: 2 attempt -> get_stream_url 2x -> tetap
        # gagal -> 500.
        assert mock_ytdlp.get_stream_url.call_count == 2
        assert isinstance(resp, web.HTTPInternalServerError)

# PATCHLOG_APPLIED
import re
import time
from pathlib import Path

import collections
import structlog
from aiohttp import web

from config import CACHE_DIR, STREAM_URL_TTL_SEC
from core.observability import get_metrics_content
from server.handlers.ws.utils import error_payload
from core.value_objects import VideoId

logger = structlog.get_logger(__name__)
STATIC_DIR = Path(__file__).parent.parent.parent / "web" / "static"

_stream_rate_limit = collections.defaultdict(list)
STREAM_RATE_LIMIT_MAX = 20

async def serve_index(request):
    resp = web.FileResponse(STATIC_DIR / "index.html")
    resp.headers["Cache-Control"] = "no-cache"
    return resp

async def health_check(request):
    db = request.app["db"]
    pc = request.app.get("playback_controller")
    mpv_ok = getattr(getattr(pc, "mpv", None), "is_connected", False)
    mpv_status = "connected" if mpv_ok else "not_started"
    
    db_status = "disconnected"
    try:
        if db.conn:
            async with db.conn.execute("SELECT 1") as cursor:
                if await cursor.fetchone():
                    db_status = "connected"
    except Exception:
        pass

    status_val = "ok" if db_status == "connected" else "degraded"
    status_code = 200 if status_val == "ok" else 503
    return web.json_response({
        "status": status_val,
        "db": db_status,
        "mpv": mpv_status
    }, status=status_code)

async def serve_stream(request):
    video_id_str = request.match_info.get("video_id")
    try:
        video_id = VideoId(video_id_str)
    except ValueError:
        return web.json_response(error_payload("HTTP_ERROR", "Invalid video_id"), status=400)

    client_ip = request.remote
    now = time.monotonic()
    history = _stream_rate_limit[client_ip]
    history = [t for t in history if now - t < 60]
    if len(history) >= STREAM_RATE_LIMIT_MAX:
        return web.json_response(error_payload("HTTP_ERROR", "Terlalu banyak request. Silakan coba lagi nanti."), status=429)
    history.append(now)
    _stream_rate_limit[client_ip] = history

    referer = request.headers.get("Referer", "")
    origin = request.headers.get("Origin", "")
    host = request.host
    if host not in referer and host not in origin and request.remote not in ("127.0.0.1", "::1"):
        return web.json_response(error_payload("HTTP_ERROR", "Unauthorized origin"), status=403)

    cache_file = CACHE_DIR / f"{video_id}.mp3"
    try:
        if not cache_file.resolve().is_relative_to(CACHE_DIR.resolve()):
            return web.json_response(error_payload("HTTP_ERROR", "Akses ditolak"), status=403)
    except Exception:
        return web.json_response(error_payload("HTTP_ERROR", "Path tidak valid"), status=400)

    if cache_file.exists():
        stat = cache_file.stat()
        etag = f'"{int(stat.st_mtime)}-{stat.st_size}"'
        if request.headers.get("If-None-Match") == etag:
            return web.Response(status=304)

        return web.FileResponse(
            cache_file,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "private, max-age=3600",
                "ETag": etag
            }
        )

    db = request.app["db"]
    ytdlp = request.app["ytdlp"]
    stream_url = None

    row = await db.get_track(video_id)
    if row and row.stream_url and row.stream_url_ts:
        if time.time() - row.stream_url_ts < STREAM_URL_TTL_SEC:
            stream_url = row.stream_url

    http_session = request.app.get("http_session")
    if not http_session:
        if not stream_url:
            try:
                stream_url = await ytdlp.get_stream_url(video_id)
                await db.update_stream_url_only(video_id, stream_url)
            except Exception as e:
                logger.error(f"Gagal fetch stream URL untuk redirect: {e}")
                return web.json_response(error_payload("HTTP_ERROR", "Stream tidak tersedia saat ini"), status=503)
        from urllib.parse import urlparse as _urlparse
        _p = _urlparse(stream_url)
        _domain = _p.netloc.lower()
        if _p.scheme != "https" or not (
            _domain.endswith(".googlevideo.com") or _domain.endswith(".youtube.com")
        ):
            logger.error(f"URL stream tidak valid untuk redirect: {stream_url}")
            return web.json_response(error_payload("HTTP_ERROR", "URL stream tidak valid"), status=403)
        return web.HTTPFound(stream_url)

    for attempt in range(2):
        if not stream_url:
            try:
                stream_url = await ytdlp.get_stream_url(video_id)
                await db.update_stream_url_only(video_id, stream_url)
            except Exception as e:
                if attempt == 1:
                    return web.json_response(error_payload("HTTP_ERROR", f"Gagal mencari stream: {e}"), status=500)
                continue

        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(stream_url)
            if parsed_url.scheme != "https":
                raise ValueError("Skema URL harus HTTPS")
            domain = parsed_url.netloc.lower()
            if not (domain.endswith(".googlevideo.com") or domain.endswith(".youtube.com")):
                raise ValueError(f"Domain tidak sah: {domain}")
        except Exception as e:
            logger.error(f"SSRF terdeteksi atau URL stream tidak valid: {stream_url} - {e}")
            return web.json_response(error_payload("HTTP_ERROR", "URL stream tidak valid"), status=403)

        try:
            headers = {}
            if "Range" in request.headers:
                headers["Range"] = request.headers["Range"]

            async with http_session.get(stream_url, headers=headers) as upstream:
                if upstream.status in (403, 410) and attempt == 0:
                    logger.warning(f"YouTube stream URL expired ({upstream.status}), refetching...")
                    stream_url = None
                    continue

                response = web.StreamResponse(
                    status=upstream.status,
                    headers={
                        "Content-Type": upstream.headers.get("Content-Type", "audio/mpeg"),
                        "Accept-Ranges": "bytes",
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "private, max-age=3600",
                    }
                )

                if "Content-Range" in upstream.headers:
                    response.headers["Content-Range"] = upstream.headers["Content-Range"]
                if "Content-Length" in upstream.headers:
                    try:
                        response.content_length = int(upstream.headers["Content-Length"])
                    except ValueError:
                        pass

                await response.prepare(request)

                async for chunk in upstream.content.iter_chunked(16384):
                    await response.write(chunk)

                await response.write_eof()
                return response

        except Exception as e:
            logger.warning(f"Proxy stream error untuk {video_id}: {e}")
            if attempt == 0:
                stream_url = None
                continue
            return web.json_response(error_payload("HTTP_ERROR", "Proxy stream error"), status=500)

async def serve_metrics(request):
    import os as _os
    client_ip = request.remote
    _localhost_ips = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}
    metrics_token = _os.environ.get("YTGUI_METRICS_TOKEN")
    is_local = client_ip in _localhost_ips
    import secrets
    has_valid_token = (
        metrics_token
        and request.headers.get("X-Metrics-Token") is not None
        and secrets.compare_digest(request.headers.get("X-Metrics-Token"), metrics_token)
    )
    if not is_local and not has_valid_token:
        return web.HTTPForbidden(text="Akses ditolak: metrics hanya untuk localhost atau gunakan X-Metrics-Token")

    content, content_type = get_metrics_content()
    ct = content_type.split(";")[0].strip()
    return web.Response(body=content, content_type=ct)

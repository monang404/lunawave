"""
Module: server.handlers.audio_stream_handler

Purpose:
    Proxy cached/streamed MP3 audio for a track, including range-request
    support for seeking. Split out of server/handlers/http.py (T3.4) so
    the streaming/range-request logic isn't bundled with the SPA/health/
    metrics endpoints.

Responsibilities:
    - Serve cached MP3 files straight from CACHE_DIR when present.
    - Otherwise resolve a fresh stream URL (DB cache -> ytdlp fallback,
      with retry on expired URLs) and either redirect to it directly
      (no http_session configured) or proxy it through, forwarding the
      Range header so seeking works.
    - Validate stream URLs are HTTPS + googlevideo.com/youtube.com before
      redirecting or proxying, to prevent open-redirect / SSRF.

Depends on:
    - config
    - core.event_bus
    - core.events

Subscribes to:
    None

Publishes:
    LogMessageEvent (on stream-URL-expired retry)

Thread Safety:
    Worker thread (async aiohttp request handlers).
"""

import re
import time

import structlog
from aiohttp import web

from config import CACHE_DIR, STREAM_URL_TTL_SEC
from server.handlers import get_tracks_repo, get_ytdlp

_STREAM_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

logger = structlog.get_logger(__name__)


async def serve_stream(request):
    video_id = request.match_info.get("video_id")
    if not video_id or not _STREAM_ID_RE.match(video_id):
        return web.HTTPBadRequest(text="Invalid video_id")

    cache_file = CACHE_DIR / f"{video_id}.mp3"
    try:
        if not cache_file.resolve().is_relative_to(CACHE_DIR.resolve()):
            return web.HTTPForbidden(text="Akses ditolak")
    except Exception:
        return web.HTTPBadRequest(text="Path tidak valid")

    if cache_file.exists():
        return web.FileResponse(cache_file, headers={"Access-Control-Allow-Origin": "*"})

    db = get_tracks_repo(request)
    ytdlp = get_ytdlp(request)
    stream_url = None

    row = await db.get_track(video_id)
    if row and row.stream_url and row.stream_url_ts:
        if time.time() - row.stream_url_ts < STREAM_URL_TTL_SEC:
            stream_url = row.stream_url

    http_session = request.app.get("http_session")
    if not http_session:
        # Tidak ada proxy session — redirect langsung ke YouTube stream URL.
        # Harus fetch dulu jika belum ada di cache agar tidak redirect ke "".
        if not stream_url:
            try:
                stream_url = await ytdlp.get_stream_url(video_id)
                await db.update_stream_url_only(video_id, stream_url)
            except Exception as e:
                logger.error(f"Gagal fetch stream URL untuk redirect: {e}")
                return web.HTTPServiceUnavailable(text="Stream tidak tersedia saat ini")
        # Validasi domain sebelum redirect (cegah open-redirect / SSRF)
        from urllib.parse import urlparse as _urlparse

        _p = _urlparse(stream_url)
        _domain = _p.netloc.lower()
        if _p.scheme != "https" or not (
            _domain.endswith(".googlevideo.com") or _domain.endswith(".youtube.com")
        ):
            logger.error(f"URL stream tidak valid untuk redirect: {stream_url}")
            return web.HTTPForbidden(text="URL stream tidak valid")
        return web.HTTPFound(stream_url)

    for attempt in range(2):
        if not stream_url:
            try:
                stream_url = await ytdlp.get_stream_url(video_id)
                await db.update_stream_url_only(video_id, stream_url)
            except Exception as e:
                if attempt == 1:
                    return web.HTTPInternalServerError(text=f"Gagal mencari stream: {e}")
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
            return web.HTTPForbidden(text="URL stream tidak valid")

        try:
            headers = {}
            if "Range" in request.headers:
                headers["Range"] = request.headers["Range"]

            async with http_session.get(stream_url, headers=headers) as upstream:
                if upstream.status in (403, 410) and attempt == 0:
                    logger.warning(f"YouTube stream URL expired ({upstream.status}), refetching...")
                    import asyncio

                    from core.event_bus import bus
                    from core.events import LogMessageEvent

                    asyncio.create_task(
                        bus.publish(LogMessageEvent(message="Mencoba ulang koneksi stream..."))
                    )
                    stream_url = None
                    continue

                response = web.StreamResponse(
                    status=upstream.status,
                    headers={
                        "Content-Type": upstream.headers.get("Content-Type", "audio/mpeg"),
                        "Accept-Ranges": "bytes",
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "private, max-age=3600",
                    },
                )

                if "Content-Range" in upstream.headers:
                    response.headers["Content-Range"] = upstream.headers["Content-Range"]
                if "Content-Length" in upstream.headers:
                    try:
                        response.content_length = int(upstream.headers["Content-Length"])
                    except ValueError:
                        pass

                await response.prepare(request)

                try:
                    async for chunk in upstream.content.iter_chunked(16384):
                        await response.write(chunk)
                    await response.write_eof()
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
                    # PATCH-AUDIO-UNLOCK-PROACTIVE-01: client memutus koneksi
                    # di tengah stream (tutup tab, pindah track, seek, dsb).
                    # Sebelumnya ini jatuh ke `except Exception` generik di
                    # bawah bareng dengan error stream-URL beneran, sehingga
                    # attempt==0 memicu refetch yt-dlp yang SIA-SIA -- padahal
                    # tidak ada client lagi yang menunggu respons itu.
                    # Dibuktikan lewat simulasi write() raise
                    # ConnectionResetError: get_stream_url() sebelumnya
                    # terpanggil 2x untuk satu client-disconnect. URL stream
                    # itu sendiri terbukti valid (upstream sempat merespons
                    # 200 dan mulai ngirim data), jadi tidak perlu retry sama
                    # sekali -- cukup log info & selesai.
                    logger.info(f"Client disconnect mid-stream untuk {video_id}: {e}")
                    return response

                return response

        except Exception as e:
            logger.warning(f"Proxy stream error untuk {video_id}: {e}")
            if attempt == 0:
                stream_url = None
                continue
            return web.HTTPInternalServerError(text="Proxy stream error")

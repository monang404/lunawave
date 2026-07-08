import sys
from pathlib import Path

file_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\server\handlers\http.py")
content = file_path.read_text(encoding="utf-8")

if "import asyncio" not in content:
    content = content.replace("import time", "import asyncio\nimport time")

start_marker = "async def serve_stream(request):"
end_marker = "async def serve_metrics(request):"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find markers!")
    sys.exit(1)

new_code = """def _enforce_rate_limit(client_ip):
    now = time.monotonic()
    if len(_stream_rate_limit) > 1000:
        stale_ips = [ip for ip, hist in _stream_rate_limit.items() if not hist or (now - hist[-1] >= 60)]
        for ip in stale_ips:
            _stream_rate_limit.pop(ip, None)
        if len(_stream_rate_limit) > 5000:
            _stream_rate_limit.clear()
    history = _stream_rate_limit[client_ip]
    history = [t for t in history if now - t < 60]
    if len(history) >= STREAM_RATE_LIMIT_MAX:
        return False
    history.append(now)
    _stream_rate_limit[client_ip] = history
    return True

def _validate_origin(request):
    referer = request.headers.get("Referer", "")
    origin = request.headers.get("Origin", "")
    host = request.host
    if host not in referer and host not in origin and request.remote not in ("127.0.0.1", "::1"):
        return False
    return True

def _get_cors_origin(request):
    return request.headers.get("Origin", f"{request.scheme}://{request.host}")

def _try_serve_cache(request, video_id, cors_origin):
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
                "Access-Control-Allow-Origin": cors_origin,
                "Cache-Control": "private, max-age=3600",
                "ETag": etag
            }
        )
    return None

def _validate_stream_url(stream_url):
    from urllib.parse import urlparse
    parsed_url = urlparse(stream_url)
    if parsed_url.scheme != "https":
        raise ValueError("Skema URL harus HTTPS")
    domain = parsed_url.netloc.lower()
    if not (domain.endswith(".googlevideo.com") or domain.endswith(".youtube.com")):
        raise ValueError(f"Domain tidak sah: {domain}")
    return True

async def _proxy_stream(request, video_id, cors_origin, stream_url):
    http_session = request.app.get("http_session")
    db = request.app["db"]
    ytdlp = request.app["ytdlp"]
    
    if not http_session:
        if not stream_url:
            try:
                stream_url = await ytdlp.get_stream_url(video_id)
                await db.update_stream_url_only(video_id, stream_url)
            except Exception as e:
                logger.error(f"Gagal fetch stream URL untuk redirect: {e}")
                return web.json_response(error_payload("HTTP_ERROR", "Stream tidak tersedia saat ini"), status=503)
        try:
            _validate_stream_url(stream_url)
            return web.HTTPFound(stream_url)
        except Exception as e:
            logger.error(f"URL stream tidak valid untuk redirect: {stream_url} - {e}")
            return web.json_response(error_payload("HTTP_ERROR", "URL stream tidak valid"), status=403)

    for attempt in range(2):
        if not stream_url:
            try:
                stream_url = await ytdlp.get_stream_url(video_id)
                await db.update_stream_url_only(video_id, stream_url)
            except asyncio.TimeoutError as e:
                if attempt == 1:
                    return web.json_response(error_payload("HTTP_ERROR", f"Gagal mencari stream (Timeout): {e}"), status=504)
                await asyncio.sleep(1) # Backoff before retry
                continue
            except Exception as e:
                return web.json_response(error_payload("HTTP_ERROR", f"Gagal mencari stream: {e}"), status=500)

        try:
            _validate_stream_url(stream_url)
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
                        "Access-Control-Allow-Origin": cors_origin,
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

async def serve_stream(request):
    video_id_str = request.match_info.get("video_id")
    try:
        video_id = VideoId(video_id_str)
    except ValueError:
        return web.json_response(error_payload("HTTP_ERROR", "Invalid video_id"), status=400)

    if not _enforce_rate_limit(request.remote):
        return web.json_response(error_payload("HTTP_ERROR", "Terlalu banyak request. Silakan coba lagi nanti."), status=429)

    if not _validate_origin(request):
        return web.json_response(error_payload("HTTP_ERROR", "Unauthorized origin"), status=403)

    cors_origin = _get_cors_origin(request)

    cache_resp = _try_serve_cache(request, video_id, cors_origin)
    if cache_resp is not None:
        return cache_resp

    db = request.app["db"]
    stream_url = None
    row = await db.get_track(video_id)
    if row and row.stream_url and row.stream_url_ts:
        if time.time() - row.stream_url_ts < STREAM_URL_TTL_SEC:
            stream_url = row.stream_url

    return await _proxy_stream(request, video_id, cors_origin, stream_url)

"""

new_content = content[:start_idx] + new_code + content[end_idx:]
file_path.write_text(new_content, encoding="utf-8")
print("Refactored http.py successfully.")

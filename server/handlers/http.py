"""
Module: server.handlers.http

Purpose:
    Serve the SPA index, health check, and Prometheus metrics endpoints
    over HTTP.

Responsibilities:
    - Serve index.html with no-cache headers for SPA routing.
    - Report DB/mpv connectivity for health checks.
    - Expose Prometheus metrics, gated to localhost or a shared token.

    Audio stream proxying (range-request support) moved out to
    server/handlers/audio_stream_handler.py (T3.4) — see that module for
    serve_stream.

Depends on:
    - core.observability

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async aiohttp request handlers).
"""

from pathlib import Path

import structlog
from aiohttp import web

from core.observability import get_metrics_content
from server.handlers import get_conn

logger = structlog.get_logger(__name__)
STATIC_DIR = Path(__file__).parent.parent.parent / "web" / "static"


async def serve_index(request):
    resp = web.FileResponse(STATIC_DIR / "index.html")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


async def health_check(request):
    conn = get_conn(request)
    db_status = "connected" if conn else "disconnected"

    pc = request.app.get("playback_controller")
    mpv_ok = getattr(getattr(pc, "mpv", None), "is_connected", False)
    mpv_status = "connected" if mpv_ok else "not_started"

    return web.json_response(
        {
            "status": "ok" if db_status == "connected" else "degraded",
            "db": db_status,
            "mpv": mpv_status,
        }
    )


async def serve_metrics(request):
    import os as _os
    import secrets as _secrets

    client_ip = request.remote
    _localhost_ips = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}
    metrics_token = _os.environ.get(
        "LUNAWAVE_METRICS_TOKEN", _os.environ.get("YTGUI_METRICS_TOKEN")
    )
    is_local = client_ip in _localhost_ips
    request_token = request.headers.get("X-Metrics-Token", "")
    # PATCH-2026-07-16-001: secrets.compare_digest() alih-alih `==` untuk
    # membandingkan token, mencegah timing attack yang bisa membocorkan
    # token metrics byte demi byte.
    has_valid_token = bool(metrics_token) and _secrets.compare_digest(request_token, metrics_token)
    if not is_local and not has_valid_token:
        return web.HTTPForbidden(
            text="Akses ditolak: metrics hanya untuk localhost atau gunakan X-Metrics-Token"
        )

    content, content_type = get_metrics_content()
    ct = content_type.split(";")[0].strip()
    return web.Response(body=content, content_type=ct)

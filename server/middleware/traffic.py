"""
Module: server.middleware.traffic

Purpose:
    Centralized aiohttp middleware for HTTP traffic instrumentation
    (ADR-0010 decision OD-3): assign a short correlation id (req_id) per
    request, count traffic metrics, and log one summary line per request.

Responsibilities:
    - Bind req_id (structlog.contextvars) for the request's scope, so every
      log line emitted while handling this request can be grep-ed together.
    - Increment HTTP_REQUESTS_TOTAL(method, path, status).
    - Increment HTTP_BYTES_TOTAL(direction=in|out), best-effort.
    - Log one concise line per completed request (method, path, status,
      duration) via structlog -- except audio stream requests
      (/api/stream/<video_id>), which are logged at DEBUG instead of INFO.
      A single <audio> playback triggers many chunked/range GETs to that
      endpoint (browser re-requests ranges while seeking/buffering), so at
      INFO they drown out every other log line without adding trace value;
      the request is still counted in HTTP_REQUESTS_TOTAL/HTTP_BYTES_TOTAL
      either way.

Depends on:
    - core.observability

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async aiohttp middleware). No shared mutable state --
    req_id lives in a per-task contextvar, not on the middleware instance.
"""

import secrets
import time

import structlog
from aiohttp import web

from core.observability import HTTP_BYTES_TOTAL, HTTP_REQUESTS_TOTAL

logger = structlog.get_logger(__name__)


def _short_req_id() -> str:
    """8 hex chars -- cukup untuk correlation dalam satu sesi log, tidak
    perlu unik global (bukan UUID lengkap)."""
    return secrets.token_hex(4)


@web.middleware
async def traffic_middleware(request: web.Request, handler):
    """Middleware tunggal untuk semua request HTTP (dipasang di
    server/app.py). Tidak menyentuh routing yang sudah ada -- hanya
    membungkus handler() untuk instrumentasi.
    """
    req_id = _short_req_id()
    start = time.monotonic()
    status = 500
    resp = None

    # Bytes in -- best-effort, Content-Length bisa None/absent (mis. chunked).
    try:
        bytes_in = request.content_length
        if bytes_in:
            HTTP_BYTES_TOTAL.labels(direction="in").inc(bytes_in)
    except Exception:
        pass

    token = None
    try:
        token = structlog.contextvars.bind_contextvars(req_id=req_id)
    except Exception:
        pass

    try:
        resp = await handler(request)
        status = getattr(resp, "status", 200)
        return resp
    except web.HTTPException as exc:
        # HTTPException (mis. 403/404) adalah response yang sah di aiohttp,
        # bukan error tak terduga -- tetap dicatat statusnya lalu di-raise
        # ulang supaya aiohttp tetap mengirimkannya seperti biasa.
        status = exc.status
        raise
    finally:
        dur_ms = (time.monotonic() - start) * 1000

        try:
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method, path=request.path, status=str(status)
            ).inc()
        except Exception:
            pass

        try:
            bytes_out = getattr(resp, "content_length", None) if resp is not None else None
            if bytes_out:
                HTTP_BYTES_TOTAL.labels(direction="out").inc(bytes_out)
        except Exception:
            pass

        try:
            line = f"{request.method} {request.path} status={status} dur={dur_ms:.0f}ms"
            if request.path.startswith("/api/stream/"):
                # Range/chunk requests for audio playback are frequent and
                # expected -- keep them out of the INFO log to avoid
                # flooding it, but still emit at DEBUG for local trace.
                logger.debug(line)
            else:
                logger.info(line)
        except Exception:
            pass

        try:
            if token is not None:
                structlog.contextvars.reset_contextvars(**token)
            else:
                structlog.contextvars.unbind_contextvars("req_id")
        except Exception:
            pass

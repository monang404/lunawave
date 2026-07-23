"""
Module: server.connection_manager

Purpose:
    Manages active WebSocket connections and broadcasts events to connected clients.

Responsibilities:
    - Implement the core functionality described in the purpose.
    - Track connected_at per WS and record active-session duration on
      disconnect (ADR-0010): logged + observed to a Prometheus histogram.

Depends on:
    - core.observability

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio
import json
import secrets
import time

import structlog

from core.log_categories import LC_SESSION
from core.log_context import bind_session, unbind_session
from core.observability import ACTIVE_USER_SESSION_SECONDS, ACTIVE_WEBSOCKETS
from server.handlers.ws_log_stream import cleanup_log_viewer

logger = structlog.get_logger(component="ws.connection")


class ConnectionManager:
    def __init__(self):
        self.active_connections = []
        self.authenticated_connections = set()
        self.session_tokens = {}
        self.login_attempts = {}
        self.command_history = {}
        self.setup_attempts = {}
        self.rl_lock = asyncio.Lock()
        # ADR-0010: connected_at per ws, dipakai untuk durasi sesi aktif.
        # Dict biasa (bukan WeakKeyDictionary) supaya konsisten dengan
        # struktur active_connections/authenticated_connections yang sudah
        # ada -- entry dibersihkan sendiri di disconnect().
        self.connected_at: dict = {}
        self.client_ips: dict = {}

    async def connect(self, ws, request=None):
        self.active_connections.append(ws)
        self.connected_at[ws] = time.monotonic()
        req = request or getattr(ws, "_req", None)
        user_agent = req.headers.get("User-Agent", "") if req else ""
        referer = req.headers.get("Referer", "") if req else ""
        if not referer and req:
            page = req.query.get("page", "")
            if page:
                referer = page
        self.client_ips[ws] = {
            "ip": getattr(req, "remote", "Unknown") if req else "Unknown",
            "user_agent": user_agent,
            "referer": referer,
        }
        ACTIVE_WEBSOCKETS.inc()
        # L5.1: session_id sekali per koneksi, sama pola dengan req_id di
        # server/middleware/traffic.py -- aktif sepanjang hidup task
        # ws_handler() (connect()..disconnect() berjalan di task yang sama,
        # lihat server/handlers/websocket.py), sehingga tumpuk di atas
        # request_id per command tanpa saling menimpa (§5.2).
        session_id = secrets.token_hex(4)
        bind_session(session_id)
        logger.info(
            "ws_connected",
            category=LC_SESSION,
            client_count=len(self.active_connections),
        )

    def disconnect(self, ws):
        cleanup_log_viewer(ws)
        if ws in self.active_connections:
            self.active_connections.remove(ws)
            ACTIVE_WEBSOCKETS.dec()
        if ws in self.authenticated_connections:
            self.authenticated_connections.remove(ws)
        self.client_ips.pop(ws, None)

        duration = None
        connected_at = self.connected_at.pop(ws, None)
        if connected_at is not None:
            try:
                duration = time.monotonic() - connected_at
                ACTIVE_USER_SESSION_SECONDS.observe(duration)
            except Exception:
                # Instrumentasi tidak boleh pernah menggagalkan disconnect().
                duration = None

        logger.info(
            "ws_disconnected",
            category=LC_SESSION,
            client_count=len(self.active_connections),
            duration_s=duration,
        )

        # L5.1: lepas session_id sekarang -- hidupnya berakhir bersama
        # koneksi ini (lihat core/log_context.py: unbind_session() dipanggil
        # dari ConnectionManager.disconnect()).
        unbind_session()

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        data = json.dumps(message, ensure_ascii=False)
        # Pin ONE snapshot and reuse it for both send_str() and the
        # zip() pairing below. Re-reading self.active_connections after
        # the `await asyncio.gather(...)` (as the old code did) is unsafe:
        # a concurrent connect()/disconnect() during that await can change
        # the list's contents/order, so pairing `results` against a
        # freshly re-fetched list misattributes send results to the wrong
        # ws — confirmed via reproduction to wrongly disconnect a healthy
        # client that connected mid-broadcast (PATCH-2026-07-16-065).
        snapshot = list(self.active_connections)
        results = await asyncio.gather(
            *[ws.send_str(data) for ws in snapshot],
            return_exceptions=True,
        )
        dead = [
            ws
            for ws, result in zip(snapshot, results, strict=False)
            if isinstance(result, Exception)
        ]
        for ws in dead:
            self.disconnect(ws)

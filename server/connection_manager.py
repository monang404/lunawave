"""
Module: server.connection_manager

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
import json

import structlog

from core.observability import ACTIVE_WEBSOCKETS

logger = structlog.get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections = []
        self.authenticated_connections = set()
        self.session_tokens = {}
        self.login_attempts = {}
        self.command_history = {}
        self.rl_lock = asyncio.Lock()

    async def connect(self, ws):
        self.active_connections.append(ws)
        ACTIVE_WEBSOCKETS.inc()
        logger.info(f"WebSocket connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, ws):
        if ws in self.active_connections:
            self.active_connections.remove(ws)
            ACTIVE_WEBSOCKETS.dec()
        if ws in self.authenticated_connections:
            self.authenticated_connections.remove(ws)
        logger.info(f"WebSocket disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        data = json.dumps(message, ensure_ascii=False)
        results = await asyncio.gather(
            *[ws.send_str(data) for ws in list(self.active_connections)],
            return_exceptions=True,
        )
        dead = [
            ws
            for ws, result in zip(list(self.active_connections), results, strict=False)
            if isinstance(result, Exception)
        ]
        for ws in dead:
            self.disconnect(ws)

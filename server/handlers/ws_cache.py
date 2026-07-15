"""
Module: server.handlers.ws_cache

Purpose:
    WebSocket handler for managing cache queries and clearing.

Responsibilities:
    - Get cache size
    - Clear cache

Depends on:
    - config

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread.
"""

import json
import os

import structlog

from config import CACHE_DIR

logger = structlog.get_logger(__name__)


async def handle_cache_command(action: str, data: dict, ws, db, manager, state):
    if action == "get_cache_size":
        size = 0
        if CACHE_DIR.exists():
            for root, dirs, files in os.walk(str(CACHE_DIR)):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        size += os.path.getsize(fp)
                    except OSError:
                        pass
        await ws.send_str(json.dumps({"type": "cache_size", "data": {"size_bytes": size}}))
    elif action == "clear_cache":
        if CACHE_DIR.exists():
            for root, dirs, files in os.walk(str(CACHE_DIR)):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        os.remove(fp)
                    except OSError:
                        pass
        await manager.broadcast({"type": "log", "data": "Cache berhasil dibersihkan"})
        await ws.send_str(json.dumps({"type": "cache_cleared", "data": {}}))

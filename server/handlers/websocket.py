import asyncio
import json
import time

import aiohttp
import structlog
from aiohttp import web

from config import TRUSTED_PROXY
from core.observability import ACTIVE_WEBSOCKETS
from core.ws_actions import WSAction
from server.handlers.auth import handle_auth, handle_logout, require_auth

# Import the WS handlers registry
from server.handlers.ws import _ws_handlers
from server.handlers.ws.utils import error_payload
from server.middleware import check_rate_limit

logger = structlog.get_logger(__name__)
from core.cli_ui import STATS as _LOG_STATS


class ConnectionManager:
    def __init__(self):
        self.active_connections = set()
        self.authenticated_connections = set()
        self.session_tokens = {}
        self.login_attempts = {}
        self.command_history = {}
        self.rl_lock = asyncio.Lock()

    async def connect(self, ws):
        if len(self.active_connections) >= 1000:
            logger.warning("Max WebSocket connections reached, rejecting.")
            return False
        self.active_connections.add(ws)
        ACTIVE_WEBSOCKETS.inc()
        _LOG_STATS.clients = len(self.active_connections)
        _LOG_STATS.is_playing = True if _LOG_STATS.current_track != "—" else _LOG_STATS.is_playing
        logger.info(f"WebSocket connected. Total clients: {len(self.active_connections)}", clients=len(self.active_connections))
        return True

    def disconnect(self, ws):
        if ws in self.active_connections:
            self.active_connections.discard(ws)
            ACTIVE_WEBSOCKETS.dec()
        if ws in self.authenticated_connections:
            self.authenticated_connections.remove(ws)
        _LOG_STATS.clients = len(self.active_connections)
        logger.info(f"WebSocket disconnected. Total clients: {len(self.active_connections)}", clients=len(self.active_connections))

    async def broadcast(self, message: dict):
        if not self.authenticated_connections:
            return
        data = json.dumps(message, ensure_ascii=False)
        import asyncio
        async def send(ws):
            try:
                await ws.send_str(data)
                return None
            except Exception:
                return ws

        targets = list(self.authenticated_connections)
        results = await asyncio.gather(*(send(ws) for ws in targets))

        for dead_ws in results:
            if dead_ws is not None:
                self.disconnect(dead_ws)

async def ws_handler(request):
    playback_controller = request.app["playback_controller"]
    state = request.app["state"]
    manager = request.app["manager"]
    db = request.app["db"]
    ytdlp = request.app["ytdlp"]
    command_bus = request.app["command_bus"]

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    if not await manager.connect(ws):
        await ws.close(code=1013, message=b"Server Too Busy")
        return ws

    try:
        await ws.send_str(json.dumps({
            "type": "state",
            "data": state.to_dict(),
        }, ensure_ascii=False))
    except Exception:
        manager.disconnect(ws)
        return ws

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue
                client_ip = request.remote
                if TRUSTED_PROXY and "X-Forwarded-For" in request.headers:
                    client_ip = request.headers.get("X-Forwarded-For").split(",")[-1].strip()
                await handle_ws_message(data, ws, client_ip, state, ytdlp, manager, db, command_bus)
            elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                break
    except asyncio.CancelledError:
        logger.debug("WebSocket connection cancelled")
    except ConnectionError as e:
        logger.info(f"WebSocket client disconnected: {e}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(ws)

    return ws

async def handle_ws_message(msg: dict, ws, client_ip: str, state, ytdlp, manager, db, command_bus):
    msg_type = msg.get("type")
    action = msg.get("action", "")
    data = msg.get("data", {})
    if not isinstance(data, dict):
        logger.warning(f"Invalid payload format for 'data': expected dict, got {type(data).__name__}")
        data = {}

    if msg_type != "cmd":
        return

    now = time.time()
    if action == WSAction.AUTH:
        await handle_auth(ws, data, manager, client_ip, db, now)
        return

    if action == WSAction.LOGOUT:
        await handle_logout(ws, data, manager, db)
        return

    # Check if action requires auth (admin only)
    # All mutating / sensitive actions must be listed here.
    # Read-only / public actions (SEARCH, DISCOVER) are intentionally excluded.
    ADMIN_ONLY_ACTIONS = {
        # Playback
        WSAction.PLAY_TRACK, WSAction.TOGGLE_PAUSE, WSAction.NEXT,
        WSAction.PREV, WSAction.STOP, WSAction.SEEK,
        # Queue
        WSAction.QUEUE_ADD, WSAction.QUEUE_REMOVE, WSAction.QUEUE_REORDER,
        WSAction.QUEUE_SELECT,
        # Enqueue helpers
        WSAction.ENQUEUE_ARTIST_SONGS, WSAction.ENQUEUE_GENRE_SONGS,
        # Radio
        WSAction.RADIO_RANDOMIZE,
        # Volume / Mode
        WSAction.VOLUME_SET, WSAction.VOLUME_UP, WSAction.VOLUME_DOWN,
        WSAction.SET_MODE,
        # Output / Sponsorblock / Settings
        WSAction.SET_OUTPUT, WSAction.SET_SPONSORBLOCK,
        # Download
        WSAction.DOWNLOAD, WSAction.DELETE_DOWNLOAD,
        # Misc
        WSAction.TOGGLE_FAVORITE, WSAction.LYRICS_OFFSET,
    }
    if action in ADMIN_ONLY_ACTIONS:
        if not require_auth(manager, ws):
            await ws.send_str(json.dumps({
                "type": "error",
                "data": error_payload("AUTH_REQUIRED", "Akses ditolak. Silakan login sebagai Admin.")["error"],
            }))
            return

    if not await check_rate_limit(manager, client_ip, now):
        await ws.send_str(json.dumps({
            "type": "error",
            "data": error_payload("RATE_LIMITED", "Terlalu banyak permintaan. Mohon tunggu sesaat.")["error"]
        }))
        return

    try:
        if action in _ws_handlers:
            await _ws_handlers[action](data, ws, state, ytdlp, manager, db, command_bus)
        else:
            logger.warning(f"Unknown WS action: {action}")
    except Exception as e:
        logger.error(f"Error handling WS command '{action}': {e}", exc_info=True)
        try:
            await ws.send_str(json.dumps({
                "type": "error",
                "data": error_payload("INTERNAL", "Terjadi kesalahan internal saat memproses perintah.")["error"],
            }))
        except Exception:
            pass

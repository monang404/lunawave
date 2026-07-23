"""
Module: server.handlers.websocket

Purpose:
    Handle WebSocket connections, authenticate clients, and dispatch
    incoming commands to the CommandBus after rate-limit enforcement.

Responsibilities:
    - Reject WebSocket handshakes from cross-origin browser clients (CSWSH).
    - Manage ConnectionManager (connect/disconnect/broadcast to all clients).
    - Route authenticated WS actions to command_bus.execute().

Depends on:
    - server.handlers.auth
    - server.handlers.setup
    - server.handlers.ws_discovery
    - server.handlers.ws_download
    - server.handlers.ws_playback
    - server.handlers.ws_queue
    - server.middleware
    - server.serializers

Subscribes to:
    None

Publishes:
    CMD_* commands via command_bus.execute

Thread Safety:
    Worker thread (async; rl_lock guards rate-limit state).
"""

import json
import time
from urllib.parse import urlparse

import aiohttp
import structlog
from aiohttp import web

from core.log_categories import LC_COMMAND, LC_SECURITY, LC_SESSION
from server.handlers import get_manager, get_playback_controller, get_repos, get_state, get_ytdlp
from server.handlers.auth import handle_auth, require_auth
from server.handlers.setup import handle_setup_admin
from server.handlers.ws_discovery import handle_discovery_command
from server.handlers.ws_download import handle_download_command
from server.handlers.ws_playback import handle_playback_command
from server.handlers.ws_queue import handle_queue_command
from server.middleware import check_rate_limit
from server.serializers import state_to_dict

PLAYBACK_CMDS = {
    "play_track",
    "toggle_pause",
    "next",
    "prev",
    "stop",
    "seek",
    "set_mode",
    "set_output",
    "lyrics_offset",
    "set_sponsorblock",
    "radio_randomize",
    "volume_up",
    "volume_down",
    "volume_set",
    "set_sleep_timer",
    "set_speed",
    "set_loop",
    "set_crossfade",
    "set_loudness_normalization",
}
QUEUE_CMDS = {
    "queue_select",
    "queue_remove",
    "queue_add",
    "queue_reorder",
    "enqueue_artist_songs",
    "enqueue_genre_songs",
}
DISCOVERY_CMDS = {"search", "discover", "get_artist_detail", "discover_search"}
DOWNLOAD_CMDS = {"download", "delete_download"}
CACHE_CMDS = {"get_cache_size", "clear_cache"}


logger = structlog.get_logger(component="ws.handler")


def check_ws_origin(request) -> bool:
    """Validate the Origin header to prevent Cross-Site WebSocket Hijacking (CSWSH).

    Rules:
    - No Origin header  → allow (non-browser client: curl, Termux, Python script).
    - Origin present    → parse its host, compare with request.host (case-insensitive).
    - Mismatch          → deny (cross-origin browser page trying to hijack the socket).

    When behind a reverse proxy / tunnel (ngrok, Cloudflare), the Host header
    reflects the tunnel domain — Origin must match that same domain.
    """
    origin = request.headers.get("Origin", "")
    if not origin:
        # Non-browser clients don't send Origin; allow them.
        return True
    try:
        origin_host = urlparse(origin).netloc  # includes port if present
    except Exception:
        return False
    # request.host already contains the correct host:port from the Host header.
    return origin_host.lower() == request.host.lower()


async def ws_handler(request):
    # Reject cross-origin WebSocket handshakes (CSWSH protection).
    # Non-browser clients (no Origin header) are still allowed.
    if not check_ws_origin(request):
        logger.warning(
            "ws_handshake_rejected_origin_mismatch",
            category=LC_SECURITY,
            origin=request.headers.get("Origin", ""),
            host=request.host,
        )
        return web.Response(status=403, text="Forbidden: cross-origin WebSocket not allowed")

    get_playback_controller(request)
    state = get_state(request)
    manager = get_manager(request)
    repos = get_repos(request)
    ytdlp = get_ytdlp(request)

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    await manager.connect(ws)

    try:
        # include_lyrics=True: initial snapshot butuh lirik penuh karena
        # client yang baru connect (mis. refresh halaman mid-lagu) tidak
        # akan dapat lirik lagi sampai lyrics_index berubah berikutnya.
        await ws.send_str(
            json.dumps(
                {
                    "type": "state",
                    "data": state_to_dict(state, include_lyrics=True),
                },
                ensure_ascii=False,
            )
        )
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
                await handle_ws_message(data, ws, request.remote, state, ytdlp, manager, repos)
            elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                break
    except Exception as e:
        logger.error(
            "ws_connection_error", category=LC_SESSION, error_type=type(e).__name__, error=str(e)
        )
    finally:
        manager.disconnect(ws)

    return ws


async def handle_ws_message(msg: dict, ws, client_ip: str, state, ytdlp, manager, repos):
    msg_type = msg.get("type")
    action = msg.get("action", "")
    data = msg.get("data", {})

    if msg_type != "cmd":
        return

    now = time.time()
    if action == "auth":
        await handle_auth(ws, data, manager, client_ip, repos, now)
        return

    if action == "logout":
        token = data.get("token")
        if token and repos and repos.sessions:
            await repos.sessions.delete_session(token)
        manager.authenticated_connections.discard(ws)
        return

    if action == "setup_admin":
        # Sama seperti "auth": harus reachable SEBELUM require_auth, karena
        # saat Initial Setup belum ada admin_account sama sekali -- tidak
        # ada cara untuk "sudah login" pada titik ini.
        await handle_setup_admin(ws, data, manager, client_ip, repos, now)
        return

    if not require_auth(manager, ws):
        await ws.send_str(
            json.dumps(
                {
                    "type": "error",
                    "data": "Akses ditolak. Silakan login sebagai Admin.",
                }
            )
        )
        return

    if not await check_rate_limit(manager, client_ip, now):
        await ws.send_str(
            json.dumps({"type": "error", "data": "Terlalu banyak permintaan. Mohon tunggu sesaat."})
        )
        return

    try:
        if action in PLAYBACK_CMDS:
            await handle_playback_command(action, data)
        elif action in QUEUE_CMDS:
            await handle_queue_command(action, data, repos.artists, repos.genres)
        elif action in DISCOVERY_CMDS:
            await handle_discovery_command(action, data, ytdlp, repos.discover, ws)
        elif action in DOWNLOAD_CMDS:
            await handle_download_command(
                action, data, repos.tracks, repos.discover, manager, state
            )
        elif action in CACHE_CMDS:
            from server.handlers.ws_cache import handle_cache_command

            await handle_cache_command(action, data, ws, repos, manager, state)
    except Exception as e:
        logger.error(
            "ws_command_handling_failed",
            category=LC_COMMAND,
            command_action=action,
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True,
        )
        try:
            await ws.send_str(
                json.dumps(
                    {
                        "type": "error",
                        "data": str(e),
                    }
                )
            )
        except Exception as send_err:
            logger.debug(
                "ws_error_reply_send_failed",
                category=LC_COMMAND,
                error_type=type(send_err).__name__,
                error=str(send_err),
            )

"""
Module: server.handlers.websocket

Purpose:
    Handle WebSocket connections, authenticate clients, and dispatch
    incoming commands to the CommandBus after rate-limit enforcement.

Responsibilities:
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

import aiohttp
import structlog
from aiohttp import web

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


logger = structlog.get_logger(__name__)


async def ws_handler(request):
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
        logger.error(f"WebSocket error: {e}")
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
        logger.error(f"Error handling WS command '{action}': {e}", exc_info=True)
        try:
            await ws.send_str(
                json.dumps(
                    {
                        "type": "error",
                        "data": str(e),
                    }
                )
            )
        except Exception:
            pass

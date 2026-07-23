"""
Module: server.app

Purpose:
    Create and configure the aiohttp web application with all routes,
    services, and EventBus listeners wired together.

Responsibilities:
    - Register HTTP and WebSocket routes and the static file directory.
    - Initialize BroadcastService, StreamPrefetchService, and event listeners.

Depends on:
    - core.ports
    - engine.playback.controller
    - persistence
    - server.connection_manager
    - server.handlers.event_listeners
    - server.handlers.http
    - server.handlers.setup
    - server.handlers.websocket
    - server.broadcast_service
    - services.stream_prefetch

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread only (startup); handlers run in the async event loop.
"""

import asyncio
from pathlib import Path

import structlog
from aiohttp import web

from core.log_categories import LC_LIFECYCLE
from core.ports import MediaExtractorPort
from core.server_clock import ServerClock, server_clock
from engine.playback.controller import PlaybackController
from persistence import Repositories

logger = structlog.get_logger(component="server.app")
STATIC_DIR = Path(__file__).parent.parent / "web" / "static"

# --- Application-scoped keys (web.AppKey eliminates NotAppKeyWarning) ---
# Each key is a typed constant importable by handler accessors.
PLAYBACK_CONTROLLER: web.AppKey[PlaybackController] = web.AppKey(
    "playback_controller", PlaybackController
)
STATE: web.AppKey = web.AppKey("state")
YTDLP: web.AppKey[MediaExtractorPort] = web.AppKey("ytdlp", MediaExtractorPort)
REPOS: web.AppKey[Repositories] = web.AppKey("repos", Repositories)
CONN: web.AppKey = web.AppKey("conn")
TRACKS: web.AppKey = web.AppKey("tracks")
MANAGER: web.AppKey = web.AppKey("manager")
# ADR-0010: uptime server, dipakai /health + task periodik [STATUS] (sesi 4).
SERVER_CLOCK: web.AppKey[ServerClock] = web.AppKey("server_clock", ServerClock)


def create_app(
    playback_controller: PlaybackController, ytdlp: MediaExtractorPort, repos: Repositories
) -> web.Application:
    from server.connection_manager import ConnectionManager
    from server.handlers.audio_stream_handler import serve_stream
    from server.handlers.http import health_check, serve_client, serve_index, serve_metrics
    from server.handlers.setup import setup_required
    from server.handlers.websocket import ws_handler
    from server.middleware.traffic import traffic_middleware

    app = web.Application(middlewares=[traffic_middleware])
    manager = ConnectionManager()

    app[PLAYBACK_CONTROLLER] = playback_controller
    app[STATE] = playback_controller.state
    app[YTDLP] = ytdlp
    app[REPOS] = repos
    app[CONN] = repos.conn
    app[TRACKS] = repos.tracks
    app[MANAGER] = manager
    # ADR-0010: reuse the module-level singleton so main.py's server_clock.init()
    # call (startup) and this AppKey both point at the same instance.
    app[SERVER_CLOCK] = server_clock
    # Bug #9 fix: ClientSession sudah dibuat di main.py dan di-pass ke plugins.
    # Tidak perlu buat session baru di sini agar tidak ada resource leak.

    from server.broadcast_service import BroadcastService
    from server.handlers.event_listeners import setup_event_listeners
    from services.stream_prefetch import StreamPrefetchService

    assert repos.tracks is not None, "repos.init() must be called before create_app()"
    prefetch_service = StreamPrefetchService(repos.tracks, ytdlp)
    broadcast_service = BroadcastService(manager)
    setup_event_listeners(playback_controller, prefetch_service, broadcast_service)

    app.router.add_get("/", serve_client)
    app.router.add_get("/admin", serve_index)
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/api/stream/{video_id}", serve_stream)
    app.router.add_get("/api/setup-required", setup_required)
    app.router.add_get("/health", health_check)
    app.router.add_get("/metrics", serve_metrics)
    app.router.add_static("/static", STATIC_DIR, name="static")

    return app


async def run_server(app: web.Application, host: str = "0.0.0.0", port: int = 8765):
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    try:
        await site.start()
    except Exception as e:
        logger.critical(
            "server_bind_failed",
            category=LC_LIFECYCLE,
            host=host,
            port=port,
            error_type=type(e).__name__,
            error=str(e),
        )
        raise
    logger.info(
        "web_server_started",
        category=LC_LIFECYCLE,
        host=host,
        port=port,
    )

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()

# PATCHLOG_APPLIED
import asyncio
from pathlib import Path

import structlog
from aiohttp import web

from core.ports import DatabasePort, MediaExtractorPort
from engine.playback.controller import PlaybackController
from server.handlers.http import health_check, serve_index, serve_metrics, serve_stream
from server.handlers.websocket import ConnectionManager, ws_handler

logger = structlog.get_logger(__name__)
STATIC_DIR = Path(__file__).parent.parent / "web" / "static"

def create_app(playback_controller: PlaybackController, ytdlp: MediaExtractorPort, db: DatabasePort, manager: ConnectionManager, command_bus=None, event_bus=None) -> web.Application:
    app = web.Application()

    app["playback_controller"] = playback_controller
    app["state"] = playback_controller.state
    app["ytdlp"] = ytdlp
    app["db"] = db
    app["manager"] = manager
    if command_bus:
        app["command_bus"] = command_bus
    if event_bus:
        app["event_bus"] = event_bus

    app.router.add_get("/", serve_index)
    app.router.add_get("/admin", serve_index)
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/api/stream/{video_id}", serve_stream)
    app.router.add_get("/health", health_check)
    app.router.add_get("/metrics", serve_metrics)
    app.router.add_static("/static", STATIC_DIR, name="static", append_version=True)

    return app

async def run_server(app: web.Application, host: str = "0.0.0.0", port: int = 8765):
    import logging as _l
    _l.getLogger('aiohttp.access').setLevel(_l.CRITICAL + 1)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    import sys as _sys; _sys.stderr.write(f"\033[32mserver  ✓ listening\033[0m  http://{host}:{port}\n")

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()

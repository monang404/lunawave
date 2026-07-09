
import asyncio
import sys
from pathlib import Path

import structlog
from aiohttp import web

from core.ports import DatabasePort, MediaExtractorPort
from engine.playback.controller import PlaybackController
from server.handlers.http import health_check, serve_index, serve_metrics, serve_stream
from server.handlers.websocket import ConnectionManager, ws_handler

logger = structlog.get_logger(__name__)

def create_app(playback_controller: PlaybackController, ytdlp: MediaExtractorPort, db: DatabasePort, manager: ConnectionManager, command_bus=None, event_bus=None, http_session=None) -> web.Application:
    try:
        from scripts.build_js import build
        build()
    except Exception as e:
        logger.warning(f"Failed to bundle JS: {e}")

    from server.middleware import security_headers_middleware
    app = web.Application(middlewares=[security_headers_middleware])

    app["playback_controller"] = playback_controller
    app["state"] = playback_controller.state
    app["ytdlp"] = ytdlp
    app["db"] = db
    app["manager"] = manager
    app["http_session"] = http_session
    app["command_bus"] = command_bus
    app["event_bus"] = event_bus

    from server.routes import ROUTE_HEALTH, ROUTE_INDEX, ROUTE_METRICS, ROUTE_STATIC, ROUTE_STREAM, ROUTE_WS, STATIC_DIR
    app.router.add_get(ROUTE_INDEX, serve_index)
    app.router.add_get(ROUTE_WS, ws_handler)
    app.router.add_get(ROUTE_STREAM, serve_stream)
    app.router.add_get(ROUTE_HEALTH, health_check)
    app.router.add_get(ROUTE_METRICS, serve_metrics)
    app.router.add_static(ROUTE_STATIC, STATIC_DIR, name="static", append_version=True)

    return app

async def run_server(app: web.Application, host: str = "0.0.0.0", port: int = 8765):
    import logging as _l
    import concurrent.futures
    import os
    
    loop = asyncio.get_running_loop()
    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=min(32, (os.cpu_count() or 1) + 4),
        thread_name_prefix='aiohttp_worker'
    )
    loop.set_default_executor(executor)
    
    _l.getLogger('aiohttp.access').setLevel(_l.CRITICAL + 1)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    sys.stderr.write(f"\033[32mserver  ✓ listening\033[0m  http://{host}:{port}\n")

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()

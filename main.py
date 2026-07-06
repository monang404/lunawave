# PATCHLOG_APPLIED
__version__ = "1.0.0"

import asyncio
import stat
import sys

import structlog

from config import BASE_DIR
from core.log_config import setup_logging

setup_logging()

try:
    log_path = BASE_DIR / "ytplayer.log"
    log_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
except OSError:
    pass

async def main():
    from core.bootstrap import build_app_context, shutdown_app_context
    from core.background_tasks import start_background_tasks
    from server.app import run_server

    ctx = await build_app_context()
    tasks = start_background_tasks(ctx)
    try:
        await run_server(ctx.app, host=ctx.host, port=ctx.port)
    except asyncio.CancelledError:
        pass
    finally:
        await shutdown_app_context(ctx, tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

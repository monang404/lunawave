import asyncio
import structlog
import aiohttp
from pathlib import Path

from core.task_utils import safe_create_task
from core.bootstrap import AppContext

async def _connectivity_checker(state, http_session):
    while True:
        try:
            async with http_session.get(
                "https://connectivitycheck.gstatic.com/generate_204",
                timeout=aiohttp.ClientTimeout(total=3)
            ) as r:
                state.is_online = (r.status == 204)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            state.is_online = False
        except Exception as e:
            structlog.get_logger(__name__).warning(f"Connectivity check unexpected error: {e}")
            state.is_online = False

        await asyncio.sleep(60)

async def _db_cleanup(db):
    while True:
        await asyncio.sleep(86400)
        try:
            from config import DB_PATH
            try:
                if DB_PATH.exists():
                    await db.backup(Path(str(DB_PATH) + ".bak"))
                    structlog.get_logger(__name__).info("Database backed up successfully.")
            except Exception as e:
                structlog.get_logger(__name__).error(f"DB backup failed: {e}")

            await db.evict_stale_tracks()
            await db.cleanup_sessions()
        except Exception as e:
            structlog.get_logger(__name__).error(f"DB cleanup failed: {e}")

def start_background_tasks(ctx: AppContext) -> list:
    connectivity_task = safe_create_task(
        _connectivity_checker(ctx.state, ctx.http_session), 
        name="connectivity_checker"
    )
    db_cleanup_task = safe_create_task(
        _db_cleanup(ctx.db), 
        name="db_cleanup"
    )
    return [connectivity_task, db_cleanup_task]

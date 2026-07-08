import asyncio
from pathlib import Path

import aiohttp
import structlog

from core.bootstrap import AppContext
from core.task_utils import safe_create_task


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
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = Path(str(DB_PATH) + f".{timestamp}.bak")
                    await db.backup(backup_path)
                    structlog.get_logger(__name__).info(f"Database backed up to {backup_path.name}")
                    
                    # S05-076: Rotasi 7 hari
                    backup_dir = DB_PATH.parent
                    backups = sorted(backup_dir.glob("lunawave.db.*.bak"))
                    if len(backups) > 7:
                        for old_backup in backups[:-7]:
                            old_backup.unlink(missing_ok=True)
                            structlog.get_logger(__name__).info(f"Deleted old backup: {old_backup.name}")
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

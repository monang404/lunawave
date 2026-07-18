"""
Module: bootstrap.maintenance

Purpose:
    Stage 3 of application startup: schedule the periodic DB maintenance
    loop and the MPV connection watchdog as background tasks. Extracted
    from main.py's `main()` (T2.4) without changing call order.

Inputs:
    Populated `bootstrap.services.context` (must run after
    `init_core_services()`).

Outputs:
    Appends `db_maintenance` and `mpv_watchdog` tasks to `context.tasks`.

Side Effects:
    Deletes stale tracks / expired sessions from the DB on a timer, flips
    player state to ERROR if MPV stays disconnected.

CLI:
    None (imported by main.py).

Responsibilities:
    - Run periodic upkeep as background asyncio tasks.

Depends on:
    - bootstrap.services
    - core.task_utils
    - core.state

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio

import structlog

from bootstrap.services import context
from core.state import PlayerStatus
from core.task_utils import safe_create_task


# DB Maintenance: eviction track stale + cleanup session expired.
async def db_maintenance():
    ctx = context
    # Jalankan sekali di awal, baru masuk loop periodik
    try:
        deleted = await ctx.repos.tracks.evict_stale_tracks()
        if deleted:
            structlog.get_logger(__name__).info(
                f"DB maintenance (awal): {deleted} track stale dihapus"
            )
    except Exception as e:
        structlog.get_logger(__name__).warning(
            f"DB maintenance awal (evict_stale_tracks) gagal: {e}"
        )
    try:
        await ctx.repos.sessions.cleanup_sessions()
    except Exception as e:
        structlog.get_logger(__name__).warning(
            f"DB maintenance awal (cleanup_sessions) gagal: {e}"
        )

    while True:
        await asyncio.sleep(6 * 3600)  # tiap 6 jam
        try:
            deleted = await ctx.repos.tracks.evict_stale_tracks()
            if deleted:
                structlog.get_logger(__name__).info(
                    f"DB maintenance: {deleted} track stale dihapus"
                )
        except Exception as e:
            structlog.get_logger(__name__).warning(
                f"DB maintenance (evict_stale_tracks) gagal: {e}"
            )
        try:
            await ctx.repos.sessions.cleanup_sessions()
        except Exception as e:
            structlog.get_logger(__name__).warning(
                f"DB maintenance (cleanup_sessions) gagal: {e}"
            )


def schedule_db_maintenance():
    """Schedule the DB maintenance loop as a background task."""
    context.tasks.append(safe_create_task(db_maintenance(), name="db_maintenance"))


# MPV watchdog: no longer polls/reconnects itself. MpvObserver now owns
# reconnect (immediate, bounded retries) so there is a single reconnect
# path instead of two racing ones. This watchdog only handles the case
# where mpv never comes back at all (observer gave up after its own
# retries): it surfaces that as a visible error state instead of silently
# leaving playback stuck, without spawning yet another mpv process or
# reloading/seeking the track itself.
async def mpv_watchdog():
    ctx = context
    while True:
        await asyncio.sleep(10)
        if (
            getattr(ctx.mpv, "is_available", True)
            and not getattr(ctx.mpv, "is_connected", False)
            and ctx.state.status not in (PlayerStatus.ERROR, PlayerStatus.IDLE)
        ):
            structlog.get_logger(__name__).error(
                "MPV masih terputus setelah reconnect otomatis gagal."
            )
            ctx.state.status = PlayerStatus.ERROR
            ctx.state.error_msg = "Koneksi ke MPV terputus dan gagal reconnect."


def start_mpv_watchdog():
    """Schedule the MPV connection watchdog as a background task."""
    context.tasks.append(safe_create_task(mpv_watchdog(), name="mpv_watchdog"))

"""
Module: main

Purpose:
    Bootstrap all LunaWave subsystems and start the async aiohttp web server.

Inputs:
    Environment variables: LUNAWAVE_HOST, LUNAWAVE_PORT, LUNAWAVE_ADMIN_USER,
    LUNAWAVE_ADMIN_PASS (or LUNAWAVE_BASE for path overrides).

Outputs:
    Running web server on configured host/port with WebSocket and REST API.

Side Effects:
    Opens SQLite DB, spawns mpv process, binds TCP port, writes log file.

CLI:
    python main.py

Responsibilities:
    - Orchestrate the bootstrap stages (see bootstrap/) and run the server.

Depends on:
    - bootstrap.services
    - bootstrap.startup_tasks
    - bootstrap.maintenance
    - core.log_config
    - server.app

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio
import stat

import structlog

from config import BASE_DIR, WEB_HOST, WEB_PORT
from core.log_categories import LC_LIFECYCLE
from core.log_config import log_session_end, log_session_start, setup_logging

setup_logging()

logger = structlog.get_logger(component="core.main")

try:
    log_path = BASE_DIR / "lunawave.log"
    log_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
except OSError:
    pass

from bootstrap.maintenance import schedule_db_maintenance, schedule_status_log, start_mpv_watchdog
from bootstrap.services import context, init_core_services
from bootstrap.startup_tasks import run_startup_checks


# 8. Start Web Server (create app, print banner, serve, then shut everything
# down once the server returns or is cancelled). Kept in main.py rather than
# bootstrap/ since it owns the full app lifecycle (start -> cleanup), not a
# standalone startup stage.
async def run_server():
    ctx = context
    import os

    pid = os.getpid()
    try:
        # Import lokal (bukan top-level) agar server.app.create_app /
        # server.app.run_server tetap bisa di-patch dari test lewat
        # "server.app.<nama>" (sama seperti pola asli sebelum T2.4).
        from server.app import create_app
        from server.app import run_server as _web_run_server

        app = create_app(ctx.playback_controller, ctx.ytdlp, ctx.repos)

        host = WEB_HOST
        port = WEB_PORT

        import socket

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            display_host = s.getsockname()[0]
            s.close()
        except Exception:
            display_host = host if host != "0.0.0.0" else "127.0.0.1"

        url_client = f"http://{display_host}:{port}"
        url_admin = f"http://{display_host}:{port}/admin"
        print("=====================================================")
        print("|   LunaWave Web Server                             |")
        print(f"|   Client : {url_client:<37} |")
        print(f"|   Admin  : {url_admin:<37} |")

        # T-B14.1: config.IS_PASSWORD_AUTO_GENERATED sudah dihapus -- tidak
        # ada lagi password auto-generated untuk ditampilkan di sini.
        # admin_account (SQLite) sekarang satu-satunya source of truth;
        # instalasi baru tanpa admin_account diarahkan ke Initial Setup
        # oleh frontend/server itu sendiri, bukan lewat banner ini.
        print("=====================================================")

        # ADR-0010: baris pemisah sesi di lunawave.log (dan console), sesuai
        # contoh output RFC observability_logging.md. Best-effort/fail-safe
        # sendiri di sisi log_config -- tidak pernah menggagalkan startup.
        log_session_start(pid, host=host, port=port)

        await _web_run_server(app, host=host, port=port)

    except asyncio.CancelledError:
        pass
    finally:
        import traceback

        for t in ctx.tasks:
            if t.done() and not t.cancelled():
                exc = t.exception()
                if exc:
                    logger.error(
                        "background_task_crashed",
                        category=LC_LIFECYCLE,
                        task_name=t.get_name(),
                        error_type=type(exc).__name__,
                        error=str(exc),
                    )
                    print(f"\n[FATAL ERROR] App crashed due to task failure: {exc}")
                    traceback.print_exception(type(exc), exc, exc.__traceback__)

        # Cancel remaining tasks and WAIT for them to actually finish.
        # cancel() hanya menjadwalkan CancelledError, tidak menunggu task selesai.
        # PATCH-2026-07-16-001: tanpa await ini, background loop task
        # (mpv_watchdog, db_maintenance, connectivity_checker) bisa masih
        # pending-cancellation saat proses exit, berpotensi menyebabkan hang.
        for t in ctx.tasks:
            t.cancel()
        if ctx.tasks:
            await asyncio.gather(*ctx.tasks, return_exceptions=True)

        # Cleanup resources
        await ctx.nowplaying.cleanup()
        try:
            await ctx.mpv.close()
        except Exception:
            pass
        ctx.lyrics_fetcher.cleanup()
        ctx.sponsorblock.cleanup()
        ctx.ytdlp.cancel_download()
        await ctx.http_session.close()
        await ctx.repos.close()

        logger.info("shutdown_completed", category=LC_LIFECYCLE)

        # ADR-0010: penutup pasangan log_session_start() di atas -- ditulis
        # paling akhir supaya menandai proses shutdown benar-benar selesai.
        log_session_end(pid)


async def main():
    await init_core_services()
    await run_startup_checks()
    schedule_db_maintenance()
    start_mpv_watchdog()
    schedule_status_log()
    await run_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

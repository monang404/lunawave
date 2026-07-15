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
    - Implement the core functionality described in the purpose.

Depends on:
    - cache.db
    - cache.resolver
    - core.event_bus
    - core.log_config
    - core.state
    - core.task_utils
    - engine.command_router
    - engine.download_manager
    - engine.mpv_controller
    - engine.playback.controller
    - engine.queue_manager
    - engine.radio_engine
    - engine.volume_service
    - engine.ytdlp_client
    - plugins.lyrics_fetcher
    - plugins.notifications
    - plugins.sponsorblock
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

import aiohttp
import structlog

from cache.db import Database
from config import BASE_DIR, WEB_HOST, WEB_PORT
from core.event_bus import bus
from core.log_config import setup_logging
from core.state import AppState, AudioOutput, PlayerStatus
from core.task_utils import safe_create_task
from engine.command_router import CommandRouter
from engine.download_manager import DownloadManager
from engine.mpv_controller import MpvController
from engine.ytdlp_client import YtDlpClient
from plugins.notifications import TermuxNowPlaying

setup_logging()

try:
    log_path = BASE_DIR / "lunawave.log"
    log_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
except OSError:
    pass

from plugins.lyrics_fetcher import LyricsFetcher
from plugins.sponsorblock import SponsorBlockHandler


async def main():
    state = AppState()

    # 1. Inisialisasi DB dan MPV secara paralel untuk mempersingkat startup
    print("  [1/5] Membuka database + menghubungkan audio player (paralel)...")
    db = Database()
    mpv = MpvController()

    async def _init_mpv():
        try:
            await mpv.connect()
        except Exception as e:
            structlog.get_logger(__name__).error(f"mpv not available: {e}")
            state.error_msg = (
                "MPV tidak ditemukan. Jalankan: pkg install mpv (Termux) "
                "atau install MPV dan tambahkan ke PATH (Windows/Linux)."
            )
            state.status = PlayerStatus.ERROR

    await asyncio.gather(db.init(), _init_mpv())

    # 2. Initialize Core Engine (YtDlpClient ringan — hanya buat ThreadPoolExecutor)
    print("  [2/5] Menginisialisasi YT-DLP Engine...")
    ytdlp = YtDlpClient()

    print("  [3/5] Menyiapkan layanan playback...")

    # 3. Shared HTTP session
    http_session = aiohttp.ClientSession()

    # 4. Global Services Initialization
    from cache.resolver import CacheResolver
    from engine.loudness.service import LoudnessService
    from engine.playback.controller import PlaybackController
    from engine.queue_manager import QueueMode
    from engine.radio_engine import RadioMode
    from engine.volume_service import VolumeService

    resolver = CacheResolver(db, ytdlp)

    sponsorblock = SponsorBlockHandler(mpv, state=state, session=http_session, event_bus=bus)
    lyrics_fetcher = LyricsFetcher(state, session=http_session, event_bus=bus)
    loudness_service = LoudnessService(db)

    queue_mode = QueueMode()
    radio_mode = RadioMode(ytdlp, state, db=db)

    volume_service = VolumeService(bus, mpv, state)
    playback_controller = PlaybackController(
        bus,
        state,
        mpv,
        resolver,
        sponsorblock,
        lyrics_fetcher,
        queue_mode,
        radio_mode,
        loudness_service,
    )

    from engine.sleep_timer import SleepTimer

    sleep_timer = SleepTimer(bus)

    DownloadManager(bus, state, ytdlp)
    CommandRouter(playback_controller, volume_service, sleep_timer)

    # Termux now-playing notification (no-op outside Termux)
    nowplaying = TermuxNowPlaying(bus, state)
    await nowplaying.start()

    # Connectivity Check
    async def check_connectivity():
        while True:
            try:
                async with http_session.get(
                    "https://connectivitycheck.gstatic.com/generate_204",
                    timeout=aiohttp.ClientTimeout(total=3),
                ) as r:
                    state.is_online = r.status == 204
            except (TimeoutError, aiohttp.ClientError):
                state.is_online = False
            except Exception as e:
                structlog.get_logger(__name__).warning(f"Connectivity check unexpected error: {e}")
                state.is_online = False

            await asyncio.sleep(300)  # 60→300 det: cek konektivitas cukup sekali per 5 menit

    connectivity_task = safe_create_task(check_connectivity(), name="connectivity_checker")
    tasks = [connectivity_task]

    # Resume last playback
    try:
        async with db.conn.execute(
            "SELECT video_id, last_position FROM tracks WHERE last_played IS NOT NULL ORDER BY last_played DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            if row and row["video_id"]:
                vid = row["video_id"]
                last_pos = float(row["last_position"] or 0.0)
                track = await db.get_track(vid)
                if track and last_pos > 0:
                    await playback_controller.play_track(
                        track, start_position=last_pos, start_paused=True
                    )
                    structlog.get_logger(__name__).info(
                        f"Resumed last track: {track.title} at {last_pos}s"
                    )
    except Exception as e:
        structlog.get_logger(__name__).error(f"Gagal load last_position: {e}")

    # DB Maintenance: eviction track stale + cleanup session expired.
    async def db_maintenance():
        # Jalankan sekali di awal, baru masuk loop periodik
        try:
            deleted = await db.evict_stale_tracks()
            if deleted:
                structlog.get_logger(__name__).info(
                    f"DB maintenance (awal): {deleted} track stale dihapus"
                )
        except Exception as e:
            structlog.get_logger(__name__).warning(
                f"DB maintenance awal (evict_stale_tracks) gagal: {e}"
            )
        try:
            await db.cleanup_sessions()
        except Exception as e:
            structlog.get_logger(__name__).warning(
                f"DB maintenance awal (cleanup_sessions) gagal: {e}"
            )

        while True:
            await asyncio.sleep(6 * 3600)  # tiap 6 jam
            try:
                deleted = await db.evict_stale_tracks()
                if deleted:
                    structlog.get_logger(__name__).info(
                        f"DB maintenance: {deleted} track stale dihapus"
                    )
            except Exception as e:
                structlog.get_logger(__name__).warning(
                    f"DB maintenance (evict_stale_tracks) gagal: {e}"
                )
            try:
                await db.cleanup_sessions()
            except Exception as e:
                structlog.get_logger(__name__).warning(
                    f"DB maintenance (cleanup_sessions) gagal: {e}"
                )

    tasks.append(safe_create_task(db_maintenance(), name="db_maintenance"))

    # 7.5 MPV auto-reconnect checker
    async def mpv_reconnect_checker():
        while True:
            await asyncio.sleep(30)  # 5→30 det: reconnect check cukup sekali per 30 detik
            if (
                getattr(mpv, "is_available", True)
                and not getattr(mpv, "is_connected", False)
                and state.status != PlayerStatus.ERROR
            ):
                structlog.get_logger(__name__).warning("MPV terputus! Mencoba reconnect...")
                try:
                    await mpv.close()
                except Exception:
                    pass
                try:
                    await mpv.connect()
                    if (
                        state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED)
                        and state.current_track
                    ):
                        uri = await resolver.resolve(state.current_track)
                        await mpv.play(uri)
                        await mpv.seek(state.position)

                        from engine.loudness.gain_calculator import build_af_filter, compute_gain_db

                        row = await db.get_track(state.current_track.video_id)
                        gain_db = 0.0
                        if row and row.loudness_lufs is not None:
                            gain_db = compute_gain_db(row.loudness_lufs)

                        if getattr(state, "loudness_normalization_enabled", True):
                            await mpv.set_af(build_af_filter(gain_db))
                        else:
                            await mpv.set_af(build_af_filter(0.0))

                        if (
                            getattr(state, "audio_output", AudioOutput.DEVICE)
                            == AudioOutput.BROWSER
                        ):
                            await mpv.set_volume(0)
                        else:
                            await mpv.set_volume(state.volume)
                        if state.status == PlayerStatus.PLAYING:
                            await mpv.resume()
                except Exception as e:
                    structlog.get_logger(__name__).error(f"MPV reconnect failed: {e}")

    tasks.append(safe_create_task(mpv_reconnect_checker(), name="mpv_reconnect_checker"))

    # 8. Start Web Server
    try:
        from server.app import create_app, run_server

        app = create_app(playback_controller, ytdlp, db)

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

        from config import ADMIN_USERNAME, IS_PASSWORD_AUTO_GENERATED

        if IS_PASSWORD_AUTO_GENERATED:
            print("|                                                   |")
            print("|   Kredensial Mode Admin:                          |")
            print(f"|   User: {ADMIN_USERNAME:<40} |")
            print("|   Pass: (lihat file di bawah — dibuat saat first-run) |")
            print("|   File: cache/admin_password.txt                  |")
        print("=====================================================")

        await run_server(app, host=host, port=port)

    except asyncio.CancelledError:
        pass
    finally:
        import traceback

        for t in tasks:
            if t.done() and not t.cancelled():
                exc = t.exception()
                if exc:
                    structlog.get_logger(__name__).error(f"Task {t.get_name()} crashed: {exc}")
                    print(f"\n[FATAL ERROR] App crashed due to task failure: {exc}")
                    traceback.print_exception(type(exc), exc, exc.__traceback__)

        # Cancel remaining tasks
        for t in tasks:
            t.cancel()

        # Cleanup resources
        await nowplaying.cleanup()
        try:
            await mpv.close()
        except:
            pass
        lyrics_fetcher.cleanup()
        sponsorblock.cleanup()
        ytdlp.cancel_download()
        await http_session.close()
        await db.close()

        structlog.get_logger(__name__).info("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

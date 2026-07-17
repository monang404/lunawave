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

    # Event untuk koordinasi: _resume_last_track menunggu MPV selesai connect
    # tanpa memblok run_server — browser bisa akses UI sementara kedua task jalan.
    _mpv_ready_event = asyncio.Event()

    # 1. Inisialisasi DB (server membutuhkan DB, jadi ini tetap blocking)
    print("  [1/5] Membuka database...")
    db = Database()
    mpv = MpvController()
    await db.init()

    async def _init_mpv():
        try:
            await mpv.connect()
            _mpv_ready_event.set()  # beri sinyal ke _resume_last_track bahwa MPV siap
        except Exception as e:
            structlog.get_logger(__name__).error(f"mpv not available: {e}")
            state.error_msg = (
                "MPV tidak ditemukan. Jalankan: pkg install mpv (Termux) "
                "atau install MPV dan tambahkan ke PATH (Windows/Linux)."
            )
            state.status = PlayerStatus.ERROR
            _mpv_ready_event.set()  # set juga saat error agar resume tidak hang

    # 2. Initialize Core Engine (YtDlpClient ringan — hanya buat ThreadPoolExecutor)
    print("  [2/5] Menginisialisasi YT-DLP Engine...")
    ytdlp = YtDlpClient()

    print("  [3/5] Menyiapkan layanan playback...")
    print("  (Audio player dihubungkan di background — server akan listen duluan)")

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

    # MPV connect dijalankan sebagai background task — server tidak perlu menunggu.
    # _mpv_ready_event akan di-set oleh _init_mpv() saat koneksi selesai (sukses/gagal).
    tasks.append(safe_create_task(_init_mpv(), name="mpv_initial_connect"))

    # Resume last playback — dijalankan sebagai background task agar tidak memblok
    # run_server(). Menunggu MPV siap via _mpv_ready_event (tanpa timeout) sebelum
    # memanggil play_track(), sehingga browser sudah bisa connect ke UI sementara
    # resume (dan kemungkinan network call yt-dlp) masih diproses di belakang layar.
    async def _resume_last_track():
        # Tunggu MPV siap sebelum resume — tanpa timeout agar resume tidak di-skip
        # di hardware lambat (Termux/Android). Karena ini background task, menunggu
        # di sini tidak memblok server sama sekali.
        await _mpv_ready_event.wait()
        if state.status == PlayerStatus.ERROR:
            # MPV gagal start, tidak ada gunanya mencoba resume
            return
        try:
            async with db.conn.execute(
                "SELECT video_id, last_position FROM tracks WHERE last_played IS NOT NULL ORDER BY last_played DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                if row and row["video_id"]:
                    last_pos = float(row["last_position"] or 0.0)
                    track = await db.get_track(row["video_id"])
                    if track and last_pos > 0:
                        await playback_controller.play_track(
                            track, start_position=last_pos, start_paused=True
                        )
                        structlog.get_logger(__name__).info(
                            f"Resumed last track: {track.title} at {last_pos}s"
                        )
        except Exception as e:
            structlog.get_logger(__name__).error(f"Gagal load last_position: {e}")

    tasks.append(safe_create_task(_resume_last_track(), name="resume_last_track"))

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

    # 7.5 MPV watchdog: no longer polls/reconnects itself. MpvObserver now
    # owns reconnect (immediate, bounded retries) so there is a single
    # reconnect path instead of two racing ones. This watchdog only handles
    # the case where mpv never comes back at all (observer gave up after its
    # own retries): it surfaces that as a visible error state instead of
    # silently leaving playback stuck, without spawning yet another mpv
    # process or reloading/seeking the track itself.
    async def mpv_watchdog():
        while True:
            await asyncio.sleep(10)
            if (
                getattr(mpv, "is_available", True)
                and not getattr(mpv, "is_connected", False)
                and state.status not in (PlayerStatus.ERROR, PlayerStatus.IDLE)
            ):
                structlog.get_logger(__name__).error(
                    "MPV masih terputus setelah reconnect otomatis gagal."
                )
                state.status = PlayerStatus.ERROR
                state.error_msg = "Koneksi ke MPV terputus dan gagal reconnect."

    tasks.append(safe_create_task(mpv_watchdog(), name="mpv_watchdog"))

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
            print("|   Pass: (lihat file di bawah - dibuat saat first-run) |")
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

        # Cancel remaining tasks and WAIT for them to actually finish.
        # cancel() hanya menjadwalkan CancelledError, tidak menunggu task selesai.
        # PATCH-2026-07-16-001: tanpa await ini, background loop task
        # (mpv_watchdog, db_maintenance, connectivity_checker) bisa masih
        # pending-cancellation saat proses exit, berpotensi menyebabkan hang.
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Cleanup resources
        await nowplaying.cleanup()
        try:
            await mpv.close()
        except Exception:
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

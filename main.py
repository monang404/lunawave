# PATCHLOG_APPLIED
import asyncio
import stat
import sys

import aiohttp
import structlog

from cache.db import Database
from config import BASE_DIR, WEB_HOST, WEB_PORT
from core.log_config import setup_logging
from core.state import AppState, PlayerStatus
from core.task_utils import safe_create_task
from engine.command_router import CommandRouter
from engine.download_manager import DownloadManager
from engine.mpv_controller import MpvController
from engine.ytdlp_client import YtDlpClient
from plugins.notifications import TermuxNowPlaying

setup_logging()

try:
    log_path = BASE_DIR / "ytplayer.log"
    log_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
except OSError:
    pass

from plugins.lyrics import LyricsFetcher
from plugins.sponsorblock import SponsorBlockHandler


async def main():
    from core.command_bus import CommandBus
    from core.event_bus import EventBus
    event_bus = EventBus()
    command_bus = CommandBus()

    state = AppState()

    sys.stderr.write("\033[90m  [1/5]\033[0m Membuka database perpustakaan...\n")
    db = Database()
    await db.init()

    sys.stderr.write("\033[90m  [2/5]\033[0m Menginisialisasi YT-DLP Engine...\n")
    ytdlp = YtDlpClient()

    sys.stderr.write("\033[90m  [3/5]\033[0m Menghubungkan ke audio player (MPV)...\n")
    mpv = MpvController(event_bus=event_bus)
    try:
        await mpv.connect()
        mpv.is_available = True
    except Exception as e:
        structlog.get_logger(__name__).critical(f"mpv not available: {e}")
        state.error_msg = (
            "MPV tidak ditemukan. Jalankan: pkg install mpv (Termux) "
            "atau install MPV dan tambahkan ke PATH (Windows/Linux)."
        )
        state.status = PlayerStatus.ERROR
        mpv.is_available = False

    http_session = aiohttp.ClientSession()

    from cache.resolver import CacheResolver
    from engine.playback.controller import PlaybackController
    from engine.queue_manager import QueueMode
    from engine.radio_engine import RadioMode
    from engine.volume_service import VolumeService

    resolver = CacheResolver(db, ytdlp)

    sponsorblock = SponsorBlockHandler(
        mpv, state=state, session=http_session, event_bus=event_bus
    )
    lyrics_fetcher = LyricsFetcher(
        state, session=http_session, event_bus=event_bus
    )

    queue_mode = QueueMode()
    radio_mode = RadioMode(ytdlp, state, db=db)

    volume_service = VolumeService(event_bus, mpv, state)
    playback_controller = PlaybackController(
        event_bus, state, mpv, resolver,
        sponsorblock, lyrics_fetcher, queue_mode, radio_mode
    )

    download_manager = DownloadManager(event_bus, command_bus, state, ytdlp)
    command_router = CommandRouter(command_bus, playback_controller, volume_service)

    nowplaying = TermuxNowPlaying(event_bus, command_bus, state)
    await nowplaying.start()

    async def check_connectivity():
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

    connectivity_task = safe_create_task(check_connectivity(), name="connectivity_checker")
    tasks = [connectivity_task]

    async def db_cleanup():
        while True:
            await asyncio.sleep(86400)
            try:
                await db.evict_stale_tracks()
                await db.cleanup_sessions()
            except Exception as e:
                structlog.get_logger(__name__).error(f"DB cleanup failed: {e}")

    tasks.append(safe_create_task(db_cleanup(), name="db_cleanup"))



    try:
        from server.app import create_app, run_server
        from server.handlers.event_listeners import setup_event_listeners
        from server.handlers.websocket import ConnectionManager
        from server.services.broadcast_service import BroadcastService
        from server.services.stream_prefetch import StreamPrefetchService

        manager = ConnectionManager()
        prefetch_service = StreamPrefetchService(db, ytdlp)
        broadcast_service = BroadcastService(manager)
        setup_event_listeners(playback_controller, prefetch_service, broadcast_service)

        app = create_app(playback_controller, ytdlp, db, manager, command_bus=command_bus, event_bus=event_bus)

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
        sys.stderr.write(
            f"\n\033[1;32m{'─'*54}\033[0m\n"
            f"  \033[1m▸ ytgui\033[0m  Web Server\n"
            f"  Client : \033[36m{url_client}\033[0m\n"
            f"  Admin  : \033[36m{url_admin}\033[0m\n"
        )

        from config import ADMIN_USERNAME, IS_PASSWORD_AUTO_GENERATED
        if IS_PASSWORD_AUTO_GENERATED:
            sys.stderr.write(
                f"  User   : [33m{ADMIN_USERNAME}[0m\n"
                f"  Pass   : [33m(lihat cache/admin_password.txt)[0m\n"
            )
        sys.stderr.write(f"[1;32m{'─'*54}[0m\n\n")

        await run_server(app, host=host, port=port)

    except asyncio.CancelledError:
        pass
    finally:
        import traceback
        for t in tasks:
            if t.done() and not t.cancelled():
                e = t.exception()  # type: ignore
                if e:
                    structlog.get_logger(__name__).critical(f"Task {t.get_coro().__name__} crashed: {e}")
                    print(f"\n[FATAL ERROR] App crashed due to task failure: {e}")
                    traceback.print_exception(type(e), e, e.__traceback__)

        for t in tasks:
            t.cancel()

        await nowplaying.cleanup()
        try: await mpv.close()
        except Exception: pass
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

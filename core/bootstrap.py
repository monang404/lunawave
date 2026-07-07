import sys
import structlog
import socket
from dataclasses import dataclass
from typing import Any
import aiohttp

from cache.db import Database
from config import WEB_HOST, WEB_PORT
from core.state import AppState, PlayerStatus
from engine.mpv_controller import MpvController
from engine.ytdlp_client import YtDlpClient
from plugins.notifications import TermuxNowPlaying
from plugins.lyrics import LyricsFetcher
from plugins.sponsorblock import SponsorBlockHandler
from core.command_bus import CommandBus
from core.event_bus import EventBus
from cache.resolver import CacheResolver
from engine.playback.controller import PlaybackController
from engine.queue_manager import QueueMode
from engine.radio_engine import RadioMode
from engine.volume_service import VolumeService
from engine.download_manager import DownloadManager
from engine.command_router import CommandRouter

from server.app import create_app
from server.handlers.event_listeners import setup_event_listeners
from server.handlers.websocket import ConnectionManager
from server.services.broadcast_service import BroadcastService
from server.services.stream_prefetch import StreamPrefetchService

@dataclass
class AppContext:
    app: Any
    db: Database
    mpv: MpvController
    ytdlp: YtDlpClient
    http_session: aiohttp.ClientSession
    state: AppState
    event_bus: EventBus
    command_bus: CommandBus
    playback_controller: PlaybackController
    manager: ConnectionManager
    nowplaying: TermuxNowPlaying
    lyrics_fetcher: LyricsFetcher
    sponsorblock: SponsorBlockHandler
    host: str
    port: int

async def build_app_context() -> AppContext:
    event_bus = EventBus()
    command_bus = CommandBus()
    state = AppState()

    sys.stderr.write("\033[90m  [1/5]\033[0m Membuka database perpustakaan...\n")
    db = Database()
    await db.init()

    sys.stderr.write("\033[90m  [2/5]\033[0m Menginisialisasi YT-DLP Engine...\n")
    ytdlp = YtDlpClient()

    sys.stderr.write("\033[90m  [3/5]\033[0m Menghubungkan ke audio player (MPV)....\n")
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
    from engine.playback.controller import PlaybackDependencies
    playback_deps = PlaybackDependencies(
        bus=event_bus,
        state=state,
        mpv=mpv,
        resolver=resolver,
        sponsorblock=sponsorblock,
        lyrics_fetcher=lyrics_fetcher,
        queue_mode=queue_mode,
        radio_mode=radio_mode,
        db=db
    )
    playback_controller = PlaybackController(deps=playback_deps)

    from engine.playback.playback_commands import PlaybackCommands
    from engine.playback.queue_commands import QueueCommands
    from engine.playback.settings_commands import SettingsCommands
    from engine.playback.radio_commands import RadioCommands

    playback_commands = PlaybackCommands(playback_controller)
    queue_commands = QueueCommands(playback_controller)
    settings_commands = SettingsCommands(playback_controller)
    radio_commands = RadioCommands(playback_controller)

    _download_manager = DownloadManager(event_bus, command_bus, state, ytdlp)
    _command_router = CommandRouter(
        command_bus,
        playback_commands,
        queue_commands,
        settings_commands,
        radio_commands,
        volume_service
    )

    nowplaying = TermuxNowPlaying(event_bus, command_bus, state)
    await nowplaying.start()

    manager = ConnectionManager()
    prefetch_service = StreamPrefetchService(db, ytdlp)
    broadcast_service = BroadcastService(manager)
    setup_event_listeners(playback_controller, prefetch_service, broadcast_service)

    app = create_app(playback_controller, ytdlp, db, manager, command_bus=command_bus, event_bus=event_bus, http_session=http_session)

    host = WEB_HOST
    port = WEB_PORT

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
        f"  \033[1m▸ LunaWave\033[0m  Web Server\n"
        f"  Client : \033[36m{url_client}\033[0m\n"
        f"  Admin  : \033[36m{url_admin}\033[0m\n"
    )

    from config import ADMIN_USERNAME, IS_PASSWORD_AUTO_GENERATED
    if IS_PASSWORD_AUTO_GENERATED:
        sys.stderr.write(
            f"  User   : \033[33m{ADMIN_USERNAME}\033[0m\n"
            f"  Pass   : \033[33m(lihat cache/admin_password.txt)\033[0m\n"
        )
    sys.stderr.write(f"\033[1;32m{'─'*54}\033[0m\n\n")

    return AppContext(
        app=app,
        db=db,
        mpv=mpv,
        ytdlp=ytdlp,
        http_session=http_session,
        state=state,
        event_bus=event_bus,
        command_bus=command_bus,
        playback_controller=playback_controller,
        manager=manager,
        nowplaying=nowplaying,
        lyrics_fetcher=lyrics_fetcher,
        sponsorblock=sponsorblock,
        host=host,
        port=port
    )

async def shutdown_app_context(ctx: AppContext, tasks: list):
    import traceback
    for t in tasks:
        if t.done() and not t.cancelled():
            e = t.exception()
            if e:
                structlog.get_logger(__name__).critical(f"Task {t.get_coro().__name__} crashed: {e}")
                print(f"\n[FATAL ERROR] App crashed due to task failure: {e}")
                traceback.print_exception(type(e), e, e.__traceback__)

    for t in tasks:
        t.cancel()

    await ctx.nowplaying.cleanup()
    try:
        await ctx.mpv.close()
    except Exception:
        pass
    ctx.lyrics_fetcher.cleanup()
    ctx.sponsorblock.cleanup()
    ctx.ytdlp.cancel_download()
    await ctx.http_session.close()
    await ctx.db.close()

    structlog.get_logger(__name__).info("Shutdown complete.")

"""
Module: bootstrap.services

Purpose:
    Stage 1 of application startup: open the DB, connect core adapters
    (MPV, yt-dlp), and wire every domain service used by the rest of the
    app (resolver, playback controller, radio, volume, sleep timer, etc).
    Extracted from main.py's `main()` (T2.4, section "1-6" of the original
    God Function) without changing call order.

Inputs:
    None (reads config via the modules it wires).

Outputs:
    A populated `BootstrapContext` (module-level singleton `context`)
    consumed by bootstrap.startup_tasks, bootstrap.maintenance, and
    main.py's server/shutdown stage.

Side Effects:
    Opens SQLite DB, spawns/attaches mpv IPC client, opens shared HTTP
    session, starts Termux now-playing integration.

CLI:
    None (imported by main.py).

Responsibilities:
    - Build and hold every long-lived service object needed at runtime.

Depends on:
    - persistence
    - adapters.mpv
    - adapters.ytdlp
    - plugins.notifications
    - plugins.lyrics_fetcher
    - plugins.sponsorblock
    - persistence.stream_cache
    - engine.loudness.service
    - engine.playback.controller
    - engine.queue_manager
    - engine.radio
    - engine.volume_service
    - engine.sleep_timer
    - engine.command_router
    - engine.download_manager
    - core.event_bus
    - core.state

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio

import aiohttp
import structlog

from adapters.mpv import MpvController
from adapters.ytdlp import YtDlpClient
from core.event_bus import bus
from core.state import AppState, PlayerStatus
from engine.command_router import CommandRouter
from engine.download_manager import DownloadManager
from persistence import Repositories
from plugins.lyrics_fetcher import LyricsFetcher
from plugins.notifications import TermuxNowPlaying
from plugins.sponsorblock import SponsorBlockHandler


class BootstrapContext:
    """Holds every service built during startup so later bootstrap stages
    (startup_tasks, maintenance) and main.py's shutdown block can reach
    them without re-wiring. Populated once by `init_core_services()`."""

    def __init__(self):
        self.state: AppState | None = None
        self.mpv_ready_event: asyncio.Event | None = None
        self.repos = None
        self.mpv = None
        self.ytdlp = None
        self.http_session: aiohttp.ClientSession | None = None
        self.resolver = None
        self.sponsorblock = None
        self.lyrics_fetcher = None
        self.loudness_service = None
        self.queue_mode = None
        self.radio_mode = None
        self.volume_service = None
        self.playback_controller = None
        self.sleep_timer = None
        self.download_manager = None
        self.command_router = None
        self.nowplaying = None
        self.tasks: list[asyncio.Task] = []


# Module-level singleton — main.py's four bootstrap calls all operate on
# this shared context, mirroring the local variables the original God
# Function used to close over.
context = BootstrapContext()


async def _init_mpv():
    """Background task: connect MPV, signal `mpv_ready_event` either way
    (success or failure) so `_resume_last_track` never hangs waiting."""
    ctx = context
    try:
        await ctx.mpv.connect()
        ctx.mpv_ready_event.set()
    except Exception as e:
        structlog.get_logger(__name__).error(f"mpv not available: {e}")
        ctx.state.error_msg = (
            "MPV tidak ditemukan. Jalankan: pkg install mpv (Termux) "
            "atau install MPV dan tambahkan ke PATH (Windows/Linux)."
        )
        ctx.state.status = PlayerStatus.ERROR
        ctx.mpv_ready_event.set()  # set juga saat error agar resume tidak hang


async def init_core_services() -> BootstrapContext:
    """Bootstrap stage 1: DB, MPV, yt-dlp, shared HTTP session, and every
    domain service (resolver, playback controller, radio, volume, sleep
    timer, download manager, command router, now-playing integration).
    Mirrors steps 1-6 of the original main() God Function verbatim."""
    ctx = context
    ctx.state = AppState()

    # Event untuk koordinasi: _resume_last_track menunggu MPV selesai connect
    # tanpa memblok run_server — browser bisa akses UI sementara kedua task jalan.
    ctx.mpv_ready_event = asyncio.Event()

    # 1. Inisialisasi DB (server membutuhkan DB, jadi ini tetap blocking)
    print("  [1/5] Membuka database...")
    ctx.repos = Repositories()
    ctx.mpv = MpvController()
    await ctx.repos.init()

    # 2. Initialize Core Engine (YtDlpClient ringan — hanya buat ThreadPoolExecutor)
    print("  [2/5] Menginisialisasi YT-DLP Engine...")
    ctx.ytdlp = YtDlpClient()

    print("  [3/5] Menyiapkan layanan playback...")
    print("  (Audio player dihubungkan di background — server akan listen duluan)")

    # 3. Shared HTTP session
    ctx.http_session = aiohttp.ClientSession()

    # 4. Global Services Initialization
    from persistence.stream_cache import CacheResolver, ResolverDbCompat
    from engine.loudness.service import LoudnessService
    from engine.playback.controller import PlaybackController
    from engine.queue_manager import QueueMode
    from engine.radio import RadioMode
    from engine.sleep_timer import SleepTimer
    from engine.volume_service import VolumeService

    ctx.resolver = CacheResolver(
        ResolverDbCompat(ctx.repos.tracks, ctx.repos.artists, ctx.repos.discover), ctx.ytdlp
    )

    ctx.sponsorblock = SponsorBlockHandler(
        ctx.mpv, state=ctx.state, session=ctx.http_session, event_bus=bus
    )
    ctx.lyrics_fetcher = LyricsFetcher(ctx.state, session=ctx.http_session, event_bus=bus)
    ctx.loudness_service = LoudnessService(ctx.repos.tracks)

    ctx.queue_mode = QueueMode()
    ctx.radio_mode = RadioMode(
        ctx.ytdlp, ctx.state, artists=ctx.repos.artists, library=ctx.repos.library
    )

    ctx.volume_service = VolumeService(bus, ctx.mpv, ctx.state)
    ctx.playback_controller = PlaybackController(
        bus,
        ctx.state,
        ctx.mpv,
        ctx.resolver,
        ctx.sponsorblock,
        ctx.lyrics_fetcher,
        ctx.queue_mode,
        ctx.radio_mode,
        ctx.loudness_service,
    )

    ctx.sleep_timer = SleepTimer(bus)

    ctx.download_manager = DownloadManager(bus, ctx.state, ctx.ytdlp)
    ctx.command_router = CommandRouter(ctx.playback_controller, ctx.volume_service, ctx.sleep_timer)

    # Termux now-playing notification (no-op outside Termux)
    ctx.nowplaying = TermuxNowPlaying(bus, ctx.state)
    await ctx.nowplaying.start()

    return ctx

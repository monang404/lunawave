"""
Module: tests.integration.conftest

Purpose:
    Shared fixtures for integration tests. Wires up real components
    (EventBus, MpvController, Database, YtDlpClient, PlaybackController)
    but points them to temporary directories and memory databases to
    prevent side effects on the dev environment.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
import os
import shutil
import pytest
import aiohttp
from pathlib import Path
from aiohttp import web

from core.state import AppState
from core.event_bus import bus
from engine.mpv_controller import MpvController
from engine.ytdlp_client import YtDlpClient
from cache.db import Database
from cache.resolver import CacheResolver
from plugins.sponsorblock import SponsorBlockHandler
from plugins.lyrics import LyricsFetcher
from engine.queue_manager import QueueMode
from engine.radio_engine import RadioMode
from engine.volume_service import VolumeService
from engine.playback.controller import PlaybackController
from engine.download_manager import DownloadManager
from engine.command_router import CommandRouter

from server.app import create_app


@pytest.fixture
async def integration_app(tmp_path, monkeypatch):
    """
    Spawns a fully wired LunaWave application instance with real components
    but isolated storage (temp dir, memory DB).
    """
    # Isolate environment
    monkeypatch.setenv("LUNAWAVE_BASE", str(tmp_path))
    import config
    # Ensure CACHE_DIR and other paths from config use tmp_path
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "data" / "lunawave.db")
    (tmp_path / "cache").mkdir(parents=True, exist_ok=True)

    # We must reset EventBus state if we want to run multiple tests cleanly,
    # but EventBus is a singleton. For integration tests, we can just clear listeners.
    bus._subscribers.clear()

    state = AppState()

    # 1. Initialize real DB in memory
    db = Database(db_path=Path(":memory:"))
    await db.init()

    # 2. Initialize real MPV (will spawn subprocess)
    # We use a custom socket path in the temp dir so it doesn't conflict
    mpv_socket = tmp_path / "cache" / "sockets" / "mpv.sock"
    mpv_socket.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "MPV_SOCKET", str(mpv_socket))
    mpv = MpvController()
    try:
        await mpv.connect()
    except Exception:
        pytest.skip("MPV not available in test environment, skipping integration test.")

    # 3. YtDlpClient
    if not shutil.which("yt-dlp"):
        pytest.skip("yt-dlp not available in test environment, skipping integration test.")
    ytdlp = YtDlpClient()

    http_session = aiohttp.ClientSession()
    resolver = CacheResolver(db, ytdlp)

    sponsorblock = SponsorBlockHandler(mpv, state=state, session=http_session, event_bus=bus)
    lyrics_fetcher = LyricsFetcher(state, session=http_session, event_bus=bus)

    queue_mode = QueueMode()
    radio_mode = RadioMode(ytdlp, state, db=db)

    volume_service = VolumeService(bus, mpv, state)
    playback_controller = PlaybackController(
        bus, state, mpv, resolver,
        sponsorblock, lyrics_fetcher, queue_mode, radio_mode
    )

    download_manager = DownloadManager(bus, state, ytdlp)
    command_router = CommandRouter(playback_controller, volume_service)

    app = create_app(playback_controller, ytdlp, db)

    yield app

    # Teardown
    await http_session.close()
    await db.close()
    await mpv.close()

    import subprocess
    # Ensure MPV process is killed if disconnect didn't
    if os.name != 'nt':
        subprocess.run(["pkill", "-f", "mpv"], capture_output=True)
    else:
        subprocess.run(["taskkill", "/f", "/im", "mpv.exe"], capture_output=True)

@pytest.fixture
def loop(event_loop):
    """Backwards compatibility for pytest-aiohttp which expects 'loop'."""
    return event_loop

@pytest.fixture
async def app_client(aiohttp_client, integration_app):
    return await aiohttp_client(integration_app)

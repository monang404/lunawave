"""tests/unit/engine/test_download_manager.py — mirrors engine/download_manager.py

Semua I/O (shutil.move, Path.mkdir, ytdlp.download_mp3) di-mock agar
test berjalan tanpa filesystem nyata dan tanpa yt-dlp.

Purpose:
    Auto-generated purpose.

Subscribes to:
    - DownloadCompleteEvent
    - DownloadProgressEvent
    - LogMessageEvent

Publishes:
    None
"""

import asyncio
from unittest.mock import patch

import pytest

from core.command_bus import CommandBus
from core.event_bus import EventBus
from core.events import DownloadCompleteEvent, LogMessageEvent
from core.state import AppState, TrackInfo
from tests.fakes.fake_media_extractor import FakeMediaExtractor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_track(video_id="vid1", local_path=None):
    return TrackInfo(
        video_id=video_id,
        title="Lagu Test",
        artist="Artis Test",
        duration=200,
        local_path=local_path,
    )


def make_env(current_track=None):
    """Return (bus, state, ytdlp, isolated_command_bus) for one test."""
    bus = EventBus()
    state = AppState()
    if current_track:
        state.current_track = current_track
    ytdlp = FakeMediaExtractor()
    return bus, state, ytdlp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_command_bus():
    """Fresh CommandBus to avoid handler pollution across tests."""
    return CommandBus()


@pytest.fixture
def env():
    return make_env()


# ---------------------------------------------------------------------------
# Import helper — deferred to avoid side-effects at module level
# ---------------------------------------------------------------------------


def make_manager(bus, state, ytdlp, isolated_bus):
    """Instantiate DownloadManager with an isolated command bus."""
    from engine.download_manager import DownloadManager

    with patch("engine.download_manager.command_bus", isolated_bus):
        mgr = DownloadManager(bus=bus, state=state, ytdlp=ytdlp)
    return mgr


# ---------------------------------------------------------------------------
# _on_download guard conditions
# ---------------------------------------------------------------------------


class TestOnDownloadGuards:
    async def test_publishes_log_when_no_target_track(self):
        bus, state, ytdlp = make_env()  # state.current_track is None
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        received = []
        bus.subscribe(LogMessageEvent, received.append)

        await mgr._on_download(None)

        assert len(received) == 1
        assert "Tidak ada" in received[0].message

    async def test_publishes_log_when_track_already_has_local_path(self):
        track = make_track(local_path="/already/downloaded.mp3")
        bus, state, ytdlp = make_env(current_track=track)
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        received = []
        bus.subscribe(LogMessageEvent, received.append)

        await mgr._on_download(None)

        assert any("sudah tersimpan" in m.message for m in received)

    async def test_publishes_log_when_download_already_locked(self):
        track = make_track()
        bus, state, ytdlp = make_env(current_track=track)
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        received = []
        bus.subscribe(LogMessageEvent, received.append)

        # Manually acquire the lock to simulate in-progress download
        async with mgr._download_lock:
            await mgr._on_download(None)

        assert any("sedang berjalan" in m.message for m in received)

    async def test_uses_explicit_track_arg_over_current_track(self):
        """When an explicit track is passed, it takes priority over current_track."""
        explicit_track = make_track(video_id="explicit")
        current_track = make_track(video_id="current")
        bus, state, ytdlp = make_env(current_track=current_track)
        ytdlp.download_paths["explicit"] = "/tmp/explicit.mp3"
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        captured_downloads = []

        async def fake_do_download(track):
            captured_downloads.append(track.video_id)

        mgr._do_download = fake_do_download
        await mgr._on_download(explicit_track)
        await asyncio.sleep(0.05)

        # explicit must be used, not current
        assert "explicit" in captured_downloads


# ---------------------------------------------------------------------------
# _do_download happy path
# ---------------------------------------------------------------------------


class TestDoDownload:
    async def test_do_download_publishes_complete_event(self, tmp_path):
        track = make_track()
        bus, state, ytdlp = make_env(current_track=track)
        ytdlp.download_paths["vid1"] = str(tmp_path / "vid1.mp3")
        (tmp_path / "vid1.mp3").write_bytes(b"audio")
        isolated = CommandBus()

        # Override download_mp3 to call progress hook with a proper yt-dlp dict
        async def fake_dl(video_id, on_progress=None):
            if on_progress:
                on_progress({"status": "downloading", "downloaded_bytes": 100, "total_bytes": 100})
            return ytdlp.download_paths.get(video_id, f"/tmp/{video_id}.mp3")

        ytdlp.download_mp3 = fake_dl
        mgr = make_manager(bus, state, ytdlp, isolated)

        received = []
        bus.subscribe(DownloadCompleteEvent, received.append)

        with patch("shutil.move"), patch("pathlib.Path.mkdir"):
            await mgr._do_download(track)

        assert len(received) == 1
        assert received[0].track.video_id == "vid1"

    async def test_do_download_publishes_start_log(self, tmp_path):
        track = make_track()
        bus, state, ytdlp = make_env(current_track=track)
        ytdlp.download_paths["vid1"] = str(tmp_path / "vid1.mp3")

        async def fake_dl(video_id, on_progress=None):
            return ytdlp.download_paths.get(video_id, f"/tmp/{video_id}.mp3")

        ytdlp.download_mp3 = fake_dl
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        received = []
        bus.subscribe(LogMessageEvent, received.append)

        with patch("shutil.move"), patch("pathlib.Path.mkdir"):
            await mgr._do_download(track)

        messages = [m.message for m in received]
        assert any("Memulai download" in m for m in messages)

    async def test_do_download_sets_local_path_on_track(self, tmp_path):
        track = make_track()
        bus, state, ytdlp = make_env(current_track=track)
        ytdlp.download_paths["vid1"] = str(tmp_path / "vid1.mp3")

        async def fake_dl(video_id, on_progress=None):
            return ytdlp.download_paths.get(video_id, f"/tmp/{video_id}.mp3")

        ytdlp.download_mp3 = fake_dl
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        with patch("shutil.move"), patch("pathlib.Path.mkdir"):
            await mgr._do_download(track)

        assert track.local_path is not None
        assert "Artis Test" in track.local_path

    async def test_do_download_clears_progress_on_success(self, tmp_path):
        track = make_track()
        bus, state, ytdlp = make_env(current_track=track)
        ytdlp.download_paths["vid1"] = str(tmp_path / "vid1.mp3")

        async def fake_dl(video_id, on_progress=None):
            return ytdlp.download_paths.get(video_id, f"/tmp/{video_id}.mp3")

        ytdlp.download_mp3 = fake_dl
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        with patch("shutil.move"), patch("pathlib.Path.mkdir"):
            await mgr._do_download(track)

        assert state.download_progress is None

    async def test_do_download_publishes_error_log_on_exception(self):
        track = make_track()
        bus, state, ytdlp = make_env(current_track=track)
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        # Make download_mp3 raise
        async def bad_download(*_a, **_kw):
            raise RuntimeError("yt-dlp broke")

        ytdlp.download_mp3 = bad_download

        received = []
        bus.subscribe(LogMessageEvent, received.append)

        with patch("pathlib.Path.mkdir"):
            await mgr._do_download(track)

        assert any("gagal" in m.message.lower() for m in received)

    async def test_do_download_clears_progress_on_error(self):
        track = make_track()
        bus, state, ytdlp = make_env(current_track=track)
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        async def bad_download(*_a, **_kw):
            raise RuntimeError("fail")

        ytdlp.download_mp3 = bad_download

        with patch("pathlib.Path.mkdir"):
            await mgr._do_download(track)

        assert state.download_progress is None


# ---------------------------------------------------------------------------
# _update_progress
# ---------------------------------------------------------------------------


class TestUpdateProgress:
    async def test_update_progress_sets_state_download_progress(self):
        bus, state, ytdlp = make_env()
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        mgr._update_progress(0.42)
        assert state.download_progress == pytest.approx(0.42)

    async def test_update_progress_fires_download_progress_event(self):
        bus, state, ytdlp = make_env()
        isolated = CommandBus()
        mgr = make_manager(bus, state, ytdlp, isolated)

        from core.events import DownloadProgressEvent

        received = []
        bus.subscribe(DownloadProgressEvent, received.append)

        mgr._update_progress(0.75)
        await asyncio.sleep(0.05)  # allow safe_create_task to run

        assert len(received) == 1
        assert received[0].progress == pytest.approx(0.75)

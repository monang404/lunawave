import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from engine.download_manager import DownloadManager
from core.state import AppState, TrackInfo
from core.commands import DownloadCommand

@pytest.fixture
def bus():
    return AsyncMock()

@pytest.fixture
def command_bus():
    bus = MagicMock()
    bus.register = MagicMock()
    return bus

@pytest.fixture
def state():
    state = AppState()
    state.current_track = TrackInfo(video_id="vid1", title="Test Track", artist="Artist", duration=180)
    return state

@pytest.fixture
def ytdlp():
    return AsyncMock()

@pytest.fixture
def manager(bus, command_bus, state, ytdlp):
    return DownloadManager(bus, command_bus, state, ytdlp)

@pytest.mark.asyncio
async def test_on_download_no_target(manager, state):
    state.current_track = None
    await manager._on_download(None)
    manager.bus.publish.assert_called_once()
    args, _ = manager.bus.publish.call_args
    assert "Tidak ada lagu" in args[0].message

@pytest.mark.asyncio
async def test_on_download_already_local(manager, state):
    track = TrackInfo(video_id="vid2", title="Title", artist="Art", duration=100, local_path="local.mp3")
    await manager._on_download(track)
    manager.bus.publish.assert_called_once()
    args, _ = manager.bus.publish.call_args
    assert "sudah tersimpan lokal" in args[0].message

@pytest.mark.asyncio
async def test_on_download_already_downloading(manager, state):
    track = TrackInfo(video_id="vid3", title="Title", artist="Art", duration=100)
    manager._downloading_ids.add("vid3")
    await manager._on_download(track)
    manager.bus.publish.assert_called_once()
    args, _ = manager.bus.publish.call_args
    assert "sedang berjalan" in args[0].message

@pytest.mark.asyncio
async def test_do_download_success(manager, state, ytdlp):
    track = TrackInfo(video_id="vid4", title="Title", artist="Art", duration=100)
    manager._downloading_ids.add("vid4")
    
    with patch("shutil.copy2"):
        ytdlp.download_mp3.return_value = "cache/vid4.mp3"
        await manager._do_download(track)
        
    assert track.local_path == "cache/vid4.mp3"
    assert "vid4" not in manager._downloading_ids
    # Should publish log messages and complete event
    assert manager.bus.publish.call_count >= 2

@pytest.mark.asyncio
async def test_do_download_error(manager, state, ytdlp):
    track = TrackInfo(video_id="vid5", title="Title", artist="Art", duration=100)
    manager._downloading_ids.add("vid5")
    
    ytdlp.download_mp3.side_effect = Exception("Failed")
    await manager._do_download(track)
    
    assert track.local_path is None
    assert "vid5" not in manager._downloading_ids
    assert manager.bus.publish.call_count >= 2

@pytest.mark.asyncio
async def test_update_progress(manager, state):
    manager._update_progress(0.5)
    assert state.download_progress == 0.5

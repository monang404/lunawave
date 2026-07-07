import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from engine.playback.playback_commands import PlaybackCommands
from core.state import AppState, PlaybackMode, TrackInfo

class FakeController:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._advance_to_next = AsyncMock()
        self.play_track = AsyncMock()

@pytest.mark.asyncio
async def test_on_next_releases_lock_before_advance():
    controller_mock = FakeController()
    
    async def mock_advance():
        assert not controller_mock._lock.locked(), "Lock is held during _advance_to_next!"
        
    controller_mock._advance_to_next.side_effect = mock_advance
    
    controller_mock.state = AppState()
    controller_mock.mpv = MagicMock()
    controller_mock.bus = MagicMock()
    controller_mock.queue_mode = MagicMock()
    controller_mock.radio_mode = MagicMock()
    
    cmds = PlaybackCommands(controller_mock)
    
    await cmds.on_next()
    controller_mock._advance_to_next.assert_called_once()

@pytest.mark.asyncio
async def test_on_prev_releases_lock_before_play_track():
    controller_mock = FakeController()
    
    async def mock_play_track(track):
        assert not controller_mock._lock.locked(), "Lock is held during play_track!"
        
    controller_mock.play_track.side_effect = mock_play_track
    
    controller_mock.state = AppState()
    controller_mock.state.history.append(TrackInfo(video_id="v1", title="test", artist="artist", duration=100))
    controller_mock.mpv = MagicMock()
    controller_mock.bus = MagicMock()
    controller_mock.queue_mode = MagicMock()
    controller_mock.radio_mode = MagicMock()
    
    cmds = PlaybackCommands(controller_mock)
    
    await cmds.on_prev()
    controller_mock.play_track.assert_called_once()

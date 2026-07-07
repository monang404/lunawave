import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from engine.playback.controller import PlaybackController, PlaybackDependencies
from core.state import AppState, TrackInfo

@pytest.mark.asyncio
async def test_play_track_retry_captures_retry_count():
    deps = MagicMock()
    deps.bus = MagicMock()
    deps.bus.publish = AsyncMock()
    deps.mpv = MagicMock()
    deps.db = MagicMock()
    deps.state = AppState()
    
    controller = PlaybackController(deps)
    controller.track_loader = MagicMock()
    # Force an exception to trigger retry
    controller.track_loader.load_track = AsyncMock(side_effect=Exception("Load failed"))
    controller._advance_to_next = AsyncMock()
    
    # We will track what value sleep was called with
    sleep_calls = []
    
    async def fake_sleep(delay):
        sleep_calls.append(delay)
        # Simulate another task changing _retry_count during sleep
        controller._retry_count = 99
        
    track = TrackInfo(video_id="v1", title="Test", artist="Artist", duration=0)
    
    with patch('asyncio.sleep', new_callable=lambda: fake_sleep):
        await controller.play_track(track)
        
    # The first failure increments _retry_count to 1 inside the lock.
    # The delay should be 2 ** 1 = 2, regardless of it being changed to 99 during sleep.
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == 2
    
    # And advance to next should be called since track matches
    controller._advance_to_next.assert_called_once()

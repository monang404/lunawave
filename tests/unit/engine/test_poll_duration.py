import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from engine.playback.controller import PlaybackController
from core.state import AppState, TrackInfo

@pytest.mark.asyncio
async def test_poll_duration_does_not_publish_if_dur_is_none():
    deps = MagicMock()
    deps.bus = MagicMock()
    deps.bus.publish = AsyncMock()
    deps.mpv = MagicMock()
    deps.db = MagicMock()
    deps.state = AppState()
    
    controller = PlaybackController(deps)
    track = TrackInfo(video_id="v1", title="Test", artist="Artist", duration=0)
    controller.state.current_track = track
    
    # Simulate get_duration returning None
    controller.mpv.get_duration = AsyncMock(return_value=None)
    
    async def fake_sleep(delay):
        pass
        
    with patch('asyncio.sleep', new_callable=lambda: fake_sleep):
        await controller._poll_duration(track)
        
    # Since duration is None for both attempts, it should never publish QueueUpdatedEvent
    controller.bus.publish.assert_not_called()

import pytest
from unittest.mock import AsyncMock, MagicMock
from collections import deque
from engine.queue_manager import QueueMode
from core.state import PlayerStatus, TrackInfo

@pytest.mark.asyncio
async def test_queue_mode_next_empty():
    mode = QueueMode()
    controller = MagicMock()
    controller.state.queue = deque()
    controller.bus.publish = AsyncMock()
    
    await mode.next(controller)
    
    assert controller.state.status == PlayerStatus.IDLE
    assert controller.state.current_track is None
    controller.bus.publish.assert_called_once()

@pytest.mark.asyncio
async def test_queue_mode_next_with_items():
    mode = QueueMode()
    controller = MagicMock()
    track = TrackInfo(video_id="test", title="Test", artist="A", duration=10)
    controller.state.queue = deque([track])
    controller.play_track = AsyncMock()
    
    await mode.next(controller)
    
    controller.play_track.assert_called_once_with(track)
    assert len(controller.state.queue) == 0

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from engine.playback.controller import PlaybackController, PlaybackDependencies
from core.events import TrackEndedEvent
from core.state import AppState, PlaybackMode

@pytest.mark.asyncio
async def test_duplicate_eof_is_ignored():
    deps = MagicMock()
    deps.state = AppState()
    deps.state.playback_mode = PlaybackMode.QUEUE
    deps.queue_mode = AsyncMock()
    deps.radio_mode = AsyncMock()
    
    controller = PlaybackController(deps)
    controller._advance_to_next = AsyncMock()
    
    # Simulate two EOF events firing in parallel
    event = TrackEndedEvent(reason="eof")
    
    task1 = asyncio.create_task(controller._on_track_ended(event))
    task2 = asyncio.create_task(controller._on_track_ended(event))
    
    await asyncio.gather(task1, task2)
    
    # Advance to next should only be called ONCE
    controller._advance_to_next.assert_called_once()

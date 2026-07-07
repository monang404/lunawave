import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from engine.playback.controller import PlaybackController
from core.events import TrackEndedEvent
from core.state import AppState, PlayerStatus

@pytest.mark.asyncio
async def test_on_track_ended_error_guard():
    deps = MagicMock()
    deps.bus = MagicMock()
    deps.bus.publish = AsyncMock()
    deps.mpv = MagicMock()
    deps.db = MagicMock()
    deps.state = AppState()
    
    controller = PlaybackController(deps)
    controller.track_loader = MagicMock()
    controller._advance_to_next = AsyncMock()
    
    event = TrackEndedEvent(reason="error")
    
    async def fake_sleep(delay):
        # Simulate user intervening by changing state during sleep
        controller.state.status = PlayerStatus.LOADING
        
    with patch('asyncio.sleep', new_callable=lambda: fake_sleep):
        await controller._on_track_ended(event)
        
    # Since status became LOADING (!= ERROR), it should NOT advance to next
    controller._advance_to_next.assert_not_called()
    
    # Let's test when no one intervenes
    controller.state.status = PlayerStatus.ERROR
    controller._advance_to_next.reset_mock()
    
    async def fake_sleep_no_intervene(delay):
        pass
        
    with patch('asyncio.sleep', new_callable=lambda: fake_sleep_no_intervene):
        await controller._on_track_ended(event)
        
    # It should advance now
    controller._advance_to_next.assert_called_once()

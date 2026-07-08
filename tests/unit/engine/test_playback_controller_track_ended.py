from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.events import TrackEndedEvent
from core.state import AppState, PlaybackMode
from engine.playback.controller import PlaybackController


@pytest.mark.asyncio
async def test_on_track_ended_empty_reason_advances():
    deps = MagicMock()
    deps.bus = MagicMock()
    deps.mpv = MagicMock()
    deps.db = MagicMock()
    deps.state = AppState()
    deps.state.playback_mode = PlaybackMode.QUEUE

    controller = PlaybackController(deps)
    controller.state = deps.state
    controller._advance_to_next = AsyncMock()

    event = TrackEndedEvent(reason="")

    with patch('asyncio.sleep', new_callable=AsyncMock) as _sleep_mock:
        await controller._on_track_ended(event)

        # Should advance for empty reason
        controller._advance_to_next.assert_called_once()

        # Reset mock and test unhandled reason
        controller._advance_to_next.reset_mock()
        event_unhandled = TrackEndedEvent(reason="unknown_reason")
        await controller._on_track_ended(event_unhandled)

        # Should also advance for unknown reason
        controller._advance_to_next.assert_called_once()

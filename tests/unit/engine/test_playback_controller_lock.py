from unittest.mock import AsyncMock, MagicMock

import pytest

from core.events import TrackDurationEvent
from core.state import AppState
from engine.playback.controller import PlaybackController


@pytest.mark.asyncio
async def test_playback_controller_uses_lock_for_state_mutation():
    deps = MagicMock()
    deps.bus = MagicMock()
    deps.bus.publish = AsyncMock()
    deps.mpv = MagicMock()
    deps.db = MagicMock()
    deps.state = AppState()

    controller = PlaybackController(deps)

    # Track when the lock is acquired
    original_acquire = controller._lock.acquire
    acquire_called = False

    async def mock_acquire(*args, **kwargs):
        nonlocal acquire_called
        acquire_called = True
        return await original_acquire(*args, **kwargs)

    controller._lock.acquire = mock_acquire

    # Dispatch an event that mutates state
    event = TrackDurationEvent(duration=120.0)
    await controller._on_track_duration(event)

    assert acquire_called, "The lock was not acquired during state mutation!"
    assert controller.state.duration == 120.0

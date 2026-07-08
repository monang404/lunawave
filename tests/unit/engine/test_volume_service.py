import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.state import AppState
from engine.volume_service import VolumeService


@pytest.mark.asyncio
async def test_volume_service_race_condition():
    bus = MagicMock()
    bus.publish = AsyncMock()
    mpv = MagicMock()
    mpv.set_volume = AsyncMock()
    state = AppState()
    state.volume = 50

    service = VolumeService(bus, mpv, state)

    # We want to simulate two concurrent calls
    # Since they use async with self._lock, they should be serialized
    # and not read stale state.

    await asyncio.gather(
        service._on_volume_up(),
        service._on_volume_up(),
        service._on_volume_up()
    )

    # Since initial volume is 50, three volume ups (+5) should make it 65
    assert state.volume == 65

    await asyncio.gather(
        service._on_volume_down(),
        service._on_volume_down()
    )

    # Two volume downs (-5) from 65 should make it 55
    assert state.volume == 55

@pytest.mark.asyncio
async def test_volume_service_set_volume():
    bus = MagicMock()
    bus.publish = AsyncMock()
    mpv = MagicMock()
    mpv.set_volume = AsyncMock()
    state = AppState()
    state.volume = 50

    service = VolumeService(bus, mpv, state)

    cmd = MagicMock()
    cmd.volume = 75

    await service._on_volume_set(cmd)

    assert state.volume == 75

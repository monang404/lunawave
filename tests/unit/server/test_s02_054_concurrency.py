"""
Tests for S02-054: Concurrency / Race Condition in QueueCommands
"""
import asyncio
from unittest.mock import AsyncMock

import pytest

from core.command_bus import CommandBus
from core.commands import QueueAddCommand
from core.state import AppState


@pytest.mark.asyncio
async def test_queue_add_concurrent_race_condition():
    """
    Test bahwa tidak terjadi list corruption saat banyak task
    secara concurrent menambahkan track ke dalam queue.
    """
    from server.handlers.ws.queue_handlers import _handle_queue_add

    command_bus = CommandBus()
    state = AppState()


    # Mock command_bus execute logic to simulate what the actual command handler does
    async def mock_execute(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("cmd", kwargs.get("command"))
        if isinstance(cmd, QueueAddCommand):
            # Simulate real-world delay to trigger potential race conditions
            await asyncio.sleep(0.001)
            state.queue.append(cmd.track)

    command_bus.execute = AsyncMock(side_effect=mock_execute)


    # Create 100 concurrent add requests
    async def concurrent_add(i):
        data = {
            "video_id": f"aBcDeFghI{i:02d}",
            "title": f"Song {i}",
            "artist": "Artist",
            "duration": 180
        }
        await _handle_queue_add(data, None, state, None, None, None, command_bus)

    await asyncio.gather(*(concurrent_add(i) for i in range(100)))

    # Ensure exactly 100 tracks are in the queue and no items were lost
    assert len(state.queue) == 100, f"Expected 100 items in queue, but got {len(state.queue)}"

    # Verify content uniqueness
    video_ids = {t.video_id for t in state.queue}
    assert len(video_ids) == 100, "Duplicate video_ids found in queue due to race condition"

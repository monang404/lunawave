from collections import deque
from unittest.mock import AsyncMock, MagicMock

import pytest

from engine.playback.playback_commands import PlaybackCommands
from engine.playback.queue_commands import QueueCommands


@pytest.mark.asyncio
async def test_on_queue_remove_uses_lock():
    mock_lock = AsyncMock()
    mock_lock.__aenter__ = AsyncMock()
    mock_lock.__aexit__ = AsyncMock()

    mock_pc = MagicMock()
    mock_pc._lock = mock_lock
    mock_pc.state = MagicMock()
    mock_pc.state.queue = [MagicMock(title="Song A"), MagicMock(title="Song B")]
    mock_pc.bus = AsyncMock()

    cmd = MagicMock()
    cmd.index = 0

    qc = QueueCommands(mock_pc)

    await qc.on_queue_remove(cmd)

    mock_lock.__aenter__.assert_called_once()
    mock_lock.__aexit__.assert_called_once()
    assert len(mock_pc.state.queue) == 1
    assert mock_pc.bus.publish.call_count == 2


@pytest.mark.asyncio
async def test_on_queue_select_uses_lock():
    mock_lock = AsyncMock()
    mock_lock.__aenter__ = AsyncMock()
    mock_lock.__aexit__ = AsyncMock()

    mock_pc = AsyncMock()
    mock_pc._lock = mock_lock
    mock_pc.state.queue = [MagicMock(title="Song A"), MagicMock(title="Song B")]

    cmd = MagicMock()
    cmd.index = 1

    qc = QueueCommands(mock_pc)

    await qc.on_queue_select(cmd)

    mock_lock.__aenter__.assert_called_once()
    mock_lock.__aexit__.assert_called_once()
    mock_pc.play_track.assert_called_once()


@pytest.mark.asyncio
async def test_on_next_uses_lock():
    mock_lock = AsyncMock()
    mock_lock.__aenter__ = AsyncMock()
    mock_lock.__aexit__ = AsyncMock()

    mock_pc = AsyncMock()
    mock_pc._lock = mock_lock
    mock_pc.state = MagicMock()
    mock_pc.state.queue = [MagicMock(title="Next Song")]
    mock_pc.state.repeat_mode = "off"

    pc_cmds = PlaybackCommands(mock_pc)

    await pc_cmds.on_next(MagicMock())

    mock_lock.__aenter__.assert_called_once()
    mock_lock.__aexit__.assert_called_once()

import pytest
from unittest.mock import AsyncMock, MagicMock
from engine.playback.radio_commands import RadioCommands
from core.commands import RadioRandomizeCommand

@pytest.fixture
def mock_playback_controller():
    controller = MagicMock()
    controller.mpv = AsyncMock()
    controller.radio_mode = AsyncMock()
    controller.bus = AsyncMock()
    
    lock_mock = AsyncMock()
    lock_mock.__aenter__.return_value = None
    lock_mock.__aexit__.return_value = None
    controller._lock = lock_mock
    
    return controller

@pytest.mark.asyncio
async def test_radio_randomize_command(mock_playback_controller):
    commands = RadioCommands(mock_playback_controller)
    await commands.on_radio_randomize(RadioRandomizeCommand(seed_artist="test_vid"))
    
    assert mock_playback_controller.bus.publish.call_count == 2

from unittest.mock import AsyncMock, patch

import pytest

from core.command_bus import CMD_SET_MODE, CMD_TOGGLE_PAUSE
from core.state import PlaybackMode
from server.handlers.ws_playback import handle_playback_command


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
async def test_handle_playback_command_toggle_pause(mock_execute):
    await handle_playback_command("toggle_pause", {})
    mock_execute.assert_called_once_with(CMD_TOGGLE_PAUSE)


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
async def test_handle_playback_command_set_mode(mock_execute):
    await handle_playback_command("set_mode", {"mode": "radio"})
    mock_execute.assert_called_once_with(CMD_SET_MODE, PlaybackMode.RADIO)

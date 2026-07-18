from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.command_bus import (
    CMD_LYRICS_OFFSET,
    CMD_NEXT,
    CMD_PLAY_TRACK,
    CMD_PREV,
    CMD_RADIO_RANDOMIZE,
    CMD_SEEK,
    CMD_SET_LOUDNESS_NORMALIZATION,
    CMD_SET_MODE,
    CMD_SET_OUTPUT,
    CMD_SET_SPONSORBLOCK,
    CMD_STOP,
    CMD_TOGGLE_PAUSE,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_SET,
    CMD_VOLUME_UP,
)
from core.state import AudioOutput, PlaybackMode
from server.handlers.ws_playback import handle_playback_command
from server.serializers import dict_to_track


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


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
@patch("server.handlers.ws_playback.dict_to_track")
async def test_handle_playback_command_play_track(mock_dict_to_track, mock_execute):
    mock_track = MagicMock()
    mock_dict_to_track.return_value = mock_track
    await handle_playback_command("play_track", {"id": "123"})
    mock_execute.assert_called_once_with(CMD_PLAY_TRACK, mock_track)


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
@patch("server.handlers.ws_playback.dict_to_track", return_value=None)
async def test_handle_playback_command_play_track_invalid(mock_dict_to_track, mock_execute):
    await handle_playback_command("play_track", {})
    mock_execute.assert_not_called()


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
async def test_handle_playback_command_set_sponsorblock(mock_execute):
    await handle_playback_command("set_sponsorblock", {"enabled": False})
    mock_execute.assert_called_once_with(CMD_SET_SPONSORBLOCK, False)


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
async def test_handle_playback_command_set_loudness_normalization(mock_execute):
    await handle_playback_command("set_loudness_normalization", {"enabled": True})
    mock_execute.assert_called_once_with(CMD_SET_LOUDNESS_NORMALIZATION, True)


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
async def test_handle_playback_command_set_loudness_normalization_default_false(mock_execute):
    await handle_playback_command("set_loudness_normalization", {})
    mock_execute.assert_called_once_with(CMD_SET_LOUDNESS_NORMALIZATION, False)


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
async def test_handle_playback_command_lyrics_offset(mock_execute):
    await handle_playback_command("lyrics_offset", {"offset": -1.5})
    mock_execute.assert_called_once_with(CMD_LYRICS_OFFSET, {"offset": -1.5})


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
async def test_handle_playback_command_radio_randomize(mock_execute):
    await handle_playback_command("radio_randomize", {"seed_artist": "Coldplay"})
    mock_execute.assert_called_once_with(CMD_RADIO_RANDOMIZE, {"seed_artist": "Coldplay"})


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
async def test_handle_playback_command_set_output(mock_execute):
    await handle_playback_command("set_output", {"output": "browser"})
    mock_execute.assert_called_once_with(CMD_SET_OUTPUT, AudioOutput.BROWSER)


@pytest.mark.asyncio
@patch("server.handlers.ws_playback.command_bus.execute", new_callable=AsyncMock)
async def test_handle_playback_command_other_commands(mock_execute):
    await handle_playback_command("next", {"random": True})
    mock_execute.assert_called_once_with(CMD_NEXT, {"random": True})
    mock_execute.reset_mock()

    await handle_playback_command("prev", {})
    mock_execute.assert_called_once_with(CMD_PREV, {})
    mock_execute.reset_mock()

    await handle_playback_command("stop", {})
    mock_execute.assert_called_once_with(CMD_STOP)
    mock_execute.reset_mock()

    await handle_playback_command("seek", {"position": 12.5})
    mock_execute.assert_called_once_with(CMD_SEEK, 12.5)
    mock_execute.reset_mock()

    await handle_playback_command("volume_up", {})
    mock_execute.assert_called_once_with(CMD_VOLUME_UP)
    mock_execute.reset_mock()

    await handle_playback_command("volume_down", {})
    mock_execute.assert_called_once_with(CMD_VOLUME_DOWN)
    mock_execute.reset_mock()

    await handle_playback_command("volume_set", {"volume": 42})
    mock_execute.assert_called_once_with(CMD_VOLUME_SET, {"volume": 42})

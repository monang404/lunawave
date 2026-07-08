import pytest
from unittest.mock import AsyncMock, MagicMock
from engine.playback.settings_commands import SettingsCommands
from core.state import PlaybackMode, AudioOutput, PlayerStatus
from core.commands import SetModeCommand, SetOutputCommand, SetSponsorblockCommand, LyricsOffsetCommand

@pytest.fixture
def mock_playback_controller():
    controller = MagicMock()
    controller.state = MagicMock()
    controller.state.playback_mode = PlaybackMode.QUEUE
    controller.mpv = AsyncMock()
    controller.bus = AsyncMock()
    controller.radio_mode = AsyncMock()
    controller._lock = AsyncMock()
    # Mocking async lock context manager
    controller._lock.__aenter__.return_value = None
    controller._lock.__aexit__.return_value = None
    return controller

@pytest.mark.asyncio
async def test_set_mode_to_radio(mock_playback_controller):
    commands = SettingsCommands(mock_playback_controller)
    await commands.on_set_mode(SetModeCommand(mode=PlaybackMode.RADIO))
    assert mock_playback_controller.state.playback_mode == PlaybackMode.RADIO
    assert mock_playback_controller.state.status == PlayerStatus.LOADING
    mock_playback_controller.radio_mode.on_activated.assert_called_once_with(mock_playback_controller)
    mock_playback_controller.bus.publish.assert_called()

@pytest.mark.asyncio
async def test_set_mode_from_radio(mock_playback_controller):
    mock_playback_controller.state.playback_mode = PlaybackMode.RADIO
    commands = SettingsCommands(mock_playback_controller)
    await commands.on_set_mode(SetModeCommand(mode=PlaybackMode.QUEUE))
    
    assert mock_playback_controller.state.playback_mode == PlaybackMode.QUEUE
    assert mock_playback_controller.state.current_track is None
    assert mock_playback_controller.state.status == PlayerStatus.IDLE
    mock_playback_controller.radio_mode.on_deactivated.assert_called_once()
    mock_playback_controller.mpv.pause.assert_called_once()
    mock_playback_controller.bus.publish.assert_called()

@pytest.mark.asyncio
async def test_set_output_browser(mock_playback_controller):
    commands = SettingsCommands(mock_playback_controller)
    await commands.on_set_output(SetOutputCommand(output=AudioOutput.BROWSER))
    assert mock_playback_controller.state.audio_output == AudioOutput.BROWSER
    mock_playback_controller.mpv.set_volume.assert_called_once_with(0)

@pytest.mark.asyncio
async def test_set_output_server(mock_playback_controller):
    commands = SettingsCommands(mock_playback_controller)
    mock_playback_controller.state.volume = 80
    await commands.on_set_output(SetOutputCommand(output=AudioOutput.DEVICE))
    assert mock_playback_controller.state.audio_output == AudioOutput.DEVICE
    mock_playback_controller.mpv.set_volume.assert_called_once_with(80)

@pytest.mark.asyncio
async def test_set_sponsorblock(mock_playback_controller):
    commands = SettingsCommands(mock_playback_controller)
    await commands.on_set_sponsorblock(SetSponsorblockCommand(enabled=True))
    assert mock_playback_controller.state.sponsorblock_active is True
    mock_playback_controller.bus.publish.assert_called()

@pytest.mark.asyncio
async def test_lyrics_offset(mock_playback_controller):
    commands = SettingsCommands(mock_playback_controller)
    await commands.on_lyrics_offset(LyricsOffsetCommand(offset=5.5))
    assert mock_playback_controller.state.lyrics_offset == 5.5
    mock_playback_controller.bus.publish.assert_called()

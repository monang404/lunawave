import pytest
from unittest.mock import MagicMock
from engine.command_router import CommandRouter

@pytest.fixture
def mock_playback_controller():
    controller = MagicMock()
    return controller

@pytest.fixture
def mock_deps(mock_playback_controller):
    command_bus = MagicMock()
    playback_commands = MagicMock()
    queue_commands = MagicMock()
    settings_commands = MagicMock()
    radio_commands = MagicMock()
    volume_service = MagicMock()
    return command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service

def test_command_router_registration(mock_deps):
    command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service = mock_deps
    router = CommandRouter(command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service)
    # Just instantiating it registers all commands
    assert command_bus.register.call_count > 10

def test_command_router_playback_commands_registered(mock_deps):
    command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service = mock_deps
    router = CommandRouter(command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service)
    # Check if specific commands are registered
    registered_commands = [call.args[0].__name__ for call in command_bus.register.mock_calls]
    
    assert "PlayTrackCommand" in registered_commands
    assert "TogglePauseCommand" in registered_commands
    assert "NextCommand" in registered_commands
    assert "PrevCommand" in registered_commands
    assert "SeekCommand" in registered_commands

def test_command_router_queue_commands_registered(mock_deps):
    command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service = mock_deps
    router = CommandRouter(command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service)
    registered_commands = [call.args[0].__name__ for call in command_bus.register.mock_calls]
    
    assert "QueueAddCommand" in registered_commands
    assert "QueueRemoveCommand" in registered_commands
    assert "QueueReorderCommand" in registered_commands
    assert "QueueSelectCommand" in registered_commands
    assert "QueueReplaceCommand" in registered_commands

def test_command_router_settings_commands_registered(mock_deps):
    command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service = mock_deps
    router = CommandRouter(command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service)
    registered_commands = [call.args[0].__name__ for call in command_bus.register.mock_calls]
    
    assert "SetModeCommand" in registered_commands
    assert "SetOutputCommand" in registered_commands
    assert "SetSponsorblockCommand" in registered_commands
    assert "VolumeUpCommand" in registered_commands
    assert "VolumeDownCommand" in registered_commands
    assert "VolumeSetCommand" in registered_commands
    assert "LyricsOffsetCommand" in registered_commands

def test_command_router_radio_commands_registered(mock_deps):
    command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service = mock_deps
    router = CommandRouter(command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service)
    registered_commands = [call.args[0].__name__ for call in command_bus.register.mock_calls]
    
    assert "RadioRandomizeCommand" in registered_commands

from server.handlers.ws.registry import register_ws_handler
from core.commands import (
    VolumeUpCommand, VolumeDownCommand, VolumeSetCommand, SetOutputCommand, SetSponsorblockCommand, LyricsOffsetCommand, SetModeCommand
)
from core.state import AudioOutput, PlaybackMode
from core.constants import DEFAULT_VOLUME, DEFAULT_PLAYBACK_MODE, DEFAULT_AUDIO_OUTPUT
from core.ws_actions import WSAction

@register_ws_handler(WSAction.VOLUME_UP)
async def _handle_volume_up(data, ws, state, ytdlp, manager, db, command_bus):
    await command_bus.execute(VolumeUpCommand())

@register_ws_handler(WSAction.VOLUME_DOWN)
async def _handle_volume_down(data, ws, state, ytdlp, manager, db, command_bus):
    await command_bus.execute(VolumeDownCommand())

@register_ws_handler("volume_set")
async def _handle_volume_set(data, ws, state, ytdlp, manager, db, command_bus):
    try:
        vol = max(0, min(150, int(data.get("volume", DEFAULT_VOLUME))))
        await command_bus.execute(VolumeSetCommand(volume=vol))
    except (ValueError, TypeError):
        pass

@register_ws_handler("set_mode")
async def _handle_set_mode(data, ws, state, ytdlp, manager, db, command_bus):
    mode_str = data.get("mode", DEFAULT_PLAYBACK_MODE).upper()
    mode = PlaybackMode.RADIO if mode_str == "RADIO" else PlaybackMode.QUEUE
    await command_bus.execute(SetModeCommand(mode=mode))

@register_ws_handler("set_output")
async def _handle_set_output(data, ws, state, ytdlp, manager, db, command_bus):
    output_str = data.get("output", DEFAULT_AUDIO_OUTPUT)
    output_val = AudioOutput.BROWSER if output_str == "browser" else AudioOutput.DEVICE
    await command_bus.execute(SetOutputCommand(output=output_val))

@register_ws_handler(WSAction.SET_SPONSORBLOCK)
async def _handle_set_sponsorblock(data, ws, state, ytdlp, manager, db, command_bus):
    enabled = data.get("enabled", True)
    await command_bus.execute(SetSponsorblockCommand(enabled=bool(enabled)))

@register_ws_handler(WSAction.LYRICS_OFFSET)
async def _handle_lyrics_offset(data, ws, state, ytdlp, manager, db, command_bus):
    try:
        offset = float(data.get("offset", 0.0))
        await command_bus.execute(LyricsOffsetCommand(offset=offset))
    except (ValueError, TypeError):
        pass

from server.handlers.ws.registry import register_ws_handler
from core.ws_actions import WSAction
from core.commands import (
    PlayTrackCommand, TogglePauseCommand, NextCommand, PrevCommand, StopCommand, SeekCommand
)
from core.state import TrackInfo

@register_ws_handler(WSAction.PLAY_TRACK)
async def _handle_play_track(data, ws, state, ytdlp, manager, db, command_bus):
    track = TrackInfo.from_dict(data)
    if track:
        await command_bus.execute(PlayTrackCommand(track=track))

@register_ws_handler(WSAction.TOGGLE_PAUSE)
async def _handle_toggle_pause(data, ws, state, ytdlp, manager, db, command_bus):
    await command_bus.execute(TogglePauseCommand())

@register_ws_handler(WSAction.NEXT)
async def _handle_next(data, ws, state, ytdlp, manager, db, command_bus):
    video_id = data.get("video_id") if isinstance(data, dict) else None
    await command_bus.execute(NextCommand(video_id=video_id))

@register_ws_handler(WSAction.PREV)
async def _handle_prev(data, ws, state, ytdlp, manager, db, command_bus):
    await command_bus.execute(PrevCommand())

@register_ws_handler(WSAction.STOP)
async def _handle_stop(data, ws, state, ytdlp, manager, db, command_bus):
    await command_bus.execute(StopCommand())

@register_ws_handler(WSAction.SEEK)
async def _handle_seek(data, ws, state, ytdlp, manager, db, command_bus):
    try:
        position = max(0.0, float(data.get("position", 0)))
        await command_bus.execute(SeekCommand(position=position))
    except (ValueError, TypeError):
        pass

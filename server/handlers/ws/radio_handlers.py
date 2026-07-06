from server.handlers.ws.registry import register_ws_handler
from core.commands import RadioRandomizeCommand
from core.ws_actions import WSAction

@register_ws_handler(WSAction.RADIO_RANDOMIZE)
async def _handle_radio_randomize(data, ws, state, ytdlp, manager, db, command_bus):
    seed_artist = data.get("seed_artist") if isinstance(data, dict) else None
    await command_bus.execute(RadioRandomizeCommand(seed_artist=seed_artist))

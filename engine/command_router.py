import structlog

from core.commands import (
    LyricsOffsetCommand,
    NextCommand,
    PlayTrackCommand,
    PrevCommand,
    QueueAddCommand,
    QueueRemoveCommand,
    QueueReorderCommand,
    QueueReplaceCommand,
    QueueSelectCommand,
    RadioRandomizeCommand,
    SeekCommand,
    SetModeCommand,
    SetOutputCommand,
    SetSponsorblockCommand,
    StopCommand,
    TogglePauseCommand,
    VolumeDownCommand,
    VolumeSetCommand,
    VolumeUpCommand,
)

logger = structlog.get_logger(__name__)

class CommandRouter:
    """
    Rutes Global CommandBus requests ke RoomPlaybackController yang sesuai.
    """
    def __init__(self, command_bus, playback_commands, queue_commands, settings_commands, radio_commands, volume_service):
        self.command_bus = command_bus
        self.playback_commands = playback_commands
        self.queue_commands = queue_commands
        self.settings_commands = settings_commands
        self.radio_commands = radio_commands
        self.volume_service = volume_service

        self.command_bus.register(PlayTrackCommand, self._route(self.playback_commands.on_play_track))
        self.command_bus.register(TogglePauseCommand, self._route(self.playback_commands.on_toggle_pause))
        self.command_bus.register(NextCommand, self._route(self.playback_commands.on_next))
        self.command_bus.register(PrevCommand, self._route(self.playback_commands.on_prev))
        self.command_bus.register(StopCommand, self._route(self.playback_commands.on_stop))
        self.command_bus.register(SeekCommand, self._route(self.playback_commands.on_seek))

        self.command_bus.register(SetModeCommand, self._route(self.settings_commands.on_set_mode))
        self.command_bus.register(SetOutputCommand, self._route(self.settings_commands.on_set_output))
        self.command_bus.register(SetSponsorblockCommand, self._route(self.settings_commands.on_set_sponsorblock))
        self.command_bus.register(LyricsOffsetCommand, self._route(self.settings_commands.on_lyrics_offset))

        self.command_bus.register(QueueSelectCommand, self._route(self.queue_commands.on_queue_select))
        self.command_bus.register(QueueRemoveCommand, self._route(self.queue_commands.on_queue_remove))
        self.command_bus.register(QueueAddCommand, self._route(self.queue_commands.on_queue_add))
        self.command_bus.register(QueueReplaceCommand, self._route(self.queue_commands.on_queue_replace))
        self.command_bus.register(QueueReorderCommand, self._route(self.queue_commands.on_queue_reorder))

        self.command_bus.register(RadioRandomizeCommand, self._route(self.radio_commands.on_radio_randomize))

        self.command_bus.register(VolumeUpCommand, self._route(self.volume_service._on_volume_up))
        self.command_bus.register(VolumeDownCommand, self._route(self.volume_service._on_volume_down))
        self.command_bus.register(VolumeSetCommand, self._route(self.volume_service._on_volume_set))

    def _route(self, action):
        async def handler(command):
            import asyncio
            import inspect
            sig = inspect.signature(action)

            if len(sig.parameters) > 0:
                res = action(command)
            else:
                res = action()

            if asyncio.iscoroutine(res):
                return await res
            return res
        return handler

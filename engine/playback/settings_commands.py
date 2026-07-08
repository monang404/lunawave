import structlog

from core.events import LogMessageEvent, QueueUpdatedEvent
from core.log_config import STATS as _LOG_STATS
from core.state import AudioOutput, PlaybackMode, PlayerStatus

logger = structlog.get_logger(__name__)

class SettingsCommands:
    def __init__(self, playback_controller):
        self.playback_controller = playback_controller
        self.state = playback_controller.state
        self.mpv = playback_controller.mpv
        self.bus = playback_controller.bus
        self.radio_mode = playback_controller.radio_mode

    async def on_set_mode(self, cmd):
        should_activate_radio = False
        async with self.playback_controller._lock:
            if self.state.playback_mode != cmd.mode:
                previous_mode = self.state.playback_mode
                self.state.playback_mode = cmd.mode

                if previous_mode == PlaybackMode.RADIO:
                    await self.radio_mode.on_deactivated()
                    await self.mpv.pause()
                    self.state.current_track = None
                    self.state.status = PlayerStatus.IDLE
                    self.playback_controller._retry_count = 0
                    _LOG_STATS.is_playing = False

                if cmd.mode == PlaybackMode.RADIO:
                    self.state.status = PlayerStatus.LOADING
                    self.playback_controller._retry_count = 0
                    should_activate_radio = True

                await self.bus.publish(LogMessageEvent(message=f"Mode diubah ke {cmd.mode.name}"))
                await self.bus.publish(QueueUpdatedEvent())

        if should_activate_radio:
            await self.radio_mode.on_activated(self.playback_controller)

    async def on_set_output(self, cmd):
        self.state.audio_output = cmd.output
        if cmd.output == AudioOutput.BROWSER:
            await self.mpv.set_volume(0)
        else:
            await self.mpv.set_volume(self.state.volume)
        await self.bus.publish(LogMessageEvent(message=f"Output suara diubah ke: {'Browser' if cmd.output == AudioOutput.BROWSER else 'HP'}"))
        await self.bus.publish(QueueUpdatedEvent())

    async def on_set_sponsorblock(self, cmd):
        self.state.sponsorblock_active = cmd.enabled
        await self.bus.publish(LogMessageEvent(message=f"SponsorBlock: {'ON' if cmd.enabled else 'OFF'}"))
        await self.bus.publish(QueueUpdatedEvent())

    async def on_lyrics_offset(self, cmd):
        self.state.lyrics_offset = float(cmd.offset)
        from core.events import LyricsUpdatedEvent
        await self.bus.publish(LyricsUpdatedEvent())

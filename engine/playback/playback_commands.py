import structlog
from core.state import PlayerStatus, PlaybackMode
from core.events import LogMessageEvent, QueueUpdatedEvent
from core.log_config import STATS as _LOG_STATS

logger = structlog.get_logger(__name__)

class PlaybackCommands:
    def __init__(self, playback_controller):
        self.playback_controller = playback_controller
        self.state = playback_controller.state
        self.mpv = playback_controller.mpv
        self.bus = playback_controller.bus
        self.queue_mode = playback_controller.queue_mode
        self.radio_mode = playback_controller.radio_mode

    async def on_play_track(self, cmd):
        async with self.playback_controller._lock:
            if self.state.playback_mode == PlaybackMode.RADIO:
                await self.radio_mode.on_deactivated()
                self.state.playback_mode = PlaybackMode.QUEUE
                await self.bus.publish(QueueUpdatedEvent())
            await self.playback_controller.play_track(cmd.track)

    async def on_toggle_pause(self, cmd=None):
        if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED):
            await self.mpv.toggle_pause()

    async def on_next(self, cmd=None):
        async with self.playback_controller._lock:
            if cmd and getattr(cmd, "video_id", None):
                if not self.state.current_track or self.state.current_track.video_id != cmd.video_id:
                    logger.info(f"Ignoring skip: requested {cmd.video_id} != current {getattr(self.state.current_track, 'video_id', None)}")
                    return
            await self.playback_controller._advance_to_next()

    async def on_prev(self, cmd=None):
        async with self.playback_controller._lock:
            if self.state.history:
                track = self.state.history.pop()
                self.state.current_track = None
                await self.playback_controller.play_track(track)
            else:
                await self.bus.publish(LogMessageEvent(message="Tidak ada lagu sebelumnya"))

    async def on_stop(self, cmd=None):
        self.playback_controller._retry_count = 0
        try:
            await self.mpv.pause()
        except Exception as e:
            logger.warning(f"mpv.pause() gagal saat stop: {e}")
        self.state.status = PlayerStatus.IDLE
        _LOG_STATS.is_playing = False
        self.state.current_track = None
        self.state.queue.clear()
        self.state.radio_queue.clear()
        self.state.position = 0.0
        self.state.lyrics_lines = []
        self.state.lyrics_index = 0
        await self.bus.publish(LogMessageEvent(message="Pemutaran dihentikan"))
        await self.bus.publish(QueueUpdatedEvent())

    async def on_seek(self, cmd):
        if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED):
            await self.mpv.seek(cmd.position)
            self.state.position = cmd.position

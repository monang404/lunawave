import structlog

from core.events import LogMessageEvent, QueueUpdatedEvent
from core.state import PlaybackMode, PlayerStatus
from core.task_utils import safe_create_task

logger = structlog.get_logger(__name__)

class RadioCommands:
    def __init__(self, playback_controller):
        self.playback_controller = playback_controller
        self.state = playback_controller.state
        self.mpv = playback_controller.mpv
        self.bus = playback_controller.bus
        self.radio_mode = playback_controller.radio_mode

    async def on_radio_randomize(self, cmd):
        seed = None
        async with self.playback_controller._lock:
            seed = cmd.seed_artist if cmd else None
            # S02-044: Izinkan dari mode QUEUE juga — otomatis switch ke RADIO dulu
            if self.state.playback_mode != PlaybackMode.RADIO:
                self.state.playback_mode = PlaybackMode.RADIO
                logger.info("RadioRandomize: auto-switch ke RADIO mode")

            self.state.radio_queue.clear()
            await self.mpv.pause()
            self.state.current_track = None
            self.state.status = PlayerStatus.LOADING
            self.state.position = 0.0
            self.radio_mode._artist_rotation = []
            await self.bus.publish(QueueUpdatedEvent())
            await self.bus.publish(LogMessageEvent(message="Mengacak ulang stasiun radio..."))

        safe_create_task(
            self.radio_mode._fetch_and_play_initial(self.playback_controller, seed_artist=seed),
            name="radio_randomize_fetch"
        )


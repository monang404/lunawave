"""
Purpose: Mengelola kontrol volume MPV.
Subscribes to: CMD_VOLUME_UP, CMD_VOLUME_DOWN
Publishes: LOG_MESSAGE
"""

import asyncio

from core.event_bus import EventBus
from core.events import LogMessageEvent
from core.ports import AudioPlayerPort
from core.state import AppState, AudioOutput
from core.value_objects import Volume


class VolumeService:
    def __init__(self, bus: EventBus, mpv: AudioPlayerPort, state: AppState):
        self.bus = bus
        self.mpv = mpv
        self.state = state
        self._lock = asyncio.Lock()

    async def _on_volume_up(self, cmd=None):
        async with self._lock:
            from core.constants import MAX_VOLUME
            new_vol = min(MAX_VOLUME, self.state.volume + 5)
            await self._apply_volume(new_vol)

    async def _on_volume_down(self, cmd=None):
        async with self._lock:
            new_vol = max(0, self.state.volume - 5)
            await self._apply_volume(new_vol)

    async def _on_volume_set(self, cmd):
        try:
            vol = Volume(getattr(cmd, "volume", 80))
        except (ValueError, TypeError):
            return

        async with self._lock:
            await self._apply_volume(vol)

    async def _apply_volume(self, new_vol: int):
        self.state.volume = new_vol
        if getattr(self.state, "audio_output", AudioOutput.DEVICE) == AudioOutput.BROWSER:
            await self.mpv.set_volume(0)
        else:
            await self.mpv.set_volume(new_vol)
        from core.events import QueueUpdatedEvent
        await self.bus.publish(QueueUpdatedEvent())
        await self.bus.publish(LogMessageEvent(message=f"Volume: {new_vol}%"))

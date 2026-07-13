"""
Module: engine.playback.mode_ops

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
from core.events import QueueUpdatedEvent, LogMessageEvent
from core.state import AppState, PlayerStatus, PlaybackMode, AudioOutput
from core.ports import AudioPlayerPort
from engine.radio import RadioMode

class ModeOps:
    """
    Operasi konfigurasi mode, output, dan sponsorblock.
    Dipanggil oleh PlaybackController.
    """
    def __init__(self, state: AppState, bus, lock: asyncio.Lock, mpv: AudioPlayerPort, radio_mode: RadioMode):
        self.state = state
        self.bus = bus
        self._lock = lock
        self.mpv = mpv
        self.radio_mode = radio_mode

    async def set_mode(self, mode: PlaybackMode) -> bool:
        """Mengatur mode playback. Mengembalikan True jika radio mode harus diaktifkan."""
        should_activate_radio = False
        async with self._lock:
            if self.state.playback_mode != mode:
                previous_mode = self.state.playback_mode
                self.state.playback_mode = mode

                if previous_mode == PlaybackMode.RADIO:
                    await self.radio_mode.on_deactivated()
                    await self.mpv.pause()
                    self.state.current_track = None
                    self.state.status = PlayerStatus.IDLE

                if mode == PlaybackMode.RADIO:
                    self.state.status = PlayerStatus.LOADING
                    should_activate_radio = True

                await self.bus.publish(LogMessageEvent(message=f"Mode diubah ke {mode.name}"))
                await self.bus.publish(QueueUpdatedEvent())

        return should_activate_radio

    async def randomize_radio(self, data: dict | None) -> tuple[bool, str | None]:
        """Mengacak ulang radio. Mengembalikan tuple (should_fetch, seed_artist)."""
        seed = None
        should_fetch = False
        async with self._lock:
            if self.state.playback_mode == PlaybackMode.RADIO:
                seed = data.get("seed_artist") if data else None
                self.state.radio_queue.clear()
                await self.mpv.pause()
                self.state.current_track = None
                self.state.status = PlayerStatus.LOADING
                self.state.position = 0.0
                if hasattr(self.radio_mode, 'artist_selector'):
                    self.radio_mode.artist_selector.reset_rotation()
                else:
                    self.radio_mode._artist_rotation = []
                await self.bus.publish(QueueUpdatedEvent())
                await self.bus.publish(LogMessageEvent(message="Mengacak ulang stasiun radio..."))
                should_fetch = True
            else:
                await self.bus.publish(LogMessageEvent(message="Radio tidak aktif"))

        return should_fetch, seed

    async def set_output(self, output: AudioOutput):
        self.state.audio_output = output
        if output == AudioOutput.BROWSER:
            await self.mpv.set_volume(0)
        else:
            await self.mpv.set_volume(self.state.volume)
        msg = "Browser" if output == AudioOutput.BROWSER else "HP"
        await self.bus.publish(LogMessageEvent(message=f"Output suara diubah ke: {msg}"))
        await self.bus.publish(QueueUpdatedEvent())

    async def toggle_sponsorblock(self, enabled: bool):
        self.state.sponsorblock_active = enabled
        status_msg = "ON" if enabled else "OFF"
        await self.bus.publish(LogMessageEvent(message=f"SponsorBlock: {status_msg}"))
        await self.bus.publish(QueueUpdatedEvent())

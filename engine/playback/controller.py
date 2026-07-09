
"""
Purpose: Central controller for playback orchestration.
Subscribes to: TRACK_ENDED, TRACK_PROGRESS, "track.pause.changed"
Publishes: TRACK_STARTED, LOG_MESSAGE, QUEUE_UPDATED
"""

import asyncio

import structlog

from cache.resolver import CacheResolver
from core.event_bus import EventBus
from core.events import (
    LogMessageEvent,
    MpvReconnectedEvent,
    QueueUpdatedEvent,
    TrackDurationEvent,
    TrackEndedEvent,
    TrackPauseChangedEvent,
    TrackProgressEvent,
    TrackStartedEvent,
)
from core.ports import AudioPlayerPort, DatabasePort, LyricsProvider, SponsorBlockProvider
from core.state import AppState, AudioOutput, PlaybackMode, PlayerStatus, TrackInfo
from core.task_utils import safe_create_task
from engine.playback.track_loader import TrackLoader
from engine.queue_manager import QueueMode
from engine.radio_engine import RadioMode

logger = structlog.get_logger(__name__)
from dataclasses import dataclass



@dataclass
class PlaybackDependencies:
    bus: EventBus
    state: AppState
    mpv: AudioPlayerPort
    resolver: CacheResolver
    sponsorblock: SponsorBlockProvider
    lyrics_fetcher: LyricsProvider
    queue_mode: QueueMode
    radio_mode: RadioMode
    db: DatabasePort

class PlaybackController:
    def __init__(self, deps: PlaybackDependencies):
        self.bus = deps.bus
        self.state = deps.state
        self.mpv = deps.mpv
        self.resolver = deps.resolver
        self.queue_mode = deps.queue_mode
        self.radio_mode = deps.radio_mode
        self.db = deps.db
        self.track_loader = TrackLoader(deps.resolver, deps.sponsorblock, deps.lyrics_fetcher, deps.db)

        self._lock = asyncio.Lock()
        self._play_lock = asyncio.Lock()  # A-05: proteksi race condition di play_track
        self._retry_count = 0
        self._eof_advancing = False  # S02-023: guard agar EOF tidak memicu advance ganda
        self._last_persistent_dict_hash = None

        self.bus.subscribe(TrackEndedEvent, self._on_track_ended)
        self.bus.subscribe(TrackProgressEvent, self._on_track_progress)
        self.bus.subscribe(TrackPauseChangedEvent, self._on_pause_changed)
        self.bus.subscribe(TrackDurationEvent, self._on_track_duration)
        self.bus.subscribe(MpvReconnectedEvent, self._on_mpv_reconnected)
        
        self._persist_state_task = safe_create_task(self._persist_state_loop(), name="persist_state_loop")

    async def _persist_state_loop(self):
        import json
        import hashlib
        from config import BASE_DIR
        path = BASE_DIR / "data" / "state.json"
        while True:
            try:
                await asyncio.sleep(5)
                current_dict = self.state.to_persistent_dict()
                current_hash = hashlib.md5(json.dumps(current_dict, sort_keys=True).encode()).hexdigest()
                if current_hash != self._last_persistent_dict_hash:
                    await self.state.save_to_disk(path)
                    self._last_persistent_dict_hash = current_hash
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in _persist_state_loop: {e}")

    async def _on_mpv_reconnected(self, event: MpvReconnectedEvent):
        if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED, PlayerStatus.LOADING) and self.state.current_track:
            logger.info("MPV reconnected, restoring playback state...")
            try:
                uri = await self.resolver.resolve(self.state.current_track)
                await self.mpv.play(uri)
                await self.mpv.seek(self.state.position)
                if getattr(self.state, "audio_output", AudioOutput.DEVICE) == AudioOutput.BROWSER:
                    await self.mpv.set_volume(0)
                else:
                    await self.mpv.set_volume(self.state.volume)

                if self.state.status == PlayerStatus.PLAYING:
                    await self.mpv.resume()
                else:
                    await self.mpv.pause()
            except Exception as e:
                logger.error(f"Failed to restore playback after MPV reconnect: {e}")

    async def _on_track_duration(self, event: TrackDurationEvent):
        if event.duration and event.duration > 0:
            async with self._lock:
                if abs(self.state.duration - event.duration) >= 1.0:
                    self.state.duration = event.duration
                    if self.state.current_track:
                        self.state.current_track.duration = int(event.duration)
                        safe_create_task(self.db.upsert_track(self.state.current_track), name="upsert_track_duration")
                    await self.bus.publish(QueueUpdatedEvent())

    async def play_track(self, track: TrackInfo):
        should_retry = False
        current_retry_count = 0
        async with self._play_lock:  # A-05: cegah concurrent play_track race
            if self.state.current_track:
                self.state.history.append(self.state.current_track)

            self.state.current_track = track
            self.state.status = PlayerStatus.LOADING
            self.state.position = 0.0
            self.state.duration = float(track.duration)
            self.state.lyrics_lines = []
            self.state.lyrics_index = 0

            try:
                uri = await self.track_loader.load_track(track)

                await self.mpv.play(uri)

                if getattr(self.state, "audio_output", AudioOutput.DEVICE) == AudioOutput.BROWSER:
                    await self.mpv.set_volume(0)
                    await self.bus.publish(LogMessageEvent(message="Audio output is browser, mpv silent (volume=0)."))
                else:
                    await self.mpv.set_volume(self.state.volume)

                await self.mpv.resume()

                self.state.status = PlayerStatus.PLAYING
                self._retry_count = 0
                await self.bus.publish(TrackStartedEvent(track=track))

                if self.state.duration == 0:
                    safe_create_task(self._poll_duration(track), name="poll_duration")

            except Exception as e:
                logger.error(f"Failed to play track {track.title}: {e}", exc_info=True)
                self.state.status = PlayerStatus.ERROR
                self.state.error_msg = f"Error: {e}"
                await self.bus.publish(LogMessageEvent(message=f"Gagal memutar lagu: {track.title} | {type(e).__name__}: {str(e)}"))

                self._retry_count += 1
                if self._retry_count >= 3:
                    await self.bus.publish(LogMessageEvent(message="Terlalu banyak kegagalan beruntun. Pemutaran dihentikan."))
                    self._retry_count = 0
                else:
                    should_retry = True
                    current_retry_count = self._retry_count

        if should_retry:
            backoff = 2 ** current_retry_count
            await asyncio.sleep(backoff)
            if self.state.current_track == track:
                await self._advance_to_next()

    async def _poll_duration(self, track: TrackInfo):
        await asyncio.sleep(2)
        if self.state.current_track != track:
            return
        dur = await self.mpv.get_duration()
        if dur is not None and dur > 0:
            async with self._lock:
                self.state.duration = dur
                track.duration = int(dur)
                if track:
                    safe_create_task(self.db.upsert_track(track), name="upsert_track_duration_poll")
            await self.bus.publish(QueueUpdatedEvent())
        else:
            await asyncio.sleep(5)
            if self.state.current_track == track:
                dur = await self.mpv.get_duration()
                if dur is not None and dur > 0:
                    async with self._lock:
                        self.state.duration = dur
                        track.duration = int(dur)
                        if track:
                            safe_create_task(self.db.upsert_track(track), name="upsert_track_duration_poll")
                    await self.bus.publish(QueueUpdatedEvent())

    async def _on_track_ended(self, event: TrackEndedEvent):
        reason = event.reason
        logger.info(f"[AUTOPLAY] Track ended with reason: {reason}")


        if reason in ("eof", ""):
            if getattr(self, "_eof_advancing", False):
                logger.debug("Mencegah pemanggilan ganda _advance_to_next akibat eof paralel")
                return
            self._eof_advancing = True
            try:
                await asyncio.sleep(0.35)
                await self._advance_to_next()
            finally:
                self._eof_advancing = False
        elif reason == "stop":
            pass
        elif reason == "error":
            async with self._lock:
                self.state.status = PlayerStatus.ERROR
            await self.bus.publish(LogMessageEvent(message="Terjadi kesalahan pemutaran"))
            await asyncio.sleep(2)
            async with self._lock:
                if self.state.status != PlayerStatus.ERROR:
                    return
            await self._advance_to_next()
        else:
            logger.warning(f"Unhandled TrackEndedEvent reason: {reason!r}, advancing to next track")
            await asyncio.sleep(0.35)
            await self._advance_to_next()

    async def _advance_to_next(self):
        if self.state.playback_mode == PlaybackMode.QUEUE:
            await self.queue_mode.next(self)
        else:
            await self.radio_mode.next(self)

    async def _on_track_progress(self, event: TrackProgressEvent):
        async with self._lock:
            self.state.position = event.position
        if self.state.playback_mode == PlaybackMode.RADIO:
            self.radio_mode.check_prefetch(self, self.state.position, self.state.duration)

    async def _on_pause_changed(self, event: TrackPauseChangedEvent):
        async with self._lock:
            if event.is_paused:
                if self.state.status == PlayerStatus.PLAYING:
                    self.state.status = PlayerStatus.PAUSED
            else:
                if self.state.status == PlayerStatus.PAUSED:
                    self.state.status = PlayerStatus.PLAYING

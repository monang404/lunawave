"""
Module: engine.playback.controller

Purpose:
    Orchestrate all playback logic: track loading, queue/radio advancement,
    pause/seek, and mode switching via CommandBus commands.

Responsibilities:
    - Handle CMD_PLAY_TRACK, CMD_NEXT, CMD_PREV, CMD_STOP, CMD_SEEK, and
      mode/queue/lyrics commands.
    - Delegate queue advancement to QueueMode or RadioMode.

Depends on:
    - core.event_bus, core.events, core.ports, core.state, core.task_utils,
      engine.playback.mode_ops, engine.playback.queue_ops,
      engine.playback.track_loader, engine.queue_manager, engine.radio_engine

Subscribes to:
    TrackEndedEvent, TrackProgressEvent, TrackPauseChangedEvent,
    TrackDurationEvent

Publishes:
    TrackStartedEvent, QueueUpdatedEvent, LogMessageEvent

Thread Safety:
    Worker thread (async; _lock and _play_lock guard concurrent access).
"""

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.loudness.service import LoudnessService

import structlog

from core.event_bus import EventBus
from core.events import (
    LogMessageEvent,
    QueueUpdatedEvent,
    TrackDurationEvent,
    TrackEndedEvent,
    TrackPauseChangedEvent,
    TrackProgressEvent,
    TrackStartedEvent,
)
from core.ports import AudioPlayerPort, LyricsProvider, SponsorBlockProvider, StreamResolverPort
from core.state import AppState, AudioOutput, PlaybackMode, PlayerStatus, TrackInfo
from core.task_utils import safe_create_task
from engine.playback.mode_ops import ModeOps
from engine.playback.queue_ops import QueueOps
from engine.playback.track_ended_ops import TrackEndedOps, poll_duration
from engine.playback.track_loader import TrackLoader
from engine.queue_manager import QueueMode
from engine.radio_engine import RadioMode

logger = structlog.get_logger(__name__)


class PlaybackController:
    def __init__(
        self,
        bus: EventBus,
        state: AppState,
        mpv: AudioPlayerPort,
        resolver: StreamResolverPort,
        sponsorblock: SponsorBlockProvider,
        lyrics_fetcher: LyricsProvider,
        queue_mode: QueueMode,
        radio_mode: RadioMode,
        loudness_service: "LoudnessService | None" = None,
    ):
        self.bus = bus
        self.state = state
        self.mpv = mpv
        self.resolver = resolver
        self.queue_mode = queue_mode
        self.radio_mode = radio_mode
        self.track_loader = TrackLoader(
            resolver, sponsorblock, lyrics_fetcher, loudness_service, state
        )

        self._lock = asyncio.Lock()
        self._play_lock = asyncio.Lock()
        self._queue_ops = QueueOps(self.state, self.bus, self._lock)
        self._mode_ops = ModeOps(self.state, self.bus, self._lock, self.mpv, self.radio_mode)
        self._track_ended_ops = TrackEndedOps(self)
        self._retry_count = 0
        self._loading = False
        self._last_position_save = 0.0
        self._last_play_start_ts = 0.0

        # Subscribe events
        self.bus.subscribe(TrackEndedEvent, lambda e: safe_create_task(self._on_track_ended(e)))
        self.bus.subscribe(
            TrackProgressEvent, lambda e: safe_create_task(self._on_track_progress(e))
        )
        self.bus.subscribe(TrackPauseChangedEvent, self._on_pause_changed)
        self.bus.subscribe(TrackDurationEvent, self._on_track_duration)

    async def _on_track_duration(self, event: TrackDurationEvent):
        if event.duration and self.state.duration == 0:
            self.state.duration = event.duration
            if self.state.current_track:
                self.state.current_track.duration = int(event.duration)
                # Simpan metadata durasi ke database agar cache berikutnya sudah tahu durasinya
                safe_create_task(
                    self.resolver.db.upsert_track(self.state.current_track),
                    name="upsert_track_duration",
                )
            await self.bus.publish(QueueUpdatedEvent())

    async def play_track(
        self, track: TrackInfo, start_position: float = 0.0, start_paused: bool = False
    ):
        async with self._play_lock:  # A-05: cegah concurrent play_track race
            if self.state.current_track:
                self.state.history.append(self.state.current_track)
            self.state.current_track = track
            self.state.status = PlayerStatus.LOADING
            self.state.position = start_position
            self.state.duration = float(track.duration)
            self.state.lyrics_lines = []
            self.state.lyrics_index = 0
            try:
                loaded = await self.track_loader.load_track(track)
                uri = loaded.uri
                self._loading = True
                self._last_play_start_ts = asyncio.get_event_loop().time()
                await self.mpv.play(uri)
                await asyncio.sleep(0.15)

                # Loudness Normalization (Phase 6/7)
                from engine.loudness.gain_calculator import build_af_filter

                # BUGFIX: simpan gain_db track ini di state supaya toggle_loudness_normalization()
                # (mode_ops.py) bisa langsung re-apply `af` filter ke track yang sedang berjalan,
                # tanpa nunggu track berikutnya di-load. Sebelumnya toggle di tengah lagu tidak
                # berefek audio sampai lagu selanjutnya.
                self.state.current_track_gain_db = loaded.gain_db

                if getattr(self.state, "loudness_normalization_enabled", False):
                    await self.mpv.set_af(build_af_filter(loaded.gain_db))
                else:
                    await self.mpv.set_af(build_af_filter(0.0))

                if getattr(self.state, "audio_output", AudioOutput.DEVICE) == AudioOutput.BROWSER:
                    # BACKEND-FIX-01: Pastikan mpv silent di browser mode.
                    await self.mpv.set_volume(0)
                    await self.bus.publish(
                        LogMessageEvent(message="Audio output is browser, mpv silent (volume=0).")
                    )
                else:
                    if getattr(self.state, "crossfade_enabled", False):
                        from engine.playback.crossfade import apply_crossfade_in

                        safe_create_task(apply_crossfade_in(self.mpv, self.state), name="fade_in")
                    else:
                        await self.mpv.set_volume(self.state.volume)

                if start_paused:
                    await self.mpv.pause()
                else:
                    await self.mpv.resume()  # RC-TERMUX-02

                if start_position > 0:
                    await self.mpv.seek(start_position)

                self.state.status = PlayerStatus.PAUSED if start_paused else PlayerStatus.PLAYING
                self._retry_count = 0
                self._loading = False  # RC-TERMUX-01
                await self.bus.publish(TrackStartedEvent(track=track))

                # Fetch duration actively if not available
                if self.state.duration == 0:
                    safe_create_task(self._poll_duration(track), name="poll_duration")

            except Exception as e:
                self._loading = False  # RC-TERMUX-01: clear flag jika error
                logger.error(f"Failed to play track {track.title}: {e}", exc_info=True)
                self.state.status = PlayerStatus.ERROR
                self.state.error_msg = f"Error: {e}"
                await self.bus.publish(
                    LogMessageEvent(
                        message=f"Gagal memutar lagu: {track.title} | {type(e).__name__}: {str(e)}"
                    )
                )

                self._retry_count += 1
                if self._retry_count >= 3:
                    await self.bus.publish(
                        LogMessageEvent(
                            message="Terlalu banyak kegagalan beruntun. Pemutaran dihentikan."
                        )
                    )
                    self._retry_count = 0
                else:
                    backoff = 2**self._retry_count
                    await asyncio.sleep(backoff)
                    # Ensure we don't call _on_next if we are no longer trying to play this track
                    if self.state.current_track == track:
                        safe_create_task(
                            self._advance_to_next(), name=f"advance_after_failure_{track.video_id}"
                        )

    async def _poll_duration(self, track: TrackInfo):
        await poll_duration(self.state, self.mpv, self.resolver, self.bus, track)

    async def _on_cmd_play_track(self, track: TrackInfo):
        async with self._lock:
            if self.state.playback_mode == PlaybackMode.RADIO:
                await self.radio_mode.on_deactivated()
                self.state.playback_mode = PlaybackMode.QUEUE
                await self.bus.publish(QueueUpdatedEvent())
            await self.play_track(track)

    async def _on_track_ended(self, event: TrackEndedEvent):
        await self._track_ended_ops.on_track_ended(event)

    async def _on_track_progress(self, event: TrackProgressEvent):
        self.state.position = event.position

        if (
            getattr(self.state, "crossfade_enabled", False)
            and getattr(self.state, "audio_output", AudioOutput.DEVICE) != AudioOutput.BROWSER
        ):
            if self.state.duration > 0 and self.state.status == PlayerStatus.PLAYING:
                from engine.playback.crossfade import check_crossfade_out

                remaining = self.state.duration - self.state.position
                safe_create_task(check_crossfade_out(self.mpv, self.state, remaining))

        if self.state.playback_mode == PlaybackMode.RADIO:
            self.radio_mode.check_prefetch(self, self.state.position, self.state.duration)

        import time

        if time.time() - getattr(self, "_last_ps", 0.0) >= 10.0 and self.state.current_track:
            self._last_ps = time.time()
            safe_create_task(
                self.resolver.db.set_last_position(
                    self.state.current_track.video_id, event.position
                )
            )

    async def _on_cmd_toggle_pause(self, _data=None):
        if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED):
            new_status = (
                PlayerStatus.PAUSED
                if self.state.status == PlayerStatus.PLAYING
                else PlayerStatus.PLAYING
            )
            self.state.status = new_status
            _, actual_pos = await asyncio.gather(
                self.mpv.toggle_pause(),
                self.mpv.get_position(),
            )
            if actual_pos:
                self.state.position = actual_pos
            await self.bus.publish(
                TrackPauseChangedEvent(is_paused=(new_status == PlayerStatus.PAUSED))
            )

    async def _on_next(self, data=None):
        async with self._lock:
            if data and isinstance(data, dict) and "video_id" in data:
                if (
                    not self.state.current_track
                    or self.state.current_track.video_id != data["video_id"]
                ):
                    logger.info(
                        f"Ignoring skip: requested {data['video_id']} != current {getattr(self.state.current_track, 'video_id', None)}"
                    )
                    return
            await self._advance_to_next()

    async def _advance_to_next(self):
        # Track Completion/Skip for Bandit (Phase 5)
        if self.state.current_track and self.state.duration > 0:
            if self.state.position >= self.state.duration * 0.9:
                safe_create_task(
                    self.resolver.db.record_completion(self.state.current_track.artist)
                )
            else:
                safe_create_task(self.resolver.db.record_skip(self.state.current_track.artist))

        if self.state.playback_mode == PlaybackMode.QUEUE:
            await self.queue_mode.next(self)
        else:
            await self.radio_mode.next(self)

    async def _on_prev(self, _data=None):
        async with self._lock:
            if self.state.history:
                track = self.state.history.pop()
                self.state.current_track = None
                await self.play_track(track)
            else:
                await self.bus.publish(LogMessageEvent(message="Tidak ada lagu sebelumnya"))

    async def _on_stop(self, _data=None):
        self._retry_count = 0  # TASK-0.2: reset retry state agar tidak bocor ke lagu berikutnya
        await self.mpv.pause()
        self.state.status = PlayerStatus.IDLE
        self.state.current_track = None
        self.state.queue.clear()
        self.state.radio_queue.clear()
        self.state.position = 0.0
        self.state.lyrics_lines = []
        self.state.lyrics_index = 0
        await self.bus.publish(LogMessageEvent(message="Pemutaran dihentikan"))
        await self.bus.publish(QueueUpdatedEvent())

    async def _on_seek(self, position: float):
        if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED):
            await self.mpv.seek(position)
            self.state.position = position

    async def _on_set_mode(self, mode: PlaybackMode):
        should_activate_radio = await self._mode_ops.set_mode(mode)
        if should_activate_radio:
            await self.radio_mode.on_activated(self)

    async def _on_queue_select(self, index: int):
        track = await self._queue_ops.queue_select(index)
        if track:
            await self.play_track(track)

    async def _on_queue_remove(self, index: int):
        await self._queue_ops.remove_track(index)

    async def _on_queue_add(self, track: TrackInfo):
        await self._queue_ops.add_track(track)

    async def _on_queue_replace(self, tracks: list[TrackInfo]):
        await self._queue_ops.replace_queue(tracks)

    async def _on_queue_reorder(self, data: dict):
        from_index = data.get("from_index")
        to_index = data.get("to_index")
        if from_index is not None and to_index is not None:
            await self._queue_ops.reorder(from_index, to_index)

    async def _on_radio_randomize(self, data=None):
        should_fetch, seed = await self._mode_ops.randomize_radio(data)
        if should_fetch:
            from core.task_utils import safe_create_task

            safe_create_task(
                self.radio_mode._fetch_and_play_initial(self, seed_artist=seed),
                name="radio_randomize_fetch",
            )

    async def _on_pause_changed(self, event: TrackPauseChangedEvent):
        if self._loading:
            logger.info(
                f"[PAUSE] Ignoring pause-changed (is_paused={event.is_paused}) during track load"
            )
            return
        if event.is_paused:
            if self.state.status == PlayerStatus.PLAYING:
                self.state.status = PlayerStatus.PAUSED
        else:
            if self.state.status == PlayerStatus.PAUSED:
                self.state.status = PlayerStatus.PLAYING

    async def _on_set_output(self, output: AudioOutput):
        await self._mode_ops.set_output(output)

    async def _on_set_sponsorblock(self, enabled: bool):
        await self._mode_ops.toggle_sponsorblock(enabled)

    async def _on_set_loudness_normalization(self, enabled: bool):
        await self._mode_ops.toggle_loudness_normalization(enabled)

    async def _on_lyrics_offset(self, data: dict):
        offset = data.get("offset", 0.0)
        self.state.lyrics_offset = float(offset)
        from core.events import LyricsUpdatedEvent

        await self.bus.publish(LyricsUpdatedEvent())

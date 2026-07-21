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
      engine.playback.track_loader, engine.queue_manager, engine.radio

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
    MpvReconnectedEvent,
    QueueUpdatedEvent,
    TrackDurationEvent,
    TrackEndedEvent,
    TrackPauseChangedEvent,
    TrackProgressEvent,
    TrackStartedEvent,
)
from core.exceptions import BotCheckError, RateLimitedError, VideoUnavailableError
from core.ports import AudioPlayerPort, LyricsProvider, SponsorBlockProvider, StreamResolverPort
from core.state import AppState, AudioOutput, PlaybackMode, PlayerStatus, TrackInfo
from core.task_utils import safe_create_task
from engine.playback.failure_ops import FailureOps
from engine.playback.mode_ops import ModeOps
from engine.playback.queue_controller import QueueController
from engine.playback.queue_ops import QueueOps
from engine.playback.settings_controller import SettingsController
from engine.playback.track_ended_ops import TrackEndedOps, poll_duration
from engine.playback.track_loader import TrackLoader
from engine.queue_manager import QueueMode
from engine.radio import RadioMode

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
        self._failure_ops = FailureOps(self)
        # PATCH: T2.3.1/T2.3.2 — QueueController dan SettingsController
        # menangani command CMD_QUEUE_* dan CMD_SET_*/CMD_RADIO_RANDOMIZE/
        # CMD_LYRICS_OFFSET (diekstrak dari PlaybackController sesuai
        # IMPLEMENTATION_PLAN.md §2.3; controller.py ini adalah izin
        # eksplisit untuk menyentuh file ❄️ Frozen ini).
        self._queue_controller = QueueController(self)
        self._settings_controller = SettingsController(self)
        # `_retry_count` TIDAK pernah dipakai untuk retry track yang SAMA --
        # tiap kegagalan play_track (apapun tracknya) selalu lompat ke
        # _advance_to_next() dengan backoff naik, dan berhenti total tanpa
        # advance lagi setelah 3x berturut-turut. Jadi counter ini sudah
        # berfungsi sebagai circuit breaker LINTAS-TRACK (bukan cuma
        # per-track) sejak awal -- lihat percabangan except di bawah.
        self._retry_count = 0
        self._loading = False
        self._last_position_save = 0.0
        self._last_play_start_ts = 0.0
        # PATCH-2026-07-16-001: track fade-in task supaya bisa di-cancel
        self._fade_task: asyncio.Task | None = None

        # Subscribe events.
        # PATCH-2026-07-16-001: 3 lambda closure di bawah ini SENGAJA disimpan
        self._on_track_ended_sub = lambda e: safe_create_task(self._on_track_ended(e))
        self._on_track_progress_sub = lambda e: safe_create_task(self._on_track_progress(e))
        self._on_mpv_reconnected_sub = lambda e: safe_create_task(self._on_mpv_reconnected(e))

        self.bus.subscribe(TrackEndedEvent, self._on_track_ended_sub)
        self.bus.subscribe(TrackProgressEvent, self._on_track_progress_sub)
        self.bus.subscribe(TrackPauseChangedEvent, self._on_pause_changed)
        self.bus.subscribe(TrackDurationEvent, self._on_track_duration)
        self.bus.subscribe(MpvReconnectedEvent, self._on_mpv_reconnected_sub)

    def dispose(self):
        """Unsubscribe semua handler yang didaftarkan di __init__.
        Dipanggil saat controller benar-benar dihancurkan (mis. room
        dibongkar) supaya EventBus tidak menyimpan strong ref ke lambda
        closure controller ini selamanya."""
        self.bus.unsubscribe(TrackEndedEvent, self._on_track_ended_sub)
        self.bus.unsubscribe(TrackProgressEvent, self._on_track_progress_sub)
        self.bus.unsubscribe(TrackPauseChangedEvent, self._on_pause_changed)
        self.bus.unsubscribe(TrackDurationEvent, self._on_track_duration)
        self.bus.unsubscribe(MpvReconnectedEvent, self._on_mpv_reconnected_sub)
        if self._fade_task and not self._fade_task.done():
            self._fade_task.cancel()

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

    async def _on_mpv_reconnected(self, _event: MpvReconnectedEvent):
        """mpv dropped and MpvObserver just reconnected it -- the underlying
        process is fresh/idle, so if we were mid-playback we need to reload
        the current track and put mpv back where the user left off."""
        if self.state.status not in (PlayerStatus.PLAYING, PlayerStatus.PAUSED):
            return
        if not self.state.current_track:
            return
        track = self.state.current_track
        position = self.state.position
        try:
            loaded = await self.track_loader.load_track(track)
            await self.mpv.play(loaded.uri)
            await asyncio.sleep(0.15)

            from engine.loudness.gain_calculator import build_af_filter

            self.state.current_track_gain_db = loaded.gain_db
            if getattr(self.state, "loudness_normalization_enabled", False):
                await self.mpv.set_af(build_af_filter(loaded.gain_db))
            else:
                await self.mpv.set_af(build_af_filter(0.0))

            if getattr(self.state, "audio_output", AudioOutput.DEVICE) == AudioOutput.BROWSER:
                await self.mpv.set_volume(0)
            else:
                await self.mpv.set_volume(self.state.volume)

            if position > 0:
                await self.mpv.seek(position)

            if self.state.status == PlayerStatus.PAUSED:
                await self.mpv.pause()
            else:
                await self.mpv.resume()

            await self.bus.publish(LogMessageEvent(message="MPV reconnect: playback dipulihkan."))
        except Exception as e:
            logger.error(f"Gagal memulihkan playback setelah mpv reconnect: {e}", exc_info=True)
            self.state.status = PlayerStatus.ERROR
            self.state.error_msg = f"Gagal memulihkan playback: {e}"

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

                        # PATCH-2026-07-16-001
                        if self._fade_task and not self._fade_task.done():
                            self._fade_task.cancel()
                        self._fade_task = safe_create_task(
                            apply_crossfade_in(self.mpv, self.state), name="fade_in"
                        )
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

            except VideoUnavailableError as e:
                # PATCH-2026-07-20-136: video dihapus/private/diblokir secara
                # permanen. Detail penanganan lihat engine/playback/failure_ops.py
                # (diekstrak dari sini supaya controller.py tetap di bawah
                # LARGE_FILE_THRESHOLD).
                await self._failure_ops.handle_video_unavailable(track, e)

            except (BotCheckError, RateLimitedError) as e:
                # PATCH-2026-07-20-136: bot-check/rate-limit -- lihat
                # engine/playback/failure_ops.py untuk detail penanganan.
                await self._failure_ops.handle_bot_check_or_rate_limited(track, e)

            except Exception as e:
                await self._failure_ops.handle_generic_error(track, e)

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

        if time.time() - self._last_position_save >= 10.0 and self.state.current_track:
            self._last_position_save = time.time()
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
        await self._queue_controller.advance_to_next()

    async def _on_prev(self, data=None):
        async with self._lock:
            if data and isinstance(data, dict) and "video_id" in data:
                if (
                    not self.state.current_track
                    or self.state.current_track.video_id != data["video_id"]
                ):
                    logger.info(
                        f"Ignoring prev: requested from {data['video_id']} != current {getattr(self.state.current_track, 'video_id', None)}"
                    )
                    return
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
        await self._settings_controller.on_set_mode(mode)

    async def _on_queue_select(self, index: int):
        await self._queue_controller.on_queue_select(index)

    async def _on_queue_remove(self, index: int):
        await self._queue_controller.on_queue_remove(index)

    async def _on_queue_add(self, track: TrackInfo):
        await self._queue_controller.on_queue_add(track)

    async def _on_queue_replace(self, tracks: list[TrackInfo]):
        await self._queue_controller.on_queue_replace(tracks)

    async def _on_queue_reorder(self, data: dict):
        await self._queue_controller.on_queue_reorder(data)

    async def _on_radio_randomize(self, data=None):
        await self._settings_controller.on_radio_randomize(data)

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
        await self._settings_controller.on_set_output(output)

    async def _on_set_sponsorblock(self, enabled: bool):
        await self._settings_controller.on_set_sponsorblock(enabled)

    async def _on_set_loudness_normalization(self, enabled: bool):
        await self._settings_controller.on_set_loudness_normalization(enabled)

    async def _on_lyrics_offset(self, data: dict):
        await self._settings_controller.on_lyrics_offset(data)

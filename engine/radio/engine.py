"""
Module: engine.radio.engine

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
import logging
from typing import TYPE_CHECKING

from core.events import LogMessageEvent, QueueUpdatedEvent
from core.ports import MediaExtractorPort
from core.state import AppState, PlayerStatus
from engine.radio.artist_selector import ArtistSelector
from engine.radio.common import ARTISTS_PER_BATCH, ARTISTS_QUICK, track_task
from engine.radio.prefetcher import RadioPrefetcher

if TYPE_CHECKING:
    from engine.playback import PlaybackController

_log = logging.getLogger(__name__)


class RadioMode:
    """
    Orchestrator radio: activate, deactivate, auto-next.
    """

    def __init__(self, ytdlp: MediaExtractorPort, state: AppState, db=None):
        self.ytdlp = ytdlp
        self.state = state
        self.db = db

        self.artist_selector = ArtistSelector(db, state)
        self.prefetcher = RadioPrefetcher(state, self.artist_selector)

        self._bg_tasks: set = set()

    # ── lifecycle ─────────────────────────────────────────────

    async def on_activated(self, controller: "PlaybackController") -> None:
        try:
            await self.artist_selector.ensure_artists_loaded()
        except RuntimeError as e:
            await controller.bus.publish(LogMessageEvent(message=f"Radio: {e}"))
            return
        self.state.radio_queue.clear()
        self.artist_selector.reset_rotation()
        track_task(self._bg_tasks, self._start(controller), name="radio_start")

    async def on_deactivated(self) -> None:
        self.state.radio_queue.clear()
        for task in list(self._bg_tasks):
            task.cancel()
        self._bg_tasks.clear()
        self.prefetcher.cancel_tasks()
        # Jangan buang _standby — bisa dipakai kalau radio dinyalakan lagi

    # ── next (dipanggil saat track habis) ─────────────────────

    async def next(self, controller: "PlaybackController") -> None:
        if self.state.radio_queue:
            track = self.state.radio_queue.popleft()
            # Kalau queue mulai tipis, pastikan standby sedang disiapkan
            if len(self.state.radio_queue) <= 5:
                track_task(
                    self._bg_tasks,
                    self.prefetcher.ensure_standby(controller),
                    name="radio_ensure_standby",
                )
            await controller.play_track(track)
        else:
            self.state.status = PlayerStatus.LOADING
            await controller.bus.publish(QueueUpdatedEvent())
            track_task(self._bg_tasks, self._start(controller), name="radio_refill")

    # ── inti: start dengan standby atau fetch cepat ───────────

    async def _start(self, controller: "PlaybackController") -> None:
        """
        Urutan prioritas:
        1. Standby sudah ada → pakai langsung (instan)
        2. Belum ada → fetch cepat ARTISTS_QUICK artis, putar segera,
           lalu background fetch sisa untuk genapi dan isi standby berikutnya
        """
        tracks = await self.prefetcher.pop_standby()

        if tracks:
            # Langsung pakai standby
            self.state.radio_queue.clear()
            self.state.radio_queue.extend(tracks[1:])
            await controller.bus.publish(QueueUpdatedEvent())
            await controller.play_track(tracks[0])
            # Siapkan standby berikutnya di background
            self.prefetcher.trigger_build_standby(controller)
            return

        # Fetch cepat: ARTISTS_QUICK artis dulu, langsung putar
        try:
            quick_tracks = await asyncio.wait_for(
                self.artist_selector.gather_batch(max_artists=ARTISTS_QUICK), timeout=20.0
            )
        except RuntimeError as e:
            # DB artists kosong — kirim pesan jelas ke frontend
            await controller.bus.publish(QueueUpdatedEvent())
            await controller.bus.publish(LogMessageEvent(message=f"Radio: {e}"))
            return
        except (TimeoutError, Exception):
            quick_tracks = []

        if quick_tracks:
            self.state.radio_queue.clear()
            self.state.radio_queue.extend(quick_tracks[1:])
            await controller.bus.publish(QueueUpdatedEvent())
            await controller.play_track(quick_tracks[0])
            # Background: fetch sisa artis dan masukkan ke queue + siapkan standby
            track_task(
                self._bg_tasks, self._backfill_and_standby(controller), name="radio_backfill"
            )
        else:
            # Broadcast state ulang agar frontend tidak stuck di "loading" tanpa info
            await controller.bus.publish(QueueUpdatedEvent())
            await controller.bus.publish(
                LogMessageEvent(message="Radio: Tidak ada hasil ditemukan.")
            )

    async def _backfill_and_standby(self, controller: "PlaybackController") -> None:
        """Fetch sisa artis (ARTISTS_PER_BATCH - ARTISTS_QUICK) lalu
        tambahkan ke queue yang sedang berjalan. Setelah itu siapkan standby."""
        extra = await self.prefetcher.fetch_batch_with_lock(
            max_artists=ARTISTS_PER_BATCH - ARTISTS_QUICK
        )
        if extra:
            self.state.radio_queue.extend(extra)
            while len(self.state.radio_queue) > 30:
                self.state.radio_queue.pop()
            await controller.bus.publish(QueueUpdatedEvent())

        # Setelah backfill selesai, langsung siapkan standby berikutnya
        self.prefetcher.trigger_build_standby(controller)

    # ── dipanggil dari playback_controller saat tombol Acak ───

    async def _fetch_and_play_initial(
        self, controller: "PlaybackController", seed_artist: str | None = None
    ) -> None:
        self.artist_selector.reset_rotation()
        await self.prefetcher.async_clear_standby()

        await controller.bus.publish(LogMessageEvent(message="Mengacak playlist radio..."))

        try:
            tracks = await asyncio.wait_for(
                self.artist_selector.gather_batch(
                    prioritized_artist=seed_artist, max_artists=ARTISTS_PER_BATCH
                ),
                timeout=40.0,
            )
        except RuntimeError as e:
            await controller.bus.publish(LogMessageEvent(message=f"Radio: {e}"))
            return
        except TimeoutError:
            await controller.bus.publish(
                LogMessageEvent(message="Radio: Timeout saat mengambil lagu. Coba lagi.")
            )
            return
        except Exception as e:
            _log.warning(f"Radio randomize gagal: {e}")
            return

        if not tracks:
            await controller.bus.publish(
                LogMessageEvent(message="Radio: Tidak ada hasil ditemukan.")
            )
            return

        self.state.radio_queue.clear()
        self.state.radio_queue.extend(tracks[1:])
        await controller.bus.publish(QueueUpdatedEvent())
        await controller.play_track(tracks[0])

        # Siapkan standby berikutnya di background untuk auto-refill
        self.prefetcher.trigger_build_standby(controller)

    def check_prefetch(
        self, controller: "PlaybackController", position: float, duration: float
    ) -> None:
        self.prefetcher.check_prefetch(controller, position, duration)

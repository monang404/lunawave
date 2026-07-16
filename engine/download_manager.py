"""
Module: engine.download_manager

Purpose:
    Handle the CMD_DOWNLOAD command by downloading the current or specified
    track via yt-dlp and moving it to the downloads/ folder.

Responsibilities:
    - Guard against concurrent downloads with an asyncio.Lock.
    - Report progress via DownloadProgressEvent and completion via
      DownloadCompleteEvent.

Depends on:
    - core.command_bus
    - core.event_bus
    - core.events
    - core.ports
    - core.state
    - core.task_utils

Subscribes to:
    CMD_DOWNLOAD

Publishes:
    LogMessageEvent, DownloadCompleteEvent, DownloadProgressEvent

Thread Safety:
    Worker thread (async with lock; progress hook runs in thread executor).
"""

import asyncio

import structlog

from core.command_bus import CMD_DOWNLOAD, command_bus
from core.event_bus import EventBus
from core.events import DownloadCompleteEvent, LogMessageEvent
from core.ports import MediaExtractorPort
from core.state import AppState, TrackInfo
from core.task_utils import safe_create_task

logger = structlog.get_logger(__name__)


class DownloadManager:
    def __init__(self, bus: EventBus, state: AppState, ytdlp: MediaExtractorPort):
        self.bus = bus
        self.state = state
        self.ytdlp = ytdlp
        self._download_lock = asyncio.Lock()
        # RACE-FIX: `_download_lock.locked()` saja tidak cukup untuk menolak
        # trigger download kedua, karena lock itu baru benar-benar ter-acquire
        # saat task `_do_download` MULAI JALAN (bukan saat dijadwalkan lewat
        # safe_create_task). Antara dua trigger download() yang datang beruntun
        # cepat (mis. klik tombol dobel, atau klik + shortcut keyboard di message
        # WS yang berbeda tapi diproses berdekatan), _on_download() bisa
        # dipanggil dua kali sebelum task pertama sempat berjalan sama sekali --
        # keduanya lolos cek .locked() dan sama-sama menjadwalkan _do_download(),
        # sehingga file yang sama ter-download dua kali secara berurutan.
        # Flag ini di-set SINKRON (tanpa ada `await` di antaranya) tepat sebelum
        # task dijadwalkan, sehingga trigger kedua langsung tertolak walau task
        # pertama belum sempat jalan sama sekali.
        self._download_scheduled = False

        command_bus.register(CMD_DOWNLOAD, self._on_download)

    async def _on_download(self, track: TrackInfo | None = None):
        target = track or self.state.current_track
        if not target:
            await self.bus.publish(
                LogMessageEvent(message="Tidak ada lagu yang dipilih untuk di-download")
            )
            return

        if target.local_path:
            await self.bus.publish(LogMessageEvent(message="Lagu sudah tersimpan lokal"))
            return

        if self._download_lock.locked() or self._download_scheduled:
            await self.bus.publish(
                LogMessageEvent(message="Download sedang berjalan, tunggu selesai.")
            )
            return

        self._download_scheduled = True
        safe_create_task(self._do_download(target), name=f"download_{target.video_id}")

    async def _do_download(self, track: TrackInfo):
        async with self._download_lock:
            try:
                self.state.download_progress = 0.0
                await self.bus.publish(LogMessageEvent(message=f"Memulai download: {track.title}"))

                loop = asyncio.get_running_loop()

                def sync_progress_hook(d):
                    if d.get("status") == "downloading":
                        total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
                        downloaded_bytes = d.get("downloaded_bytes", 0)
                        if total_bytes and total_bytes > 0:
                            percent = downloaded_bytes / total_bytes
                            loop.call_soon_threadsafe(self._update_progress, percent)

                local_path = await self.ytdlp.download_audio(
                    track.video_id, on_progress=sync_progress_hook
                )

                import re
                import shutil
                from pathlib import Path

                from config import DOWNLOAD_DIR

                downloads_dir = DOWNLOAD_DIR
                downloads_dir.mkdir(parents=True, exist_ok=True)
                safe_artist = re.sub(r'[\\/*?:"<>|]', "", track.artist)
                safe_title = re.sub(r'[\\/*?:"<>|]', "", track.title)
                # Preserve real extension (may be .opus, .m4a, .webm, etc.)
                real_ext = Path(local_path).suffix  # e.g. ".opus" or ".m4a"
                user_path = downloads_dir / f"{safe_artist} - {safe_title}{real_ext}"

                if user_path.exists():
                    try:
                        user_path.unlink()
                    except Exception as e:
                        logger.warning(f"Could not remove existing user path {user_path}: {e}")

                shutil.move(local_path, user_path)

                track.local_path = str(user_path)
                self.state.download_progress = None

                await self.bus.publish(
                    LogMessageEvent(
                        message=f"Download sukses: {track.title} (Tersimpan di folder 'downloads')"
                    )
                )
                await self.bus.publish(DownloadCompleteEvent(track=track))

            except Exception as e:
                self.state.download_progress = None
                logger.error(f"Download error: {e}", exc_info=True)
                await self.bus.publish(LogMessageEvent(message=f"Download gagal: {str(e)}"))
            finally:
                self._download_scheduled = False

    def _update_progress(self, percent: float):
        self.state.download_progress = percent
        from core.events import DownloadProgressEvent

        safe_create_task(
            self.bus.publish(DownloadProgressEvent(progress=percent)), name="pub_dl_prog"
        )

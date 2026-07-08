"""
Purpose: Mengelola download lagu dari YouTube.
Subscribes to: CMD_DOWNLOAD
Publishes: LOG_MESSAGE, DOWNLOAD_COMPLETE
"""

import asyncio
import shutil
import structlog

from core.commands import DownloadCommand
from core.event_bus import EventBus
from core.events import DownloadCompleteEvent, LogMessageEvent, DownloadProgressEvent
from core.ports import MediaExtractorPort
from core.state import AppState, TrackInfo
from core.task_utils import safe_create_task
from core.utils import user_download_path

logger = structlog.get_logger(__name__)

class DownloadManager:
    def __init__(self, bus: EventBus, command_bus, state: AppState, ytdlp: MediaExtractorPort):
        self.bus = bus
        self.command_bus = command_bus
        self.state = state
        self.ytdlp = ytdlp
        
        # Tasks S05-017 & S05-062: Use Queue instead of lock for concurrency control
        self._download_queue = asyncio.Queue()
        self._downloading_ids: set[str] = set()
        
        # Start background workers (limit concurrency to 3)
        self._workers = []
        for i in range(3):
            self._workers.append(safe_create_task(self._worker_loop(), name=f"dl_worker_{i}"))

        self.command_bus.register(DownloadCommand, self._route(self._on_download))

    def _route(self, action):
        async def handler(command):
            # Task S05-034: Removed inline import asyncio
            res = action(command.track)
            if asyncio.iscoroutine(res):
                return await res
            return res
        return handler
        
    async def _worker_loop(self):
        while True:
            track = await self._download_queue.get()
            try:
                await self._do_download(track)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Download worker error: {e}", exc_info=True)
            finally:
                self._download_queue.task_done()

    async def _on_download(self, track: TrackInfo | None = None):
        target = track or self.state.current_track
        if not target:
            await self.bus.publish(LogMessageEvent(message="Tidak ada lagu yang dipilih untuk di-download"))
            return

        if target.local_path:
            await self.bus.publish(LogMessageEvent(message="Lagu sudah tersimpan lokal"))
            return

        if target.video_id in self._downloading_ids:
            await self.bus.publish(LogMessageEvent(message="Download sedang berjalan, tunggu selesai."))
            return

        self._downloading_ids.add(target.video_id)
        await self.bus.publish(LogMessageEvent(message=f"Ditambahkan ke antrean download: {target.title}"))
        await self._download_queue.put(target)

    async def _do_download(self, track: TrackInfo):
        try:
            self.state.download_progress = 0.0
            await self.bus.publish(LogMessageEvent(message=f"Memulai download: {track.title}"))

            loop = asyncio.get_running_loop()

            def sync_progress_hook(d):
                if d.get('status') == 'downloading':
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    if total_bytes and total_bytes > 0:
                        percent = downloaded_bytes / total_bytes
                        loop.call_soon_threadsafe(self._update_progress, percent)

            local_path = await self.ytdlp.download_mp3(track.video_id, on_progress=sync_progress_hook)
            track.local_path = local_path
            self.state.download_progress = None

            user_path = user_download_path(track.artist, track.title)
            user_path.parent.mkdir(exist_ok=True)
            if not user_path.exists():
                shutil.copy2(local_path, user_path)

            await self.bus.publish(LogMessageEvent(message=f"Download sukses: {track.title} (Tersimpan di folder 'downloads')"))
            await self.bus.publish(DownloadCompleteEvent(track=track))

        except Exception as e:
            self.state.download_progress = None
            logger.error(f"Download error: {e}", exc_info=True)
            await self.bus.publish(LogMessageEvent(message=f"Download gagal: {str(e)}"))
        finally:
            self._downloading_ids.discard(track.video_id)

    def _update_progress(self, percent: float):
        self.state.download_progress = percent
        safe_create_task(self.bus.publish(DownloadProgressEvent(progress=percent)), name="pub_dl_prog")

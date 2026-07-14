"""
Module: adapters.ytdlp.downloader

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
import re

from adapters.ytdlp.common import YDL_OPTS_INFO
from config import CACHE_DIR


class YtDlpDownloader:
    """download_mp3(video_id, path) + progress hook"""

    def __init__(self, executor):
        self._executor = executor
        self.is_cancelled = False

    def cancel_download(self):
        self.is_cancelled = True

    def _check_cancel_hook(self, d):
        if self.is_cancelled:
            raise Exception("DownloadCancelled")

    async def download_mp3(self, video_id: str, on_progress=None) -> str:
        self.is_cancelled = False
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", video_id)
        out_path = CACHE_DIR / f"{safe_id}.%(ext)s"

        hooks = [self._check_cancel_hook]
        if on_progress:
            hooks.append(on_progress)

        opts = {
            **YDL_OPTS_INFO,
            "format": "bestaudio/best",
            "format_sort": ["abr", "asr"],
            "outtmpl": str(out_path),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
            "progress_hooks": hooks,
        }
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self._executor, self._download_sync, video_id, opts)
        return str(CACHE_DIR / f"{safe_id}.mp3")

    def _download_sync(self, video_id, opts):
        import yt_dlp

        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

"""
Module: adapters.ytdlp

Purpose:
    Unified client for interacting with yt-dlp for search, extraction, and downloading.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - adapters.ytdlp.downloader
    - adapters.ytdlp.resolver
    - adapters.ytdlp.searcher

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

from concurrent.futures import ThreadPoolExecutor

from adapters.ytdlp.downloader import YtDlpDownloader
from adapters.ytdlp.resolver import YtDlpResolver
from adapters.ytdlp.searcher import YtDlpSearcher


class YtDlpClient:
    """Facade — API identik dengan engine/ytdlp_client.py lama."""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._searcher = YtDlpSearcher(self._executor)
        self._resolver = YtDlpResolver(self._executor)
        self._downloader = YtDlpDownloader(self._executor)

    async def search(self, *a, **kw):
        return await self._searcher.search(*a, **kw)

    async def extract_info(self, *a, **kw):
        return await self._searcher.extract_info(*a, **kw)

    async def get_stream_url(self, *a, **kw):
        return await self._resolver.get_stream_url(*a, **kw)

    async def download_audio(self, *a, **kw):
        return await self._downloader.download_audio(*a, **kw)

    def cancel_download(self):
        self._downloader.cancel_download()

    def close(self):
        self._executor.shutdown(wait=False)

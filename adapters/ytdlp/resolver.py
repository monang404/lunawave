"""
Module: adapters.ytdlp.resolver

Purpose:
    Resolves direct stream URLs for tracks using yt-dlp.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - adapters.ytdlp.common

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio
import logging

from adapters.ytdlp.common import YDL_OPTS_INFO
from config import YTDLP_RESOLVE_TIMEOUT_SEC

_log = logging.getLogger(__name__)


class YtDlpResolver:
    """get_stream_url(video_id) → str"""

    def __init__(self, executor):
        self._executor = executor

    async def get_stream_url(self, video_id: str) -> str:
        opts = {
            **YDL_OPTS_INFO,
            "extract_flat": False,
        }
        url = f"https://www.youtube.com/watch?v={video_id}"
        loop = asyncio.get_running_loop()
        try:
            info = await asyncio.wait_for(
                loop.run_in_executor(self._executor, self._extract_sync, url, opts),
                timeout=YTDLP_RESOLVE_TIMEOUT_SEC,
            )
            if info:
                stream_url = self._pick_audio_url(info)
                if stream_url:
                    return stream_url
            raise RuntimeError(f"yt-dlp returned no stream URL for {video_id}")
        except TimeoutError:
            _log.error(
                f"get_stream_url timed out after {YTDLP_RESOLVE_TIMEOUT_SEC}s for {video_id}"
            )
            raise RuntimeError(
                f"Timeout ({YTDLP_RESOLVE_TIMEOUT_SEC}s) saat mengambil stream URL untuk {video_id}"
            )
        except RuntimeError:
            raise
        except Exception as e:
            _log.error(f"get_stream_url failed for {video_id}: {type(e).__name__}: {e}")
            raise RuntimeError(f"Gagal mengambil stream URL untuk {video_id}: {e}") from e

    def _extract_sync(self, url, opts):
        import yt_dlp

        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _pick_audio_url(self, info: dict) -> str:
        # Trust yt-dlp's own selector result — the top-level "url" key is the
        # URL of the format that the selector + format_sort in YDL_OPTS_INFO
        # already chose. Re-iterating "formats" manually here is a second,
        # competing logic that can silently produce a different (worse) result.
        url = info.get("url")
        if url:
            return url
        # Fallback: if for any reason top-level url is absent, pick best
        # audio-only format explicitly sorted by abr descending. Iterate in
        # reverse so that, when abr is missing/tied, the last-listed (usually
        # highest-itag / most-recent) format wins instead of the first one.
        formats = info.get("formats", [])
        audio_only = [
            f for f in reversed(formats) if f.get("acodec") != "none" and f.get("vcodec") == "none"
        ]
        if audio_only:
            best = max(audio_only, key=lambda f: f.get("abr") or 0)
            return best["url"]
        # Last resort: no dedicated audio-only stream at all, only muxed
        # (audio+video) formats. Still usable — mpv is launched with
        # --no-video, so the video stream is simply discarded — better than
        # failing the whole playback outright.
        muxed = [f for f in reversed(formats) if f.get("acodec") != "none"]
        if muxed:
            best = max(muxed, key=lambda f: f.get("abr") or 0)
            return best["url"]
        raise RuntimeError("yt-dlp returned no usable audio format")

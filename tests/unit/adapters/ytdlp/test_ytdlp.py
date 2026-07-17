"""
Module: tests.unit.adapters.ytdlp.test_searcher

Purpose:
    Unit tests for YtDlpSearcher._to_track and search filtering logic
    without making real network calls. yt-dlp is mocked at the executor level.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - adapters.ytdlp.downloader
    - adapters.ytdlp.resolver
    - adapters.ytdlp.searcher
    - core.state

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from adapters.ytdlp.searcher import YtDlpSearcher
from core.state import TrackInfo

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_entry(
    id="abc123",
    title="Test Song",
    uploader="Test Artist",
    duration=200,
    thumbnail="http://img.example.com/thumb.jpg",
    view_count=1000,
):
    return {
        "id": id,
        "title": title,
        "uploader": uploader,
        "duration": duration,
        "thumbnail": thumbnail,
        "view_count": view_count,
    }


def make_searcher():
    executor = MagicMock()
    return YtDlpSearcher(executor=executor)


# ---------------------------------------------------------------------------
# _to_track
# ---------------------------------------------------------------------------


class TestToTrack:
    def test_maps_basic_fields(self):
        searcher = make_searcher()
        entry = make_entry()
        track = searcher._to_track(entry)

        assert isinstance(track, TrackInfo)
        assert track.video_id == "abc123"
        assert track.title == "Test Song"
        assert track.artist == "Test Artist"
        assert track.duration == 200
        assert track.thumbnail == "http://img.example.com/thumb.jpg"
        assert track.view_count == 1000

    def test_uses_fallback_video_id_when_invalid_chars(self):
        searcher = make_searcher()
        entry = make_entry(id="invalid id with spaces!", title="My Song")
        track = searcher._to_track(entry)

        # Should generate a hash-based fallback
        assert track.video_id.startswith("vid_")

    def test_uses_fallback_video_id_when_empty(self):
        searcher = make_searcher()
        entry = make_entry(id="", title="My Song")
        track = searcher._to_track(entry)

        assert track.video_id.startswith("vid_")

    def test_handles_missing_duration(self):
        searcher = make_searcher()
        entry = make_entry()
        entry.pop("duration")
        track = searcher._to_track(entry)
        assert track.duration == 0

    def test_handles_none_duration(self):
        searcher = make_searcher()
        entry = make_entry(duration=None)
        track = searcher._to_track(entry)
        assert track.duration == 0


# ---------------------------------------------------------------------------
# search — filtering
# ---------------------------------------------------------------------------


class TestSearchFiltering:
    def _make_results(self, entries):
        return {"entries": entries}

    @pytest.mark.asyncio
    async def test_skips_entries_longer_than_600s(self):
        searcher = make_searcher()
        entries = [make_entry(duration=601), make_entry(id="short1", duration=180)]

        with patch.object(searcher, "_extract_sync", return_value=self._make_results(entries)):
            searcher._extract_sync  # ensure it's patched
            # Patch loop.run_in_executor to call _extract_sync directly
            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = AsyncMock(
                    return_value=self._make_results(entries)
                )
                results = await searcher.search("test")

        assert len(results) == 1
        assert results[0].video_id == "short1"

    @pytest.mark.asyncio
    async def test_skips_entries_with_banned_keywords(self):
        searcher = make_searcher()
        banned_entries = [
            make_entry(id="b1", title="Best Mix 2024"),
            make_entry(id="b2", title="Full Album Collection"),
            make_entry(id="b3", title="Compilation Vol 5"),
        ]
        good_entry = make_entry(id="good1", title="Normal Song", duration=200)
        entries = banned_entries + [good_entry]

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value=self._make_results(entries)
            )
            results = await searcher.search("test")

        assert len(results) == 1
        assert results[0].video_id == "good1"

    @pytest.mark.asyncio
    async def test_skips_none_entries(self):
        searcher = make_searcher()
        entries = [None, make_entry(id="valid1")]

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value=self._make_results(entries)
            )
            results = await searcher.search("test")

        assert len(results) == 1
        assert results[0].video_id == "valid1"

    @pytest.mark.asyncio
    async def test_respects_max_results(self):
        searcher = make_searcher()
        entries = [make_entry(id=f"t{i}", title=f"Track {i}", duration=100) for i in range(20)]

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value=self._make_results(entries)
            )
            results = await searcher.search("test", max_results=5)

        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_returns_empty_when_entries_all_filtered(self):
        searcher = make_searcher()
        entries = [make_entry(id="b1", duration=700)]  # too long

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value=self._make_results(entries)
            )
            results = await searcher.search("test")

        assert results == []


# ---------------------------------------------------------------------------
# YtDlpResolver._pick_audio_url
# ---------------------------------------------------------------------------


class TestPickAudioUrl:
    def test_prefers_audio_only_format(self):
        from adapters.ytdlp.resolver import YtDlpResolver

        resolver = YtDlpResolver(executor=MagicMock())
        info = {
            "formats": [
                {"acodec": "mp4a.40.2", "vcodec": "avc1", "url": "http://video.url"},
                {"acodec": "mp4a.40.2", "vcodec": "none", "url": "http://audio.url"},
            ],
        }
        result = resolver._pick_audio_url(info)
        assert result == "http://audio.url"

    def test_falls_back_to_top_level_url_when_no_audio_only(self):
        from adapters.ytdlp.resolver import YtDlpResolver

        resolver = YtDlpResolver(executor=MagicMock())
        info = {
            "formats": [
                {"acodec": "mp4a.40.2", "vcodec": "avc1", "url": "http://muxed.url"},
            ],
        }
        result = resolver._pick_audio_url(info)
        # No audio-only format exists, so it falls back to the muxed
        # (audio+video) format instead of failing outright.
        assert result == "http://muxed.url"


# ---------------------------------------------------------------------------
# YtDlpDownloader
# ---------------------------------------------------------------------------


class TestYtDlpDownloader:
    def test_cancel_sets_flag(self):
        from adapters.ytdlp.downloader import YtDlpDownloader

        dl = YtDlpDownloader(executor=MagicMock())
        assert dl.is_cancelled is False
        dl.cancel_download()
        assert dl.is_cancelled is True

    def test_cancel_hook_raises_when_cancelled(self):
        from adapters.ytdlp.downloader import YtDlpDownloader

        dl = YtDlpDownloader(executor=MagicMock())
        dl.is_cancelled = True
        with pytest.raises(Exception, match="DownloadCancelled"):
            dl._check_cancel_hook({})

    def test_cancel_hook_does_not_raise_when_not_cancelled(self):
        from adapters.ytdlp.downloader import YtDlpDownloader

        dl = YtDlpDownloader(executor=MagicMock())
        dl.is_cancelled = False
        dl._check_cancel_hook({})  # should not raise

    @pytest.mark.asyncio
    async def test_download_mp3_resets_cancel_flag_on_start(self):
        from adapters.ytdlp.downloader import YtDlpDownloader

        dl = YtDlpDownloader(executor=MagicMock())
        dl.is_cancelled = True

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=None)
            with patch("adapters.ytdlp.downloader.CACHE_DIR") as mock_dir:
                mock_dir.mkdir = MagicMock()
                mock_dir.__truediv__ = MagicMock(return_value=MagicMock())
                await dl.download_mp3("abc123")

        assert dl.is_cancelled is False

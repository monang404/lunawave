"""tests/unit/engine/test_ytdlp_client.py — mirrors engine/ytdlp_client.py

Semua tes isolasi murni: yt-dlp TIDAK pernah dipanggil ke jaringan.
Kita patch `_extract_sync` dan `_download_sync` agar executor tetap jalan
tapi tidak pernah menyentuh internet.

Purpose:
    Auto-generated purpose.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
import re
from unittest.mock import MagicMock, patch

import pytest

from adapters.ytdlp import YtDlpClient
from core.state import TrackInfo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_entry(
    video_id="abc123",
    title="Test Song",
    uploader="Test Artist",
    duration=180,
    thumbnail="https://img/thumb.jpg",
    view_count=1000,
):
    """Minimal yt-dlp flat-extract entry dict."""
    return {
        "id": video_id,
        "title": title,
        "uploader": uploader,
        "duration": duration,
        "thumbnail": thumbnail,
        "view_count": view_count,
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }


def make_search_result(entries):
    """Wrap entries in a yt-dlp search result envelope."""
    return {"entries": entries}


def make_stream_info(url="https://cdn.example.com/audio.m4a"):
    """Minimal info dict returned by yt-dlp for a single video."""
    return {
        "url": url,
        "formats": [
            {"acodec": "opus", "vcodec": "none", "url": url},
        ],
    }


# ---------------------------------------------------------------------------
# _to_track
# ---------------------------------------------------------------------------

class TestToTrack:
    def test_maps_standard_fields_correctly(self):
        client = YtDlpClient()
        entry = make_entry()
        track = client._searcher._to_track(entry)
        assert track.video_id == "abc123"
        assert track.title == "Test Song"
        assert track.artist == "Test Artist"
        assert track.duration == 180
        assert track.thumbnail == "https://img/thumb.jpg"
        assert track.view_count == 1000

    def test_duration_none_becomes_zero(self):
        client = YtDlpClient()
        entry = make_entry(duration=None)
        track = client._searcher._to_track(entry)
        assert track.duration == 0

    def test_duration_float_is_coerced_to_int(self):
        client = YtDlpClient()
        entry = make_entry(duration=183.7)
        track = client._searcher._to_track(entry)
        assert track.duration == 183

    def test_missing_video_id_generates_stable_fallback(self):
        client = YtDlpClient()
        entry = {"title": "No ID Song", "uploader": "Art", "duration": 100}
        track = client._searcher._to_track(entry)
        assert track.video_id.startswith("vid_")

    def test_invalid_video_id_chars_generates_fallback(self):
        client = YtDlpClient()
        entry = make_entry(video_id="bad/id?here")
        track = client._searcher._to_track(entry)
        # Should fall back to hashed id
        assert track.video_id.startswith("vid_")

    def test_valid_video_id_kept_as_is(self):
        client = YtDlpClient()
        entry = make_entry(video_id="dQw4w9WgXcQ")
        track = client._searcher._to_track(entry)
        assert track.video_id == "dQw4w9WgXcQ"


# ---------------------------------------------------------------------------
# _pick_audio_url
# ---------------------------------------------------------------------------

class TestPickAudioUrl:
    def test_returns_audio_only_format_url(self):
        client = YtDlpClient()
        info = {
            "url": "https://fallback.url",
            "formats": [
                {"acodec": "none", "vcodec": "h264", "url": "https://video.url"},
                {"acodec": "opus", "vcodec": "none", "url": "https://audio.url"},
            ],
        }
        assert client._resolver._pick_audio_url(info) == "https://audio.url"

    def test_falls_back_to_top_level_url_when_no_audio_only_format(self):
        client = YtDlpClient()
        info = {
            "url": "https://fallback.url",
            "formats": [
                {"acodec": "mp4a", "vcodec": "h264", "url": "https://av.url"},
            ],
        }
        assert client._resolver._pick_audio_url(info) == "https://fallback.url"

    def test_prefers_last_audio_only_format_reversed(self):
        """_pick_audio_url iterates reversed(formats), so last audio-only wins."""
        client = YtDlpClient()
        info = {
            "url": "https://fallback.url",
            "formats": [
                {"acodec": "mp4a", "vcodec": "none", "url": "https://audio1.url"},
                {"acodec": "opus", "vcodec": "none", "url": "https://audio2.url"},
            ],
        }
        # reversed: audio2 comes first in iteration → picked
        assert client._resolver._pick_audio_url(info) == "https://audio2.url"


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------

class TestSearch:
    async def test_returns_tracks_for_valid_entries(self):
        client = YtDlpClient()
        raw = make_search_result([make_entry("v1"), make_entry("v2")])

        with patch.object(client._searcher, "_extract_sync", return_value=raw):
            results = await client.search("test query")

        assert len(results) == 2
        assert all(isinstance(t, TrackInfo) for t in results)

    async def test_filters_out_videos_longer_than_10_minutes(self):
        client = YtDlpClient()
        entries = [make_entry("v1", duration=601), make_entry("v2", duration=300)]
        raw = make_search_result(entries)

        with patch.object(client._searcher, "_extract_sync", return_value=raw):
            results = await client.search("test")

        assert len(results) == 1
        assert results[0].video_id == "v2"

    async def test_filters_out_compilation_keywords_in_title(self):
        client = YtDlpClient()
        bad_titles = ["Best Mix 2024", "Full Album", "Top Playlist", "Mega Mashup", "Medley", "Megamix"]
        entries = [make_entry(f"v{i}", title=t) for i, t in enumerate(bad_titles)]
        entries.append(make_entry("good", title="Normal Song"))
        raw = make_search_result(entries)

        with patch.object(client._searcher, "_extract_sync", return_value=raw):
            results = await client.search("music")

        assert len(results) == 1
        assert results[0].video_id == "good"

    async def test_respects_max_results_limit(self):
        client = YtDlpClient()
        entries = [make_entry(f"v{i}") for i in range(10)]
        raw = make_search_result(entries)

        with patch.object(client._searcher, "_extract_sync", return_value=raw):
            results = await client.search("test", max_results=3)

        assert len(results) == 3

    async def test_skips_none_entries_in_results(self):
        client = YtDlpClient()
        raw = make_search_result([None, make_entry("v1"), None, make_entry("v2")])

        with patch.object(client._searcher, "_extract_sync", return_value=raw):
            results = await client.search("test")

        assert len(results) == 2

    async def test_returns_empty_list_when_no_entries(self):
        client = YtDlpClient()
        with patch.object(client._searcher, "_extract_sync", return_value={"entries": []}):
            results = await client.search("nothing")
        assert results == []


# ---------------------------------------------------------------------------
# get_stream_url()
# ---------------------------------------------------------------------------

class TestGetStreamUrl:
    async def test_returns_audio_url_on_success(self):
        client = YtDlpClient()
        info = make_stream_info("https://cdn.example.com/audio.m4a")

        with patch.object(client._resolver, "_extract_sync", return_value=info):
            url = await client.get_stream_url("dQw4w9WgXcQ")

        assert url == "https://cdn.example.com/audio.m4a"

    async def test_raises_runtime_error_when_extract_returns_none(self):
        client = YtDlpClient()

        with patch.object(client._resolver, "_extract_sync", return_value=None):
            with pytest.raises(RuntimeError, match="no stream URL"):
                await client.get_stream_url("vid123")

    async def test_raises_runtime_error_when_extract_returns_empty_formats(self):
        client = YtDlpClient()
        info = {"url": "", "formats": []}  # _pick_audio_url falls through to empty url

        with patch.object(client._resolver, "_extract_sync", return_value=info):
            with pytest.raises(RuntimeError):
                await client.get_stream_url("vid123")

    async def test_wraps_arbitrary_exception_as_runtime_error(self):
        client = YtDlpClient()

        with patch.object(client._resolver, "_extract_sync", side_effect=ConnectionError("net down")):
            with pytest.raises(RuntimeError, match="Gagal mengambil"):
                await client.get_stream_url("vid123")

    async def test_raises_runtime_error_on_timeout(self):
        client = YtDlpClient()

        async def slow_executor(*_):
            await asyncio.sleep(999)

        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            with pytest.raises(RuntimeError, match="Timeout"):
                await client.get_stream_url("vid123")


# ---------------------------------------------------------------------------
# download_mp3()
# ---------------------------------------------------------------------------

class TestDownloadMp3:
    async def test_returns_expected_mp3_path(self, tmp_path, monkeypatch):
        client = YtDlpClient()

        with patch.object(client._downloader, "_download_sync", return_value=None):
            monkeypatch.setattr("adapters.ytdlp.downloader.CACHE_DIR", tmp_path)
            path = await client.download_mp3("abc123")

        assert path == str(tmp_path / "abc123.mp3")

    async def test_sanitizes_video_id_in_output_path(self, tmp_path, monkeypatch):
        client = YtDlpClient()

        with patch.object(client._downloader, "_download_sync", return_value=None):
            monkeypatch.setattr("adapters.ytdlp.downloader.CACHE_DIR", tmp_path)
            path = await client.download_mp3("bad/id:here")

        # Slashes and colons become underscores
        assert "/" not in path.split("/")[-1]

    async def test_resets_is_cancelled_before_download(self, tmp_path, monkeypatch):
        client = YtDlpClient()
        client._downloader.is_cancelled = True

        with patch.object(client._downloader, "_download_sync", return_value=None):
            monkeypatch.setattr("adapters.ytdlp.downloader.CACHE_DIR", tmp_path)
            await client.download_mp3("v1")

        assert client._downloader.is_cancelled is False


# ---------------------------------------------------------------------------
# cancel_download / _check_cancel_hook
# ---------------------------------------------------------------------------

class TestCancellation:
    def test_cancel_download_sets_flag(self):
        client = YtDlpClient()
        assert client._downloader.is_cancelled is False
        client.cancel_download()
        assert client._downloader.is_cancelled is True

    def test_check_cancel_hook_raises_when_cancelled(self):
        client = YtDlpClient()
        client._downloader.is_cancelled = True
        with pytest.raises(Exception, match="DownloadCancelled"):
            client._downloader._check_cancel_hook({})

    def test_check_cancel_hook_does_not_raise_when_not_cancelled(self):
        client = YtDlpClient()
        client._downloader.is_cancelled = False
        # Should not raise
        client._downloader._check_cancel_hook({})

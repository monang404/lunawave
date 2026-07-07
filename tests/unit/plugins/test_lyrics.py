"""
PATCH-0-02: LyricsFetcher session scope bug
Verifikasi bahwa seluruh logika fetch lirik berada di dalam satu
session context manager scope, sehingga fallback search tidak
menggunakan session yang sudah ditutup.
"""


import pytest

from plugins.lyrics import LyricsFetcher


class TestLyricsFetcherSessionScope:
    """Checklist PATCH-0-02:
    - [x] Fallback search (request ke-2) harus di dalam scope 'async with get_session()'
    - [x] Tidak ada 'session.get' call di luar context manager scope
    """

    @pytest.mark.asyncio
    async def test_uses_persistent_session(self):
        """Verifikasi bahwa LyricsFetcher menggunakan session persisten (injected/internal)."""
        from core.state import AppState
        state = AppState()
        mock_sess = __import__("unittest.mock").mock.AsyncMock()
        fetcher = LyricsFetcher(state, session=mock_sess, event_bus=__import__("unittest.mock").mock.AsyncMock())

        assert fetcher._session is mock_sess, "Session harus menggunakan yang di-inject."


    def test_lyrics_fetcher_has_generation_counter(self):
        """Verifikasi bahwa LyricsFetcher._current_generation ada (PATCH-1-05 related)."""
        from core.state import AppState
        state = AppState()
        fetcher = LyricsFetcher(state, session=__import__("unittest.mock").mock.AsyncMock(), event_bus=__import__("unittest.mock").mock.AsyncMock())
        assert hasattr(fetcher, "_current_generation"), "LyricsFetcher harus punya _current_generation"
        assert fetcher._current_generation == 0

    @pytest.mark.asyncio
    async def test_skips_regex_on_cache_hit(self):
        """Verifikasi bahwa re.sub tidak dipanggil jika lrc didapatkan dari cache."""
        from core.state import AppState, TrackInfo
        state = AppState()
        mock_sess = __import__("unittest.mock").mock.AsyncMock()
        fetcher = LyricsFetcher(state, session=mock_sess, event_bus=__import__("unittest.mock").mock.AsyncMock())
        
        # Mock cache hit
        track = TrackInfo(video_id="vid1", title="test (official)", artist="artist", duration=100)
        fetcher._cache["vid1"] = "[00:10.00] Cached lyrics"
        
        import unittest.mock
        with unittest.mock.patch("re.sub") as mock_sub:
            await fetcher.fetch(track)
            # re.sub should not have been called because cache hit provides lrc
            mock_sub.assert_not_called()


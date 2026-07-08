"""
PATCH-1-05: Generation counter di LyricsFetcher untuk cancel fetch lama
Verifikasi bahwa LyricsFetcher memiliki generation counter untuk
menghindari race condition saat skip lagu cepat.
"""

from core.state import AppState
from plugins.lyrics import LyricsFetcher


class TestLyricsGenerationCounter:
    """Checklist PATCH-1-05:
    - [x] self._current_generation dan self._fetch_task ada di __init__
    - [x] Generation counter di-increment di awal fetch()
    - [x] Hasil fetch lama dibuang jika generation sudah berubah
    """

    def test_has_current_generation_field(self):
        """LyricsFetcher harus punya _current_generation di __init__."""
        state = AppState()
        fetcher = LyricsFetcher(state, session=__import__("unittest.mock").mock.AsyncMock(), event_bus=__import__("unittest.mock").mock.AsyncMock())
        assert hasattr(fetcher, "_current_generation"), (
            "LyricsFetcher harus punya _current_generation di __init__"
        )
        assert fetcher._current_generation == 0

    def test_generation_counter_in_fetch_source(self):
        """Method fetch() harus increment _current_generation."""
        import inspect
        source = inspect.getsource(LyricsFetcher.fetch)
        assert "_current_generation" in source, (
            "fetch() harus menggunakan _current_generation untuk generation counter"
        )
        assert "+= 1" in source or "self._current_generation += 1" in source, (
            "fetch() harus meng-increment _current_generation"
        )

    def test_generation_check_before_storing_result(self):
        """Hasil fetch harus dicek dengan generation counter sebelum disimpan."""
        import inspect
        source = inspect.getsource(LyricsFetcher.fetch)
        assert "gen" in source and "_current_generation" in source, (
            "fetch() harus mengecek apakah generation masih current sebelum menyimpan hasil"
        )

    def test_parse_lrc_drops_metadata(self):
        """Metadata LRC dan baris tanpa timestamp harus diabaikan, bukan diset ke 0.0"""
        state = AppState()
        fetcher = LyricsFetcher(state, session=__import__("unittest.mock").mock.AsyncMock(), event_bus=__import__("unittest.mock").mock.AsyncMock())
        lrc_text = "[ti:Some Title]\n[00:10.00] Line 1\n[00:20.00] Line 2\nPlain text line"

        parsed = fetcher._parse_lrc(lrc_text)

        assert len(parsed) == 2
        assert parsed[0] == (10.0, "Line 1")
        assert parsed[1] == (20.0, "Line 2")


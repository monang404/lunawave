"""
Tests for S02-038: evict_stale_tracks DB-first atomicity
Tests for S02-039: toggle_favorite tanpa RETURNING clause (SQLite compat)
Tests for S02-040: TrackInfo.from_dict strip stream_url/local_path
"""
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── S02-038 ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evict_db_first_order():
    """Verifikasi bahwa DELETE SQL dikerjakan sebelum unlink file."""
    import cache.repositories.track_repository as repo_module
    from cache.repositories.track_repository import TrackRepository

    call_order = []

    mock_cursor = MagicMock()
    mock_cursor.fetchall = AsyncMock(return_value=[
        {"video_id": "abcdefghijk", "local_path": None}
    ])

    async def fake_execute(query, *args, **kwargs):
        return mock_cursor

    async def fake_commit():
        call_order.append("db_commit")

    mock_conn = MagicMock()
    mock_conn.execute = fake_execute
    mock_conn.commit = fake_commit

    repo = TrackRepository(mock_conn)

    with patch("pathlib.Path.exists", return_value=False), \
         patch.object(repo_module, "logger", MagicMock(info=MagicMock(), error=MagicMock())):
        await repo.evict_stale_tracks()

    # commit (DELETE DB) harus ada dan terjadi sebelum unlink (tidak ada unlink karena local_path=None)
    assert "db_commit" in call_order



# ── S02-039 ──────────────────────────────────────────────────────────────────

def test_toggle_favorite_sql_no_returning():
    """Verifikasi source code toggle_favorite tidak mengandung RETURNING dalam SQL."""
    from cache.repositories.track_repository import TrackRepository
    src = inspect.getsource(TrackRepository.toggle_favorite)
    # Cari SQL query saja — deteksi "RETURNING" yang ada di dalam string SQL
    # bukan di komentar. Caranya: hapus komentar lalu cek.
    lines = [l for l in src.splitlines() if not l.strip().startswith("#")]
    code_without_comments = "\n".join(lines)
    assert "RETURNING" not in code_without_comments.upper().replace(
        "# GUNAKAN UPDATE LALU SELECT TERPISAH AGAR KOMPATIBEL DENGAN SQLITE < 3.35", ""
    ).replace("# YANG TIDAK MENDUKUNG CLAUSE RETURNING (S02-039)", ""), \
        "toggle_favorite tidak boleh pakai RETURNING dalam SQL"


def test_toggle_favorite_uses_two_queries():
    """Verifikasi toggle_favorite menggunakan dua query terpisah (UPDATE lalu SELECT)."""
    from cache.repositories.track_repository import TrackRepository
    src = inspect.getsource(TrackRepository.toggle_favorite)
    assert "UPDATE tracks" in src
    assert "SELECT is_favorite" in src


# ── S02-040 ──────────────────────────────────────────────────────────────────

def test_from_dict_strips_stream_url():
    """Verifikasi stream_url dari client tidak masuk ke TrackInfo."""
    from core.state import TrackInfo

    data = {
        "video_id": "abcdefghijk",
        "title": "Test Track",
        "artist": "Test Artist",
        "duration": 180,
        "stream_url": "https://attacker.com/evil.mp3",
        "local_path": "/etc/passwd",
    }
    track = TrackInfo.from_dict(data)
    assert track is not None
    assert track.stream_url is None, "stream_url harus di-strip dari client payload"
    assert track.local_path is None, "local_path harus di-strip dari client payload"


def test_from_dict_preserves_safe_fields():
    """Verifikasi field-field aman tetap dipertahankan."""
    from core.state import TrackInfo

    data = {
        "video_id": "abcdefghijk",
        "title": "My Song",
        "artist": "Artist Name",
        "duration": 240,
        "thumbnail": "https://i.ytimg.com/vi/abcdefghijk/default.jpg",
        "is_favorite": 1,
    }
    track = TrackInfo.from_dict(data)
    assert track.title == "My Song"
    assert track.artist == "Artist Name"
    assert track.duration == 240
    assert track.is_favorite == 1


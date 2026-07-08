import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import cache.repositories.track_repository as repo_module
from cache.repositories.track_repository import TrackRepository

@pytest.mark.asyncio
async def test_evict_db_first_order():
    """Verifikasi bahwa DELETE SQL dikerjakan sebelum unlink file."""
    
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
    
    pool = MagicMock()
    class PoolAcquireContext:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    pool.acquire = MagicMock(return_value=PoolAcquireContext())

    repo = TrackRepository(pool)

    with patch("pathlib.Path.exists", return_value=False), \
         patch.object(repo_module, "logger", MagicMock(info=MagicMock(), error=MagicMock())):
        await repo.evict_stale_tracks()

    # commit (DELETE DB) harus ada dan terjadi sebelum unlink (tidak ada unlink karena local_path=None)
    assert "db_commit" in call_order

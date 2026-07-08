import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from cache.repositories.track_repository import TrackRepository

@pytest.mark.asyncio
async def test_evict_stale_tracks_tuple():
    conn = MagicMock()
    
    # Mock cursor
    cursor_mock = AsyncMock()
    cursor_mock.fetchall.return_value = [{"video_id": "vid1", "local_path": None}, {"video_id": "vid2", "local_path": None}]
    
    # execute returns cursor
    async def fake_execute(*args, **kwargs):
        return cursor_mock
    conn.execute = fake_execute
    conn.commit = AsyncMock()
    
    pool = MagicMock()
    class PoolAcquireContext:
        async def __aenter__(self):
            return conn
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    pool.acquire = MagicMock(return_value=PoolAcquireContext())
    
    repo = TrackRepository(pool)

    with patch("config.CACHE_DIR") as mock_cache_dir:
        # Mock pathlib Path
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_cache_dir.__truediv__.return_value = mock_path

        await repo.evict_stale_tracks()

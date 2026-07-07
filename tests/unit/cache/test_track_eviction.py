import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from cache.repositories.track_repository import TrackRepository

@pytest.mark.asyncio
async def test_evict_stale_tracks_tuple():
    conn = AsyncMock()
    # Mock return rows for fetchall
    conn.execute.return_value.fetchall.return_value = [{"video_id": "vid1"}, {"video_id": "vid2"}]
    
    repo = TrackRepository(conn)
    
    with patch("config.CACHE_DIR") as mock_cache_dir:
        # Mock pathlib Path
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_cache_dir.__truediv__.return_value = mock_path
        
        await repo.evict_stale_tracks()
        
        # Check that execute was called with a tuple, not a list
        execute_calls = conn.execute.call_args_list
        delete_call = None
        for call in execute_calls:
            if "DELETE FROM tracks WHERE video_id IN" in call[0][0]:
                delete_call = call
                break
        
        assert delete_call is not None
        assert isinstance(delete_call[0][1], tuple)
        assert delete_call[0][1] == ("vid1", "vid2")

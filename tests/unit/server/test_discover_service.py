import pytest
import sqlite3
from unittest.mock import AsyncMock, MagicMock
from server.services.discover_service import DiscoverService

@pytest.mark.asyncio
async def test_discover_service_no_keyerror():
    db_mock = MagicMock()
    
    # Create an async context manager mock for the connection execute
    conn_mock = MagicMock()
    
    class AsyncCursorMock:
        def __init__(self, rows):
            self.rows = rows
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        def __aiter__(self):
            self.idx = 0
            return self
        async def __anext__(self):
            if self.idx < len(self.rows):
                val = self.rows[self.idx]
                self.idx += 1
                return val
            else:
                raise StopAsyncIteration

    # This mock row includes stream_url now!
    row = {
        "video_id": "v1",
        "title": "t",
        "artist": "a",
        "duration": 100,
        "thumbnail": "th",
        "local_path": None,
        "stream_url": "http://stream",
        "view_count": 0,
        "play_count": 0,
        "is_favorite": 0
    }
    
    conn_mock.execute.return_value = AsyncCursorMock([row])
    db_mock.conn = conn_mock
    
    service = DiscoverService(db_mock)
    
    # Should not raise KeyError
    recent = await service.get_recent(5)
    
    assert len(recent) == 1
    assert recent[0].stream_url == "http://stream"


@pytest.mark.asyncio
async def test_get_featured_genres_logs_error():
    db_mock = MagicMock()
    conn_mock = MagicMock()
    
    class AsyncCursorErrorMock:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        def __aiter__(self):
            return self
        async def __anext__(self):
            import sqlite3
            raise sqlite3.Error("Test DB Error")

    conn_mock.execute.return_value = AsyncCursorErrorMock()
    db_mock.conn = conn_mock
    
    service = DiscoverService(db_mock)
    
    import unittest.mock
    with unittest.mock.patch("server.services.discover_service.logger") as mock_logger:
        result = await service.get_featured_genres(5)
        
        # It should return an empty list on error
        assert result == []
        
        # logger.error should be called
        mock_logger.error.assert_called_once()
        args, _ = mock_logger.error.call_args
        assert "Data error in get_featured_genres" in args[0]
        assert "Test DB Error" in args[0]

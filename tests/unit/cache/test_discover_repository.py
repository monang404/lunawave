import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio
from cache.repositories.discover_repository import DiscoverRepository
from core.state import TrackInfo

class AiosqliteCursorMock:
    def __init__(self, rows):
        self.rows = rows
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def __aiter__(self):
        self.iter = iter(self.rows)
        return self
        
    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration
            
    async def fetchall(self):
        return self.rows
        
    def __await__(self):
        yield from asyncio.sleep(0).__await__()
        return self

@pytest.fixture
def mock_db_conn():
    conn = MagicMock()
    conn.execute = MagicMock(return_value=AiosqliteCursorMock([]))
    conn.commit = AsyncMock()
    return conn

@pytest.fixture
def repo(mock_db_conn):
    return DiscoverRepository(mock_db_conn)

@pytest.mark.asyncio
async def test_increment_artist_click(repo, mock_db_conn):
    await repo.increment_artist_click("Artist A")
    mock_db_conn.execute.assert_called_once()
    mock_db_conn.commit.assert_called_once()

@pytest.mark.asyncio
async def test_increment_artist_click_no_conn():
    repo = DiscoverRepository(None)
    await repo.increment_artist_click("Artist A")

@pytest.mark.asyncio
async def test_increment_artist_click_exception(repo, mock_db_conn):
    mock_db_conn.execute.side_effect = Exception("DB Error")
    await repo.increment_artist_click("Artist A")

@pytest.mark.asyncio
async def test_increment_genre_click(repo, mock_db_conn):
    await repo.increment_genre_click("Pop")
    mock_db_conn.execute.assert_called_once()
    mock_db_conn.commit.assert_called_once()

@pytest.mark.asyncio
async def test_increment_genre_click_no_conn():
    repo = DiscoverRepository(None)
    await repo.increment_genre_click("Pop")

@pytest.mark.asyncio
async def test_increment_genre_click_exception(repo, mock_db_conn):
    mock_db_conn.execute.side_effect = Exception("DB Error")
    await repo.increment_genre_click("Pop")

class MockCursor:
    def __init__(self, rows):
        self.rows = rows
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def __aiter__(self):
        self.iter = iter(self.rows)
        return self
        
    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration
            
    async def fetchall(self):
        return self.rows

@pytest.mark.asyncio
async def test_get_genre_artists(repo, mock_db_conn):
    mock_db_conn.execute.return_value = AiosqliteCursorMock([{"nama": "Artist A"}])
    artists = await repo.get_genre_artists("Pop")
    assert artists == ["Artist A"]

@pytest.mark.asyncio
async def test_get_genre_artists_no_conn():
    repo = DiscoverRepository(None)
    assert await repo.get_genre_artists("Pop") == []

@pytest.mark.asyncio
async def test_get_genre_artists_exception(repo, mock_db_conn):
    mock_db_conn.execute.side_effect = Exception("DB Error")
    assert await repo.get_genre_artists("Pop") == []

@pytest.mark.asyncio
async def test_get_all_artists(repo, mock_db_conn):
    mock_db_conn.execute.return_value = AiosqliteCursorMock([{"nama": "A"}, {"nama": "B"}])
    artists = await repo.get_all_artists()
    assert artists == ["A", "B"]
    
    artists = await repo.get_all_artists("Kpop")
    assert artists == ["A", "B"]

@pytest.mark.asyncio
async def test_get_all_artists_no_conn():
    repo = DiscoverRepository(None)
    assert await repo.get_all_artists() == []

@pytest.mark.asyncio
async def test_get_random_songs(repo, mock_db_conn):
    mock_db_conn.execute.return_value = AiosqliteCursorMock([
        {"youtube_id": "vid1", "judul": "Song 1", "duration": 180, "nama": "Artist A"}
    ])
    songs = await repo.get_random_songs(exclude_ids={"vid2"}, artist="Artist A")
    assert len(songs) == 1
    assert songs[0].video_id == "vid1"
    assert songs[0].title == "Song 1"
    assert songs[0].artist == "Artist A"

@pytest.mark.asyncio
async def test_get_random_songs_no_conn():
    repo = DiscoverRepository(None)
    assert await repo.get_random_songs() == []

@pytest.mark.asyncio
async def test_get_artist_songs_strict(repo, mock_db_conn):
    mock_db_conn.execute.return_value = AiosqliteCursorMock([
        {"youtube_id": "vid1", "judul": "Song 1", "duration": 180, "nama": "Artist A"}
    ])
    songs = await repo.get_artist_songs_strict("Artist A")
    assert len(songs) == 1

@pytest.mark.asyncio
async def test_get_artist_songs_strict_no_conn():
    repo = DiscoverRepository(None)
    assert await repo.get_artist_songs_strict("A") == []

@pytest.mark.asyncio
async def test_get_genre_songs(repo, mock_db_conn):
    mock_db_conn.execute.return_value = AiosqliteCursorMock([
        {"youtube_id": "vid1", "judul": "Song 1", "duration": 180, "nama": "Artist A"}
    ])
    songs = await repo.get_genre_songs("Pop")
    assert len(songs) == 1

@pytest.mark.asyncio
async def test_get_genre_songs_no_conn():
    repo = DiscoverRepository(None)
    assert await repo.get_genre_songs("Pop") == []

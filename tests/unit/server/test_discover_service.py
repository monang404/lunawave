import pytest
from unittest.mock import AsyncMock, MagicMock
from server.services.discover_service import DiscoverService
from core.state import TrackInfo, VideoId, Duration

@pytest.fixture
def mock_repos():
    track_repo = MagicMock()
    track_repo.get_recent_tracks = AsyncMock(return_value=[TrackInfo(VideoId("12345678901"), "Title", "Artist", Duration(100))])
    track_repo.get_favorite_tracks = AsyncMock(return_value=[])
    track_repo.get_cached_tracks = AsyncMock(return_value=[])
    
    discover_repo = MagicMock()
    discover_repo.get_featured_artists = AsyncMock(return_value=[{"id": 1, "nama": "Artis"}])
    discover_repo.get_featured_genres = AsyncMock(return_value=[])
    
    return track_repo, discover_repo

@pytest.mark.asyncio
async def test_discover_service_caching(mock_repos):
    track_repo, discover_repo = mock_repos
    service = DiscoverService(track_repo, discover_repo)
    
    # First call - should call repo
    res1 = await service.get_recent(5)
    assert len(res1) == 1
    track_repo.get_recent_tracks.assert_called_once_with(5)
    
    # Second call - should return from cache
    res2 = await service.get_recent(5)
    assert len(res2) == 1
    assert track_repo.get_recent_tracks.call_count == 1 # Still 1!

@pytest.mark.asyncio
async def test_get_featured_artists_caching(mock_repos):
    track_repo, discover_repo = mock_repos
    service = DiscoverService(track_repo, discover_repo)
    
    res1 = await service.get_featured_artists(5)
    assert len(res1) == 1
    discover_repo.get_featured_artists.assert_called_once_with(5)
    
    res2 = await service.get_featured_artists(5)
    assert discover_repo.get_featured_artists.call_count == 1

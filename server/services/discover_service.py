"""
Purpose: Menyediakan data discover (recent dan favorites).
Subscribes to: (tidak ada)
Publishes: (tidak ada)
"""

import time
import structlog
from core.state import TrackInfo

logger = structlog.get_logger(__name__)

class SimpleTTLCache:
    def __init__(self, ttl: int = 60):
        self.ttl = ttl
        self.cache = {}
    
    def get(self, key: str):
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['time'] < self.ttl:
                return entry['data']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, data):
        self.cache[key] = {'data': data, 'time': time.time()}

class DiscoverService:
    from core.ports import DatabasePort
    def __init__(self, track_repo: DatabasePort, discover_repo: DatabasePort):
        self.track_repo = track_repo
        self.discover_repo = discover_repo
        self._cache = SimpleTTLCache(ttl=60)

    async def get_recent(self, n: int) -> list[TrackInfo]:
        cache_key = f"recent_{n}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        data = await self.track_repo.get_recent_tracks(n)
        self._cache.set(cache_key, data)
        return data

    async def get_favorites(self, n: int) -> list[TrackInfo]:
        cache_key = f"fav_{n}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
            
        data = await self.track_repo.get_favorite_tracks(n)
        self._cache.set(cache_key, data)
        return data

    async def get_cached(self, n: int) -> list[TrackInfo]:
        cache_key = f"cached_{n}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
            
        data = await self.track_repo.get_cached_tracks(n)
        self._cache.set(cache_key, data)
        return data

    async def get_featured_artists(self, n: int) -> list[dict]:
        cache_key = f"feat_artists_{n}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
            
        data = await self.discover_repo.get_featured_artists(n)
        self._cache.set(cache_key, data)
        return data

    async def get_featured_genres(self, n: int) -> list[dict]:
        cache_key = f"feat_genres_{n}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
            
        data = await self.discover_repo.get_featured_genres(n)
        self._cache.set(cache_key, data)
        return data

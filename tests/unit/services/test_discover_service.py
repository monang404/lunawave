"""tests/unit/services/test_discover_service.py — mirrors services/discover_service.py

Menggunakan in-memory Database dari fixture `db` (conftest.py) sehingga
semua query SQL benar-benar dieksekusi tanpa mock.

Purpose:
    Auto-generated purpose.

Subscribes to:
    None

Publishes:
    None
"""

import pytest

from core.state import TrackInfo
from services.discover_service import DiscoverService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_track(video_id="v1", **kwargs):
    defaults = dict(title="T", artist="A", duration=180)
    defaults.update(kwargs)
    return TrackInfo(video_id=video_id, **defaults)


@pytest.fixture
def svc(db):
    """DiscoverService wired to the in-memory test Database."""
    return DiscoverService(db=db)


# ---------------------------------------------------------------------------
# get_recent
# ---------------------------------------------------------------------------

class TestGetRecent:
    async def test_returns_empty_when_no_tracks(self, svc):
        result = await svc.get_recent(10)
        assert result == []

    async def test_returns_tracks_ordered_by_last_played_desc(self, svc, db):
        await db.upsert_track(make_track("v1"))
        await db.upsert_track(make_track("v2"))
        # increment play count sets last_played timestamp
        await db.increment_play_count("v1")
        await db.increment_play_count("v2")
        await db.increment_play_count("v1")  # v1 more recently played

        result = await svc.get_recent(10)
        ids = [t.video_id for t in result]
        assert ids[0] == "v1"

    async def test_respects_n_limit(self, svc, db):
        for i in range(5):
            await db.upsert_track(make_track(f"v{i}"))
        result = await svc.get_recent(3)
        assert len(result) <= 3

    async def test_returns_track_info_instances(self, svc, db):
        await db.upsert_track(make_track("v1", title="My Song"))
        result = await svc.get_recent(5)
        assert all(isinstance(t, TrackInfo) for t in result)

    async def test_returns_empty_when_db_has_no_conn(self):
        """Service must not crash when DB connection is absent."""
        class NoConnDB:
            pass  # no conn attribute

        svc = DiscoverService(db=NoConnDB())
        result = await svc.get_recent(5)
        assert result == []


# ---------------------------------------------------------------------------
# get_favorites
# ---------------------------------------------------------------------------

class TestGetFavorites:
    async def test_returns_empty_when_no_tracks(self, svc):
        result = await svc.get_favorites(10)
        assert result == []

    async def test_returns_favorited_tracks(self, svc, db):
        await db.upsert_track(make_track("v1"))
        await db.upsert_track(make_track("v2"))
        await db.toggle_favorite("v1")

        result = await svc.get_favorites(10)
        ids = [t.video_id for t in result]
        assert "v1" in ids

    async def test_returns_tracks_with_play_count_too(self, svc, db):
        await db.upsert_track(make_track("v1"))
        await db.increment_play_count("v1")

        result = await svc.get_favorites(10)
        assert any(t.video_id == "v1" for t in result)

    async def test_favorites_ordered_before_play_count_tracks(self, svc, db):
        await db.upsert_track(make_track("played"))
        await db.increment_play_count("played")
        await db.upsert_track(make_track("fav"))
        await db.toggle_favorite("fav")

        result = await svc.get_favorites(10)
        ids = [t.video_id for t in result]
        assert ids.index("fav") < ids.index("played")

    async def test_respects_n_limit(self, svc, db):
        for i in range(5):
            await db.upsert_track(make_track(f"v{i}"))
            await db.increment_play_count(f"v{i}")
        result = await svc.get_favorites(2)
        assert len(result) <= 2


# ---------------------------------------------------------------------------
# get_cached
# ---------------------------------------------------------------------------

class TestGetCached:
    async def test_returns_only_tracks_with_local_path(self, svc, db):
        await db.upsert_track(make_track("v1"), local_path="/mp3/v1.mp3")
        await db.upsert_track(make_track("v2"))  # no local_path

        result = await svc.get_cached(10)
        ids = [t.video_id for t in result]
        assert "v1" in ids
        assert "v2" not in ids

    async def test_returns_empty_when_no_cached_tracks(self, svc, db):
        await db.upsert_track(make_track("v1"))
        result = await svc.get_cached(10)
        assert result == []

    async def test_respects_n_limit(self, svc, db):
        for i in range(5):
            await db.upsert_track(make_track(f"v{i}"), local_path=f"/mp3/v{i}.mp3")
        result = await svc.get_cached(2)
        assert len(result) <= 2


# ---------------------------------------------------------------------------
# get_featured_artists
# ---------------------------------------------------------------------------

class TestGetFeaturedArtists:
    async def test_returns_empty_when_no_artists(self, svc):
        result = await svc.get_featured_artists(5)
        assert result == []

    async def test_returns_artist_dicts(self, svc, db):
        await db.conn.execute("INSERT INTO artists (id, nama, kategori) VALUES (1, 'Band X', 'band')")
        await db.conn.commit()

        result = await svc.get_featured_artists(5)
        assert len(result) >= 1
        assert "nama" in result[0]
        assert "click_count" in result[0]

    async def test_returns_at_most_n_artists(self, svc, db):
        for i in range(10):
            await db.conn.execute(f"INSERT INTO artists (id, nama) VALUES ({i+1}, 'Artist {i}')")
        await db.conn.commit()

        result = await svc.get_featured_artists(3)
        assert len(result) <= 3

    async def test_click_count_defaults_to_zero(self, svc, db):
        await db.conn.execute("INSERT INTO artists (id, nama) VALUES (1, 'New Artist')")
        await db.conn.commit()

        result = await svc.get_featured_artists(5)
        assert result[0]["click_count"] == 0


# ---------------------------------------------------------------------------
# get_featured_genres
# ---------------------------------------------------------------------------

class TestGetFeaturedGenres:
    async def test_returns_empty_when_no_genres(self, svc):
        result = await svc.get_featured_genres(5)
        assert result == []

    async def test_returns_genre_dicts_with_required_keys(self, svc, db):
        await db.conn.execute("INSERT INTO genres (id, nama_genre) VALUES (1, 'rock')")
        await db.conn.commit()

        result = await svc.get_featured_genres(5)
        assert len(result) >= 1
        assert "nama_genre" in result[0]
        assert "click_count" in result[0]
        assert "id" in result[0]

    async def test_returns_at_most_n_genres(self, svc, db):
        for i in range(8):
            await db.conn.execute(f"INSERT INTO genres (id, nama_genre) VALUES ({i+1}, 'genre_{i}')")
        await db.conn.commit()

        result = await svc.get_featured_genres(4)
        assert len(result) <= 4

    async def test_click_count_defaults_to_zero(self, svc, db):
        await db.conn.execute("INSERT INTO genres (id, nama_genre) VALUES (1, 'jazz')")
        await db.conn.commit()

        result = await svc.get_featured_genres(5)
        assert result[0]["click_count"] == 0

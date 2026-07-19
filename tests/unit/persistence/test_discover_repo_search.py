"""
Module: tests.unit.persistence.test_discover_repo_search

Purpose:
    Unit tests for DiscoverRepository.search_tracks() (Quick Search
    Discover, persistence/discover_repo.py) — separate file from
    test_discover_repo.py per task breakdown T-A2, so the new method's
    coverage doesn't inflate the existing file.

Responsibilities:
    - Cover: title match, artist match, no match, kategori (Solo/Band,
      K1) filter, decade (K2) filter, and empty/whitespace query.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""


async def _make_artist(db, id, nama, kategori="band", tahun_aktif="2020s"):
    await db.conn.execute(
        "INSERT INTO artists (id, nama, kategori, tahun_aktif) VALUES (?, ?, ?, ?)",
        (id, nama, kategori, tahun_aktif),
    )
    await db.conn.commit()


async def _make_track(db, video_id, title, artist, duration=180):
    await db.conn.execute(
        "INSERT INTO tracks (video_id, title, artist, duration) VALUES (?, ?, ?, ?)",
        (video_id, title, artist, duration),
    )
    await db.conn.commit()


class TestSearchTracksBasicMatch:
    async def test_matches_by_title(self, db):
        await _make_track(db, "v1", "Bohemian Rhapsody", "Queen")
        await _make_track(db, "v2", "Another Song", "Other Artist")
        result = await db.discover.search_tracks("Bohemian")
        assert [r["video_id"] for r in result] == ["v1"]

    async def test_matches_by_artist(self, db):
        await _make_track(db, "v1", "Some Track", "Queen")
        await _make_track(db, "v2", "Other Track", "Nirvana")
        result = await db.discover.search_tracks("Queen")
        assert [r["video_id"] for r in result] == ["v1"]

    async def test_no_match_returns_empty_list(self, db):
        await _make_track(db, "v1", "Some Track", "Queen")
        result = await db.discover.search_tracks("Nonexistent Query")
        assert result == []

    async def test_query_empty_returns_empty_list_without_error(self, db):
        await _make_track(db, "v1", "Some Track", "Queen")
        assert await db.discover.search_tracks("") == []

    async def test_query_whitespace_only_returns_empty_list(self, db):
        await _make_track(db, "v1", "Some Track", "Queen")
        assert await db.discover.search_tracks("   ") == []

    async def test_no_conn_returns_empty_list(self, db):
        db.discover._conn = None
        assert await db.discover.search_tracks("Queen") == []


class TestSearchTracksKategoriFilter:
    async def test_filters_by_kategori_solo(self, db):
        await _make_artist(db, 1, "Solo Singer", kategori="solo")
        await _make_artist(db, 2, "The Band", kategori="band")
        await _make_track(db, "v1", "Song A", "Solo Singer")
        await _make_track(db, "v2", "Song B", "The Band")

        result = await db.discover.search_tracks("Song", kategori="solo")
        assert [r["video_id"] for r in result] == ["v1"]

    async def test_filters_by_kategori_band(self, db):
        await _make_artist(db, 1, "Solo Singer", kategori="solo")
        await _make_artist(db, 2, "The Band", kategori="band")
        await _make_track(db, "v1", "Song A", "Solo Singer")
        await _make_track(db, "v2", "Song B", "The Band")

        result = await db.discover.search_tracks("Song", kategori="band")
        assert [r["video_id"] for r in result] == ["v2"]

    async def test_track_artist_unmatched_to_any_artist_excluded_when_kategori_filter_active(
        self, db
    ):
        """Sama seperti caveat get_taste_spectrum: track dari artist yang
        tidak match by-name ke tabel artists tidak ikut kehitung begitu
        filter kategori aktif."""
        await _make_track(db, "v1", "Song A", "Unknown Uploader")
        result = await db.discover.search_tracks("Song", kategori="solo")
        assert result == []


class TestSearchTracksDecadeFilter:
    async def test_filters_by_decade(self, db):
        await _make_artist(db, 1, "Nineties Artist", tahun_aktif="1990s")
        await _make_artist(db, 2, "Twenties Artist", tahun_aktif="2020s")
        await _make_track(db, "v1", "Song A", "Nineties Artist")
        await _make_track(db, "v2", "Song B", "Twenties Artist")

        result = await db.discover.search_tracks("Song", decade=1990)
        assert [r["video_id"] for r in result] == ["v1"]

    async def test_combined_kategori_and_decade_filter(self, db):
        await _make_artist(db, 1, "Nineties Solo", kategori="solo", tahun_aktif="1990s")
        await _make_artist(db, 2, "Nineties Band", kategori="band", tahun_aktif="1990s")
        await _make_track(db, "v1", "Song A", "Nineties Solo")
        await _make_track(db, "v2", "Song B", "Nineties Band")

        result = await db.discover.search_tracks("Song", kategori="solo", decade=1990)
        assert [r["video_id"] for r in result] == ["v1"]

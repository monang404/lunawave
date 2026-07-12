"""tests/unit/cache/test_db.py — mirrors cache/db.py

Uses the `db` fixture from tests/conftest.py: an in-memory SQLite
`Database`, migrated and ready to use.
"""

import time

from core.state import TrackInfo


def make_track(video_id="vid1", **overrides):
    defaults = dict(video_id=video_id, title="Title", artist="Artist", duration=200)
    defaults.update(overrides)
    return TrackInfo(**defaults)


async def test_upsert_and_get_track_round_trip(db):
    track = make_track()
    await db.upsert_track(track, stream_url="https://stream/1", local_path="/mp3/1.mp3")
    result = await db.get_track("vid1")
    assert result is not None
    assert result.video_id == "vid1"
    assert result.title == "Title"
    assert result.artist == "Artist"
    assert result.duration == 200
    assert result.stream_url == "https://stream/1"
    assert result.local_path == "/mp3/1.mp3"


async def test_get_track_returns_none_for_missing_video_id(db):
    assert await db.get_track("does-not-exist") is None


async def test_upsert_track_updates_metadata_on_conflict(db):
    await db.upsert_track(make_track(title="Old Title"))
    await db.upsert_track(make_track(title="New Title"))
    result = await db.get_track("vid1")
    assert result.title == "New Title"


async def test_upsert_track_without_stream_url_preserves_existing_stream_url(db):
    await db.upsert_track(make_track(), stream_url="https://keep-me")
    await db.upsert_track(make_track(title="Updated"))  # no stream_url passed
    result = await db.get_track("vid1")
    assert result.stream_url == "https://keep-me"
    assert result.title == "Updated"


async def test_update_stream_url_only_does_not_touch_metadata(db):
    await db.upsert_track(make_track(title="Keep This Title"))
    await db.update_stream_url_only("vid1", "https://fresh-url")
    result = await db.get_track("vid1")
    assert result.title == "Keep This Title"
    assert result.stream_url == "https://fresh-url"


async def test_set_local_path_can_set_and_clear(db):
    await db.upsert_track(make_track())
    await db.set_local_path("vid1", "/mp3/vid1.mp3")
    assert (await db.get_track("vid1")).local_path == "/mp3/vid1.mp3"
    await db.set_local_path("vid1", None)
    assert (await db.get_track("vid1")).local_path is None


async def test_increment_play_count_increments_and_sets_last_played(db):
    await db.upsert_track(make_track())
    before = await db.get_track("vid1")
    assert before.play_count == 0
    await db.increment_play_count("vid1")
    after = await db.get_track("vid1")
    assert after.play_count == 1
    assert after.last_played is not None


async def test_toggle_favorite_flips_state_and_is_atomic(db):
    await db.upsert_track(make_track())
    assert (await db.get_track("vid1")).is_favorite == 0
    new_state = await db.toggle_favorite("vid1")
    assert new_state == 1
    assert (await db.get_track("vid1")).is_favorite == 1
    new_state = await db.toggle_favorite("vid1")
    assert new_state == 0


async def test_toggle_favorite_on_missing_track_returns_zero(db):
    assert await db.toggle_favorite("nope") == 0


async def test_evict_stale_tracks_removes_unplayed_stale_and_keeps_others(db):
    stale_ts = int(time.time()) - (31 * 24 * 3600)
    fresh_ts = int(time.time())

    await db.upsert_track(make_track(video_id="stale-no-url"))
    await db.upsert_track(make_track(video_id="stale-old-url"), stream_url="https://old")
    # backdate stream_url_ts on the stale-old-url row directly
    await db.conn.execute(
        "UPDATE tracks SET stream_url_ts=? WHERE video_id=?", (stale_ts, "stale-old-url")
    )
    await db.upsert_track(make_track(video_id="fresh"), stream_url="https://fresh")
    await db.upsert_track(make_track(video_id="favorite"))
    await db.toggle_favorite("favorite")
    await db.upsert_track(make_track(video_id="local-file"), local_path="/mp3/local.mp3")
    await db.upsert_track(make_track(video_id="played"))
    await db.increment_play_count("played")
    await db.conn.commit()

    deleted = await db.evict_stale_tracks()

    assert deleted == 2
    assert await db.get_track("stale-no-url") is None
    assert await db.get_track("stale-old-url") is None
    assert await db.get_track("fresh") is not None
    assert await db.get_track("favorite") is not None
    assert await db.get_track("local-file") is not None
    assert await db.get_track("played") is not None


async def test_create_verify_delete_session_lifecycle(db):
    now = int(time.time())
    await db.create_session("token-123", now + 3600)
    assert await db.verify_session("token-123") is True
    await db.delete_session("token-123")
    assert await db.verify_session("token-123") is False


async def test_verify_session_unknown_token_returns_false(db):
    assert await db.verify_session("never-created") is False


async def test_verify_session_expired_token_returns_false_and_self_deletes(db):
    """Regression test — session expiry must use wall-clock Unix time
    (time.time()), never a monotonic clock, since expires_at is persisted
    and compared across process restarts. A monotonic-clock comparison
    would make every persisted session look expired (or never expired)
    depending on the process's monotonic clock origin."""
    now = int(time.time())
    await db.create_session("expired-token", now - 10)  # already in the past
    assert await db.verify_session("expired-token") is False
    # verify_session() deletes expired rows as a side effect — confirm it's gone.
    async with db.conn.execute(
        "SELECT 1 FROM sessions WHERE token = ?", ("expired-token",)
    ) as cursor:
        assert await cursor.fetchone() is None


async def test_verify_session_boundary_expires_at_equal_now_is_expired(db):
    now = int(time.time())
    await db.create_session("boundary-token", now)
    # expires_at > now is required to be valid; equal-to-now must be expired.
    assert await db.verify_session("boundary-token") is False


async def test_cleanup_sessions_removes_all_expired_but_keeps_valid(db):
    now = int(time.time())
    await db.create_session("old-1", now - 100)
    await db.create_session("old-2", now - 1)
    await db.create_session("valid", now + 100)
    await db.cleanup_sessions()
    assert await db.verify_session("old-1") is False
    assert await db.verify_session("old-2") is False
    assert await db.verify_session("valid") is True


async def test_increment_artist_and_genre_click(db):
    await db.conn.execute("INSERT INTO artists (id, nama, kategori) VALUES (1, 'Artist A', 'band')")
    await db.conn.execute("INSERT INTO genres (id, nama_genre) VALUES (1, 'rock')")
    await db.conn.commit()

    await db.increment_artist_click("Artist A")
    await db.increment_genre_click("rock")

    async with db.conn.execute("SELECT click_count FROM artists WHERE nama='Artist A'") as cur:
        row = await cur.fetchone()
        assert row["click_count"] == 1

    async with db.conn.execute("SELECT click_count FROM genres WHERE nama_genre='rock'") as cur:
        row = await cur.fetchone()
        assert row["click_count"] == 1


async def test_get_all_artists_filters_by_kategori(db):
    await db.conn.execute("INSERT INTO artists (id, nama, kategori) VALUES (1, 'Solo Singer', 'individu')")
    await db.conn.execute("INSERT INTO artists (id, nama, kategori) VALUES (2, 'The Band', 'band')")
    await db.conn.commit()

    all_artists = await db.get_all_artists()
    assert set(all_artists) == {"Solo Singer", "The Band"}

    band_only = await db.get_all_artists(kategori="band")
    assert band_only == ["The Band"]


async def test_get_genre_artists_returns_only_artists_in_that_genre(db):
    await db.conn.execute("INSERT INTO artists (id, nama) VALUES (1, 'Rock Artist')")
    await db.conn.execute("INSERT INTO artists (id, nama) VALUES (2, 'Jazz Artist')")
    await db.conn.execute("INSERT INTO genres (id, nama_genre) VALUES (1, 'rock')")
    await db.conn.execute("INSERT INTO genres (id, nama_genre) VALUES (2, 'jazz')")
    await db.conn.execute("INSERT INTO artist_genres (artist_id, genre_id) VALUES (1, 1)")
    await db.conn.execute("INSERT INTO artist_genres (artist_id, genre_id) VALUES (2, 2)")
    await db.conn.commit()

    result = await db.get_genre_artists("rock", limit=10)
    assert result == ["Rock Artist"]


async def test_init_is_idempotent_when_called_twice_on_a_file_backed_db(tmp_path):
    from cache.db import Database

    path = tmp_path / "idempotent.db"
    database = Database(db_path=path)
    await database.init()
    await database.close()

    # Re-opening and re-running migrations must not raise.
    database2 = Database(db_path=path)
    await database2.init()
    await database2.close()

"""
Module: tests.unit.persistence.test_track_repo

Purpose:
    Unit tests for track metadata operations in the database.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - core.state

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
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
    await db.upsert_track(make_track(title="Updated"))
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

    await db.upsert_track(make_track(video_id="stale-no-url"))
    await db.upsert_track(make_track(video_id="stale-old-url"), stream_url="https://old")
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

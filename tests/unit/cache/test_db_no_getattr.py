import pytest
from cache.db import Database

def test_database_no_getattr_magic():
    """Verify that Database explicitly defines repository methods and does not have __getattr__."""
    db = Database()
    
    # Check that it doesn't have __getattr__
    assert not hasattr(db.__class__, '__getattr__'), "Database should not use __getattr__ magic proxy"
    
    # Check that methods are explicitly defined
    expected_methods = [
        "get_track",
        "upsert_track",
        "update_stream_url_only",
        "set_local_path",
        "increment_play_count",
        "toggle_favorite",
        "evict_stale_tracks",
        "increment_artist_click",
        "increment_genre_click",
        "get_genre_artists",
        "get_all_artists",
        "get_random_songs",
        "get_artist_songs_strict",
        "get_genre_songs",
        "create_session",
        "verify_session",
        "delete_session",
        "cleanup_sessions"
    ]
    
    for method in expected_methods:
        assert hasattr(db, method), f"Database must explicitly define {method}"
        assert callable(getattr(db, method)), f"Database.{method} must be callable"

def test_database_attribute_error_on_missing():
    db = Database()
    with pytest.raises(AttributeError):
        _ = db.this_method_does_not_exist

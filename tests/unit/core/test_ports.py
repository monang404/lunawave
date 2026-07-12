"""tests/unit/core/test_ports.py — mirrors core/ports.py

Priority: Rendah — these are structural Protocols with no runtime
behaviour of their own. We just make sure our test fakes (and the real
in-repo implementations) actually satisfy the ports they claim to.
"""

from core.ports import AudioPlayerPort, MediaExtractorPort

from tests.fakes.fake_audio_player import FakeAudioPlayer
from tests.fakes.fake_media_extractor import FakeMediaExtractor


def test_fake_audio_player_has_all_audio_player_port_methods():
    required = ["connect", "close", "play", "pause", "resume", "stop", "set_volume", "seek"]
    for name in required:
        assert hasattr(FakeAudioPlayer, name), f"FakeAudioPlayer missing {name}()"
    assert hasattr(FakeAudioPlayer(), "is_connected")


def test_fake_media_extractor_has_all_media_extractor_port_methods():
    required = ["search", "extract_info", "get_stream_url", "download_mp3", "cancel_download"]
    for name in required:
        assert hasattr(FakeMediaExtractor, name), f"FakeMediaExtractor missing {name}()"


def test_real_database_implements_track_and_session_repository_ports():
    from cache.db import Database

    required = [
        "upsert_track", "update_stream_url_only", "get_track", "increment_play_count",
        "create_session", "verify_session", "delete_session", "cleanup_sessions",
        "init", "close",
    ]
    for name in required:
        assert hasattr(Database, name), f"Database missing {name}() required by DatabasePort"


def test_ports_are_defined_as_protocol_classes():
    import typing

    assert typing.Protocol in AudioPlayerPort.__mro__
    assert typing.Protocol in MediaExtractorPort.__mro__

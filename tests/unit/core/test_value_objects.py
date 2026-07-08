from core.constants import MAX_VOLUME
from core.value_objects import Duration, VideoId, Volume


def test_volume_clamp():
    assert Volume(50) == 50
    assert Volume(-10) == 0
    assert Volume(MAX_VOLUME + 50) == MAX_VOLUME
    assert Volume(MAX_VOLUME) == MAX_VOLUME

def test_video_id():
    import pytest
    with pytest.raises(ValueError):
        VideoId("invalid_id")
    assert VideoId("a" * 11) == "a" * 11

def test_duration():
    assert Duration(120) == 120
    assert Duration(-5) == 0

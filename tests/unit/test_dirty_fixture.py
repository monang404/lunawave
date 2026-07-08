import json
from pathlib import Path
from core.state import TrackInfo

def test_dirty_fixture_handling():
    fixture_path = Path("tests/fixtures/sample_track_dirty.json")
    assert fixture_path.exists()
    
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    track = TrackInfo.from_dict({
        "video_id": data.get("id"),
        "title": data.get("title") or "Unknown Title",
        "artist": data.get("uploader") or "Unknown Artist",
        "duration": data.get("duration") or 0,
        "url": data.get("webpage_url")
    })
    
    assert track.video_id == "dIrTyVidEo1"
    assert track.title == "Unknown Title"
    assert track.duration == 0

import pytest
import os
import json
from pathlib import Path
from core.state import AppState, PlaybackMode, PlayerStatus, AudioOutput, TrackInfo
from core.value_objects import VideoId, Duration, Volume
from collections import deque

@pytest.fixture
def temp_state_file(tmp_path):
    return tmp_path / "data" / "state.json"

@pytest.mark.asyncio
async def test_app_state_save_and_load(temp_state_file):
    # Setup initial state
    original = AppState()
    original.status = PlayerStatus.PLAYING
    original.playback_mode = PlaybackMode.RADIO
    original.volume = Volume(50)
    original.sponsorblock_active = False
    
    t1 = TrackInfo(video_id=VideoId("11111111111"), title="Song 1", artist="Artist 1", duration=Duration(200))
    t2 = TrackInfo(video_id=VideoId("22222222222"), title="Song 2", artist="Artist 2", duration=Duration(300))
    
    original.current_track = t1
    original.queue.append(t2)
    original.history.append(t1)
    
    # Save
    await original.save_to_disk(temp_state_file)
    
    assert temp_state_file.exists()
    
    # Load
    loaded = await AppState.load_from_disk(temp_state_file)
    
    # PLAYING status should be restored as PAUSED so engine can resume cleanly
    assert loaded.status == PlayerStatus.PAUSED
    assert loaded.playback_mode == PlaybackMode.RADIO
    assert loaded.volume == Volume(50)
    assert loaded.sponsorblock_active == False
    
    assert loaded.current_track is not None
    assert loaded.current_track.video_id == "11111111111"
    
    assert len(loaded.queue) == 1
    assert loaded.queue[0].video_id == "22222222222"
    
    assert len(loaded.history) == 1
    assert loaded.history[0].video_id == "11111111111"

@pytest.mark.asyncio
async def test_app_state_load_non_existent(temp_state_file):
    loaded = await AppState.load_from_disk(temp_state_file)
    assert loaded.status == PlayerStatus.IDLE
    assert loaded.current_track is None

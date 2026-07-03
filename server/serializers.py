import re
from typing import Optional

from core.state import AppState, AudioOutput, TrackInfo

VIDEO_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{11}$")

def track_to_dict(track: Optional[TrackInfo]) -> Optional[dict]:
    if not track:
        return None
    return {
        "video_id": track.video_id,
        "title": track.title,
        "artist": track.artist,
        "duration": track.duration,
        "thumbnail": track.thumbnail,
        "is_cached": bool(track.local_path),
        "view_count": track.view_count,
        "is_favorite": bool(getattr(track, "is_favorite", 0)),
    }

def state_to_dict(state: AppState) -> dict:
    return {
        "status": state.status.name,
        "playback_mode": state.playback_mode.name,
        "current_track": track_to_dict(state.current_track),
        "position": state.position,
        "duration": state.duration,
        "volume": state.volume,
        "audio_output": getattr(state, "audio_output", AudioOutput.DEVICE).value,
        "sponsorblock_active": state.sponsorblock_active,
        "queue": [track_to_dict(t) for t in state.queue],
        "radio_queue": [track_to_dict(t) for t in state.radio_queue],
        "history_count": len(state.history),
        "lyrics_lines": list(state.lyrics_lines),
        "lyrics_timestamps": list(state.lyrics_timestamps),
        "lyrics_index": state.lyrics_index,
        "lyrics_offset": state.lyrics_offset,
        "active_tab": state.active_tab,
        "error_msg": state.error_msg,
        "is_online": state.is_online,
        "download_progress": state.download_progress,
    }

def dict_to_track(data: dict) -> Optional[TrackInfo]:
    video_id = data.get("video_id")
    if not video_id or not VIDEO_ID_REGEX.match(str(video_id)):
        return None
    duration = int(data.get("duration", 0))
    if duration < 0:
        duration = 0
    return TrackInfo(
        video_id=video_id,
        title=str(data.get("title", "Unknown"))[:255],
        artist=str(data.get("artist", "Unknown"))[:255],
        duration=duration,
        thumbnail=data.get("thumbnail"),
        local_path=data.get("local_path"),
        stream_url=data.get("stream_url"),
        view_count=data.get("view_count"),
        is_favorite=int(data.get("is_favorite", False)),
    )

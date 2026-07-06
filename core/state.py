"""
Purpose: Menyimpan state aplikasi YTGUI V2, termasuk status pemutar, mode pemutaran, lagu saat ini, antrean, riwayat, status download, lirik, dan tab aktif.
Subscribes to: (tidak ada)
Publishes: (tidak ada)
"""

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


from core.value_objects import VideoId, Volume, Duration

class PlayerStatus(Enum):
    IDLE     = auto()
    LOADING  = auto()
    PLAYING  = auto()
    PAUSED   = auto()
    ERROR    = auto()

class AudioOutput(str, Enum):
    DEVICE = "device"
    BROWSER = "browser"

class PlaybackMode(Enum):
    QUEUE = auto()
    RADIO = auto()

@dataclass
class TrackInfo:
    video_id:   VideoId
    title:      str
    artist:     str
    duration:   Duration
    thumbnail:  Optional[str] = None
    local_path: Optional[str] = None
    stream_url: Optional[str] = None
    view_count: Optional[int] = None
    stream_url_ts: Optional[int] = None
    play_count: Optional[int] = None
    last_played: Optional[int] = None
    is_favorite: Optional[int] = 0

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "artist": self.artist,
            "duration": self.duration,
            "thumbnail": self.thumbnail,
            "is_cached": bool(self.local_path),
            "view_count": self.view_count,
            "is_favorite": bool(getattr(self, "is_favorite", 0)),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Optional['TrackInfo']:
        if not data:
            return None
        try:
            video_id = VideoId(data.get("video_id", ""))
        except ValueError:
            return None
        
        duration = Duration(data.get("duration", 0))
        
        return cls(
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

from core.constants import DEFAULT_VOLUME

@dataclass
class AppState:
    status:          PlayerStatus  = PlayerStatus.IDLE
    playback_mode:   PlaybackMode  = PlaybackMode.QUEUE
    audio_output:    AudioOutput   = AudioOutput.BROWSER
    current_track:   Optional[TrackInfo] = None
    position:        float = 0.0
    duration:        Duration = field(default_factory=lambda: Duration(0))
    volume:          Volume = field(default_factory=lambda: Volume(DEFAULT_VOLUME))
    sponsorblock_active: bool = True

    queue:           deque = field(default_factory=deque)
    radio_queue:     deque = field(default_factory=deque)
    history:         deque = field(default_factory=lambda: deque(maxlen=50))

    lyrics_lines:    list[str] = field(default_factory=list)
    lyrics_timestamps: list[float] = field(default_factory=list)
    lyrics_index:    int = 0
    lyrics_offset:   float = 0.0
    lyrics_loading:  bool = False

    active_tab:      str  = "home"
    error_msg:       Optional[str] = None
    is_online:       bool = True

    download_progress: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status.name,
            "playback_mode": self.playback_mode.name,
            "current_track": self.current_track.to_dict() if self.current_track else None,
            "position": self.position,
            "duration": self.duration,
            "volume": self.volume,
            "audio_output": getattr(self, "audio_output", AudioOutput.DEVICE).value,
            "sponsorblock_active": self.sponsorblock_active,
            "queue": [t.to_dict() for t in self.queue],
            "radio_queue": [t.to_dict() for t in self.radio_queue],
            "history_count": len(self.history),
            "lyrics_lines": list(self.lyrics_lines),
            "lyrics_timestamps": list(self.lyrics_timestamps),
            "lyrics_index": self.lyrics_index,
            "lyrics_offset": self.lyrics_offset,
            "active_tab": self.active_tab,
            "error_msg": self.error_msg,
            "is_online": self.is_online,
            "download_progress": self.download_progress,
        }

"""
Purpose: Menyimpan state aplikasi YTGUI V2, termasuk status pemutar, mode pemutaran, lagu saat ini, antrean, riwayat, status download, lirik, dan tab aktif.
Subscribes to: (tidak ada)
Publishes: (tidak ada)
"""

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from pathlib import Path
import json

import aiofiles
import structlog

from core.value_objects import Duration, VideoId, Volume


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
    is_favorite: bool = False

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "artist": self.artist,
            "duration": self.duration,
            "thumbnail": self.thumbnail,
            "is_cached": bool(self.local_path),
            "view_count": self.view_count,
            "is_favorite": bool(self.is_favorite),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Optional['TrackInfo']:
        if not data:
            return None
        try:
            video_id = VideoId(data.get("video_id", ""))
        except ValueError as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.error(f"TrackInfo parsing gagal: {e}", raw_data=data)
            return None

        duration = Duration(data.get("duration", 0))

        return cls(
            video_id=video_id,
            title=str(data.get("title", "Unknown"))[:255],
            artist=str(data.get("artist", "Unknown"))[:255],
            duration=duration,
            thumbnail=data.get("thumbnail"),
            # stream_url dan local_path TIDAK diambil dari client payload (S02-040).
            # Field ini hanya boleh diisi dari DB/server untuk mencegah SSRF/injection.
            local_path=None,
            stream_url=None,
            view_count=data.get("view_count"),
            is_favorite=bool(data.get("is_favorite", False)),
        )


import asyncio

from core.constants import DEFAULT_VOLUME


@dataclass
class AppState:
    lock:            asyncio.Lock = field(default_factory=asyncio.Lock, repr=False, init=False)
    status:          PlayerStatus  = PlayerStatus.IDLE
    playback_mode:   PlaybackMode  = PlaybackMode.QUEUE
    audio_output:    AudioOutput   = AudioOutput.BROWSER
    current_track:   Optional[TrackInfo] = None
    position:        float = 0.0
    duration:        Duration = field(default_factory=lambda: Duration(0))
    volume:          Volume = field(default_factory=lambda: Volume(DEFAULT_VOLUME))
    sponsorblock_active: bool = True

    queue:           list = field(default_factory=list)
    radio_queue:           list = field(default_factory=list)
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

    def to_persistent_dict(self) -> dict:
        """Serialize state untuk disimpan ke disk. Mengabaikan state temporer seperti posisi."""
        return {
            "status": self.status.name,
            "playback_mode": self.playback_mode.name,
            "current_track": self.current_track.to_dict() if self.current_track else None,
            "volume": self.volume,
            "audio_output": getattr(self, "audio_output", AudioOutput.DEVICE).value,
            "sponsorblock_active": self.sponsorblock_active,
            "queue": [t.to_dict() for t in self.queue],
            "radio_queue": [t.to_dict() for t in self.radio_queue],
            "history": [t.to_dict() for t in self.history],
        }

    async def save_to_disk(self, path: Path):
        """Menyimpan state ke file JSON."""
        data = self.to_persistent_dict()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(path, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            structlog.get_logger(__name__).error(f"Gagal menyimpan AppState: {e}")

    @classmethod
    async def load_from_disk(cls, path: Path) -> 'AppState':
        """Memuat state dari file JSON jika ada, jika tidak kembalikan AppState baru."""
        state = cls()
        if not path.exists():
            return state

        try:
            async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)

            if "status" in data:
                # Jangan langsung set status PLAYING/LOADING karena butuh di-resume ulang oleh engine
                loaded_status = PlayerStatus[data["status"]]
                if loaded_status in (PlayerStatus.PLAYING, PlayerStatus.LOADING):
                    loaded_status = PlayerStatus.PAUSED
                state.status = loaded_status
            
            if "playback_mode" in data:
                state.playback_mode = PlaybackMode[data["playback_mode"]]
            if "volume" in data:
                state.volume = Volume(data["volume"])
            if "audio_output" in data:
                state.audio_output = AudioOutput(data["audio_output"])
            if "sponsorblock_active" in data:
                state.sponsorblock_active = bool(data["sponsorblock_active"])
            
            if data.get("current_track"):
                state.current_track = TrackInfo.from_dict(data["current_track"])
            
            if "queue" in data:
                state.queue = [TrackInfo.from_dict(t) for t in data["queue"] if t]
            if "radio_queue" in data:
                state.radio_queue = [TrackInfo.from_dict(t) for t in data["radio_queue"] if t]
            if "history" in data:
                # Default maxlen untuk history adalah 50
                state.history = deque((TrackInfo.from_dict(t) for t in data["history"] if t), maxlen=50)

        except Exception as e:
            structlog.get_logger(__name__).error(f"Gagal memuat AppState: {e}")
            
        return state

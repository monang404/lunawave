"""
Module: core.state

Purpose:
    Define shared application state dataclasses, enums, and the single
    mutable AppState object for LunaWave.

Responsibilities:
    - Provide TrackInfo, AppState, PlayerStatus, PlaybackMode, AudioOutput.
    - Hold all runtime state (queue, lyrics, download progress, volume).

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread only (mutated only from the asyncio event loop).
"""

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, StrEnum, auto


class PlayerStatus(Enum):
    IDLE = auto()
    LOADING = auto()
    PLAYING = auto()
    PAUSED = auto()
    ERROR = auto()


class AudioOutput(StrEnum):
    DEVICE = "device"
    BROWSER = "browser"


class PlaybackMode(Enum):
    QUEUE = auto()  # user-directed
    RADIO = auto()  # autonomous, self-sustaining


@dataclass
class TrackInfo:
    video_id: str
    title: str
    artist: str
    duration: int
    thumbnail: str | None = None
    local_path: str | None = None
    stream_url: str | None = None
    view_count: int | None = None
    stream_url_ts: int | None = None
    play_count: int | None = None
    last_played: int | None = None
    is_favorite: int | None = 0
    loudness_lufs: float | None = None
    last_position: float | None = 0.0


@dataclass
class AppState:
    # Playback
    status: PlayerStatus = PlayerStatus.IDLE
    playback_speed: float = 1.0
    loop_mode: str = "off"
    playback_mode: PlaybackMode = PlaybackMode.QUEUE
    audio_output: AudioOutput = AudioOutput.BROWSER
    current_track: TrackInfo | None = None
    position: float = 0.0
    duration: float = 0.0
    volume: int = 80
    sponsorblock_active: bool = True
    crossfade_enabled: bool = False
    loudness_normalization_enabled: bool = False
    # Gain (dB) yang dihitung untuk current_track saat di-load (lihat TrackLoader.load_track).
    # Disimpan di state supaya toggle_loudness_normalization() bisa langsung re-apply
    # filter `af` ke track yang sedang berjalan, tanpa perlu reload/re-resolve track.
    current_track_gain_db: float = 0.0

    # Queue (hanya aktif di QUEUE mode)
    queue: deque = field(default_factory=deque)
    # Radio (hanya aktif di RADIO mode) — TIDAK PERNAH dicampur dengan `queue`.
    # Radio harus independen dari Queue Mode (lihat Constitution).
    radio_queue: deque = field(default_factory=deque)
    history: deque = field(default_factory=lambda: deque(maxlen=50))

    # Lyrics
    lyrics_lines: list[str] = field(default_factory=list)
    lyrics_timestamps: list[float] = field(default_factory=list)
    lyrics_index: int = 0
    lyrics_offset: float = 0.0

    # UI state
    active_tab: str = "home"  # "home"|"search"|"radio"|"queue"
    error_msg: str | None = None
    is_online: bool = True

    # Download
    download_progress: float | None = None  # 0.0–1.0, None = idle

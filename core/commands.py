from dataclasses import dataclass
from typing import Optional, List
from core.state import TrackInfo, PlaybackMode, AudioOutput

class DomainCommand:
    pass

@dataclass
class PlayTrackCommand(DomainCommand):
    track: TrackInfo

@dataclass
class TogglePauseCommand(DomainCommand):
    pass

@dataclass
class NextCommand(DomainCommand):
    video_id: Optional[str] = None

@dataclass
class PrevCommand(DomainCommand):
    pass

@dataclass
class StopCommand(DomainCommand):
    pass

@dataclass
class SeekCommand(DomainCommand):
    position: float

@dataclass
class VolumeUpCommand(DomainCommand):
    pass

@dataclass
class VolumeDownCommand(DomainCommand):
    pass

@dataclass
class VolumeSetCommand(DomainCommand):
    volume: float

@dataclass
class DownloadCommand(DomainCommand):
    track: TrackInfo

@dataclass
class SetModeCommand(DomainCommand):
    mode: PlaybackMode

@dataclass
class SetOutputCommand(DomainCommand):
    output: AudioOutput

@dataclass
class SetSponsorblockCommand(DomainCommand):
    enabled: bool

@dataclass
class QueueSelectCommand(DomainCommand):
    index: int

@dataclass
class QueueAddCommand(DomainCommand):
    track: TrackInfo

@dataclass
class QueueReplaceCommand(DomainCommand):
    tracks: List[TrackInfo]

@dataclass
class QueueRemoveCommand(DomainCommand):
    index: int

@dataclass
class QueueReorderCommand(DomainCommand):
    from_index: int
    to_index: int

@dataclass
class RadioRandomizeCommand(DomainCommand):
    seed_artist: Optional[str] = None

@dataclass
class LyricsOffsetCommand(DomainCommand):
    offset: float

@dataclass
class QuitCommand(DomainCommand):
    pass
@dataclass
class SearchCommand(DomainCommand):
    query: str

@dataclass
class DiscoverCommand(DomainCommand):
    pass

@dataclass
class ToggleFavoriteCommand(DomainCommand):
    video_id: str

@dataclass
class EnqueueArtistSongsCommand(DomainCommand):
    artist: str

@dataclass
class EnqueueGenreSongsCommand(DomainCommand):
    genre: str

@dataclass
class DeleteDownloadCommand(DomainCommand):
    video_id: str

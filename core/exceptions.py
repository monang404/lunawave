class YtPlayerError(Exception):
    """Base exception for YT Termux Player Pro."""
    pass

class MpvConnectionError(YtPlayerError):
    """Raised when unable to connect to the mpv IPC socket."""
    pass


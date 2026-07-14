"""
Module: core.exceptions

Purpose:
    Define the custom exception hierarchy for LunaWave error conditions.

Responsibilities:
    - Provide typed exceptions for mpv connection, track resolution, and
      download failures that callers can catch independently.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless.
"""


class YtPlayerError(Exception):
    """Base exception for LunaWave."""

    pass


class MpvConnectionError(YtPlayerError):
    """Raised when unable to connect to the mpv IPC socket."""

    pass


class TrackResolutionError(YtPlayerError):
    """Raised when unable to resolve a track's stream URL or local path."""

    pass


class DownloadError(YtPlayerError):
    """Raised when yt-dlp fails to download a track."""

    pass

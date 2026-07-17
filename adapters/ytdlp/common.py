"""
Module: adapters.ytdlp.common

Purpose:
    Shared utilities and constants for yt-dlp integration.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless.
"""

YDL_OPTS_INFO = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "format": "bestaudio/best",
    "format_sort": ["abr", "asr"],
    "socket_timeout": 10,
    "extractor_retries": 1,
}

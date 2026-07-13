"""
Module: tests.fakes.fake_lyrics_provider

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

from core.ports import LyricsProvider

class FakeLyricsProvider(LyricsProvider):
    def __init__(self, lyrics=None):
        self._lyrics = lyrics or []

    async def get_lyrics(self, title: str, artist: str) -> list:
        return self._lyrics

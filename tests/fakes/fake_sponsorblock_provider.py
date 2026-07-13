"""
Module: tests.fakes.fake_sponsorblock_provider

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

from core.ports import SponsorBlockProvider

class FakeSponsorBlockProvider(SponsorBlockProvider):
    def __init__(self, segments=None):
        self._segments = segments or []

    async def get_segments(self, video_id: str) -> list:
        return self._segments

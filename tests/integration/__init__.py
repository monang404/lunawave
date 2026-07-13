"""
Module: tests.integration

Purpose:
    Integration test package. Tests here use real components
    (real SQLite, real aiohttp server, real event bus) but mock
    external process dependencies (MPV, yt-dlp) so they run
    without hardware dependencies.

Subscribes to:
    None

Publishes:
    None
"""

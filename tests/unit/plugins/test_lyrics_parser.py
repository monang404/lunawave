"""
Module: tests.unit.plugins.test_lyrics_parser

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

from plugins.lyrics_parser import LyricsParser


def test_parse_lrc_standard():
    lrc = """
    [00:12.50]Line 1
    [01:05.00]Line 2
    """
    result = LyricsParser.parse_lrc(lrc)
    assert len(result) == 2
    assert result[0] == (12.5, "Line 1")
    assert result[1] == (65.0, "Line 2")


def test_parse_lrc_no_decimals():
    lrc = """
    [00:12]Line 1
    [01:05]Line 2
    """
    result = LyricsParser.parse_lrc(lrc)
    assert len(result) == 2
    assert result[0] == (12.0, "Line 1")
    assert result[1] == (65.0, "Line 2")


def test_parse_lrc_invalid():
    lrc = """
    [invalid]
    Just text
    [00:10.00] Valid line
    """
    result = LyricsParser.parse_lrc(lrc)
    assert len(result) == 3
    assert result[0] == (0.0, "[invalid]")
    assert result[1] == (0.0, "Just text")
    assert result[2] == (10.0, "Valid line")

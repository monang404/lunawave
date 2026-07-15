import json

import pytest

from engine.loudness.analyzer import LoudnessAnalyzer


def test_parse_loudness_json():
    analyzer = LoudnessAnalyzer()

    # Simulate ffmpeg output
    ffmpeg_output = """
    some irrelevant text
    {
        "input_i" : "-16.5",
        "input_tp" : "-2.0",
        "input_lra" : "4.0",
        "input_thresh" : "-27.0",
        "output_i" : "-14.0"
    }
    """

    result = analyzer._parse_loudness_json(ffmpeg_output)
    assert result == -16.5


def test_parse_loudness_json_invalid():
    analyzer = LoudnessAnalyzer()

    ffmpeg_output = "No json here"
    result = analyzer._parse_loudness_json(ffmpeg_output)
    assert result is None

    ffmpeg_output = '{"wrong_key": "-10.0"}'
    result = analyzer._parse_loudness_json(ffmpeg_output)
    assert result is None


def test_parse_loudness_json_malformed():
    analyzer = LoudnessAnalyzer()

    ffmpeg_output = '{ "input_i": "not a float" }'
    result = analyzer._parse_loudness_json(ffmpeg_output)
    assert result is None

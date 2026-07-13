"""
Module: plugins.lyrics_parser

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import re

class LyricsParser:
    @staticmethod
    def parse_lrc(lrc_text: str) -> list[tuple[float, str]]:
        pattern = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)")
        result = []
        for line in lrc_text.splitlines():
            line = line.strip()
            if not line:
                continue
            m = pattern.match(line)
            if m:
                minutes, seconds, text = m.groups()
                timestamp = int(minutes) * 60 + float(seconds)
                result.append((timestamp, text.strip()))
            else:
                if line:
                    result.append((0.0, line))
        return sorted(result, key=lambda x: x[0])

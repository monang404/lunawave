import re


class VideoId(str):
    _RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

    def __new__(cls, value: str):
        if not value or not cls._RE.match(str(value)):
            raise ValueError(f"video_id tidak valid: {value!r}")
        return super().__new__(cls, str(value))

from core.constants import MAX_VOLUME


class Volume(int):
    def __new__(cls, value: int):
        return super().__new__(cls, max(0, min(MAX_VOLUME, int(value))))

class Duration(int):
    def __new__(cls, value: int):
        val = int(value)
        if val < 0:
            val = 0
        return super().__new__(cls, val)

"""
Module: engine.loudness.analyzer

Purpose:
    Ukur integrated loudness (LUFS) sebuah track via satu-pass ffmpeg
    `loudnorm` filter mode measure-only (tidak re-encode, tidak menyimpan file
    baru).

Responsibilities:
    - Jalankan ffmpeg sebagai subprocess di thread executor.
    - Parse output JSON dari stderr ffmpeg untuk ambil `input_i`.
    - Fail-safe: kembalikan None (bukan raise) kalau ffmpeg gagal/timeout,
      supaya caller tidak pernah menganggap ini kritikal terhadap playback.

Depends on:
    - config

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Dipanggil dari event loop, kerja berat didelegasikan ke ThreadPoolExecutor
    milik caller (lihat LoudnessService).
"""

import json
import re
import subprocess

import structlog

from config import LOUDNESS_ANALYZE_TIMEOUT_SEC

logger = structlog.get_logger(__name__)

_JSON_BLOCK_RE = re.compile(r"\{[^{}]*\"input_i\"[^{}]*\}", re.DOTALL)


class LoudnessAnalyzer:
    """measure(uri) -> LUFS terukur, atau None kalau gagal/timeout."""

    def measure_sync(self, uri: str) -> float | None:
        """Dipanggil lewat run_in_executor -- BLOCKING, jangan panggil langsung
        dari event loop."""
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-i",
            uri,
            "-af",
            "loudnorm=print_format=json",
            "-f",
            "null",
            "-",
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=LOUDNESS_ANALYZE_TIMEOUT_SEC,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            logger.debug(f"Loudness analysis timeout: {uri}")
            return None
        except OSError as e:
            logger.error(f"ffmpeg tidak bisa dijalankan: {e}")
            return None

        match = _JSON_BLOCK_RE.search(result.stderr)
        if not match:
            logger.debug(f"Loudness analysis: tidak ada output JSON dari ffmpeg untuk {uri}")
            return None

        try:
            data = json.loads(match.group(0))
            return float(data["input_i"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Loudness analysis: gagal parse JSON: {e}")
            return None

"""
Module: engine.loudness.service

Purpose:
    Orkestrasi analisis loudness: cek apakah track sudah pernah diukur,
    kalau belum -> ukur via LoudnessAnalyzer lalu simpan ke DB.

Responsibilities:
    - analyze_and_store(): idempotent, aman dipanggil berkali-kali untuk
      track yang sama (skip kalau sudah ada loudness_lufs).

Depends on:
    - core.ports
    - engine.loudness.analyzer

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async); kerja berat ffmpeg didelegasikan ke ThreadPoolExecutor.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import structlog

from core.ports import TrackRepositoryPort
from engine.loudness.analyzer import LoudnessAnalyzer

logger = structlog.get_logger(__name__)


class LoudnessService:
    def __init__(self, db: TrackRepositoryPort, executor: ThreadPoolExecutor | None = None):
        self.db = db
        self.analyzer = LoudnessAnalyzer()
        # max_workers=1 sengaja dibatasi -- ffmpeg loudnorm analysis itu
        # CPU-heavy, dan salah satu target platform (Termux/Android) punya
        # CPU terbatas (lihat docs/CONSTRAINTS.md). Satu analisis background
        # dalam satu waktu sudah cukup, tidak perlu paralel.
        self._executor = executor or ThreadPoolExecutor(max_workers=1)

    async def analyze_and_store(self, video_id: str, uri: str) -> None:
        """Idempotent -- aman dipanggil tiap kali track dimuat. Kalau sudah
        pernah dianalisis (both lufs AND true_peak tersedia), langsung return."""
        row = await self.db.get_track(video_id)
        if row and row.loudness_lufs is not None and row.true_peak_dbtp is not None:
            return  # Sudah pernah diukur lengkap, tidak perlu ulang

        loop = asyncio.get_running_loop()
        measurement = await loop.run_in_executor(self._executor, self.analyzer.measure_sync, uri)
        if measurement is None:
            return  # Analisis gagal -- diam saja, coba lagi di play berikutnya

        try:
            await self.db.set_loudness(video_id, measurement.lufs, measurement.true_peak)
        except Exception as e:
            logger.warning(f"Gagal simpan loudness untuk {video_id}: {e}")

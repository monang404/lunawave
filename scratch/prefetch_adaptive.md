---
title: Rencana Implementasi — Adaptive Prefetch Threshold (Rolling p90)
status: Draft — belum dieksekusi
depends_on_read: AI_CONTEXT.md, docs/STATUS.md, docs/PATCHLOG.md (2-3 entri terakhir)
---

# prefetch_adaptive.md — Adaptive Prefetch Threshold untuk Radio Mode

> **Wajib dibaca dulu:** `AI_CONTEXT.md`, `docs/STATUS.md`,
> `docs/PATCHLOG.md` (2-3 entri terakhir). Tidak ada file berisiko tinggi
> (`engine/playback/controller.py`, `server/handlers/websocket.py`) yang
> disentuh di rencana ini — semua perubahan ada di file yang aman diedit.

## Ringkasan

`RadioPrefetcher.check_prefetch()` sekarang pakai threshold statis
30 detik (`(duration - position) <= 30.0`) untuk memutuskan kapan mulai
resolve stream_url lagu berikutnya. Angka ini tebakan, sama sekali tidak
tahu kondisi jaringan aktual — padahal target platform utama (Termux/mobile)
punya varians latensi jauh lebih liar dibanding WiFi desktop.

Rencana ini mengganti threshold statis dengan **rolling p90** dari waktu
resolve aktual (bukan rata-rata — percentile tinggi secara eksplisit
melindungi dari kasus terburuk yang baru terjadi, karena tujuannya
menghindari stutter, bukan mengejar performa rata-rata).

**Titik pengukuran:** `cache/resolver.py` Rule 3 saja (`await
self.ytdlp.get_stream_url(...)`) — Rule 1 (file lokal) dan Rule 2 (cache
belum kadaluwarsa) instan dan TIDAK BOLEH ikut terukur, supaya p90 tidak
keliru rendah karena tercampur kejadian yang tidak butuh network.

**Titik penyimpanan:** in-memory saja (rolling window kecil, 20 sample),
BUKAN di DB — ini kondisi jaringan yang berubah terus-menerus, tidak perlu
persist lintas restart.

## Prasyarat sebelum mulai

1. Baca `AI_CONTEXT.md`, `docs/STATUS.md`, `docs/PATCHLOG.md`
2. `python automation/find_owner.py RadioPrefetcher` dan `python automation/find_owner.py CacheResolver`
3. `python automation/doctor.py` — pastikan repo hijau sebelum mulai

---

## Batch 1 — `LatencyWindow` (file baru, stateless-generic)

**Tujuan:** utility rolling-window + percentile, generik (bukan spesifik
radio/resolver), supaya bisa dites terisolasi tanpa mock apapun.

**File baru:** `core/latency_window.py`

```python
"""
Module: core.latency_window

Purpose:
    Rolling window durasi (detik) untuk menghitung percentile ke-n dari
    N sample terakhir. Dipakai untuk threshold adaptif yang bereaksi ke
    kondisi jaringan aktual, bukan angka statis.

Responsibilities:
    - Simpan maksimal `maxlen` durasi terakhir.
    - Hitung percentile dengan fallback default kalau sample belum cukup.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Tidak thread-safe untuk akses konkuren dari banyak coroutine yang
    menulis bersamaan — dipakai di satu writer (CacheResolver.resolve())
    per instance, sesuai pola single-writer yang sudah ada di project ini.
"""

from collections import deque


class LatencyWindow:
    def __init__(self, maxlen: int = 20):
        self._samples: deque[float] = deque(maxlen=maxlen)

    def record(self, duration_sec: float) -> None:
        if duration_sec >= 0:
            self._samples.append(duration_sec)

    def percentile(self, p: int, default: float) -> float:
        """Kembalikan `default` kalau sample < 5 (belum cukup data untuk
        percentile yang berarti)."""
        if len(self._samples) < 5:
            return default
        ordered = sorted(self._samples)
        idx = min(int(len(ordered) * p / 100), len(ordered) - 1)
        return ordered[idx]

    def sample_count(self) -> int:
        return len(self._samples)
```

**Test baru:** `tests/unit/core/test_latency_window.py`
```python
"""
Module: tests.unit.core.test_latency_window

Purpose:
    Unit tests untuk LatencyWindow — rolling percentile durasi resolve.

Depends on:
    - core.latency_window

Thread Safety:
    Main thread (sync, tidak butuh event loop).
"""

from core.latency_window import LatencyWindow


def test_returns_default_when_insufficient_samples():
    w = LatencyWindow()
    w.record(5.0)
    w.record(6.0)
    assert w.percentile(90, default=30.0) == 30.0


def test_percentile_after_enough_samples():
    w = LatencyWindow(maxlen=20)
    for v in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        w.record(float(v))
    p90 = w.percentile(90, default=30.0)
    assert p90 == 9.0  # index int(10*0.9)=9 -> nilai ke-10 (0-indexed ke-9) di list terurut


def test_window_drops_oldest_beyond_maxlen():
    w = LatencyWindow(maxlen=5)
    for v in [100, 100, 100, 100, 100, 1, 1, 1, 1, 1]:
        w.record(float(v))
    # 5 sample lama (100) sudah kebuang, cuma sisa lima 1.0
    assert w.percentile(90, default=999) == 1.0


def test_negative_duration_ignored():
    w = LatencyWindow()
    for v in [1, 2, 3, 4, 5]:
        w.record(float(v))
    w.record(-1.0)  # harus diabaikan (mis. clock skew)
    assert w.sample_count() == 5
```

**Setelah selesai:**
- `pytest tests/unit/core/test_latency_window.py -v`
- `python automation/doctor.py` dan `python automation/generate_file_index.py`
- Prepend PATCHLOG. File terdampak: `core/latency_window.py`, `tests/unit/core/test_latency_window.py`

---

## Batch 2 — Ukur waktu resolve di `CacheResolver`

**Tujuan:** cuma **mencatat**, belum ada yang membaca/konsumsi datanya di
batch ini — jadi aman, tidak mengubah perilaku apapun yang teramati.

**File:** `cache/resolver.py`

```python
import time
from core.latency_window import LatencyWindow

class CacheResolver:
    def __init__(self, db: TrackRepositoryPort, ytdlp: MediaExtractorPort):
        self.db = db
        self.ytdlp = ytdlp
        self.latency_window = LatencyWindow()  # public — dibaca RadioPrefetcher nanti

    async def resolve(self, track: TrackInfo) -> str:
        row = await self.db.get_track(track.video_id)

        # Rule 1 & 2 tidak berubah — TIDAK diukur (instan, bukan network)
        if row and row.local_path:
            ...
        if row and row.stream_url and row.stream_url_ts:
            ...

        # Rule 3 — satu-satunya yang diukur
        t0 = time.monotonic()
        url = await self.ytdlp.get_stream_url(track.video_id)
        self.latency_window.record(time.monotonic() - t0)

        track.stream_url = url
        await self.db.upsert_track(track, stream_url=url)
        return url
```

**Setelah selesai:**
- Update `tests/unit/cache/test_resolver.py` — assert `latency_window.sample_count()` bertambah setelah Rule 3 kepanggil, assert TIDAK bertambah kalau Rule 1/2 yang kepakai
- `python automation/doctor.py`
- Prepend PATCHLOG. File terdampak: `cache/resolver.py`, `tests/unit/cache/test_resolver.py`

---

## Batch 3 — Konstanta config

**Tujuan:** angka-angka tuning (safety factor, batas min/max) jadi config,
bukan hardcode di `prefetcher.py` — ikut pola `STREAM_URL_TTL_SEC` dkk yang
sudah ada.

**File:** `config.py`

```python
# Adaptive prefetch (lihat prefetch_adaptive.md)
PREFETCH_DEFAULT_THRESHOLD_SEC = 30.0  # dipakai kalau sample resolve belum cukup (<5)
PREFETCH_SAFETY_FACTOR = 1.5           # threshold = p90 * factor
PREFETCH_MIN_THRESHOLD_SEC = 10.0      # jangan pernah lebih pendek dari ini
PREFETCH_MAX_THRESHOLD_SEC = 60.0      # jangan pernah lebih panjang dari ini
```

**Setelah selesai:**
- `python automation/doctor.py`
- Prepend PATCHLOG. File terdampak: `config.py`

---

## Batch 4 — Wire ke `RadioPrefetcher.check_prefetch()`

**Tujuan:** ganti threshold statis dengan p90 dari `LatencyWindow` yang
sudah diisi Batch 2, diklem ke `[MIN, MAX]` biar tidak ada outlier tunggal
yang bikin threshold meledak atau terlalu mepet.

**File:** `engine/radio/prefetcher.py`

```python
from config import (
    PREFETCH_DEFAULT_THRESHOLD_SEC,
    PREFETCH_SAFETY_FACTOR,
    PREFETCH_MIN_THRESHOLD_SEC,
    PREFETCH_MAX_THRESHOLD_SEC,
)

class RadioPrefetcher:
    ...

    def _current_threshold(self, controller: "PlaybackController") -> float:
        window = controller.track_loader.resolver.latency_window
        p90 = window.percentile(90, default=PREFETCH_DEFAULT_THRESHOLD_SEC)
        raw = p90 * PREFETCH_SAFETY_FACTOR
        return max(PREFETCH_MIN_THRESHOLD_SEC, min(raw, PREFETCH_MAX_THRESHOLD_SEC))

    def check_prefetch(
        self, controller: "PlaybackController", position: float, duration: float
    ) -> None:
        """Trigger prefetch stream_url untuk lagu berikutnya jika waktu tersisa
        <= threshold adaptif (p90 waktu resolve terakhir * safety factor,
        diklem ke [MIN, MAX])."""
        threshold = self._current_threshold(controller)
        if duration > 0 and (duration - position) <= threshold:
            current_vid = self.state.current_track.video_id if self.state.current_track else None
            if current_vid and self._last_prefetch_vid != current_vid:
                self._last_prefetch_vid = current_vid
                track_task(self._bg_tasks, self._prefetch_next(controller), name="radio_prefetch")
```

> **Catatan akses:** `controller.track_loader.resolver` — sesuaikan dengan
> path akses sebenarnya di `PlaybackController` (cek `__init__` untuk
> memastikan `track_loader` memang exposed sebagai atribut publik; kalau
> tidak, tambah properti kecil untuk expose `resolver` tanpa membongkar
> struktur controller — INGAT, `controller.py` adalah file restricted,
> tambahkan properti read-only sekecil mungkin dan verifikasi manual).

**Setelah selesai:**
- Update `tests/unit/engine/radio/test_prefetcher.py` — `MockPlaybackController` perlu `track_loader.resolver.latency_window` palsu; test kasus: window kosong → pakai `PREFETCH_DEFAULT_THRESHOLD_SEC`; window berisi sample lambat → threshold naik tapi diklem ke `PREFETCH_MAX_THRESHOLD_SEC`; window berisi sample sangat cepat → threshold turun tapi diklem ke `PREFETCH_MIN_THRESHOLD_SEC`
- `python automation/doctor.py`
- Prepend PATCHLOG. File terdampak: `engine/radio/prefetcher.py`, `tests/unit/engine/radio/test_prefetcher.py`

---

## Batch 5 — (Opsional) Prometheus visibility

**Tujuan:** dual-purpose — data yang sama juga berguna untuk monitoring,
bukan cuma keputusan threshold. Ikuti pola `COMMAND_LATENCY` yang sudah ada.

**File:** `core/observability.py`

```python
RESOLVE_LATENCY = Histogram(
    "lunawave_stream_resolve_duration_seconds",
    "Duration of yt-dlp stream URL resolution (Rule 3 cache miss only)",
)
```

`cache/resolver.py` tinggal tambah `RESOLVE_LATENCY.observe(duration)` di
baris yang sama dengan `self.latency_window.record(duration)` di Batch 2.

**Setelah selesai:**
- `python automation/doctor.py`
- Prepend PATCHLOG. File terdampak: `core/observability.py`, `cache/resolver.py`

---

## Batch 6 — ADR & dokumentasi

**File baru:** `docs/adr/0008-adaptive-prefetch-threshold.md` (format sama
seperti ADR-0004: Konteks / Keputusan / Alasan / Konsekuensi / Referensi)

**File diupdate:** `docs/backend/background_jobs.md` (radio prefetch sudah
disebut di situ), `docs/STATUS.md`

**Setelah selesai:**
- `python automation/generate_file_index.py`
- `python automation/generate_report.py`
- `python automation/doctor.py`
- Prepend PATCHLOG final merangkum seluruh batch

---

## Urutan eksekusi & alasan

1→2→3→4 berurutan: window dulu (murni utility, testable sendiri), lalu
pengukuran (masih tidak mengubah perilaku apapun yang teramati user), baru
konstanta config, baru terakhir baca+konsumsi jadi threshold aktif. 5
opsional dan independen, bisa disisipkan kapan saja setelah 2. 6 menutup
dokumentasi setelah semua terverifikasi.

## Definition of done

- [ ] Semua batch di-commit terpisah dengan PATCHLOG masing-masing
- [ ] `python automation/doctor.py --strict` PASS
- [ ] Tes manual: nyalakan radio di jaringan lambat (throttle manual kalau
      bisa) dan jaringan cepat, bandingkan log waktu prefetch trigger —
      pastikan threshold benar-benar berubah, bukan tetap 30 detik
- [ ] Tidak ada regresi di gap/stutter antar-lagu dibanding baseline sebelumnya

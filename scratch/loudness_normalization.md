---
title: Rencana Implementasi — Loudness Normalization (Nyamain Volume Antar Lagu)
status: Draft — belum dieksekusi
depends_on_read: AI_CONTEXT.md, docs/STATUS.md, docs/PATCHLOG.md (2-3 entri terakhir)
---

# loudness_normalization.md — Per-Track Loudness Normalization (EBU R128 / ReplayGain-style)

> **Wajib dibaca dulu sebelum eksekusi apapun di bawah:** `AI_CONTEXT.md`,
> `docs/STATUS.md`, `docs/PATCHLOG.md` (2-3 entri terakhir). Dokumen ini
> mengasumsikan kamu sudah baca ketiganya dan paham konvensi hexagonal
> ports/adapters, command bus, dan aturan "tidak boleh refactor 2 tahap
> sekaligus dalam 1 commit".

## Ringkasan

Saat ini tidak ada normalisasi volume sama sekali — `engine/volume_service.py`
cuma menerapkan volume yang di-set user (`CMD_VOLUME_*`) langsung ke MPV via
`set_volume()`. Lagu kenceng dan lagu pelan diputar dengan gain yang sama persis,
jadi user harus atur manual tiap ganti lagu.

Rencana ini menambahkan **normalisasi loudness per-track ala Spotify/ReplayGain**:

1. **Analisis sekali** — tiap track diukur *integrated loudness*-nya (LUFS, standar
   EBU R128) pakai `ffmpeg` filter `loudnorm` mode measure-only (satu pass, tidak
   re-encode). **Tidak nambah dependency baru** — `ffmpeg` sudah jadi requirement
   wajib project ini (dipakai `FFmpegExtractAudio` postprocessor di
   `adapters/ytdlp/downloader.py`, lihat `README.md`).
2. **Disimpan** — hasil ukur (`loudness_lufs`) disimpan permanen di kolom baru
   tabel `tracks`, sekali per `video_id`, dipakai selamanya (tidak diukur ulang).
3. **Dipakai tiap diputar** — saat track dimuat, gain (dB) dihitung dari
   `loudness_lufs` vs target (`-14 LUFS`, sama seperti Spotify), diterapkan ke MPV
   lewat audio filter (`af`) **terpisah dari knob volume user** — jadi
   `VolumeService` (`engine/volume_service.py`) sama sekali tidak disentuh dan
   tetap jadi satu-satunya pengatur volume "manual".

**Kapan analisis terjadi:** fire-and-forget saat track pertama kali dimuat
(pola yang sama persis dengan sponsorblock/lyrics fetch di
`engine/playback/track_loader.py`) — **tidak memblokir playback**. Konsekuensi
jujur yang perlu didokumentasikan: **putaran pertama sebuah lagu akan diputar
tanpa normalisasi (gain 0dB)** karena datanya belum ada; putaran kedua dan
seterusnya baru ternormalisasi. Ini trade-off yang disengaja demi tidak
menambah latency ke `play_track()` — bukan sekadar keterbatasan yang
disembunyikan.

**Sumber URI yang dianalisis = sumber URI yang diputar.** `LoudnessService`
memakai `uri` yang sama persis dengan yang sudah di-resolve `CacheResolver`
(local path atau direct stream URL dari yt-dlp) — tidak ada resolusi kedua yang
terpisah, supaya yang diukur dan yang didengar user dijamin sama.

**Pendekatan gain: track-gain sederhana, bukan `loudnorm` full dua-pass dengan
limiter.** Kita cuma menghitung `gain_db = TARGET_LUFS - measured_lufs` lalu
di-clamp (`LOUDNESS_MAX_BOOST_DB` / `LOUDNESS_MAX_CUT_DB`). Ini **tidak** ada
true-peak limiting, jadi ada risiko kecil clipping pada boost besar — makanya
clamp boost dibatasi konservatif (default +8dB). Ini keterbatasan yang sengaja
diterima demi kesederhanaan (satu ffmpeg pass, bukan dua), didokumentasikan
eksplisit di ADR (Batch 8), bukan diklaim sebagai loudnorm broadcast-grade.

## ⚠️ File berisiko tinggi — butuh izin eksplisit

`engine/playback/controller.py` masuk daftar "TIDAK BOLEH disentuh tanpa izin
eksplisit" di `AI_CONTEXT.md` (closure kompleks), **dan** statusnya di
`docs/STATUS.md` sudah ❄️ **Frozen (v1.0.0 Baseline)** — artinya project ini
sudah melewati tag rilis stabil `v1.0.0` (`PATCH-2026-07-14-040`). Menyentuh
file ini untuk fitur baru pasca-rilis adalah keputusan yang lebih besar
dibanding sekadar "restricted file" biasa — sebaiknya dikerjakan di sprint
baru pasca-v1.0.0, bukan disisipkan diam-diam.

Batch 6 di bawah **menyentuh file ini** (hanya untuk menerapkan gain di
`play_track()`) — treat sebagai persetujuan eksplisit untuk task spesifik ini
saja, BUKAN izin umum untuk refactor bebas file tersebut. Jangan gabungkan
Batch 6 dengan perubahan lain di file yang sama.

`cache/resolver.py` juga berstatus ❄️ Frozen di `docs/STATUS.md`. Rencana ini
**sengaja tidak menyentuh file itu sama sekali** — pembacaan `loudness_lufs`
dilakukan lewat `self.resolver.db.get_track()` yang sudah dipakai
`TrackLoader` (lihat Batch 5), bukan lewat perubahan di `CacheResolver`.

## Prasyarat sebelum mulai (per AI_CONTEXT.md)

1. Baca `AI_CONTEXT.md`
2. Baca `docs/STATUS.md` — cek kondisi `persistence/`, `engine/playback/`,
   `engine/playback/controller.py` (Frozen/restricted)
3. Baca `docs/PATCHLOG.md` — 2-3 entri terakhir (terutama entri hardening
   v1.0.0, `PATCH-2026-07-14-039` s.d. `041`, untuk paham konvensi docstring
   dan CI gate terbaru)
4. `python automation/find_owner.py TrackLoader` dan
   `python automation/find_owner.py PlaybackController` untuk orientasi
5. `python automation/doctor.py` — pastikan repo hijau sebelum mulai

---

## Batch 1 — Skema data (additive, tanpa ubah perilaku)

**Tujuan:** tambah kolom `loudness_lufs` di tabel `tracks` + field baru di
`TrackInfo`. Murni penyiapan data — tidak ada query/behavior yang berubah,
risiko rendah, aman commit sendiri.

**File:**
- `persistence/schema.sql` — instalasi baru
- `persistence/__init__.py` — migrasi untuk DB lama (ikuti pola `is_favorite`/
  `click_count` yang sudah ada)
- `core/state.py` — tambah field di `TrackInfo`

### `persistence/schema.sql`
```sql
-- Tambahkan di definisi CREATE TABLE tracks yang sudah ada:
CREATE TABLE IF NOT EXISTS tracks (
    ...
    is_favorite  INTEGER DEFAULT 0,
    loudness_lufs REAL,          -- NULL = belum dianalisis; integrated loudness (LUFS)
    created_at   INTEGER DEFAULT (strftime('%s','now'))
);
```

### `persistence/__init__.py`
```python
# Di blok migrasi ALTER TABLE yang sudah ada, tambahkan:
migrations = [
    "ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0",
    "ALTER TABLE artists ADD COLUMN click_count INTEGER DEFAULT 0",
    "ALTER TABLE genres ADD COLUMN click_count INTEGER DEFAULT 0",
    "ALTER TABLE tracks ADD COLUMN loudness_lufs REAL",
]
```

### `core/state.py`
```python
@dataclass
class TrackInfo:
    video_id: str
    title: str
    artist: str
    duration: int
    thumbnail: str | None = None
    local_path: str | None = None
    stream_url: str | None = None
    view_count: int | None = None
    stream_url_ts: int | None = None
    play_count: int | None = None
    last_played: int | None = None
    is_favorite: int | None = 0
    loudness_lufs: float | None = None  # BARU — hasil analisis, None = belum diukur
```

**Setelah selesai:**
- `python automation/doctor.py`
- Prepend `docs/PATCHLOG.md`: `PATCH-YYYY-MM-DD-NNN — Skema: tambah loudness_lufs di tracks (persiapan loudness normalization)`
- File terdampak: `persistence/schema.sql`, `persistence/__init__.py`, `core/state.py`

**Test:** cukup pastikan migrasi tidak error di DB lama — contoh existing di
`tests/unit/persistence/` yang menguji migrasi serupa (`is_favorite`) bisa
dicontoh polanya.

---

## Batch 2 — Repository & Port: simpan & baca loudness

**Tujuan:** tambah method `set_loudness()` di `TrackRepository`, pastikan
`get_track()`/`upsert_track()` ikut membawa `loudness_lufs`, dan tambahkan
kontrak method ini ke `TrackRepositoryPort`. Belum dipanggil dari manapun di
batch ini — murni penambahan API repo, aman.

**File:**
- `persistence/track_repo.py`
- `core/ports.py`
- `persistence/__init__.py` (delegasi facade `Database`)
- `tests/fakes/fake_track_repository.py`

### `persistence/track_repo.py`
```python
async def set_loudness(self, video_id: str, lufs: float) -> None:
    """Simpan hasil pengukuran integrated loudness (LUFS). Dipanggil sekali
    per track oleh LoudnessService setelah analisis selesai."""
    await self._conn.execute(
        "UPDATE tracks SET loudness_lufs = ? WHERE video_id = ?",
        (lufs, video_id),
    )
    await self._conn.commit()
```

Update `get_track()` — tambahkan mapping field baru (ikuti pola `is_favorite`
yang sudah pakai `if "..." in row.keys()` untuk backward-compat dengan DB lama
yang belum migrasi):
```python
loudness = row["loudness_lufs"] if "loudness_lufs" in row.keys() else None
return TrackInfo(
    ...,
    is_favorite=is_fav,
    loudness_lufs=loudness,
)
```

Update `upsert_track()` — **jangan** timpa `loudness_lufs` yang sudah ada saat
metadata di-refresh (sama seperti `local_path`/`stream_url` pakai `COALESCE`):
```python
# Query upsert_track TIDAK perlu menyentuh kolom loudness_lufs sama sekali —
# kolom ini hanya diisi lewat set_loudness(), jadi ON CONFLICT existing value
# otomatis tetap (kolom tidak disebut di SET clause = tidak berubah).
```

### `core/ports.py`
```python
class TrackRepositoryPort(Protocol):
    async def upsert_track(
        self, track: TrackInfo, stream_url: str | None = None, local_path: str | None = None
    ) -> None: ...
    async def update_stream_url_only(self, video_id: str, stream_url: str) -> None: ...
    async def get_track(self, video_id: str) -> TrackInfo | None: ...
    async def increment_play_count(self, video_id: str) -> None: ...
    async def set_loudness(self, video_id: str, lufs: float) -> None: ...  # BARU
```

### `persistence/__init__.py`
```python
async def set_loudness(self, *a, **kw):
    return await self._tracks.set_loudness(*a, **kw)
```

### `tests/fakes/fake_track_repository.py`
```python
async def set_loudness(self, video_id: str, lufs: float) -> None:
    self.call_log.append(("set_loudness", video_id, lufs))
    if video_id in self._tracks:
        self._tracks[video_id].loudness_lufs = lufs
```
Jangan lupa tambahkan `loudness_lufs=existing.loudness_lufs if existing else None`
di konstruksi `TrackInfo` dalam `upsert_track()` fake (supaya nilai lama tidak
hilang saat fake di-upsert ulang, sama seperti `is_favorite` di fake ini).

**Setelah selesai:**
- `python automation/doctor.py`
- Tambah/update test di `tests/unit/persistence/test_track_repo.py`: assert
  `set_loudness()` menulis nilai yang benar, assert `get_track()` mengembalikan
  `loudness_lufs=None` untuk track yang belum dianalisis, assert
  `upsert_track()` tidak menimpa `loudness_lufs` yang sudah ada
- Prepend PATCHLOG. File terdampak: `persistence/track_repo.py`,
  `core/ports.py`, `persistence/__init__.py`,
  `tests/fakes/fake_track_repository.py`, `tests/unit/persistence/test_track_repo.py`

---

## Batch 3 — Modul gain calculator (file baru, stateless)

**Tujuan:** logika hitung gain (dB) dari LUFS terukur, murni fungsi tanpa
dependency I/O apapun — supaya gampang dites terisolasi, sama seperti pola
`sample_artists()` di modul bandit sebelumnya.

**File baru:** `engine/loudness/gain_calculator.py`

```python
"""
Module: engine.loudness.gain_calculator

Purpose:
    Hitung gain (dB) yang perlu diterapkan ke sebuah track supaya loudness-nya
    mendekati target, berdasarkan hasil pengukuran integrated loudness (LUFS).

Responsibilities:
    - compute_gain_db(): hitung gain dari LUFS terukur, di-clamp ke batas aman.
    - build_af_filter(): bentuk string filter MPV/ffmpeg (af=lavfi=[volume=XdB]).

Depends on:
    None (stateless, semua nilai masuk sebagai argumen)

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless — aman dipanggil dari mana saja.
"""

TARGET_LUFS = -14.0        # Sama seperti Spotify/YouTube Music
MAX_BOOST_DB = 8.0         # Clamp atas — tanpa true-peak limiting, boost besar berisiko clipping
MAX_CUT_DB = 12.0          # Clamp bawah — lagu yang sudah kenceng dipotong maksimal segini


def compute_gain_db(
    measured_lufs: float | None,
    target_lufs: float = TARGET_LUFS,
    max_boost_db: float = MAX_BOOST_DB,
    max_cut_db: float = MAX_CUT_DB,
) -> float:
    """Hitung gain (dB). None (belum dianalisis) -> 0.0 (passthrough, tidak
    ada normalisasi -- ini keputusan sengaja, bukan default sembarangan)."""
    if measured_lufs is None:
        return 0.0
    gain = target_lufs - measured_lufs
    return max(-max_cut_db, min(max_boost_db, gain))


def build_af_filter(gain_db: float) -> str:
    """Bentuk string untuk property `af` MPV. gain_db=0.0 tetap menghasilkan
    filter eksplisit (bukan string kosong) supaya SELALU meng-override filter
    dari track sebelumnya -- MPV adalah proses persisten yang di-reuse antar
    track (loadfile replace), `af` TIDAK otomatis reset sendiri."""
    return f"lavfi=[volume={gain_db:.2f}dB]"
```

**Test baru:** `tests/unit/engine/loudness/test_gain_calculator.py`
```python
"""
Module: tests.unit.engine.loudness.test_gain_calculator

Purpose:
    Unit test untuk perhitungan gain loudness normalization.

Depends on:
    - engine.loudness.gain_calculator

Thread Safety:
    Main thread (sync, tidak butuh event loop).
"""

from engine.loudness.gain_calculator import build_af_filter, compute_gain_db


def test_none_lufs_returns_zero_gain():
    assert compute_gain_db(None) == 0.0


def test_quiet_track_gets_positive_gain():
    # -20 LUFS jauh lebih pelan dari target -14 -> perlu boost
    assert compute_gain_db(-20.0) > 0


def test_loud_track_gets_negative_gain():
    # -8 LUFS lebih kenceng dari target -> perlu dipotong
    assert compute_gain_db(-8.0) < 0


def test_boost_is_clamped():
    # -40 LUFS ekstrem -> gain harus tetap di batas MAX_BOOST_DB
    from engine.loudness.gain_calculator import MAX_BOOST_DB

    assert compute_gain_db(-40.0) == MAX_BOOST_DB


def test_cut_is_clamped():
    from engine.loudness.gain_calculator import MAX_CUT_DB

    assert compute_gain_db(10.0) == -MAX_CUT_DB


def test_zero_gain_still_produces_explicit_filter_string():
    # Penting: 0.0dB tetap harus jadi filter eksplisit, bukan string kosong,
    # supaya selalu meng-override af dari track sebelumnya.
    assert build_af_filter(0.0) == "lavfi=[volume=0.00dB]"
```

**Setelah selesai:**
- `pytest tests/unit/engine/loudness/test_gain_calculator.py -v`
- `python automation/doctor.py` dan `python automation/generate_file_index.py`
  (ada file baru)
- Prepend PATCHLOG. File terdampak: `engine/loudness/__init__.py` (buat file
  kosong seperti pola modul lain), `engine/loudness/gain_calculator.py`,
  `tests/unit/engine/loudness/test_gain_calculator.py`

---

## Batch 4 — LoudnessAnalyzer: pengukuran via ffmpeg (file baru)

**Tujuan:** subprocess wrapper yang menjalankan `ffmpeg` filter `loudnorm`
mode measure-only untuk dapat nilai integrated loudness (LUFS). Dijalankan di
executor terpisah (bukan event loop) — sama persis pola
`adapters/ytdlp/downloader.py` yang sudah `run_in_executor` untuk kerja berat.

**File baru:** `engine/loudness/analyzer.py`
**File diupdate:** `config.py` (tambah konstanta)

### `config.py`
```python
# Loudness Normalization
LOUDNESS_ANALYZE_TIMEOUT_SEC = 45  # Lebih lama dari YTDLP_RESOLVE_TIMEOUT_SEC
                                    # karena decode seluruh track, bukan cuma metadata
```

### `engine/loudness/analyzer.py`
```python
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
            "-i", uri,
            "-af", "loudnorm=print_format=json",
            "-f", "null",
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
            logger.warning(f"Loudness analysis timeout: {uri}")
            return None
        except OSError as e:
            logger.error(f"ffmpeg tidak bisa dijalankan: {e}")
            return None

        match = _JSON_BLOCK_RE.search(result.stderr)
        if not match:
            logger.warning(f"Loudness analysis: tidak ada output JSON dari ffmpeg untuk {uri}")
            return None

        try:
            data = json.loads(match.group(0))
            return float(data["input_i"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Loudness analysis: gagal parse JSON: {e}")
            return None
```

> **Catatan `shell=False` eksplisit:** mengikuti standar yang sudah ditegakkan
> di `PATCH-2026-07-14-041` (`launcher/network.py`) — jangan pernah pakai
> `shell=True` untuk subprocess yang menerima input dari URL/track manapun.

**Setelah selesai:**
- Test dengan `unittest.mock.patch("subprocess.run")` — jangan panggil ffmpeg
  asli di unit test (lambat, butuh binary tersedia di CI). Kasus yang wajib
  dites: JSON valid → LUFS benar, timeout → None, ffmpeg tidak ada (`OSError`)
  → None, stderr tanpa JSON block → None
- `python automation/doctor.py` dan `python automation/generate_file_index.py`
- Prepend PATCHLOG. File terdampak: `engine/loudness/analyzer.py`, `config.py`,
  `tests/unit/engine/loudness/test_analyzer.py`

---

## Batch 5 — LoudnessService: orkestrasi + wiring fire-and-forget

**Tujuan:** gabungkan `LoudnessAnalyzer` + repo jadi satu service, panggil
dari `TrackLoader` sebagai background task **hanya untuk mengukur & menyimpan**
— **belum** menerapkan gain ke MPV (itu Batch 6, sengaja dipisah karena
Batch 6 menyentuh file restricted).

**File baru:** `engine/loudness/service.py`
**File diupdate:** `engine/playback/track_loader.py`, `main.py` (wiring)

### `engine/loudness/service.py`
```python
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
        pernah dianalisis, langsung return tanpa kerja tambahan."""
        row = await self.db.get_track(video_id)
        if row and row.loudness_lufs is not None:
            return  # Sudah pernah diukur, tidak perlu ulang

        loop = asyncio.get_running_loop()
        lufs = await loop.run_in_executor(self._executor, self.analyzer.measure_sync, uri)
        if lufs is None:
            return  # Analisis gagal -- diam saja, coba lagi di play berikutnya

        try:
            await self.db.set_loudness(video_id, lufs)
        except Exception as e:
            logger.warning(f"Gagal simpan loudness untuk {video_id}: {e}")
```

### `engine/playback/track_loader.py`
```python
class TrackLoader:
    def __init__(
        self,
        resolver: StreamResolverPort,
        sponsorblock: SponsorBlockProvider,
        lyrics_fetcher: LyricsProvider,
        loudness_service: "LoudnessService | None" = None,  # BARU, optional utk backward-compat test lama
    ):
        self.resolver = resolver
        self.sponsorblock = sponsorblock
        self.lyrics_fetcher = lyrics_fetcher
        self.loudness_service = loudness_service

    async def load_track(self, track: TrackInfo) -> str:
        uri = await self.resolver.resolve(track)

        safe_create_task(
            self.resolver.db.increment_play_count(track.video_id),
            name=f"incr_play_count_{track.video_id}",
        )
        safe_create_task(
            self.sponsorblock.fetch_segments(track.video_id),
            name=f"fetch_sponsorblock_{track.video_id}",
        )
        safe_create_task(self.lyrics_fetcher.fetch(track), name=f"fetch_lyrics_{track.video_id}")

        # BARU -- fire-and-forget, idempotent, tidak menunda mpv.play(uri)
        if self.loudness_service:
            safe_create_task(
                self.loudness_service.analyze_and_store(track.video_id, uri),
                name=f"analyze_loudness_{track.video_id}",
            )

        return uri
```

### `main.py`
```python
from engine.loudness.service import LoudnessService

loudness_service = LoudnessService(db)
playback_controller = PlaybackController(
    bus, state, mpv, resolver, sponsorblock, lyrics_fetcher, queue_mode, radio_mode,
    loudness_service=loudness_service,  # lihat Batch 6 untuk perubahan constructor PlaybackController
)
```
> Detail penyambungan `loudness_service` ke `PlaybackController` (yang lalu
> meneruskannya ke `TrackLoader`) dieksekusi di Batch 6 bersamaan dengan
> perubahan constructor — supaya `main.py` tidak diubah dua kali untuk satu
> fitur yang sama.

**Setelah selesai:**
- Update `tests/unit/engine/playback/test_track_loader.py` (buat kalau belum
  ada) — assert `analyze_and_store` dipanggil sebagai fire-and-forget task
  saat `loudness_service` di-inject, assert tetap jalan normal kalau
  `loudness_service=None` (backward-compat)
- `python automation/doctor.py`
- Prepend PATCHLOG. File terdampak: `engine/loudness/service.py`,
  `engine/playback/track_loader.py`, `tests/unit/engine/playback/test_track_loader.py`

---

## Batch 6 — ⚠️ Terapkan gain di `controller.py` + `set_af` di MPV port

**File berisiko tinggi — lihat peringatan di atas dokumen ini (restricted +
Frozen v1.0.0 Baseline).**

**Tujuan:** setelah `mpv.play(uri)`, terapkan gain (dB) hasil hitung
`compute_gain_db()` lewat audio filter MPV — terpisah total dari
`VolumeService`/knob volume user.

**File:**
- `core/ports.py` — tambah `set_af()` ke `AudioPlayerPort`
- `adapters/mpv/__init__.py` — implementasi `set_af()`
- `tests/fakes/fake_audio_player.py` — tambah fake `set_af()`
- `engine/playback/track_loader.py` — `load_track()` return `LoadedTrack`
  (uri + gain_db) alih-alih `str` polos
- `engine/playback/controller.py` — panggil `set_af()` di `play_track()`

### `core/ports.py`
```python
class AudioPlayerPort(Protocol):
    ...
    async def set_volume(self, volume: int) -> None: ...
    async def set_af(self, filter_str: str) -> None: ...  # BARU
    ...
```

### `adapters/mpv/__init__.py`
```python
async def set_af(self, filter_str: str):
    if not self.is_connected:
        return
    await self._ipc.set_property("af", filter_str)
```

### `tests/fakes/fake_audio_player.py`
```python
async def set_af(self, filter_str: str) -> None:
    self.call_log.append(("set_af", filter_str))
    self.af = filter_str
```

### `engine/playback/track_loader.py`
```python
from dataclasses import dataclass


@dataclass
class LoadedTrack:
    uri: str
    gain_db: float = 0.0


class TrackLoader:
    async def load_track(self, track: TrackInfo) -> LoadedTrack:
        uri = await self.resolver.resolve(track)

        safe_create_task(...)  # play count, sponsorblock, lyrics -- tidak berubah

        gain_db = 0.0
        if self.loudness_service:
            row = await self.resolver.db.get_track(track.video_id)
            if row and row.loudness_lufs is not None:
                from engine.loudness.gain_calculator import compute_gain_db

                gain_db = compute_gain_db(row.loudness_lufs)
            safe_create_task(
                self.loudness_service.analyze_and_store(track.video_id, uri),
                name=f"analyze_loudness_{track.video_id}",
            )

        return LoadedTrack(uri=uri, gain_db=gain_db)
```

> **Kenapa query DB lagi padahal `resolver.resolve()` sudah query juga?**
> Sengaja tidak dioptimasi jadi satu query — `cache/resolver.py` berstatus
> Frozen, jadi kita hindari menyentuhnya sama sekali (lihat peringatan di atas
> dokumen ini). Satu SELECT SQLite tambahan itu murah, konsisten dengan gaya
> project ini yang memilih kesederhanaan/keamanan refactor di atas
> micro-optimization (lihat prinsip "bukan sekadar ada dan gimmick" — di sini
> substansinya adalah *tidak mengganggu file yang sudah stabil*, bukan jumlah
> query).

### `engine/playback/controller.py`
```python
async def play_track(self, track: TrackInfo):
    async with self._play_lock:
        ...
        try:
            loaded = await self.track_loader.load_track(track)  # UBAH: uri -> loaded

            self._loading = True
            await self.mpv.play(loaded.uri)  # UBAH: gunakan loaded.uri
            await asyncio.sleep(0.15)

            # BARU -- SELALU dipanggil, termasuk gain_db=0.0, supaya af dari
            # track sebelumnya (MPV proses persisten!) selalu ter-override.
            from engine.loudness.gain_calculator import build_af_filter

            await self.mpv.set_af(build_af_filter(loaded.gain_db))

            if getattr(self.state, "audio_output", AudioOutput.DEVICE) == AudioOutput.BROWSER:
                await self.mpv.set_volume(0)
                ...
            else:
                await self.mpv.set_volume(self.state.volume)
            ...
```

Constructor `PlaybackController` juga perlu terima `loudness_service` dan
meneruskannya ke `TrackLoader`:
```python
def __init__(
    self, bus, state, mpv, resolver, sponsorblock, lyrics_fetcher, queue_mode, radio_mode,
    loudness_service=None,  # BARU
):
    ...
    self.track_loader = TrackLoader(resolver, sponsorblock, lyrics_fetcher, loudness_service)
```

**Yang HARUS diverifikasi manual sebelum commit** (file closure kompleks +
Frozen baseline):
- **Kritis:** putar lagu A (ternormalisasi, gain != 0), lalu langsung lagu B
  (belum ternormalisasi, gain = 0) — pastikan lagu B benar-benar 0dB, BUKAN
  mewarisi gain lagu A. Ini bug paling berbahaya di batch ini kalau `set_af`
  lupa dipanggil di salah satu jalur.
- Pastikan `set_af()` tidak menambah latency terasa sebelum `TrackStartedEvent`
  dipublish (harus 1 `set_property` IPC call saja, cepat)
- Pastikan retry path (`_retry_count` / `safe_create_task(self._advance_to_next())`
  saat error) tetap jalan normal — `loaded.uri` dipakai di jalur error log juga
  kalau ada referensi `uri` lama di situ, cek dan sesuaikan
- Jalankan test playback controller yang sudah ada **penuh**, bukan cuma yang
  baru ditambah (`tests/unit/engine/playback/test_controller.py`)

**Setelah selesai:**
- Test baru/update di `tests/unit/engine/playback/test_controller.py`: assert
  `mpv.set_af(...)` selalu dipanggil setelah `mpv.play(...)`, assert gain 0dB
  untuk track yang `loudness_lufs=None`, assert gain non-zero untuk track yang
  sudah punya `loudness_lufs` di fake DB, assert `af` di-reset ke `0.00dB`
  ketika lagu berikutnya belum ternormalisasi (skenario A→B di atas)
- `python automation/doctor.py --strict` (file restricted, ekstra hati-hati)
- Prepend PATCHLOG dengan catatan eksplisit "menyentuh file restricted, lihat
  loudness_normalization.md §Batch 6"
- Update `docs/STATUS.md` baris untuk `engine/playback/controller.py` (catat
  penambahan baris + alasan, ikuti pola entri Batch 9 yang sudah ada)
- File terdampak: `core/ports.py`, `adapters/mpv/__init__.py`,
  `tests/fakes/fake_audio_player.py`, `engine/playback/track_loader.py`,
  `engine/playback/controller.py`, `main.py`,
  `tests/unit/engine/playback/test_controller.py`,
  `tests/unit/adapters/mpv/test_mpv_controller.py` (kalau ada test terpisah
  untuk facade ini)

---

## Batch 7 — Toggle on/off: `CMD_SET_LOUDNESS_NORMALIZATION`

**Tujuan:** user bisa matikan fitur ini kalau mau (mengikuti pola persis
`CMD_SET_SPONSORBLOCK` / `toggle_sponsorblock()` yang sudah ada di
`engine/playback/mode_ops.py`). File-file di batch ini **tidak restricted**.

**File:**
- `core/state.py` — tambah `loudness_normalization_enabled: bool = True` di `AppState`
- `core/commands.py` — tambah `CMD_SET_LOUDNESS_NORMALIZATION`
- `engine/playback/mode_ops.py` — tambah `toggle_loudness_normalization()`
- `engine/playback/controller.py` — tambah handler, dan cek flag ini sebelum
  hitung gain (kalau `False`, selalu `build_af_filter(0.0)`)
- `engine/command_router.py` — daftarkan routing command baru
- `server/serializers.py` — expose ke frontend

### `core/state.py`
```python
@dataclass
class AppState:
    ...
    sponsorblock_active: bool = True
    loudness_normalization_enabled: bool = True  # BARU
```

### `core/commands.py`
```python
CMD_SET_LOUDNESS_NORMALIZATION = "cmd.set.loudness_normalization"  # data: bool
```

### `engine/playback/mode_ops.py`
```python
async def toggle_loudness_normalization(self, enabled: bool):
    self.state.loudness_normalization_enabled = enabled
    status_msg = "ON" if enabled else "OFF"
    await self.bus.publish(LogMessageEvent(message=f"Loudness Normalization: {status_msg}"))
    await self.bus.publish(QueueUpdatedEvent())
```

### `engine/playback/controller.py`
```python
async def _on_set_loudness_normalization(self, enabled: bool):
    await self._mode_ops.toggle_loudness_normalization(enabled)
```
Di `play_track()`, sebelum `build_af_filter`:
```python
gain_db = loaded.gain_db if self.state.loudness_normalization_enabled else 0.0
await self.mpv.set_af(build_af_filter(gain_db))
```

### `engine/command_router.py`
```python
from core.commands import CMD_SET_LOUDNESS_NORMALIZATION
...
self.bus.subscribe(
    CMD_SET_LOUDNESS_NORMALIZATION,
    self._route(lambda c, data: c._on_set_loudness_normalization(data)),
)
```

### `server/serializers.py`
```python
"loudness_normalization_enabled": state.loudness_normalization_enabled,
```

**Setelah selesai:**
- Update `tests/unit/engine/playback/test_controller.py` dan
  `tests/unit/engine/test_command_router.py`: assert toggle command mengubah
  `state.loudness_normalization_enabled` dan mempengaruhi `set_af()` call
  berikutnya
- `python automation/doctor.py`
- Prepend PATCHLOG. File terdampak: semua file di atas + file test terkait

---

## Batch 8 — ADR & dokumentasi

**File baru:** `docs/adr/0007-loudness-normalization-track-gain.md` (ikuti
format ADR-0004 sebagai contoh: Konteks / Keputusan / Alasan / Konsekuensi /
Referensi — sebutkan eksplisit trade-off "single-pass, no true-peak limiting"
dan "putaran pertama tidak ternormalisasi" di bagian Konsekuensi)

**File diupdate:**
- `docs/backend/services.md` — sebut `engine/loudness/` sebagai layanan baru
- `docs/backend/persistence.md` — sebut kolom `loudness_lufs` di skema tracks
- `docs/STATUS.md` — baris baru untuk `engine/loudness/` (3 file baru) dan
  update baris `engine/playback/controller.py` (sudah dicatat di Batch 6)
- `README.md` — opsional: sebutkan fitur ini di daftar fitur, tidak wajib
  ubah instruksi instalasi karena `ffmpeg` sudah jadi requirement sebelumnya

**Setelah selesai:**
- `python automation/generate_file_index.py`
- `python automation/generate_report.py`
- `python automation/doctor.py --strict`
- Prepend PATCHLOG final: rangkum semua batch di atas sebagai satu
  sprint/fitur selesai

---

## Urutan eksekusi & alasan urutan

1→2→3→4 aman dikerjakan berurutan cepat (additive, stateless/mockable, tidak
menyentuh file restricted maupun Frozen). 5 mulai menyentuh alur nyata
(`track_loader.py`) tapi **belum** mengubah apa yang didengar user — cuma
mengukur & menyimpan di background, jadi rollback-nya aman dan murah. 6
ditaruh sendirian karena satu-satunya batch yang menyentuh file restricted
*dan* Frozen v1.0.0 — kalau ada masalah di 1-5, rollback tidak menyeret
`controller.py`. 7 (toggle) sengaja setelah 6, bukan sebelum, karena toggle
baru berguna kalau efeknya (gain di `play_track()`) sudah benar-benar ada. 8
menutup dengan dokumentasi setelah semua terverifikasi jalan.

## Definition of done

- [ ] Semua 8 batch di-commit terpisah, tiap batch punya entri PATCHLOG sendiri
- [ ] `python automation/doctor.py --strict` PASS di commit terakhir
- [ ] Diputar manual minimal 1 sesi: mainkan lagu pelan lalu lagu kenceng
      berturut-turut (lagu yang **sudah pernah dianalisis sebelumnya**,
      supaya `loudness_lufs` sudah terisi) — perbedaan volume terdengar
      jauh lebih rata dibanding sebelum fitur ini
- [ ] Skenario "lagu A ternormalisasi → lagu B belum ternormalisasi" dites
      manual — pastikan lagu B benar-benar diputar di 0dB, bukan warisan gain
      lagu A (lihat catatan kritis di Batch 6)
- [ ] Toggle `loudness_normalization_enabled=False` dites manual — memastikan
      gain kembali 0dB meskipun `loudness_lufs` sudah ada di DB
- [ ] `loudness_lufs` di DB terisi otomatis setelah sebuah track diputar
      (cek manual via sqlite3 CLI: `SELECT video_id, loudness_lufs FROM tracks WHERE loudness_lufs IS NOT NULL;`)
- [ ] Perangkat Termux (CPU terbatas) diuji tidak mengalami lag terasa saat
      analisis loudness berjalan di background (executor `max_workers=1`)

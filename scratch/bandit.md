---
title: Rencana Implementasi — Thompson Sampling Bandit untuk Radio Mode
status: Draft — belum dieksekusi
depends_on_read: AI_CONTEXT.md, docs/STATUS.md, docs/PATCHLOG.md (2-3 entri terakhir)
---

# bandit.md — Radio Artist Selection via Thompson Sampling

> **Wajib dibaca dulu sebelum eksekusi apapun di bawah:** `AI_CONTEXT.md`,
> `docs/STATUS.md`, `docs/PATCHLOG.md` (2-3 entri terakhir). Dokumen ini
> mengasumsikan kamu sudah baca ketiganya dan paham konvensi single-writer,
> command bus, dan aturan "tidak boleh refactor 2 tahap sekaligus dalam 1 commit".

## Ringkasan

Radio mode saat ini memilih artis seed secara `random.choice()` murni
(`engine/radio/artist_selector.py`), dan `get_random_songs()` di
`persistence/library_repo.py` cuma menerima **satu** artis prioritas — sisanya
diisi acak lewat `ORDER BY RANDOM() LIMIT 12`, bukan komposisi artis yang
benar-benar terkontrol.

Rencana ini mengganti pemilihan artis jadi **Thompson Sampling (Beta-Bernoulli)**:
tiap artis dapat skor `Beta(alpha, beta)` dari histori selesai/skip, di-sample
tiap kali batch dibangun, top-k diambil. Artis baru (`alpha=1, beta=1`) otomatis
dapat porsi eksplorasi wajar tanpa aturan tambahan — cold-start ditangani oleh
matematikanya sendiri, bukan oleh rule manual.

**Titik pencatatan sinyal** (selesai vs skip) sudah ditemukan tanpa perlu jalur
baru: `_advance_to_next()` di `engine/playback/controller.py` dipanggil baik
dari EOF natural maupun skip manual — bedanya cuma rasio
`state.position / state.duration` saat dipanggil.

**Bacaan stats bandit dilakukan ulang dari DB tiap `gather_batch()` dipanggil**
(bukan di-cache sekali di awal sesi radio, bukan juga di-update manual paralel
di memori) — supaya cuma ada satu sumber kebenaran (DB) dan bandit langsung
bereaksi ke perilaku user dalam satu sesi yang sama.

## ⚠️ File berisiko tinggi — butuh izin eksplisit

`engine/playback/controller.py` masuk daftar "TIDAK BOLEH disentuh tanpa izin
eksplisit" di `AI_CONTEXT.md` (closure kompleks). Batch 6 di bawah **menyentuh
file ini** — treat sebagai persetujuan eksplisit untuk task spesifik ini saja
(nambah satu pemanggilan pencatatan skip/selesai di `_advance_to_next()`),
BUKAN izin umum untuk refactor bebas file tersebut. Jangan gabungkan Batch 6
dengan perubahan lain di file yang sama.

## Prasyarat sebelum mulai (per AI_CONTEXT.md)

1. Baca `AI_CONTEXT.md`
2. Baca `docs/STATUS.md` — cek kondisi `engine/radio/`, `persistence/`, `engine/playback/controller.py`
3. Baca `docs/PATCHLOG.md` — 2-3 entri terakhir
4. `python automation/find_owner.py ArtistSelector` dan `python automation/find_owner.py get_random_songs` untuk orientasi
5. `python automation/doctor.py` — pastikan repo hijau sebelum mulai

---

## Batch 1 — Skema data (additive, tanpa ubah perilaku)

**Tujuan:** tambah kolom `reward_alpha`, `reward_beta` di tabel `artists`. Tidak
mengubah query/behavior apapun — murni penyiapan kolom, jadi risiko rendah dan
aman untuk commit sendiri.

**File:**
- `persistence/schema.sql` — instalasi baru
- `persistence/__init__.py` — migrasi untuk DB lama (ikuti pola `click_count` yang sudah ada)

### `persistence/schema.sql`
```sql
-- Tambahkan di definisi CREATE TABLE artists yang sudah ada:
CREATE TABLE IF NOT EXISTS artists (
    ...
    reward_alpha INTEGER DEFAULT 1,
    reward_beta INTEGER DEFAULT 1
);
```

### `persistence/__init__.py`
```python
# Di blok migrasi ALTER TABLE yang sudah ada, tambahkan:
migrations = [
    "ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0",
    "ALTER TABLE artists ADD COLUMN click_count INTEGER DEFAULT 0",
    "ALTER TABLE genres ADD COLUMN click_count INTEGER DEFAULT 0",
    "ALTER TABLE artists ADD COLUMN reward_alpha INTEGER DEFAULT 1",
    "ALTER TABLE artists ADD COLUMN reward_beta INTEGER DEFAULT 1",
]
```

**Setelah selesai:**
- `python automation/doctor.py`
- Prepend `docs/PATCHLOG.md`: `PATCH-YYYY-MM-DD-NNN — Skema: tambah reward_alpha/reward_beta di artists (persiapan bandit)`
- File terdampak (list per baris di PATCHLOG): `persistence/schema.sql`, `persistence/__init__.py`

**Test:** cukup pastikan migrasi tidak error di DB lama (test existing di `tests/unit/persistence/` yang sudah menguji migrasi serupa untuk `click_count` bisa dicontoh polanya).

---

## Batch 2 — Repository: catat & baca reward

**Tujuan:** tambah method di `ArtistRepository` untuk increment dan membaca
alpha/beta. Belum dipanggil dari manapun di batch ini — jadi aman, murni
penambahan API repo.

**File:** `persistence/artist_repo.py`

```python
async def record_completion(self, artist_name: str) -> None:
    """Track selesai penuh — reward positif untuk bandit."""
    if not self._conn:
        return
    try:
        await self._conn.execute(
            "UPDATE artists SET reward_alpha = COALESCE(reward_alpha, 1) + 1 WHERE nama = ?",
            (artist_name,),
        )
        await self._conn.commit()
    except Exception as e:
        logger.error(f"Error recording completion: {e}")

async def record_skip(self, artist_name: str) -> None:
    """Track skip dini — reward negatif untuk bandit."""
    if not self._conn:
        return
    try:
        await self._conn.execute(
            "UPDATE artists SET reward_beta = COALESCE(reward_beta, 1) + 1 WHERE nama = ?",
            (artist_name,),
        )
        await self._conn.commit()
    except Exception as e:
        logger.error(f"Error recording skip: {e}")

async def get_reward_stats(self) -> dict[str, tuple[int, int]]:
    """Ambil {nama_artis: (alpha, beta)} untuk semua artis. Dipanggil ulang
    tiap gather_batch() — JANGAN di-cache di caller."""
    if not self._conn:
        return {}
    query = "SELECT nama, COALESCE(reward_alpha, 1) as a, COALESCE(reward_beta, 1) as b FROM artists"
    async with self._conn.execute(query) as cursor:
        rows = await cursor.fetchall()
    return {row["nama"]: (row["a"], row["b"]) for row in rows}
```

**Setelah selesai:**
- `python automation/doctor.py`
- Tambah test di `tests/unit/persistence/test_artist_repo.py` (buat baru jika belum ada): assert increment benar, assert default 1/1 untuk artis baru
- Prepend PATCHLOG. File terdampak: `persistence/artist_repo.py`, `tests/unit/persistence/test_artist_repo.py`

---

## Batch 3 — Modul bandit (file baru, stateless)

**Tujuan:** logika Thompson Sampling murni, tanpa dependency ke DB/state
apapun — supaya bisa dites terisolasi.

**File baru:** `engine/radio/artist_bandit.py`

```python
"""
Module: engine.radio.artist_bandit

Purpose:
    Thompson Sampling (Beta-Bernoulli) untuk memilih artis radio berdasarkan
    histori selesai/skip, dengan eksplorasi otomatis untuk artis yang
    datanya masih sedikit.

Responsibilities:
    - Sampling k artis dari daftar kandidat berdasar skor Beta(alpha, beta).

Depends on:
    None (stateless, semua data alpha/beta masuk sebagai argumen)

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless — aman dipanggil dari mana saja.
"""

import random
from dataclasses import dataclass


@dataclass
class ArtistStat:
    name: str
    alpha: int = 1  # jumlah selesai (+prior)
    beta: int = 1   # jumlah skip (+prior)


def sample_artists(candidates: list[ArtistStat], k: int) -> list[str]:
    """Thompson Sampling: sample satu angka dari Beta(alpha, beta) tiap
    kandidat, urutkan turun, ambil k nama teratas.

    Artis dengan histori bagus (alpha tinggi relatif beta) cenderung dapat
    angka sampling tinggi, tapi artis dengan data sedikit (alpha=beta=1,
    varians besar) tetap punya peluang terpilih — di situlah eksplorasi
    terjadi secara alami.
    """
    if not candidates:
        return []
    scored = [(random.betavariate(c.alpha, c.beta), c.name) for c in candidates]
    scored.sort(reverse=True)
    return [name for _, name in scored[:k]]
```

**Test baru:** `tests/unit/engine/radio/test_artist_bandit.py`
```python
"""
Module: tests.unit.engine.radio.test_artist_bandit

Purpose:
    Unit tests untuk sampling Thompson Sampling artis radio.

Depends on:
    - engine.radio.artist_bandit

Thread Safety:
    Main thread (sync, tidak butuh event loop).
"""

from engine.radio.artist_bandit import ArtistStat, sample_artists


def test_empty_candidates_returns_empty():
    assert sample_artists([], k=4) == []


def test_returns_at_most_k():
    candidates = [ArtistStat(name=f"A{i}") for i in range(10)]
    result = sample_artists(candidates, k=4)
    assert len(result) == 4
    assert len(set(result)) == 4  # tidak ada duplikat


def test_strong_artist_selected_more_often_statistically():
    """Artis dengan alpha tinggi harus lebih sering terpilih dari 1000 trial,
    tapi tidak 100% (masih ada peluang eksplorasi)."""
    strong = ArtistStat(name="Strong", alpha=100, beta=1)
    weak = ArtistStat(name="Weak", alpha=1, beta=100)
    picks = [sample_artists([strong, weak], k=1)[0] for _ in range(1000)]
    assert picks.count("Strong") > picks.count("Weak")
    assert picks.count("Weak") > 0  # eksplorasi tetap terjadi sesekali


def test_new_artist_has_uniform_prior():
    """Artis baru (alpha=beta=1) harus punya peluang wajar walau bersaing
    dengan artis lama yang datanya netral juga."""
    new_a = ArtistStat(name="New")
    new_b = ArtistStat(name="AlsoNew")
    picks = [sample_artists([new_a, new_b], k=1)[0] for _ in range(200)]
    assert picks.count("New") > 0
    assert picks.count("AlsoNew") > 0
```

**Setelah selesai:**
- `pytest tests/unit/engine/radio/test_artist_bandit.py -v`
- `python automation/doctor.py` dan `python automation/generate_file_index.py` (ada file baru)
- Prepend PATCHLOG. File terdampak: `engine/radio/artist_bandit.py`, `tests/unit/engine/radio/test_artist_bandit.py`

---

## Batch 4 — Wire bandit ke `ArtistSelector`

**Tujuan:** ganti `random.choice(self._seed_artists)` dengan hasil
`sample_artists()`. Di batch ini `gather_batch()` masih mengirim **satu**
artis ke `get_random_songs()` (yang teratas dari hasil sample) — belum
mengubah signature `get_random_songs()`. Ini sengaja dipisah dari Batch 5
supaya tidak melanggar aturan "no two-stage refactor in one commit".

**File:** `engine/radio/artist_selector.py`

```python
from engine.radio.artist_bandit import ArtistStat, sample_artists

class ArtistSelector:
    def __init__(self, db, state: AppState):
        self.db = db
        self.state = state
        self._seed_artists: list[str] = []
        self._artist_rotation: list[str] = []

    async def _sampled_seed_artist(self) -> str | None:
        if not self._seed_artists:
            return None
        stats = {}
        if self.db and getattr(self.db, "conn", None):
            try:
                stats = await self.db.artist_repo.get_reward_stats()  # sesuaikan akses repo
            except Exception as e:
                _log.warning(f"Gagal ambil reward stats: {e}")
        candidates = [
            ArtistStat(name=name, alpha=stats.get(name, (1, 1))[0], beta=stats.get(name, (1, 1))[1])
            for name in self._seed_artists
        ]
        picked = sample_artists(candidates, k=1)
        return picked[0] if picked else None

    async def gather_batch(
        self, prioritized_artist: str | None = None, max_artists: int = ARTISTS_PER_BATCH
    ) -> list:
        limit = max_artists * TRACKS_PER_ARTIST_TARGET
        existing = self.build_exclusion_set()

        if not prioritized_artist and self._seed_artists:
            prioritized_artist = await self._sampled_seed_artist()  # <-- ganti random.choice

        # ... sisa method tidak berubah
```

> **Catatan integrasi repo:** sesuaikan `self.db.artist_repo.get_reward_stats()`
> dengan cara akses repo yang sebenarnya dipakai di `db` port/adapter kamu
> (cek `core/ports.py` untuk kontrak `DatabasePort` — mungkin perlu expose
> method baru di port kalau `ArtistRepository` belum diakses langsung dari sana).

**Setelah selesai:**
- Update test `tests/unit/engine/radio/test_artist_selector.py` — `MockDB` perlu tambah `get_reward_stats()` (atau `artist_repo.get_reward_stats()` tergantung integrasi)
- `python automation/doctor.py`
- Prepend PATCHLOG. File terdampak: `engine/radio/artist_selector.py`, `tests/unit/engine/radio/test_artist_selector.py`

---

## Batch 5 — `get_random_songs()`: terima banyak artis

**Tujuan:** ubah query supaya komposisi batch benar-benar terkontrol
(stratified explicit sampling), bukan efek samping `ORDER BY RANDOM() LIMIT`.
Dipisah dari Batch 4 supaya tiap batch bisa direview/rollback independen.

**File:** `persistence/library_repo.py`

Pendekatan: terima `artists: list[str] | None` (bukan `artist: str | None`),
jaga backward-compat dengan parameter lama sebagai deprecated alias satu
versi (per aturan "setiap file yang dipindah wajib ada backward-compat alias"
— walau ini bukan pindah file, prinsip yang sama diterapkan untuk perubahan
signature publik):

```python
async def get_random_songs(
    self,
    limit: int = 12,
    exclude_ids: set[str] | None = None,
    artists: list[str] | None = None,   # BARU — list, bukan satu
    artist: str | None = None,           # DEPRECATED — tetap didukung 1 versi
    max_per_artist: int = 3,
) -> list[TrackInfo]:
    if artist and not artists:
        artists = [artist]  # backward-compat shim
    # ... UNION ALL per artis di `artists` dengan LIMIT max_per_artist masing-masing,
    # sisa slot (limit - len(artists)*max_per_artist) diisi RANDOM() seperti sebelumnya
```

> Detail query UNION ALL disusun saat eksekusi batch ini — pastikan tetap
> pakai parameterized query (bukan f-string) untuk mencegah SQL injection,
> ikuti pola `placeholders = ",".join("?" for _ in exclude_ids)` yang sudah
> ada di file yang sama.

**Setelah selesai:**
- Update `tests/unit/persistence/test_library_repo.py` — test kasus lama (1 artist via `artist=`) dan kasus baru (`artists=[...]`)
- `python automation/doctor.py`
- Prepend PATCHLOG. File terdampak: `persistence/library_repo.py`, `tests/unit/persistence/test_library_repo.py`

---

## Batch 6 — ⚠️ Pencatatan skip/selesai di `controller.py`

**File berisiko tinggi — lihat peringatan di atas dokumen ini.**

**Tujuan:** di `_advance_to_next()`, sebelum lanjut ke mode berikutnya, hitung
rasio posisi/durasi track yang baru saja ditinggalkan dan catat sebagai
completion atau skip.

**File:** `engine/playback/controller.py`

```python
SKIP_THRESHOLD_RATIO = 0.3  # < 30% durasi = dianggap skip

async def _advance_to_next(self):
    await self._record_listen_outcome()
    if self.state.playback_mode == PlaybackMode.QUEUE:
        await self.queue_mode.next(self)
    else:
        await self.radio_mode.next(self)

async def _record_listen_outcome(self):
    track = self.state.current_track
    if not track or not self.db or not getattr(self.db, "conn", None):
        return
    duration = self.state.duration or track.duration or 0
    if duration <= 0:
        return
    ratio = self.state.position / duration
    try:
        if ratio >= SKIP_THRESHOLD_RATIO:
            await self.db.artist_repo.record_completion(track.artist)
        else:
            await self.db.artist_repo.record_skip(track.artist)
    except Exception as e:
        logger.warning(f"Gagal mencatat listen outcome: {e}")
```

**Yang HARUS diverifikasi manual sebelum commit** (karena file ini closure
kompleks per `AI_CONTEXT.md`):
- Pastikan `_record_listen_outcome()` tidak menambah latency terasa ke jalur
  auto-advance (harus `await` cepat — cuma 1 UPDATE query)
- Pastikan tidak dipanggil dobel kalau `_on_next` dipanggil dua kali untuk
  track yang sama (cek guard `video_id` yang sudah ada di `_on_next`)
- Jalankan test playback controller yang sudah ada penuh, bukan cuma yang baru ditambah

**Setelah selesai:**
- Test baru/update di test controller yang relevan (cek `tests/unit/engine/` untuk lokasi test controller yang sudah ada)
- `python automation/doctor.py --strict` (file restricted, ekstra hati-hati)
- Prepend PATCHLOG dengan catatan eksplisit "menyentuh file restricted, lihat bandit.md §Batch 6"
- Update `docs/STATUS.md` baris untuk `engine/playback/controller.py`

---

## Batch 7 — ADR & dokumentasi

**File baru:** `docs/adr/0007-thompson-sampling-radio-selection.md` (ikuti
format ADR-0004 sebagai contoh: Konteks / Keputusan / Alasan / Konsekuensi / Referensi)

**File diupdate:**
- `docs/backend/services.md` atau `docs/backend/persistence.md` — sebut mekanisme baru
- `docs/STATUS.md` — baris baru untuk `engine/radio/artist_bandit.py`

**Setelah selesai:**
- `python automation/generate_file_index.py`
- `python automation/generate_report.py`
- `python automation/doctor.py`
- Prepend PATCHLOG final: rangkum semua batch di atas sebagai satu sprint/fitur selesai

---

## Urutan eksekusi & alasan urutan

1→2→3 aman dikerjakan berurutan cepat (additive, tidak ada perilaku berubah,
tidak menyentuh file restricted). 4 dan 5 sengaja dipisah jadi 2 commit walau
salling berkaitan erat, sesuai aturan "no two-stage refactor sekaligus". 6
ditaruh paling akhir dari perubahan kode karena satu-satunya yang menyentuh
file restricted — kalau ada masalah di 1-5, rollback tidak menyeret file
berisiko tinggi itu. 7 menutup dengan dokumentasi setelah semua terverifikasi
jalan.

## Definition of done

- [ ] Semua 7 batch di-commit terpisah, tiap batch punya entri PATCHLOG sendiri
- [ ] `python automation/doctor.py --strict` PASS di commit terakhir
- [ ] Radio mode dites manual minimal 1 sesi penuh (nyalakan radio, biarkan
      beberapa lagu selesai natural, skip beberapa lagu manual, matikan
      radio, nyalakan lagi — pastikan tidak ada crash/exception di log)
- [ ] `reward_alpha`/`reward_beta` di DB berubah sesuai perilaku dengar (cek manual via sqlite3 CLI)

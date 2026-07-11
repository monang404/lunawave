# PATCH_PLAYCOUNT_LAZYIMPORT_DISCOVER.md

Baca `AI_CONTEXT.md` dulu. Ini bukan task final — kumpulan temuan dari scan
lanjutan setelah `PATCH_PAUSE_DELAY.md`, `PATCH_BATTERY_DRAIN.md`, dan
`PATCH_STARTUP_SPEED.md`. Belum di-apply. Disusun per prioritas dampak.

---

## RINGKASAN

| # | Bug | File | Dampak |
|---|-----|------|--------|
| 1 | `increment_play_count` blocking playback start | `engine/playback/track_loader.py` | Tinggi — jeda tiap ganti lagu |
| 2 | `import syncedlyrics` top-level | `plugins/lyrics.py` | Sedang — startup lebih lambat |
| 3 | Query discover sequential (3 lokasi) | `server/handlers/event_listeners.py`, `server/handlers/websocket.py` | Sedang — Discover tab & refresh lag |
| 4 | `observe_property` sequential saat connect | `engine/mpv_controller.py` | Kecil — hanya sekali saat startup mpv |

Tidak ada perubahan API/arsitektur. Tidak ada file baru.

**Catatan akses file:** `server/handlers/websocket.py` ditandai
"jangan disentuh tanpa izin eksplisit" di `AI_CONTEXT.md`. Task 3 menyentuh
file ini — minta konfirmasi eksplisit sebelum apply, meskipun perubahannya
mengikuti pola yang sama seperti fix `broadcast()` yang sudah disetujui
sebelumnya.

---

## TASK 1 — `engine/playback/track_loader.py`: Jangan blok playback demi statistik

### ROOT CAUSE

```python
async def load_track(self, track: TrackInfo) -> str:
    uri = await self.resolver.resolve(track)
    await self.resolver.db.increment_play_count(track.video_id)   # <-- blocking
    safe_create_task(self.sponsorblock.fetch_segments(track.video_id), ...)
    safe_create_task(self.lyrics_fetcher.fetch(track), ...)
    return uri
```

`increment_play_count` adalah write DB yang cuma dipakai untuk statistik
favorit/discover — bukan sesuatu yang dibutuhkan sebelum `mpv.play(uri)`
dipanggil di `controller.play_track()`. Tapi di-`await` di jalur kritis,
jadi setiap ganti lagu ikut menunggu write SQLite selesai dulu. Sponsorblock
dan lyrics fetch di baris bawahnya sudah benar (fire-and-forget via
`safe_create_task`) — play count harusnya diperlakukan sama.

### PERUBAHAN

**Cari:**
```python
        # Resolve URI
        uri = await self.resolver.resolve(track)

        # C-02: Increment play count for favorites
        await self.resolver.db.increment_play_count(track.video_id)

        # Fetch sponsorblock and lyrics
        safe_create_task(self.sponsorblock.fetch_segments(track.video_id), name=f"fetch_sponsorblock_{track.video_id}")
        safe_create_task(self.lyrics_fetcher.fetch(track), name=f"fetch_lyrics_{track.video_id}")

        return uri
```

**Ganti dengan:**
```python
        # Resolve URI
        uri = await self.resolver.resolve(track)

        # C-02: Increment play count for favorites.
        # Fire-and-forget — statistik ini tidak boleh menunda mpv.play(uri)
        # yang dipanggil segera setelah load_track() return.
        safe_create_task(self.resolver.db.increment_play_count(track.video_id), name=f"incr_playcount_{track.video_id}")

        # Fetch sponsorblock and lyrics
        safe_create_task(self.sponsorblock.fetch_segments(track.video_id), name=f"fetch_sponsorblock_{track.video_id}")
        safe_create_task(self.lyrics_fetcher.fetch(track), name=f"fetch_lyrics_{track.video_id}")

        return uri
```

### VERIFIKASI

```bash
python -m pytest tests/ -x -q
```
Manual test: ganti lagu berkali-kali cepat → cek play_count tetap
bertambah benar di DB (boleh cek lewat Discover/Favorites setelah beberapa
detik), dan playback mulai tanpa jeda tambahan dibanding sebelumnya.

---

## TASK 2 — `plugins/lyrics.py`: Lazy import `syncedlyrics`

### ROOT CAUSE

```python
import syncedlyrics   # top-level, line 30
```

`syncedlyrics` cuma dipakai satu kali, sebagai fallback terakhir kalau
lrclib gagal (baris ~141: `loop.run_in_executor(None, syncedlyrics.search, ...)`),
jadi jarang benar-benar tereksekusi. Tapi karena diimpor top-level, dan
`main.py` mengimpor `LyricsFetcher` saat module load (sebelum event loop
jalan), modul ini ikut dimuat penuh saat startup — persis kelas bug yang
sama dengan `yt_dlp` di `PATCH_STARTUP_SPEED.md` Task 3, cuma kelewat saat
itu karena fokusnya di `ytdlp_client.py`.

### PERUBAHAN

**Cari (bagian import atas file):**
```python
import re
import structlog
import aiohttp
import bisect
import asyncio
import syncedlyrics
from contextlib import asynccontextmanager
```

**Ganti dengan:**
```python
import re
import structlog
import aiohttp
import bisect
import asyncio
from contextlib import asynccontextmanager
```

**Cari (di method yang memakainya, sekitar baris 135-141):**
```python
                logger.info("lrclib failed. Falling back to syncedlyrics (Musixmatch/NetEase/etc)...")
                logger.info(f"syncedlyrics query: {search_query}")
                try:
                    lrc = await asyncio.wait_for(loop.run_in_executor(None, syncedlyrics.search, search_query), timeout=5.0)
```

**Ganti dengan:**
```python
                logger.info("lrclib failed. Falling back to syncedlyrics (Musixmatch/NetEase/etc)...")
                logger.info(f"syncedlyrics query: {search_query}")
                import syncedlyrics  # lazy import — modul besar, hanya dipakai di fallback terakhir ini
                try:
                    lrc = await asyncio.wait_for(loop.run_in_executor(None, syncedlyrics.search, search_query), timeout=5.0)
```

### VERIFIKASI

```bash
python -m pytest tests/ -x -q
```
Manual test: matikan koneksi ke lrclib (atau paksa gagal) → pastikan
fallback ke syncedlyrics tetap jalan normal dan lyrics tetap muncul.
Cek startup time sedikit membaik dibanding sebelum patch (terutama di
Termux, di mana import modul besar lebih terasa).

---

## TASK 3 — Paralelkan query discover data (3 lokasi)

### ROOT CAUSE

Pola berikut muncul identik di 3 tempat: 4-5 query DB independent
dijalankan satu-satu dengan `await` berurutan, padahal tidak ada
dependency antar query:

```python
recent = await ds.get_recent(15)
favorites = await ds.get_favorites(15)      # tidak ada di semua lokasi
cached = await ds.get_cached(15)
featured_artists = await ds.get_featured_artists(100)
featured_genres = await ds.get_featured_genres(100)
```

Sama seperti bug DB init + mpv connect di `PATCH_STARTUP_SPEED.md` Task 4:
total waktu tunggu jadi jumlah semua query padahal bisa jadi `max()` saja
lewat `asyncio.gather`.

Lokasi:
1. `server/handlers/event_listeners.py` — `_on_download_complete()`
2. `server/handlers/websocket.py` — action `"discover"`
3. `server/handlers/websocket.py` — action `"delete_download"`

### PERUBAHAN

#### 3a. `server/handlers/event_listeners.py`

**Cari:**
```python
            ds = DiscoverService(playback_controller.resolver.db)
            recent = await ds.get_recent(15)
            cached = await ds.get_cached(15)
            featured_artists = await ds.get_featured_artists(100)
            featured_genres = await ds.get_featured_genres(100)
```

**Ganti dengan:**
```python
            ds = DiscoverService(playback_controller.resolver.db)
            # 4 query independent — jalankan bersamaan, bukan berurutan
            recent, cached, featured_artists, featured_genres = await asyncio.gather(
                ds.get_recent(15),
                ds.get_cached(15),
                ds.get_featured_artists(100),
                ds.get_featured_genres(100),
            )
```

Tambahkan `import asyncio` di module level jika belum ada.

#### 3b. `server/handlers/websocket.py` — action `"discover"`

**Cari:**
```python
        elif action == "discover":
            ds = DiscoverService(db)
            recent = await ds.get_recent(15)
            favorites = await ds.get_favorites(15)
            cached = await ds.get_cached(15)
            featured_artists = await ds.get_featured_artists(100)
            featured_genres = await ds.get_featured_genres(100)
```

**Ganti dengan:**
```python
        elif action == "discover":
            ds = DiscoverService(db)
            # 5 query independent — jalankan bersamaan, bukan berurutan
            recent, favorites, cached, featured_artists, featured_genres = await asyncio.gather(
                ds.get_recent(15),
                ds.get_favorites(15),
                ds.get_cached(15),
                ds.get_featured_artists(100),
                ds.get_featured_genres(100),
            )
```

(`favorites` tidak dipakai di payload response saat ini — cek dulu apakah
memang sengaja tidak dikirim, atau itu bug terpisah yang layak dicek belah.)

#### 3c. `server/handlers/websocket.py` — action `"delete_download"`

**Cari:**
```python
                    ds = DiscoverService(db)
                    recent = await ds.get_recent(15)
                    cached = await ds.get_cached(15)
                    featured_artists = await ds.get_featured_artists(100)
                    featured_genres = await ds.get_featured_genres(100)
```

**Ganti dengan:**
```python
                    ds = DiscoverService(db)
                    recent, cached, featured_artists, featured_genres = await asyncio.gather(
                        ds.get_recent(15),
                        ds.get_cached(15),
                        ds.get_featured_artists(100),
                        ds.get_featured_genres(100),
                    )
```

Pastikan `import asyncio` ada di module level `websocket.py` (kemungkinan
sudah ditambahkan kalau Task `PATCH_PAUSE_DELAY.md`/`PATCH_STARTUP_SPEED.md`
sudah di-apply lebih dulu).

### VERIFIKASI

```bash
python -m pytest tests/ -x -q
```
Manual test: buka tab Discover → data harus tetap lengkap dan benar
(recent/favorites/cached/featured), tapi loading terasa lebih cepat,
terutama setelah download selesai atau hapus file download.

---

## TASK 4 (opsional, dampak kecil) — `engine/mpv_controller.py`: Paralelkan observe_property

### ROOT CAUSE

```python
await self._command(["observe_property", 1, "time-pos"])
await self._command(["observe_property", 2, "pause"])
await self._command(["observe_property", 3, "duration"])
```

Tiga command independent dikirim berurutan saat `_observe_events()` mulai.
Hanya jalan sekali per connect/reconnect, jadi dampaknya kecil — masukkan
kalau sedang merapikan file ini saja, tidak perlu jadi task terpisah.

### PERUBAHAN

**Cari:**
```python
        try:
            await self._command(["observe_property", 1, "time-pos"])
            await self._command(["observe_property", 2, "pause"])
            await self._command(["observe_property", 3, "duration"])
```

**Ganti dengan:**
```python
        try:
            await asyncio.gather(
                self._command(["observe_property", 1, "time-pos"]),
                self._command(["observe_property", 2, "pause"]),
                self._command(["observe_property", 3, "duration"]),
            )
```

### VERIFIKASI

Manual test: connect ke mpv → progress, pause-state, dan duration event
semua tetap masuk normal setelah play track pertama.

---

## CATATAN

- Task 1 dan 2 aman diterapkan independen, tidak saling bergantung.
- Task 3 menyentuh file yang ditandai restricted (`websocket.py`) —
  minta izin eksplisit dulu sebelum apply, sesuai aturan di `AI_CONTEXT.md`.
- Task 4 boleh dilewati kalau tidak sedang menyentuh `mpv_controller.py`
  untuk alasan lain — dampaknya tidak signifikan dibanding 3 task di atas.
- Belum ada task yang di-apply di sesi ini — dokumen ini murni hasil scan
  untuk direview sebelum eksekusi.

# PATCH_DB_MAINTENANCE_LYRICS_PAYLOAD.md

Baca `AI_CONTEXT.md` dulu. Belum di-apply — dokumen rencana dari scan
lanjutan (setelah `PATCH_PAUSE_DELAY.md`, `PATCH_BATTERY_DRAIN.md`,
`PATCH_STARTUP_SPEED.md`, `PATCH_PLAYCOUNT_LAZYIMPORT_DISCOVER.md`).

**Catatan versi:** dokumen `PATCH_PLAYCOUNT_LAZYIMPORT_DISCOVER.md`
sebelumnya sempat menyebut fitur favorit — itu sudah tidak relevan karena
fitur favorit sudah dihapus total dari project. Dua bug di dokumen ini
tidak berkaitan dengan fitur favorit sama sekali, jadi tetap valid.

---

## RINGKASAN

| # | Bug | File | Dampak |
|---|-----|------|--------|
| 1 | DB maintenance (eviction + session cleanup) tidak pernah dijadwalkan | `main.py`, `cache/db.py` (tidak diubah, cuma dipanggil) | Tinggi — DB bengkak tanpa batas |
| 2 | `state` broadcast duplikat payload lirik penuh di setiap event | `server/serializers.py`, `server/services/broadcast_service.py`, `server/handlers/event_listeners.py` | Sedang — bandwidth/CPU JSON serialize berulang tanpa guna |

Tidak ada perubahan API/arsitektur. Tidak ada file baru.

---

## TASK 1 — Jadwalkan `evict_stale_tracks()` dan `cleanup_sessions()`

### ROOT CAUSE

`cache/db.py` sudah punya dua method maintenance yang lengkap dan benar:

```python
async def evict_stale_tracks(self) -> int: ...   # baris 85
async def cleanup_sessions(self) -> None: ...     # baris 258
```

Tapi tidak ada satupun pemanggil di seluruh codebase:

```bash
grep -rn "cleanup_sessions\|evict_stale_tracks" --include="*.py" .
# hanya muncul di definisi method itu sendiri
```

Bandingkan dengan `mpv_reconnect_checker` (tiap 30 detik) dan
`check_connectivity` (tiap 5 menit) di `main.py` — keduanya dijadwalkan
sebagai background task sejak awal. Dua method maintenance ini kelihatannya
lupa di-wire saat ditulis.

**Dampak nyata:**
- `resolver.resolve()` (Rule 3, cache miss) memanggil `upsert_track()`
  setiap kali sebuah video baru di-resolve — row masuk ke tabel `tracks`
  selamanya, walau video itu cuma dicoba sekali dan tak pernah diputar lagi.
- Setiap login admin sukses membuat row baru di tabel `sessions` yang
  tidak pernah dihapus meski sudah expired (`expires_at` terlewat).
- Di device dengan storage terbatas (Termux), `lunawave.db` tumbuh tanpa
  batas seiring waktu, dan semakin besar tabel `tracks` semakin lambat
  juga query discover (`get_recent`, `get_cached`, dst).

### PERUBAHAN

**File:** `main.py`

**Cari blok background task yang sudah ada** (setelah `nowplaying.start()`,
sebelum bagian `# 7.5 MPV auto-reconnect checker`):

```python
    # Connectivity Check
    async def check_connectivity():
        while True:
            try:
                async with http_session.get(
                    "https://connectivitycheck.gstatic.com/generate_204",
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as r:
                    state.is_online = (r.status == 204)
            except (aiohttp.ClientError, asyncio.TimeoutError):
                state.is_online = False
            except Exception as e:
                structlog.get_logger(__name__).warning(f"Connectivity check unexpected error: {e}")
                state.is_online = False

            await asyncio.sleep(60)

    connectivity_task = safe_create_task(check_connectivity(), name="connectivity_checker")
    tasks = [connectivity_task]
```

**Tambahkan setelah baris `tasks = [connectivity_task]`:**

```python
    # DB Maintenance: eviction track stale + cleanup session expired.
    # Sebelumnya kedua method ini ada di cache/db.py tapi tidak pernah
    # dipanggil — DB bisa tumbuh tanpa batas tanpa ini.
    async def db_maintenance():
        while True:
            await asyncio.sleep(6 * 3600)  # tiap 6 jam — cukup, tidak perlu sering
            try:
                deleted = await db.evict_stale_tracks()
                if deleted:
                    structlog.get_logger(__name__).info(f"DB maintenance: {deleted} track stale dihapus")
            except Exception as e:
                structlog.get_logger(__name__).warning(f"DB maintenance (evict_stale_tracks) gagal: {e}")
            try:
                await db.cleanup_sessions()
            except Exception as e:
                structlog.get_logger(__name__).warning(f"DB maintenance (cleanup_sessions) gagal: {e}")

    tasks.append(safe_create_task(db_maintenance(), name="db_maintenance"))
```

**Opsional tapi disarankan:** jalankan sekali juga saat startup (bukan
cuma nunggu 6 jam pertama), supaya instalasi lama yang baru pertama kali
kena patch ini langsung terbersihkan tanpa nunggu:

```python
    async def db_maintenance():
        # Jalankan sekali di awal, baru masuk loop periodik
        try:
            deleted = await db.evict_stale_tracks()
            if deleted:
                structlog.get_logger(__name__).info(f"DB maintenance (awal): {deleted} track stale dihapus")
        except Exception as e:
            structlog.get_logger(__name__).warning(f"DB maintenance awal (evict_stale_tracks) gagal: {e}")
        try:
            await db.cleanup_sessions()
        except Exception as e:
            structlog.get_logger(__name__).warning(f"DB maintenance awal (cleanup_sessions) gagal: {e}")

        while True:
            await asyncio.sleep(6 * 3600)
            try:
                deleted = await db.evict_stale_tracks()
                if deleted:
                    structlog.get_logger(__name__).info(f"DB maintenance: {deleted} track stale dihapus")
            except Exception as e:
                structlog.get_logger(__name__).warning(f"DB maintenance (evict_stale_tracks) gagal: {e}")
            try:
                await db.cleanup_sessions()
            except Exception as e:
                structlog.get_logger(__name__).warning(f"DB maintenance (cleanup_sessions) gagal: {e}")

    tasks.append(safe_create_task(db_maintenance(), name="db_maintenance"))
```

Pilih salah satu versi (dengan atau tanpa run-sekali-di-awal) sesuai
preferensi — keduanya aman.

### VERIFIKASI

```bash
python -m pytest tests/ -x -q
```
Manual test:
- Cek `cache/lunawave.db` sebelum & sesudah patch di device yang sudah
  lama dipakai — pastikan `evict_stale_tracks()` menghapus row yang
  memang stale (play_count=0, bukan lokal, stream_url kadaluwarsa >30 hari)
  tanpa menyentuh track yang masih relevan (favorit dihapus jadi kriteria
  itu sudah tidak berlaku — pastikan query di `evict_stale_tracks()`
  tidak lagi mereferensikan kolom `is_favorite` yang sudah dihapus dari
  schema, kalau kolomnya memang sudah dibuang saat fitur favorit dicabut).
- Cek tabel `sessions` — token yang sudah lewat `expires_at` harus hilang
  setelah maintenance jalan.
- Pastikan tidak ada crash kalau `db_maintenance` gagal sekali (mis. DB
  locked sesaat) — loop harus lanjut ke siklus berikutnya, bukan mati.

**PENTING:** karena fitur favorit sudah dihapus, cek dulu apakah
`evict_stale_tracks()` di `cache/db.py` masih mereferensikan kolom
`is_favorite` (lihat query `WHERE ... AND (is_favorite = 0 OR is_favorite IS NULL)`).
Kalau kolom itu sudah dibuang dari schema saat fitur favorit dihapus,
query ini perlu disesuaikan dulu (hapus klausanya) sebelum Task 1 ini
di-apply — kalau tidak, query akan error karena kolom tidak ada.

---

## TASK 2 — Jangan duplikasi payload lirik penuh di setiap `state` broadcast

### ROOT CAUSE

`server/serializers.py::state_to_dict()` selalu menyertakan
`lyrics_lines` dan `lyrics_timestamps` (bisa 200+ baris per lagu) di
**setiap** broadcast bertipe `"state"`:

```python
def state_to_dict(state: AppState) -> dict:
    return {
        ...
        "lyrics_lines": list(state.lyrics_lines),
        "lyrics_timestamps": list(state.lyrics_timestamps),
        "lyrics_index": state.lyrics_index,
        "lyrics_offset": state.lyrics_offset,
        ...
    }
```

Padahal sudah ada channel broadcast khusus untuk lirik —
`broadcast_lyrics()` — yang dipicu oleh `LyricsUpdatedEvent` dan sudah
di-throttle (lihat `PATCH_BATTERY_DRAIN.md` Task 3). Tiga event yang
memicu `broadcast_state()` di `event_listeners.py` —
`TrackStartedEvent`, `QueueUpdatedEvent`, `DownloadCompleteEvent` — semua
ikut menyeret payload lirik penuh yang sebenarnya sudah/akan dikirim
lewat message `"lyrics"` terpisah. Ini kerja JSON-serialize + kirim WS
yang berulang tanpa manfaat tambahan bagi client.

**Yang HARUS dijaga (supaya tidak regresi):** initial snapshot saat
client baru connect (`server/handlers/websocket.py`, tepat setelah
`manager.connect(ws)`) **butuh** lirik penuh — karena ini satu-satunya
titik di mana client yang baru refresh/connect mid-lagu bisa dapat lirik
tanpa menunggu `lyrics_index` berubah lagi. Karena itu fix-nya bukan
menghapus field ini begitu saja dari `state_to_dict()`, tapi membuatnya
opsional lewat parameter.

### PERUBAHAN

#### 2a. `server/serializers.py`

**Cari:**
```python
def state_to_dict(state: AppState) -> dict:
    return {
        "status": state.status.name,
        "playback_mode": state.playback_mode.name,
        "current_track": track_to_dict(state.current_track),
        "position": state.position,
        "duration": state.duration,
        "volume": state.volume,
        "audio_output": getattr(state, "audio_output", AudioOutput.DEVICE).value,
        "sponsorblock_active": state.sponsorblock_active,
        "queue": [track_to_dict(t) for t in state.queue],
        "radio_queue": [track_to_dict(t) for t in state.radio_queue],
        "history_count": len(state.history),
        "lyrics_lines": list(state.lyrics_lines),
        "lyrics_timestamps": list(state.lyrics_timestamps),
        "lyrics_index": state.lyrics_index,
        "lyrics_offset": state.lyrics_offset,
        "active_tab": state.active_tab,
        "error_msg": state.error_msg,
        "is_online": state.is_online,
        "download_progress": state.download_progress,
    }
```

**Ganti dengan:**
```python
def state_to_dict(state: AppState, include_lyrics: bool = True) -> dict:
    """include_lyrics=False dipakai untuk broadcast periodik (track start,
    queue update, download complete) yang tidak butuh payload lirik penuh
    lagi — lirik penuh sudah/akan dikirim lewat message "lyrics" terpisah
    (lihat broadcast_lyrics). Default True dipertahankan untuk initial
    snapshot saat client baru connect, yang memang butuh lirik penuh."""
    data = {
        "status": state.status.name,
        "playback_mode": state.playback_mode.name,
        "current_track": track_to_dict(state.current_track),
        "position": state.position,
        "duration": state.duration,
        "volume": state.volume,
        "audio_output": getattr(state, "audio_output", AudioOutput.DEVICE).value,
        "sponsorblock_active": state.sponsorblock_active,
        "queue": [track_to_dict(t) for t in state.queue],
        "radio_queue": [track_to_dict(t) for t in state.radio_queue],
        "history_count": len(state.history),
        "lyrics_index": state.lyrics_index,
        "lyrics_offset": state.lyrics_offset,
        "active_tab": state.active_tab,
        "error_msg": state.error_msg,
        "is_online": state.is_online,
        "download_progress": state.download_progress,
    }
    if include_lyrics:
        data["lyrics_lines"] = list(state.lyrics_lines)
        data["lyrics_timestamps"] = list(state.lyrics_timestamps)
    return data
```

#### 2b. `server/services/broadcast_service.py`

**Cari:**
```python
    async def broadcast_state(self, state: AppState):
        await self.manager.broadcast({
            "type": "state",
            "data": state_to_dict(state),
        })
```

**Ganti dengan:**
```python
    async def broadcast_state(self, state: AppState, include_lyrics: bool = False):
        # Default False: broadcast periodik (track start/queue update/download
        # complete) tidak perlu menyeret ulang payload lirik penuh — sudah
        # ditangani broadcast_lyrics(). Panggil dengan include_lyrics=True
        # khusus untuk initial snapshot saat client baru connect.
        await self.manager.broadcast({
            "type": "state",
            "data": state_to_dict(state, include_lyrics=include_lyrics),
        })
```

#### 2c. `server/handlers/websocket.py` — initial snapshot tetap kirim lirik penuh

**Cari:**
```python
    try:
        await ws.send_str(json.dumps({
            "type": "state",
            "data": state_to_dict(state),
        }, ensure_ascii=False))
```

**Ganti dengan:**
```python
    try:
        # include_lyrics=True: initial snapshot butuh lirik penuh karena
        # client yang baru connect (mis. refresh halaman mid-lagu) tidak
        # akan dapat lirik lagi sampai lyrics_index berubah berikutnya.
        await ws.send_str(json.dumps({
            "type": "state",
            "data": state_to_dict(state, include_lyrics=True),
        }, ensure_ascii=False))
```

Catatan: pemanggilan `broadcast_service.broadcast_state(state)` yang
sudah ada di `event_listeners.py` (untuk `TrackStartedEvent`,
`QueueUpdatedEvent`, `DownloadCompleteEvent`) **tidak perlu diubah** —
default `include_lyrics=False` di `broadcast_service.py` sudah otomatis
berlaku untuk ketiganya.

### VERIFIKASI

```bash
python -m pytest tests/ -x -q
```
Manual test:
1. Play lagu yang ada lirik → tab lirik muncul normal (via message
   `"lyrics"`, tidak berubah).
2. Refresh halaman browser di tengah lagu yang sedang ada lirik →
   lirik tetap langsung muncul (dari initial snapshot `include_lyrics=True`),
   tidak nunggu index berubah dulu.
3. Update queue (tambah/hapus/reorder) atau selesai download → cek
   payload WS message `"state"` di DevTools Network tab tidak lagi
   membawa `lyrics_lines`/`lyrics_timestamps` (field lain tetap ada).
4. Ganti lagu (radio/queue) beberapa kali cepat → pastikan lirik lagu
   baru tetap sinkron seperti biasa.

---

## CATATAN

- Task 1 dan Task 2 independen, bisa diterapkan terpisah.
- Task 1: sebelum apply, cek dulu apakah `evict_stale_tracks()` di
  `cache/db.py` masih mereferensikan kolom `is_favorite` yang mungkin
  sudah dibuang bareng penghapusan fitur favorit — sesuaikan query itu
  dulu kalau perlu.
- Task 2 mengubah signature `state_to_dict()` dan `broadcast_state()`
  (menambah parameter opsional dengan default aman) — bukan perubahan
  arsitektur, tapi tetap cek semua pemanggil lain kalau ada yang belum
  ke-cover di atas (grep `state_to_dict(` dan `broadcast_state(` di
  seluruh codebase sebelum apply, untuk memastikan tidak ada titik lain
  yang butuh `include_lyrics=True` selain initial snapshot).
- Belum ada task yang di-apply di sesi ini — dokumen ini murni hasil
  scan untuk direview sebelum eksekusi.

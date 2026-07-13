# Caching

← [architecture/backend.md](../architecture/backend.md) | [Blueprint.md](../Blueprint.md)

---

## Gambaran Umum

LunaWave memiliki dua jenis cache yang berbeda tujuan:

| Cache | Lokasi | Isi | Persisten |
|---|---|---|---|
| Stream URL Cache | `cache/resolver.py` | URL stream yt-dlp (TTL pendek) | Opsional (SQLite) |
| MP3 File Cache | `cache/mp3/` | File MP3 yang sudah didownload | ✅ Permanen |

---

## Stream URL Cache (`cache/resolver.py`)

### Masalah yang Diselesaikan

yt-dlp perlu waktu 1–3 detik untuk me-resolve URL stream dari video_id. Jika URL di-cache, pemutaran ulang track yang sama instan.

### Strategi Cache

```
get_stream_url(video_id)
        │
        ├── Cek in-memory cache (dict)
        │       └── Hit + tidak expired → return langsung
        │
        ├── Cek SQLite cache (opsional, untuk persistensi lintas restart)
        │       └── Hit + tidak expired → return, update in-memory
        │
        └── Miss → yt-dlp resolve → simpan ke in-memory + SQLite → return
```

### TTL (Time to Live)

| Jenis URL | TTL |
|---|---|
| YouTube stream URL | 6 jam (URL YouTube expire setelah ~6 jam) |
| URL dari sumber lain | 24 jam |

TTL dikonfigurasi di `config.py`:
```python
STREAM_URL_CACHE_TTL_SECONDS = 6 * 3600
```

### Invalidasi Manual

```python
await resolver.invalidate(video_id)      # hapus satu entry
await resolver.invalidate_all()           # clear semua cache
```

Dipanggil jika ada error saat load (URL sudah expired sebelum TTL).

### Interface

```python
class CacheResolver:
    async def get_stream_url(self, video_id: str) -> str | None
    async def set_stream_url(self, video_id: str, url: str) -> None
    async def invalidate(self, video_id: str) -> None
    async def invalidate_all(self) -> None
    async def is_cached(self, video_id: str) -> bool
```

Test → `tests/unit/cache/test_resolver.py`

---

## MP3 File Cache (`cache/mp3/`)

### Gambaran Umum

Folder penyimpanan permanen file MP3 yang didownload via `CMD_DOWNLOAD_START`.

```
cache/mp3/
├── abc123.mp3
├── def456.mp3
└── ...
```

Penamaan file: `{video_id}.mp3` — tidak ada subdirectory.

### Hubungan dengan Database

Setelah download selesai, path file disimpan di `persistence/track_repo.py`:

```python
await track_repo.update_file_path(
    video_id="abc123",
    file_path="cache/mp3/abc123.mp3"
)
```

Saat play, `track_loader.py` cek `file_path` di database terlebih dahulu:

```
load_track(video_id)
        │
        ├── track_repo.get(video_id).file_path ada?
        │       └── Ya → load dari file lokal (tidak perlu yt-dlp)
        │
        └── Tidak ada → resolve stream URL via yt-dlp
```

### Manajemen Storage

Saat ini tidak ada auto-cleanup. File MP3 menumpuk secara manual.

Rencana masa depan (bukan priority sekarang):
- Tambah `max_cache_size_mb` di config
- Auto-delete file terlama jika melebihi limit

### Gitignore

```gitignore
cache/mp3/
data/lunawave.db
```

Keduanya runtime artifact — tidak di-commit ke repo.

---

## Hubungan Cache ↔ Persistence ↔ Background Jobs

```
CMD_DOWNLOAD_START
        │
        ▼
download_manager.py
        │
        ├── cache/resolver.py (resolve URL dulu)
        │
        ├── adapters/ytdlp/downloader.py (download file)
        │       └── output → cache/mp3/{video_id}.mp3
        │
        └── persistence/track_repo.py (update file_path di DB)

CMD_PLAY
        │
        ▼
engine/playback/track_loader.py
        │
        ├── persistence/track_repo.py.file_path? → load dari cache/mp3/ (lokal)
        │
        └── cache/resolver.py.get_stream_url()  → stream dari yt-dlp
```

---

## Dokumen Terkait

- [backend/persistence.md](persistence.md) — SQLite track repository
- [backend/background_jobs.md](background_jobs.md) — Download manager yang mengisi MP3 cache
- [architecture/data_flow.md](../architecture/data_flow.md) — Flow download end-to-end

# Backend Services

← [architecture/backend.md](../architecture/backend.md) | [Blueprint.md](../Blueprint.md)

---

## Engine Layer

Engine adalah domain logic utama LunaWave. Semua handler di engine hanya berbicara ke `core/` lewat ports — tidak ada import langsung ke `adapters/` atau `persistence/` kecuali lewat injeksi dependency.

---

### `engine/command_router.py`

Menerima `CMD_*` dari `command_bus` dan mendispatch ke handler yang tepat.

```python
# Pola routing
HANDLERS = {
    CMD_PLAY:           playback_controller.handle_play,
    CMD_PAUSE:          playback_controller.handle_pause,
    CMD_SKIP_NEXT:      playback_controller.handle_skip_next,
    CMD_SKIP_PREV:      playback_controller.handle_skip_prev,
    CMD_SEEK:           playback_controller.handle_seek,
    CMD_SET_VOLUME:     volume_service.handle_set_volume,
    CMD_QUEUE_ADD:      queue_manager.handle_add,
    CMD_QUEUE_REMOVE:   queue_manager.handle_remove,
    CMD_QUEUE_REORDER:  queue_manager.handle_reorder,
    CMD_RADIO_START:    radio_engine.handle_start,
    CMD_DOWNLOAD_START: download_manager.handle_start,
    CMD_DOWNLOAD_CANCEL:download_manager.handle_cancel,
    CMD_SEARCH:         discover_service.handle_search,
}
```

Test → `tests/unit/engine/test_command_router.py`

---

### `engine/playback/controller.py`

Orchestrator playback. Slim — hanya routing, tidak ada logic detail di sini.

**Tanggung jawab:**
- Menerima CMD_PLAY → panggil `track_loader.load_track()`
- Menerima CMD_PAUSE / CMD_SKIP → panggil port `AudioPlayerPort`
- Publish `EVENT_PLAYBACK_*` ke event bus setelah setiap aksi

**Tidak boleh:**
- Akses langsung ke MPV (lewat port saja)
- Akses langsung ke database (lewat `persistence/` saja)

Sub-modul:

| File | Tanggung Jawab |
|---|---|
| `track_loader.py` | Resolve URL (cache → yt-dlp) lalu load ke player |
| `queue_ops.py` 🆕 | next/prev track dari queue saat playback selesai |
| `mode_ops.py` 🆕 | Switch mode normal/radio/shuffle |

Test → `tests/unit/engine/playback/`

---

### `engine/radio/engine.py`

Orchestrator radio mode. Mengelola siklus: pilih artis → search → filter → enqueue → prefetch.

**Alur radio:**

```
CMD_RADIO_START
      │
      ▼
artist_selector.select_next(history)
      │
      ▼
ytdlp_adapter.search(artist + " music")
      │
      ▼
track_filter.filter(results, history, current_queue)
      │
      ▼
queue_manager.enqueue(track)
      │
      ▼
prefetcher.schedule_next()   ← async, tidak blocking
      │
      ▼
EventBus.publish(EVENT_RADIO_TRACK_QUEUED)
```

**⚠️ Titik rawan:** `track_filter.py` adalah sumber bug radio mode yang paling umum — filter terlalu agresif menyebabkan queue kosong. Prioritas test tertinggi di modul ini.

Sub-modul:

| File | Tanggung Jawab | Catatan |
|---|---|---|
| `engine.py` | Orchestrator, export `RadioMode` | |
| `prefetcher.py` | Background prefetch track berikutnya | Async task |
| `artist_selector.py` | Pilih artis berikutnya berdasar riwayat | |
| `track_filter.py` | Filter duplikat, recently-played, blacklist | ⚠️ Bug-prone |

Test → `tests/unit/engine/radio/` — `test_track_filter.py` prioritas tertinggi.

---

### `engine/queue_manager.py`

Manajemen queue track. State queue disimpan di `core/state.py`, bukan di sini.

**Operasi:**
- `add(track, position=None)` — tambah ke akhir atau posisi tertentu
- `remove(index)` — hapus dari posisi
- `reorder(from_index, to_index)` — drag & drop
- `clear()` — kosongkan queue
- `get_next()` / `get_prev()` — dipakai oleh playback

Setiap operasi → publish `EVENT_QUEUE_UPDATED`.

Test → `tests/unit/engine/test_queue_manager.py`

---

### `engine/volume_service.py`

Wrapper tipis untuk set/get volume.

```python
async def handle_set_volume(volume: int) -> None:
    clamped = max(0, min(100, volume))
    await audio_player_port.set_volume(clamped)
    state.volume = clamped
    await event_bus.publish(EVENT_VOLUME_CHANGED, {"volume": clamped})
```

Test → `tests/unit/engine/test_volume_service.py`

---

## Services Layer

### `services/discover_service.py`

Logic discover: mix artis dari library, trending, rekomendasi berdasar riwayat.

**Tanggung jawab:**
- Query `artist_repo` dan `track_repo` untuk data lokal
- Susun rekomendasi (belum ada ML — rule-based untuk sekarang)
- Return `List[TrackInfo]` ke handler

Test → `tests/unit/services/test_discover_service.py`

---

### `server/services/broadcast_service.py`

Subscribe ke `event_bus` dan broadcast state ke semua koneksi WebSocket aktif.

```python
# Setiap event yang relevan → serialize state → kirim ke semua WS
async def on_event(event_type: str, payload: dict) -> None:
    message = serialize_state(state, event_type, payload)
    await connection_manager.broadcast(message)
```

Berkaitan dengan → [backend/api.md](api.md) (format pesan)

Test → `tests/unit/server/services/test_broadcast_service.py`

---

### `server/services/stream_prefetch.py`

Prefetch URL stream untuk track berikutnya di queue, sebelum dibutuhkan.

**Kapan berjalan:** setelah `EVENT_TRACK_CHANGED`, resolve URL track ke-2 di queue secara background.

**Kenapa:** yt-dlp resolve bisa 1–3 detik. Prefetch menghilangkan jeda saat skip.

Test → `tests/unit/server/services/test_stream_prefetch.py`

---

## Plugins

Plugin mengimplementasikan port dari `core/ports.py`. Tidak ada dependency ke `engine/` atau `server/`.

### `plugins/lyrics_fetcher.py`

Implements `LyricsProvider`.

```python
async def fetch(self, title: str, artist: str) -> LyricsResult | None:
    # coba provider 1 (LRCLIB), fallback ke provider 2
```

### `plugins/lyrics_parser.py`

Parse format LRC (timed lyrics) dan SRT menjadi `List[LyricLine]`.

```python
@dataclass
class LyricLine:
    timestamp: float   # detik
    text: str
```

### `plugins/lyrics_sync.py`

Subscribe `EVENT_POSITION_CHANGED` → cari lyric line yang tepat → publish `EVENT_LYRIC_LINE`.

### `plugins/sponsorblock.py`

Implements `SponsorBlockProvider`. Fetch segment dari SponsorBlock API, publish `EVENT_SEGMENT_SKIP` saat posisi masuk segment sponsor.

### `plugins/notifications.py`

Implements `NotificationProvider`. Kirim desktop notification saat track berubah.

---

## Fake Implementations

Semua port memiliki fake untuk unit test:

| Fake | Implements | Lokasi |
|---|---|---|
| `FakeAudioPlayer` | `AudioPlayerPort` | `tests/fakes/fake_audio_player.py` |
| `FakeMediaExtractor` | `MediaExtractorPort` | `tests/fakes/fake_media_extractor.py` |
| `FakeLyricsProvider` | `LyricsProvider` | `tests/fakes/fake_lyrics_provider.py` |
| `FakeSponsorBlock` | `SponsorBlockProvider` | `tests/fakes/fake_sponsorblock_provider.py` |

---

## Dokumen Terkait

- [architecture/domain.md](../architecture/domain.md) — Port & Protocol definitions
- [backend/background_jobs.md](background_jobs.md) — Download manager & radio prefetch detail
- [backend/api.md](api.md) — Format pesan WebSocket
- [testing/unit_testing.md](../testing/unit_testing.md) — Tabel unit test engine & services

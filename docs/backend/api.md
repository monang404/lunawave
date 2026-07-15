# API Reference

← [architecture/backend.md](../architecture/backend.md) | [Blueprint.md](../Blueprint.md)

---

## Gambaran Umum

LunaWave menyediakan dua jalur API:

- **WebSocket** `/ws` — komunikasi real-time dua arah (aksi + state broadcast)
- **HTTP** — auth, file statis, status

Semua aksi user dikirim lewat WebSocket. HTTP hanya untuk bootstrap (login, load `index.html`).

Alasan single-channel WS → [ADR-0005](../adr/0005-websocket-single-channel.md)

---

## WebSocket API

### Koneksi

```
ws://localhost:{PORT}/ws?token={AUTH_TOKEN}
```

Token diperoleh dari `POST /auth/login`. Koneksi tanpa token atau token invalid langsung ditutup dengan kode `4001`.

### Format Pesan — Client → Server (Command)

```json
{
  "cmd": "string",
  "payload": {}
}
```

### Format Pesan — Server → Client (State)

```json
{
  "type": "state | full_state | error",
  "playback": {},
  "queue": [],
  "volume": 75,
  "mode": "normal | radio | shuffle",
  "downloads": [],
  "radio": null
}
```

---

## WebSocket Commands

### Playback

| Command | Payload | Keterangan |
|---|---|---|
| `play_track` | `{"video_id": "abc123"}` | Mainkan track dari video_id |
| `toggle_pause` | `{}` | Pause/resume toggle |
| `stop` | `{}` | Stop dan reset posisi |
| `next` | `{}` | Skip ke track berikutnya |
| `prev` | `{}` | Kembali ke track sebelumnya |
| `seek` | `{"position": 42.5}` | Seek ke posisi (detik) |
| `volume_set` | `{"volume": 75}` | Set volume (0–100) |
| `volume_up` | `{}` | Volume naik |
| `volume_down` | `{}` | Volume turun |
| `set_mode` | `{"mode": "QUEUE\|RADIO"}` | Ganti mode playback |
| `set_output` | `{"output": "browser\|device"}` | Ganti output audio |
| `set_loop` | `{"mode": "off\|track\|queue"}` | Set loop mode |
| `set_speed` | `{"speed": 1.5}` | Set kecepatan putar (0.25–4.0) |
| `set_sleep_timer` | `{"minutes": 15}` | Sleep timer (0 = off) |
| `set_crossfade` | `{"enabled": true}` | Toggle crossfade |
| `set_sponsorblock` | `{"enabled": true}` | Toggle SponsorBlock |
| `lyrics_offset` | `{"offset": -0.5}` | Adjust lyrics offset (detik) |

### Queue

| Command | Payload | Keterangan |
|---|---|---|
| `queue_add` | `{"video_id": "abc", "position": null}` | Tambah ke queue (null = akhir) |
| `queue_remove` | `{"index": 2}` | Hapus dari index |
| `queue_reorder` | `{"from_index": 1, "to_index": 3}` | Pindah posisi (drag & drop) |
| `queue_select` | `{"index": 0}` | Mainkan langsung dari posisi queue |
| `enqueue_artist_songs` | `{"artist": "Radiohead"}` | Tambah semua lagu artis ke queue |
| `enqueue_genre_songs` | `{"genre": "Rock"}` | Tambah semua lagu genre ke queue |

### Radio

| Command | Payload | Keterangan |
|---|---|---|
| `radio_randomize` | `{"seed_artist": null}` | Randomize sumber artis radio |

### Download

| Command | Payload | Keterangan |
|---|---|---|
| `download` | `{}` | Download track yang sedang diputar |
| `delete_download` | `{"video_id": "abc123"}` | Hapus file download lokal |

### Search & Discover

| Command | Payload | Keterangan |
|---|---|---|
| `search` | `{"query": "bohemian rhapsody"}` | Cari track |
| `discover` | `{}` | Dapatkan data discover (recent, cached) |

### Cache

| Command | Payload | Keterangan |
|---|---|---|
| `get_cache_size` | `{}` | Query ukuran folder cache MP3 |
| `clear_cache` | `{}` | Hapus semua file MP3 di cache |

---

## WebSocket State Events

Server broadcast state setelah setiap perubahan yang relevan.

### `state` — State Snapshot (Periodik & Event-driven)

Dikirim setelah setiap perubahan yang relevan. Berisi **state lengkap**.

```json
{
  "type": "state",
  "status": "PLAYING",
  "playback_mode": "QUEUE",
  "current_track": {
    "video_id": "abc123",
    "title": "Creep",
    "artist": "Radiohead",
    "duration": 243,
    "thumbnail": "https://...",
    "is_cached": false,
    "is_favorite": false
  },
  "position": 42.5,
  "duration": 243.0,
  "volume": 80,
  "playback_speed": 1.0,
  "loop_mode": "off",
  "crossfade_enabled": false,
  "audio_output": "browser",
  "sponsorblock_active": false,
  "loudness_normalization_enabled": true,
  "queue": [{"video_id": "def", "title": "Karma Police", ...}],
  "radio_queue": [],
  "history_count": 3,
  "lyrics_index": 12,
  "lyrics_offset": 0,
  "active_tab": "home",
  "error_msg": null,
  "is_online": true,
  "download_progress": null
}
```

### `lyric_line` — Lyric Sync

```json
{
  "type": "lyric_line",
  "line": "I wish I was special",
  "timestamp": 68.4,
  "next_timestamp": 72.1
}
```

### `download_progress`

```json
{
  "type": "download_progress",
  "video_id": "abc123",
  "pct": 63,
  "status": "downloading | done | error"
}
```

### `error`

```json
{
  "type": "error",
  "code": "STREAM_NOT_FOUND | DOWNLOAD_FAILED | RADIO_NO_TRACKS | AUTH_EXPIRED",
  "message": "Deskripsi error untuk display"
}
```

---

## HTTP API

### `POST /auth/login`

```json
// Request
{ "password": "your_password" }

// Response 200
{ "token": "eyJ...", "expires_in": 86400 }

// Response 401
{ "detail": "Invalid password" }
```

### `GET /`

Serve `web/static/index.html`. Redirect ke `/portal` jika belum auth.

### `GET /portal`

Serve halaman login (`portal.html`).

### `GET /static/{path}`

Serve file statis (JS, CSS, icons).

### `GET /status`

Health check, tidak memerlukan auth.

```json
{
  "status": "ok",
  "version": "1.2.0",
  "uptime": 3600
}
```

### `GET /stream/{video_id}`

Stream audio langsung (tanpa download). Proxy ke URL stream yang di-resolve dari yt-dlp.

Memerlukan token auth di header atau query param.

---

## Middleware

### Auth Middleware (`server/middleware.py`)

- WebSocket: validasi token dari query param `?token=`
- HTTP: validasi token dari header `Authorization: Bearer {token}`
- Endpoint `/status`, `/portal`, `/auth/login` dibebaskan dari auth

### CORS

Dikonfigurasi hanya untuk origin lokal (`localhost`, `127.0.0.1`) karena LunaWave tidak didesain sebagai layanan publik.

---

## Kode Error WebSocket

| Kode | Arti |
|---|---|
| `4001` | Token tidak valid atau tidak ada |
| `4002` | Token expired |
| `4003` | Server sedang shutdown |
| `1000` | Normal closure |
| `1011` | Server error tak terduga |

---

## Dokumen Terkait

- [backend/services.md](services.md) — Handler yang memproses setiap command
- [architecture/data_flow.md](../architecture/data_flow.md) — Sequence diagram request flow
- [frontend/state_management.md](../frontend/state_management.md) — Cara frontend memproses state
- [frontend/routing.md](../frontend/routing.md) — WS message routing di frontend
- [ADR-0005](../adr/0005-websocket-single-channel.md) — Kenapa single channel WS?

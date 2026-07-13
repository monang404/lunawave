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
| `play` | `{"video_id": "abc123"}` | Mainkan track dari video_id |
| `pause` | `{}` | Pause/resume toggle |
| `stop` | `{}` | Stop dan reset posisi |
| `skip_next` | `{}` | Skip ke track berikutnya |
| `skip_prev` | `{}` | Kembali ke track sebelumnya |
| `seek` | `{"position": 42.5}` | Seek ke posisi (detik) |
| `set_volume` | `{"volume": 75}` | Set volume (0–100) |

### Queue

| Command | Payload | Keterangan |
|---|---|---|
| `queue_add` | `{"video_id": "abc", "position": null}` | Tambah ke queue (null = akhir) |
| `queue_remove` | `{"index": 2}` | Hapus dari index |
| `queue_reorder` | `{"from": 1, "to": 3}` | Pindah posisi (drag & drop) |
| `queue_clear` | `{}` | Kosongkan queue |

### Radio

| Command | Payload | Keterangan |
|---|---|---|
| `radio_start` | `{"artist": "Radiohead"}` | Mulai mode radio dari artis |
| `radio_stop` | `{}` | Hentikan mode radio |

### Download

| Command | Payload | Keterangan |
|---|---|---|
| `download_start` | `{"video_id": "abc123"}` | Mulai download MP3 |
| `download_cancel` | `{"video_id": "abc123"}` | Batalkan download |

### Search & Discover

| Command | Payload | Keterangan |
|---|---|---|
| `search` | `{"query": "bohemian rhapsody"}` | Cari track |
| `discover` | `{"mode": "mix | trending | recent"}` | Dapatkan rekomendasi |

---

## WebSocket State Events

Server broadcast state setelah setiap perubahan yang relevan.

### `state` — Partial Update

Dikirim setelah aksi spesifik. Hanya field yang berubah yang disertakan.

```json
{
  "type": "state",
  "playback": {
    "status": "playing",
    "position": 42.5,
    "duration": 243.0,
    "track": {
      "video_id": "abc123",
      "title": "Creep",
      "artist": "Radiohead",
      "duration": 243,
      "thumbnail_url": "https://..."
    }
  }
}
```

### `full_state` — Full Snapshot

Dikirim saat koneksi pertama kali terhubung atau setelah reconnect.

```json
{
  "type": "full_state",
  "playback": { ... },
  "queue": [
    { "video_id": "abc", "title": "Creep", "artist": "Radiohead", "duration": 243 },
    { "video_id": "def", "title": "Karma Police", "artist": "Radiohead", "duration": 264 }
  ],
  "volume": 75,
  "mode": "radio",
  "radio": {
    "active": true,
    "current_artist": "Radiohead",
    "history": ["abc", "xyz"]
  },
  "downloads": [
    { "video_id": "ghi", "title": "High and Dry", "status": "downloading", "pct": 63 }
  ]
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

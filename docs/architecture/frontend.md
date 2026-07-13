# Frontend Architecture

← [architecture/overview.md](overview.md) | [Blueprint.md](../Blueprint.md)

---

## Filosofi Frontend

LunaWave menggunakan **vanilla JS tanpa framework** secara sengaja.

Alasan lengkap → [ADR-0006](../adr/0006-vanilla-js-over-framework.md)

Ringkasannya:
- Proyek ini adalah music player — DOM-nya stabil, bukan aplikasi CRUD kompleks
- Tidak ada build step (Webpack, Vite, dll.) = tidak ada dependency drift
- PWA offline-first lebih mudah dikontrol tanpa virtual DOM

---

## Peta Modul JavaScript

### Root

| File | Tanggung Jawab | Baris (saat ini) |
|---|---|---|
| `config.js` | Konstanta URL, timeout, feature flags | ~30 |
| `store.js` | State global client-side | ~90 |
| `dom.js` | Selector cache, DOM helpers | ~80 |
| `main.js` | Init: mount listeners, connect WS, check auth | ~120 |
| `portal.js` | Login portal logic | ~60 |
| `ws.js` | WebSocket lifecycle + routing pesan masuk | ~190 (slim) |

### `js/audio/`

| File | Tanggung Jawab |
|---|---|
| `playback-sync.js` 🆕 | Sinkronisasi `<audio>` element dengan state server |
| `visualizer.js` 🆕 | Canvas visualizer (opsional, bisa disabled) |

> Dipecah dari `audio.js` yang sebelumnya merangkap terlalu banyak.

### `js/events/`

| File | Tanggung Jawab |
|---|---|
| `index.js` | Mount semua event listener, entry point |
| `queue-events.js` | Drag/drop, reorder, hapus dari queue |
| `lyrics-events.js` | Toggle lirik, scroll sync |
| `settings-events.js` | Buka/tutup settings sheet, save preference |
| `transport-events.js` 🆕 | Play/pause/skip button handler |
| `progress-events.js` 🆕 | Seek bar: drag, click, release |
| `search-input-events.js` 🆕 | Debounce input, trigger search |
| `action-modal-events.js` 🆕 | Confirm/cancel modal actions |
| `click-delegation-events.js` 🆕 | Event delegation untuk list item dinamis |
| `keyboard-shortcut-events.js` 🆕 | Keyboard shortcut global |

> Semua dipecah dari `player-events.js` yang sebelumnya >300 baris.

### `js/render/`

| File | Tanggung Jawab |
|---|---|
| `player.js` | Render player bar (progress, controls, metadata) |
| `now-playing.js` | Render panel now-playing |
| `lyrics.js` | Render & highlight lirik sinkron |
| `search.js` | Render search result cards |
| `queue.js` | Render queue list |
| `discover-tab.js` 🆕 | Render discover tab (mix, trending) |
| `radio-tab.js` 🆕 | Render radio mode UI |
| `full-state.js` 🆕 | Render ulang full state setelah WS reconnect |

> `discover-tab.js` dan `radio-tab.js` dipecah dari `discover.js` yang sebelumnya merangkap dua tab.
> `full-state.js` dipindah dari `ws.js` untuk memisahkan routing dari rendering.

### `js/utils/`

| File | Tanggung Jawab |
|---|---|
| `format.js` 🆕 | Format durasi, tanggal, nama artis |
| `toast.js` 🆕 | Tampilkan toast notification |

### `js/services/`

| File | Tanggung Jawab |
|---|---|
| `auth.js` | HTTP request auth, token storage, refresh |

### `js/platform/`

| File | Tanggung Jawab |
|---|---|
| `keyboard.js` | Keyboard shortcut registry |
| `touch.js` | Touch gesture handler (swipe, long-press) |
| `viewport.js` | Viewport size, orientation change handler |

---

## Peta Modul CSS

### Prinsip CSS LunaWave

**Tidak ada refactor CSS besar-besaran.** File CSS yang belum disentuh dan berfungsi dengan baik dibiarkan. Penambahan dilakukan dengan menambah file baru, bukan memecah file yang ada kecuali ada alasan kuat.

Alasan lengkap → [frontend/ui_architecture.md](../frontend/ui_architecture.md)

### Struktur

| Folder/File | Tanggung Jawab |
|---|---|
| `tokens.css` | Design tokens: warna, spacing, radius, font |
| `portal.css` | Style login portal (terpisah dari app) |
| `base/` | Reset, typography, root variables |
| `layout/` | Grid, flex containers, panel layout |
| `platform/` | Mobile-specific, desktop-specific overrides |
| `components/toasts.css` | Toast notification |
| `components/lyrics.css` | Lirik panel & highlight |
| `components/queue.css` | Queue list & drag handle |
| `components/search.css` | Search result cards |
| `components/settings-sheet.css` | Settings bottom sheet |
| `components/player-controls.css` | Player bar: progress, buttons |
| `components/player-bar/` 🔧 | Pecahan `player-controls.css` — *hanya jika cascade bisa dipisah bersih* |
| `components/cards/` 🔧 | Discover & search cards — *prioritas rendah* |
| `vendor/tabler-icons.min.css` | Icon library |
| `vendor/fonts/` | Font files |

> 🔧 = opsional, hanya dikerjakan jika ada alasan nyata.

---

## Strategi CSS Konservatif

```
Tidak diubah:
├── file yang tidak rusak
├── file yang belum disentuh
└── refactor demi estetika semata

Boleh dipecah jika:
├── file > 200 baris
├── cascade bisa dipisah bersih tanpa memecah specificity
└── ada bug yang disebabkan oleh file yang terlalu besar
```

Detail lengkap → [frontend/ui_architecture.md](../frontend/ui_architecture.md)

---

## State Flow Frontend

```
WebSocket Message Masuk
        │
        ▼
    ws.js
  (routing)
        │
        ├──→ render/full-state.js   (full state update)
        ├──→ render/player.js        (playback state)
        ├──→ render/queue.js         (queue update)
        ├──→ render/lyrics.js        (lyric sync)
        └──→ render/discover-tab.js  (discover update)

User Action
        │
        ▼
  events/*.js
        │
        ▼
  store.js (optimistic update, opsional)
        │
        ▼
  WebSocket Send → Server
```

Detail → [frontend/state_management.md](../frontend/state_management.md)

---

## PWA

| File | Tanggung Jawab |
|---|---|
| `manifest.json` | PWA metadata: nama, ikon, display mode, theme color |
| `sw.js` | Service worker: precache, offline fallback, update strategy |
| `icons/icon-192.png` | Ikon PWA 192×192 |
| `icons/icon-512.png` | Ikon PWA 512×512 |

Detail → [frontend/pwa.md](../frontend/pwa.md)

---

## Dokumen Terkait

- [frontend/ui_architecture.md](../frontend/ui_architecture.md) — Detail CSS strategy & component map
- [frontend/state_management.md](../frontend/state_management.md) — store.js & WS state sync
- [frontend/routing.md](../frontend/routing.md) — Event routing & WS message routing
- [frontend/pwa.md](../frontend/pwa.md) — Service worker & manifest
- [testing/frontend_testing.md](../testing/frontend_testing.md) — Frontend test (opsional)
- [ADR-0006](../adr/0006-vanilla-js-over-framework.md) — Kenapa vanilla JS?

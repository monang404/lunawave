# Dependency Audit — ytgui / bagas.fm
> Source of truth: active source code (`.py`, `.js`, `.html`). Semua markdown/docs diabaikan.
> Tanggal audit: 2026-07-03

---

## Ringkasan Eksekutif

| Kategori | Jumlah |
|---|---|
| Deprecated Package | 1 |
| Unused Package (partial) | 1 |
| Security Vulnerability | 2 |
| Heavy Library | 2 |
| Duplicate Functionality | 2 |
| Version Conflict / Pinning Risk | 3 |
| Breaking Change Risk | 2 |
| Missing dari requirements.txt | 1 |

---

## 1. DEPRECATED PACKAGE

### `structlog==24.4.0` — Stale Pin
- **File**: `requirements.txt` baris 5
- **Digunakan**: `main.py`, `server/app.py`, `server/handlers/http.py`, `server/handlers/websocket.py`, `server/handlers/event_listeners.py`, `cache/resolver.py`, `server/services/stream_prefetch.py`, `core/log_config.py`
- **Status**: Versi `24.4.0` dirilis 2024. Versi terbaru di PyPI adalah `25.x`. Bukan deprecated, tapi pin ini sudah lebih dari setahun tanpa update.
- **Risiko**: Rendah secara fungsional. Versi baru membawa performance fix dan API perbaikan untuk `structlog.stdlib`. Tidak ada breaking change antara `24.x → 25.x` berdasarkan changelog.
- **Rekomendasi**: Naikkan ke `structlog>=24.4.0` (loose pin) atau `structlog==25.1.0` (latest).

---

## 2. UNUSED PACKAGE (Partial)

### `opentelemetry-sdk` — `BatchSpanProcessor` & `ConsoleSpanExporter` di-import tapi tidak digunakan
- **File**: `core/observability.py` baris 4
- **Import**:
  ```python
  from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
  ```
- **Kenyataan di source**: Fungsi `setup_tracing()` hanya membuat `TracerProvider()` tanpa menambahkan exporter apapun. `BatchSpanProcessor` dan `ConsoleSpanExporter` **tidak pernah dipanggil**.
- **Dampak**: `opentelemetry-sdk` tetap dibutuhkan untuk `TracerProvider` dan `tracer` (dipakai di `core/command_bus.py`). Tapi dua simbol di atas dead import.
- **Efek samping**: Span yang dibuat di `CommandBus` tidak di-export ke mana pun — tracing ada tapi invisible. Ini mungkin by design (placeholder), tapi harus didokumentasikan.
- **Rekomendasi**: Hapus dua dead import, atau implementasikan exporter sungguhan (OTLP/Jaeger). Kalau placeholder, tambahkan komentar `# TODO: add exporter`.

---

## 3. SECURITY VULNERABILITY

### 3a. `/metrics` endpoint terbuka tanpa auth
- **File**: `server/app.py` baris 45, `server/handlers/http.py` → `serve_metrics`
- **Source**:
  ```python
  app.router.add_get("/metrics", serve_metrics)
  ```
- **Analisis**: Endpoint `/metrics` menyajikan data Prometheus internal (command count, latency histogram, WebSocket gauge, event counter). Tidak ada `require_auth` decorator di route ini, berbeda dengan route lain yang menggunakan `handle_auth`.
- **Data yang bocor**: Pola penggunaan, jumlah command, koneksi aktif — cukup untuk fingerprinting.
- **Risiko**: Medium. Di jaringan lokal (Termux/LAN) risiko lebih rendah, tapi berbahaya jika server di-expose ke internet.
- **Rekomendasi**: Tambahkan `require_auth` di `serve_metrics`, atau batasi ke `127.0.0.1` via middleware.

### 3b. `@tabler/icons-webfont@latest` dari CDN — Supply Chain Risk
- **File**: `web/static/index.html` baris CDN
  ```html
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css">
  ```
- **Masalah**: `@latest` adalah floating reference. Setiap deploy bisa pull versi berbeda. Jika CDN atau package registry dikompromis, atau breaking change di icon fonts baru, UI rusak tanpa perubahan apapun di repo.
- **Contoh risiko nyata**: Tabler Icons v3 merename banyak icon dari konvensi lama.
- **Rekomendasi**: Pin ke versi spesifik: `@tabler/icons-webfont@3.x.x`. Atau self-host file CSS/font di `/static/`.

---

## 4. HEAVY LIBRARY

### 4a. `opentelemetry-api` + `opentelemetry-sdk` — Overhead untuk usage minimal
- **File**: `requirements.txt` baris 7-8, `core/observability.py`
- **Digunakan**: Hanya untuk satu `tracer.start_as_current_span()` call di `core/command_bus.py` baris 36.
- **Berat**: `opentelemetry-sdk` menarik banyak dependency (protobuf, dll). Di Termux/Android, ini berarti waktu install lebih lama dan RAM lebih besar.
- **Tidak ada exporter aktif**: Span dibuat tapi tidak dikirim ke mana pun (lihat poin 2).
- **Rekomendasi**: Untuk deployment Termux, pertimbangkan menghapus opentelemetry dan ganti satu span itu dengan structlog timing biasa. Jika ingin tetap ada, pasang exporter sungguhan agar cost-nya worth it.

### 4b. `prometheus_client>=0.20.0` — Overkill untuk single-user music player
- **File**: `requirements.txt` baris 6, `core/observability.py`, `server/handlers/http.py`
- **Digunakan**: 4 metric (Counter × 2, Histogram × 1, Gauge × 1). Endpoint `/metrics` tidak diauth.
- **Konteks**: Prometheus biasanya digunakan di production multi-instance. Untuk bagas.fm yang single-user di Termux, overhead library ini tidak proporsional.
- **Berat**: Library stabil, tapi berat untuk kebutuhan saat ini.
- **Rekomendasi**: Bisa diganti dengan in-memory counter sederhana + JSON endpoint. Atau pertahankan jika ada rencana monitoring serius — tapi amankan dulu endpoint-nya.

---

## 5. DUPLICATE FUNCTIONALITY

### 5a. `aiosqlite` vs `sqlite3` — Dua DB driver aktif
- **File**: `cache/db.py` (aiosqlite), `data/export_to_sqlite.py`, `data/import_artists.py`, `scratch/check_db.py` (sqlite3)
- **Analisis**:
  - Runtime production (`cache/db.py`) menggunakan `aiosqlite` — tepat untuk async server.
  - Script data (`data/`, `scratch/`) menggunakan `sqlite3` stdlib — wajar untuk one-off scripts.
- **Ini bukan duplikasi yang berbahaya**, tapi perlu dicatat agar tidak ada yang secara tidak sengaja menggunakan `sqlite3` di production code (blocking I/O di event loop).
- **Rekomendasi**: Tambahkan komentar di `data/*.py` bahwa file tersebut bukan bagian runtime. Pastikan tidak ada import `sqlite3` di `server/`, `engine/`, `cache/`, `core/`.

### 5b. `aiohttp.ClientSession` dibuat ganda — Duplicate session tanpa sharing
- **File**: `main.py` baris 57, `plugins/sponsorblock.py` baris 44, `plugins/lyrics.py` baris 37
- **Analisis**:
  - `main.py` membuat `http_session = aiohttp.ClientSession()` dan meneruskannya ke `SponsorBlockHandler(session=http_session)` dan `LyricsFetcher(session=http_session)` — ini benar.
  - Namun `SponsorBlockHandler.fetch_segments()` memiliki fallback `aiohttp.ClientSession()` jika `self._session is None`.
  - `LyricsFetcher._get_session()` juga punya fallback yang membuat session baru.
- **Risiko**: Jika ada code path yang memanggil plugin tanpa meneruskan session (misal, dalam tests atau instansiasi manual), session baru yang tidak dikelola akan bocor (`ResourceWarning: Unclosed client session`).
- **Dampak saat ini**: Di `main.py` normal flow, session sudah di-share dengan benar. Risiko aktif ada di test dan future refactor.
- **Rekomendasi**: Hapus fallback `aiohttp.ClientSession()` dari kedua plugin dan raise `RuntimeError` jika session tidak diinject. Ini enforce proper DI.

---

## 6. VERSION CONFLICT / PINNING RISK

### 6a. `yt-dlp==2026.3.17` — Pin terlalu ketat, cepat usang
- **File**: `requirements.txt` baris 1
- **Masalah**: yt-dlp merilis update hampir setiap minggu untuk mengikuti perubahan YouTube. Pin ke versi spesifik `2026.3.17` (sudah 3+ bulan lalu pada saat audit) berarti YouTube bisa memblokir format/signature yang digunakan versi ini.
- **Efek nyata**: Stream URL resolution gagal → track tidak bisa diputar. Sudah terbukti di session debugging sebelumnya (query format issues).
- **Rekomendasi**: Ganti ke `yt-dlp>=2026.3.17` atau bahkan `yt-dlp` (latest always). yt-dlp relatif stable dalam public API-nya untuk use case ini.

### 6b. `aiohttp==3.14.1` — Pin exact di major release baru
- **File**: `requirements.txt` baris 3
- **Konteks**: aiohttp 3.11+ memperkenalkan banyak perubahan internal. 3.14 adalah versi terbaru (rilis 2026).
- **Risiko**: Versi ini belum banyak battle-tested. Pin exact (`==`) berarti tidak dapat security patch minor tanpa edit manual.
- **Kode yang berisiko**: `web.AppRunner`, `web.TCPSite`, `aiohttp.ClientTimeout`, `aiohttp.WSMsgType` — semua API ini stabil di 3.x tapi perlu diverifikasi per changelog 3.12 → 3.14.
- **Rekomendasi**: Ganti ke `aiohttp>=3.11.0,<4.0` untuk fleksibilitas patch minor.

### 6c. `aiosqlite==0.22.1` — Pin exact, library stabil
- **File**: `requirements.txt` baris 2
- **Risiko**: Rendah. aiosqlite adalah library kecil dengan API yang sangat stabil.
- **Rekomendasi**: Bisa dilonggarkan ke `aiosqlite>=0.20.0` untuk kemudahan update.

---

## 7. BREAKING CHANGE RISK

### 7a. `syncedlyrics==1.0.1` — API bisa berubah sewaktu-waktu
- **File**: `requirements.txt` baris 4, `plugins/lyrics.py` baris 6, 107-111
- **Penggunaan**:
  ```python
  lrc = await asyncio.wait_for(
      loop.run_in_executor(None, syncedlyrics.search, search_query),
      timeout=5.0
  )
  ```
- **Masalah**: `syncedlyrics` adalah library komunitas kecil yang mengandalkan scraping dari Musixmatch/NetEase/Lrclib. API eksternal ini sering berubah, yang menyebabkan library ini perlu update cepat.
- **Risiko breaking**: Pin ke `1.0.1` tanpa `>=` bisa ketinggalan fix penting kalau salah satu provider berubah.
- **Mitigasi yang sudah ada**: Code menggunakan `try/except` dan timeout 5s — bagus. Tapi kegagalan silent mungkin tidak terdeteksi lama.
- **Rekomendasi**: Ganti ke `syncedlyrics>=1.0.1`. Tambahkan log metric saat syncedlyrics fail rate tinggi.

### 7b. `Google Fonts` via CDN — Privacy & Availability Risk
- **File**: `web/static/index.html`
  ```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" ...>
  ```
- **Masalah**:
  1. Di beberapa negara/jaringan korporat, `fonts.googleapis.com` diblokir → UI render tanpa font (fallback system font, bisa merusak layout).
  2. Di environment offline/lokal (Termux tanpa internet), font tidak load sama sekali.
  3. Privacy: setiap client yang membuka app melakukan request ke Google (IP logging).
- **Konteks Termux**: Koneksi bisa intermittent. Jika font CDN timeout, halaman tetap fungsional tapi tampilan degraded.
- **Rekomendasi**: Self-host Inter font di `/static/fonts/`. Sudah ada `noscript` fallback yang bagus — tinggal extend ke offline-first.

---

## 8. MISSING DARI `requirements.txt`

### `ytmusicapi` — Digunakan di data scripts, tidak di requirements
- **File**: `data/enrich_data.py` baris 6, `data/enrich_duration.py` baris 3
- **Import**:
  ```python
  from ytmusicapi import YTMusic
  ```
- **Status**: File `data/` adalah offline enrichment scripts (bukan runtime production). Tapi karena tidak ada di `requirements.txt` maupun `requirements-dev.txt`, siapapun yang mencoba menjalankan script ini akan mendapat `ModuleNotFoundError`.
- **Rekomendasi**: Tambahkan ke `requirements-dev.txt` atau buat `requirements-data.txt` terpisah dengan `ytmusicapi`.

---

## Prioritas Tindakan

| Prioritas | Item | Action |
|---|---|---|
| 🔴 CRITICAL | `yt-dlp==2026.3.17` pin ketat | Ganti ke `>=` |
| 🔴 CRITICAL | `/metrics` tanpa auth | Tambah `require_auth` |
| 🟠 HIGH | `@tabler/icons-webfont@latest` floating | Pin versi spesifik |
| 🟠 HIGH | `BatchSpanProcessor`/`ConsoleSpanExporter` dead import | Hapus atau implementasikan |
| 🟠 HIGH | `aiohttp.ClientSession` fallback bocor | Hapus fallback, enforce DI |
| 🟡 MEDIUM | Google Fonts CDN | Self-host Inter |
| 🟡 MEDIUM | `syncedlyrics` pin exact | Ganti ke `>=` |
| 🟡 MEDIUM | opentelemetry overhead tanpa exporter | Hapus atau tambah exporter |
| 🟢 LOW | `structlog==24.4.0` stale pin | Loosening versi |
| 🟢 LOW | `aiosqlite`, `aiohttp` pin exact | Loosening versi |
| 🟢 LOW | `ytmusicapi` missing dari dev deps | Tambah ke requirements-dev |

---

## `requirements.txt` yang Direkomendasikan

```txt
yt-dlp>=2026.3.17
aiosqlite>=0.20.0
aiohttp>=3.11.0,<4.0
syncedlyrics>=1.0.1
structlog>=24.4.0
prometheus_client>=0.20.0
opentelemetry-api>=1.25.0
opentelemetry-sdk>=1.25.0
```

```txt
# requirements-dev.txt
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-aiohttp>=1.0.5
ytmusicapi>=1.0.0
```

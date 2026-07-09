# API Regression Audit — LunaWave (server layer)

Scope: `server/`, `core/` (bagian yang men-support API: ws_actions, command_bus, commands, constants, rate_limit, value_objects), tidak termasuk database internal (`cache/`) dan frontend (`web/`).

---

## 🔴 CRITICAL #1 — `NameError` di route `GET /` (index) — handler salah / dependency hilang

**File:** `server/handlers/http.py`, fungsi `serve_index` (baris ~20)

```python
async def serve_index(request):
    resp = web.FileResponse(STATIC_DIR / "index.html")
    ...
```

**Penyebab:** `STATIC_DIR` dipakai tapi **tidak pernah di-import** di `http.py`. Konstanta ini sebenarnya didefinisikan di `server/routes.py` dan hanya di-import ke `server/app.py`:

```python
# server/routes.py
STATIC_DIR = Path(...) / "web" / "static"

# server/app.py
from server.routes import ..., STATIC_DIR   # hanya di app.py
```

`http.py` sendiri hanya meng-import `CACHE_DIR, STREAM_URL_TTL_SEC` dari `config`, tidak ada `STATIC_DIR` sama sekali.

**Dampak:** Setiap request ke `ROUTE_INDEX` (`"/"`) akan langsung crash dengan `NameError: name 'STATIC_DIR' is not defined` → response 500 pada halaman utama aplikasi. Ini efektif membuat seluruh web UI tidak bisa diakses.

**Kenapa lolos:** Tidak ada test yang meng-exercise `GET /` (dicek: tidak ada satupun test di `tests/` yang memanggil route index atau `serve_index`).

**Fix:** Tambahkan `from server.routes import STATIC_DIR` di `server/handlers/http.py`.

---

## 🔴 CRITICAL #2 — Auth middleware/gate untuk WS command rusak — atribut `WSAction` tidak ada

**File:** `server/handlers/websocket.py`, baris 139 (`handle_ws_message`)

```python
ADMIN_ONLY_ACTIONS = {WSAction.SET_OUTPUT, WSAction.SET_SPONSORBLOCK, WSAction.DELETE_DOWNLOAD, WSAction.STOP, WSAction.SETTINGS_UPDATE}
```

**Penyebab:** `WSAction.SETTINGS_UPDATE` **tidak pernah didefinisikan** di `core/ws_actions.py`. Enum yang ada hanya: `VOLUME_UP/DOWN/SET, SET_MODE, SET_OUTPUT, SET_SPONSORBLOCK, LYRICS_OFFSET`, dst — tidak ada `SETTINGS_UPDATE`. Verifikasi grep di seluruh repo: satu-satunya referensi ke `SETTINGS_UPDATE` adalah baris ini sendiri.

**Dampak:** Baris ini dieksekusi di **setiap** pesan WS bertipe `"cmd"` (bukan hanya untuk auth/logout), karena letaknya di luar blok `try/except` dalam `handle_ws_message`. Artinya **semua command WebSocket** (play, pause, next, prev, seek, queue, search, discover, dsb — bukan hanya action admin) akan melempar:

```
AttributeError: type object 'WSAction' has no attribute 'SETTINGS_UPDATE'
```

Exception ini terjadi sebelum masuk `try` block di `ws_handler`'s outer loop, sehingga akan tertangkap oleh `except Exception as e: logger.error("WebSocket error...")` di level `ws_handler`, yang **memutus seluruh koneksi WebSocket** setiap kali client mengirim command apapun. Ini adalah regresi paling parah — hampir seluruh realtime API (playback control) menjadi non-fungsional.

**Fix:** Hapus `WSAction.SETTINGS_UPDATE` dari set (atau tambahkan konstanta `SETTINGS_UPDATE = "settings_update"` di `core/ws_actions.py` dan buat handler-nya jika memang dimaksudkan sebagai action baru).

---

## 🟠 Catatan minor (dokumentasi tidak sinkron, bukan bug fungsional)

**File:** `CHANGELOG.md` (entry `S00-002`) vs `core/rate_limit.py` / `server/handlers/http.py`

Changelog `S00-002` menyebutkan implementasi rate-limit "in-memory dict `_stream_rate_limit`" dengan prune di 1000 item dan force-clear di 5000 item, langsung di `server/handlers/http.py`. Implementasi aktual sudah di-refactor menjadi class `RateLimiter` di `core/rate_limit.py` (`global_rate_limiter`) dengan mekanisme GC berbasis waktu (`gc_interval`), bukan berbasis jumlah item seperti yang dideskripsikan changelog. Secara fungsional tidak rusak, tapi dokumentasi (changelog) tidak lagi mencerminkan implementasi nyata — relevan untuk poin "OpenAPI/dokumentasi tidak sinkron".

---

## ✅ Area yang diperiksa dan TIDAK ditemukan regresi

- **Routing (`server/routes.py`, `server/app.py`)** — semua `ROUTE_*` konsisten dipakai di `add_get`/`add_static`, tidak ada route hilang/berubah selain bug #1 di atas.
- **WS handler registry vs `WSAction` enum** (`server/handlers/ws/*.py` vs `core/ws_actions.py`) — semua 20 action punya handler terdaftar 1:1 lewat `@register_ws_handler`, tidak ada yang orphan atau duplikat.
- **Command Bus / Commands** (`core/command_bus.py`, `core/commands.py`) — semua `*Command` yang dipanggil handler ada class-nya di `commands.py`; tidak ada dependency endpoint yang salah arah.
- **`server/handlers/auth.py`** — konstanta (`AUTH_TIMEOUT`, `MAX_LOGIN_ATTEMPTS`, `TOKEN_TTL`, `AUTH_MAX_LIMIT`) semua ada di `core/constants.py`; alur rate-limit + `_process_credentials` di luar lock konsisten dengan komentar S02-008.
- **`server/middleware.py`** (`security_headers_middleware`) — terpasang dengan benar di `create_app`, header sesuai dan tidak ada yang overridden/dobel.
- **`server/handlers/http.py`** — validasi `VideoId`, origin check, token check, SSRF guard (`_validate_stream_url` hanya izinkan `https` + domain googlevideo/youtube), status code (400/401/403/429/500/503/504) semua konsisten dengan payload error `error_payload()`.
- **`serve_metrics`** — auth bearer-token check via `secrets.compare_digest` dan localhost bypass masih benar.
- **Response schema** (`TrackInfo.to_dict/from_dict`, `AppState.to_dict`) — field yang dikirim client tidak dipakai untuk field sensitif (`stream_url`, `local_path` di-strip sesuai komentar S02-040), tidak ada perubahan schema yang tidak disengaja.
- **`server/handlers/event_listeners.py`, `server/services/broadcast_service.py`** — semua event subscriber terpasang, payload broadcast konsisten.

---

## Ringkasan Prioritas Perbaikan

| # | Severity | File | Masalah |
|---|----------|------|---------|
| 1 | Critical | `server/handlers/http.py` | `STATIC_DIR` tidak di-import → `GET /` crash 500 |
| 2 | Critical | `server/handlers/websocket.py:139` | `WSAction.SETTINGS_UPDATE` tidak ada → semua WS command crash & disconnect |
| 3 | Minor | `CHANGELOG.md` (S00-002) | Deskripsi tidak sinkron dengan implementasi rate-limit aktual di `core/rate_limit.py` |

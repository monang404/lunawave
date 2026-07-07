# LAPORAN AUDIT API — LUNAWAVE
**Tim Audit:** Senior Backend Engineer · Security Engineer · Principal Architect  
**Tanggal:** 2026-07-06  
**Scope:** Seluruh surface API — HTTP endpoints, WebSocket protocol, Auth, Rate Limit, Error Response, Caching, Validation, Versioning

---

## PETA API LUNAWAVE (As-Is)

### HTTP Endpoints
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| `GET` | `/` | ❌ Public | Serve index.html |
| `GET` | `/ws` | Partial | WebSocket upgrade |
| `GET` | `/api/stream/{video_id}` | ❌ Public | Proxy/redirect audio stream |
| `GET` | `/health` | ❌ Public | Health check |
| `GET` | `/metrics` | IP/Token | Prometheus metrics |
| `GET` | `/static/**` | ❌ Public | Static assets |

### WebSocket Actions (semua melalui `/ws`)
| Action | Auth Required | Keterangan |
|---|---|---|
| `auth` | ❌ | Login / validasi token |
| `search` | ✅ | Cari lagu di YouTube |
| `discover` | ✅ | Ambil data discover |
| `play_track` | ✅ | Putar lagu |
| `toggle_pause` | ✅ | Pause/resume |
| `next` / `prev` / `stop` | ✅ | Kontrol playback |
| `seek` | ✅ | Seek posisi |
| `queue_*` | ✅ | Operasi queue |
| `enqueue_*` | ✅ | Enqueue artist/genre |
| `radio_randomize` | ✅ | Acak radio |
| `volume_*` / `set_*` | ✅ | Pengaturan |
| `download` / `delete_download` | ✅ | Download cache |
| `toggle_favorite` | ✅ | Tandai favorit |
| `lyrics_offset` | ✅ | Offset lirik |

---

## TEMUAN AUDIT

---

### API-01 — CRITICAL: `TrackInfo.from_dict()` Menerima `stream_url` dari Client (Injection Risk)

**Kategori:** Validation · Authorization  
**Severity:** CRITICAL

**Masalah:**  
`TrackInfo.from_dict()` membaca field `stream_url` langsung dari data yang dikirim klien:

```python
# core/state.py — baris 75
return cls(
    video_id=video_id,
    title=str(data.get("title", "Unknown"))[:255],
    ...
    stream_url=data.get("stream_url"),   # ← CLIENT CONTROLLED
    local_path=data.get("local_path"),   # ← CLIENT CONTROLLED
)
```

Handler `PLAY_TRACK` dan `QUEUE_ADD` menggunakan `TrackInfo.from_dict(data)` langsung dari payload WS klien. Meskipun `CacheResolver.resolve()` mengutamakan nilai dari DB (bukan dari objek track yang masuk), field `stream_url` dan `local_path` dari klien bisa **memengaruhi log, state, dan edge-case alur resolver** yang belum ter-audit penuh. Lebih berbahaya: `local_path` dari klien yang diterima bisa ditulis ke DB via `upsert_track`.

**Lokasi File:**  
- `core/state.py` — `TrackInfo.from_dict()` baris 58–76  
- `server/handlers/ws/playback_handlers.py` — baris 10  
- `server/handlers/ws/queue_handlers.py` — baris 26  
- `server/handlers/ws/download_handlers.py` — baris 14, 19

**Solusi:**  
`from_dict()` wajib **menolak / mengabaikan** `stream_url` dan `local_path` dari input klien. Buat varian terpisah untuk deserialisasi input klien vs. internal DB.

```python
# core/state.py — tambahkan classmethod bersih untuk input klien
@classmethod
def from_client_dict(cls, data: dict) -> Optional['TrackInfo']:
    """Deserialisasi dari data klien — field sensitif DIBUANG."""
    if not data:
        return None
    try:
        video_id = VideoId(data.get("video_id", ""))
    except ValueError:
        return None
    duration = Duration(data.get("duration", 0))
    return cls(
        video_id=video_id,
        title=str(data.get("title", "Unknown"))[:255],
        artist=str(data.get("artist", "Unknown"))[:255],
        duration=duration,
        thumbnail=data.get("thumbnail"),  # sanitize URL jika perlu
        # stream_url TIDAK diterima dari klien
        # local_path TIDAK diterima dari klien
        stream_url=None,
        local_path=None,
    )

# playback_handlers.py — gunakan from_client_dict
@register_ws_handler(WSAction.PLAY_TRACK)
async def _handle_play_track(data, ws, state, ytdlp, manager, db, command_bus):
    track = TrackInfo.from_client_dict(data)  # ← bukan from_dict
    if track:
        await command_bus.execute(PlayTrackCommand(track=track))
```

---

### API-02 — CRITICAL: `/api/stream/{video_id}` Tidak Memerlukan Autentikasi

**Kategori:** Authentication · Authorization  
**Severity:** CRITICAL

**Masalah:**  
Endpoint `/api/stream/{video_id}` bersifat **public tanpa autentikasi**. Siapa saja yang mengetahui format `video_id` YouTube (11 karakter alphanumeric) dapat langsung mengakses stream audio — termasuk memicu yt-dlp untuk resolve URL baru, yang berbiaya komputasi tinggi dan berpotensi melanggar ToS YouTube. Proteksi yang ada hanya validasi `Referer`/`Origin`, yang mudah di-bypass dengan `curl -H "Referer: localhost:8765"`.

**Lokasi File:**  
- `server/handlers/http.py` — `serve_stream()` baris 50–190  
- `server/app.py` — baris 38

**Kode Bermasalah:**
```python
# Tidak ada session check sebelum memproses stream
async def serve_stream(request):
    video_id_str = request.match_info.get("video_id")
    # ← langsung proses tanpa verifikasi identity
    client_ip = request.remote
    # Referer check ini trivial di-bypass:
    if host not in referer and host not in origin and request.remote not in ("127.0.0.1", "::1"):
        return web.json_response(..., status=403)
```

**Solusi:**  
Tambahkan validasi session token via query parameter atau cookie untuk `/api/stream/`.

```python
async def serve_stream(request):
    # Validasi session token
    token = request.headers.get("X-Session-Token") or request.rel_url.query.get("token")
    db = request.app["db"]
    if not token or not await db.verify_session(token):
        return web.json_response(
            {"error": {"code": "UNAUTHORIZED", "message": "Token sesi tidak valid"}},
            status=401
        )
    # ... lanjut proses stream ...
```

Di sisi klien (browser audio):
```javascript
// audio.js — sertakan token saat request stream
const token = window.safeStorage.get("ytgui_session_token");
audio.src = `/api/stream/${videoId}?token=${encodeURIComponent(token)}`;
```

---

### API-03 — HIGH: Session Token Hanya 16 Bytes Hex (32 Karakter) — Terlalu Pendek

**Kategori:** Authentication  
**Severity:** HIGH

**Masalah:**  
Token sesi di-generate dengan `secrets.token_hex(16)` menghasilkan 32 karakter hex (128-bit entropy). Meskipun secara teoritis cukup, standar modern (OWASP) merekomendasikan minimal **256-bit (32 bytes) untuk session token**. Lebih kritis: token disimpan di `localStorage`/`sessionStorage` (via `safeStorage`) tanpa flags `HttpOnly` atau `Secure`, membuat token rentan terhadap XSS.

**Lokasi File:**  
- `server/handlers/auth.py` — baris 58  
- `web/static/js/ws.js` — baris 24 (`safeStorage.get`)

**Kode Bermasalah:**
```python
new_token = secrets.token_hex(16)   # ← 128-bit, rekomendasi OWASP = 256-bit
```

**Solusi:**
```python
# auth.py
new_token = secrets.token_hex(32)   # ← 256-bit entropy

# Atau lebih baik: gunakan URL-safe base64 token
new_token = secrets.token_urlsafe(32)  # 256-bit, URL-safe
```

Pertimbangkan juga untuk menyimpan token di `HttpOnly` cookie alih-alih localStorage:
```python
response_data = {"success": True, "token": new_token}
# Kirim via Set-Cookie jika client mendukung
```

---

### API-04 — HIGH: Tidak Ada API Versioning

**Kategori:** Versioning  
**Severity:** HIGH

**Masalah:**  
Tidak ada versioning di seluruh API — baik HTTP maupun WebSocket protocol. Endpoint HTTP hanya `/api/stream/{video_id}` tanpa prefix versi. WebSocket actions menggunakan string literal tanpa namespace versi. Saat breaking change terjadi (misalnya perubahan format `state` message atau tambah field wajib di `play_track`), **semua klien lama akan rusak sekaligus** tanpa fallback path.

**Lokasi File:**  
- `server/routes.py` — semua route definitions  
- `core/ws_actions.py` — semua action strings

**Kode Bermasalah:**
```python
ROUTE_STREAM = "/api/stream/{video_id}"   # ← no version prefix
# WSAction strings: "play_track", "auth", "discover" — no version
```

**Solusi:**

Untuk HTTP:
```python
# server/routes.py
ROUTE_STREAM = "/api/v1/stream/{video_id}"
ROUTE_HEALTH = "/api/v1/health"

# Dengan backward-compat redirect
app.router.add_get("/api/stream/{video_id}", redirect_to_v1)
```

Untuk WebSocket — sertakan `version` di handshake:
```python
# Saat connect, server kirim capabilities
await ws.send_str(json.dumps({
    "type": "server_info",
    "data": {
        "version": "1.2.0",
        "api_version": 1,
        "min_client_version": 1,
    }
}))
```

```javascript
// Klien sertakan versi saat kirim command
ws.send(JSON.stringify({
    type: "cmd",
    version: 1,
    action: action,
    data: data || {}
}));
```

---

### API-05 — HIGH: Error Response Format Tidak Konsisten

**Kategori:** Error Response  
**Severity:** HIGH

**Masalah:**  
Terdapat **3 format error berbeda** yang digunakan secara tidak konsisten:

**Format 1 — HTTP handlers** (via `error_payload()`):
```json
{ "error": { "code": "HTTP_ERROR", "message": "...", "details": {} } }
```

**Format 2 — WebSocket error**:
```json
{ "type": "error", "data": { "code": "AUTH_REQUIRED", "message": "..." } }
```

**Format 3 — WebSocket log** (untuk error bisnis):
```json
{ "type": "log", "data": "Error: stream tidak tersedia" }
```

Klien harus menangani 3 pola berbeda. Error bisnis (misalnya "artis tidak ditemukan") dikirim sebagai `log` message — tidak bisa dibedakan dari informational log oleh klien.

**Lokasi File:**  
- `server/handlers/ws/utils.py` — `error_payload()`  
- `server/handlers/websocket.py` — baris 123–130  
- `server/handlers/event_listeners.py` — baris 61 (`broadcast_log`)

**Solusi:**  
Standarisasi satu format error untuk semua konteks, dengan error codes yang terklasifikasi:

```python
# core/errors.py — error format tunggal
class ErrorCode:
    # Auth
    UNAUTHORIZED = "UNAUTHORIZED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    # Validation
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_VIDEO_ID = "INVALID_VIDEO_ID"
    # Resource
    TRACK_NOT_FOUND = "TRACK_NOT_FOUND"
    STREAM_UNAVAILABLE = "STREAM_UNAVAILABLE"
    # System
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

def make_error(code: str, message: str, details: dict = None) -> dict:
    return {
        "type": "error",
        "data": {
            "code": code,
            "message": message,
            "details": details or {},
            "timestamp": time.time(),
        }
    }

# HTTP response wrapper yang sama:
def http_error(code: str, message: str, http_status: int):
    return web.json_response(
        {"error": {"code": code, "message": message, "timestamp": time.time()}},
        status=http_status,
        content_type="application/json"
    )
```

---

### API-06 — HIGH: Rate Limiting WS dan HTTP Berbeda Implementasi, Tidak Sinkron

**Kategori:** Rate Limit  
**Severity:** HIGH

**Masalah:**  
Terdapat **dua sistem rate limit independen** yang tidak berbagi state:

1. **WS commands** — `check_rate_limit()` di `middleware.py`: 30 requests/60 detik, disimpan di `manager.command_history` (in-memory per instance)
2. **HTTP `/api/stream/`** — `_stream_rate_limit` dict di `http.py`: 20 requests/60 detik, modul-level variable terpisah

Keduanya berbasis **IP address saja** (mudah di-spoof di balik NAT/proxy). Tidak ada rate limit untuk endpoint `/health` dan `/metrics` (bisa DDoS-ed). Rate limit WS tidak berlaku untuk action `AUTH` (tapi ada limit login attempts terpisah). Rate limit tidak persistent — restart server = reset semua counter.

**Lokasi File:**  
- `server/middleware.py` — `check_rate_limit()`  
- `server/handlers/http.py` — `_stream_rate_limit`  
- `core/constants.py` — `MAX_RATE_LIMIT = 30`

**Kode Bermasalah:**
```python
# middleware.py — rate limit WS
MAX_RATE_LIMIT = 30  # 30 cmd / 60 detik

# http.py — rate limit HTTP terpisah, tidak terhubung
STREAM_RATE_LIMIT_MAX = 20  # 20 stream / 60 detik

# Tidak ada rate limit untuk:
app.router.add_get(ROUTE_HEALTH, health_check)    # ← terbuka
app.router.add_get(ROUTE_METRICS, serve_metrics)  # ← hanya IP check
```

**Solusi:**  
Konsolidasi ke satu rate limiter yang dapat dikonfigurasi per-endpoint:

```python
# core/rate_limiter.py
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RateLimitRule:
    max_requests: int
    window_seconds: int
    burst: Optional[int] = None  # bolt-on burst allowance

class RateLimiter:
    def __init__(self):
        self._buckets: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))

    def check(self, scope: str, key: str, rule: RateLimitRule) -> tuple[bool, dict]:
        now = time.monotonic()
        history = [t for t in self._buckets[scope][key] if now - t < rule.window_seconds]
        
        if len(history) >= rule.max_requests:
            retry_after = rule.window_seconds - (now - history[0])
            return False, {"retry_after": round(retry_after)}
        
        history.append(now)
        self._buckets[scope][key] = history
        return True, {}

# Konfigurasi per-scope
RULES = {
    "ws_cmd": RateLimitRule(max_requests=30, window_seconds=60),
    "ws_auth": RateLimitRule(max_requests=5, window_seconds=300),
    "http_stream": RateLimitRule(max_requests=20, window_seconds=60),
    "http_health": RateLimitRule(max_requests=60, window_seconds=60),
}
```

---

### API-07 — HIGH: Tidak Ada HTTP Request Timeout untuk Proxy Stream

**Kategori:** Timeout  
**Severity:** HIGH

**Masalah:**  
`serve_stream()` membuka koneksi upstream ke YouTube via `http_session.get(stream_url)` **tanpa timeout eksplisit**. Jika YouTube lambat merespons atau connection hang, request handler akan tergantung selamanya, menghabiskan koneksi dan memory. Dengan banyak klien simultan yang streaming, ini bisa membuat server tidak responsif (resource exhaustion).

**Lokasi File:**  
- `server/handlers/http.py` — baris 151–189

**Kode Bermasalah:**
```python
async with http_session.get(stream_url, headers=headers) as upstream:
    # ← TIDAK ADA TIMEOUT — bisa hang selamanya
    response = web.StreamResponse(status=upstream.status, ...)
    await response.prepare(request)
    async for chunk in upstream.content.iter_chunked(16384):
        await response.write(chunk)
```

**Solusi:**
```python
import aiohttp

STREAM_CONNECT_TIMEOUT = 10   # detik untuk connect
STREAM_READ_TIMEOUT = 30      # detik untuk read awal

timeout = aiohttp.ClientTimeout(
    connect=STREAM_CONNECT_TIMEOUT,
    sock_read=STREAM_READ_TIMEOUT,
    total=None  # total = None karena streaming bisa lama
)

try:
    async with http_session.get(stream_url, headers=headers, timeout=timeout) as upstream:
        # ... streaming logic ...
except asyncio.TimeoutError:
    return web.json_response(
        {"error": {"code": "GATEWAY_TIMEOUT", "message": "Upstream timeout"}},
        status=504
    )
```

---

### API-08 — HIGH: WebSocket Auth Bypass via Role `client` — Tidak Konsisten

**Kategori:** Authorization  
**Severity:** HIGH

**Masalah:**  
Di frontend, terdapat konsep `userRole` dengan nilai `"portal"`, `"admin"`, dan `"client"`. Role `"client"` diberi akses ke DISCOVER dan koneksi WS. Namun di backend, `require_auth()` hanya memeriksa apakah WS ada di `authenticated_connections` — yang hanya diisi saat autentikasi admin berhasil. Artinya role `"client"` di frontend adalah **client-side fiction** — backend tidak mengenal role ini sama sekali. Semua non-admin yang terhubung akan selalu mendapat `AUTH_REQUIRED` error untuk setiap command.

**Implikasi:** Jika ada bug di frontend yang tidak memfilter perintah berdasarkan role, atau jika klien WS custom digunakan, semua command akan gagal dengan error yang membingungkan, bukan dengan pesan otorisasi yang jelas.

**Lokasi File:**  
- `server/handlers/auth.py` — `require_auth()`  
- `server/handlers/websocket.py` — baris 121

**Kode Bermasalah:**
```python
def require_auth(manager, ws) -> bool:
    return ws in manager.authenticated_connections
    # ← hanya admin yang bisa masuk sini; tidak ada role "client"
```

**Solusi:**  
Dokumentasikan dan enforce model akses yang jelas. Jika memang hanya admin yang boleh mengirim commands, hapus konsep role "client" dari backend atau implementasikan dengan benar:

```python
# Opsi A: Formalisasi di backend
class ConnectionRole(str, Enum):
    PORTAL = "portal"    # tidak authenticated
    CLIENT = "client"    # bisa lihat state, tidak bisa kontrol
    ADMIN = "admin"      # full control

class ConnectionManager:
    def __init__(self):
        self.active_connections: set = set()
        self.connection_roles: dict = {}  # ws → ConnectionRole

    def get_role(self, ws) -> ConnectionRole:
        return self.connection_roles.get(ws, ConnectionRole.PORTAL)

# Di handle_ws_message — check role per action
def require_role(manager, ws, min_role: ConnectionRole) -> bool:
    role = manager.get_role(ws)
    role_order = [ConnectionRole.PORTAL, ConnectionRole.CLIENT, ConnectionRole.ADMIN]
    return role_order.index(role) >= role_order.index(min_role)
```

---

### API-09 — HIGH: Tidak Ada Pagination untuk Search Results

**Kategori:** Pagination  
**Severity:** HIGH

**Masalah:**  
Search handler menerima `max_results` dari klien dengan validasi `min(max(1, int(...)), 50)` — maksimal 50 hasil. Tidak ada cursor-based pagination, tidak ada `total_count`, tidak ada `has_more` flag. Untuk discover data (recent, favorites, cached) — juga tidak ada pagination, hanya hard limit. User tidak bisa memuat lebih banyak data tanpa implementasi pagination.

**Lokasi File:**  
- `server/handlers/ws/discover_handlers.py` — `_handle_search()` baris 39–52  
- `core/constants.py` — `DISCOVER_RECENT_LIMIT = 15`

**Kode Bermasalah:**
```python
@register_ws_handler(WSAction.SEARCH)
async def _handle_search(data, ws, state, ytdlp, manager, db, command_bus):
    query = data.get("query", "").strip()
    max_results = min(max(1, int(data.get("max_results", 10))), 50)
    # ← tidak ada pagination, tidak ada cursor, tidak ada total
    results = await ytdlp.search(query, max_results=max_results)
    await ws.send_str(json.dumps({
        "type": "search_results",
        "data": [t.to_dict() for t in results],   # ← tidak ada metadata pagination
    }))
```

**Solusi:**  
Tambahkan metadata pagination di response:

```python
@register_ws_handler(WSAction.SEARCH)
async def _handle_search(data, ws, state, ytdlp, manager, db, command_bus):
    query = data.get("query", "").strip()
    page = max(1, int(data.get("page", 1)))
    per_page = min(max(1, int(data.get("per_page", 10))), 20)
    
    if not query:
        return
    
    results = await ytdlp.search(query, max_results=per_page)
    
    await ws.send_str(json.dumps({
        "type": "search_results",
        "data": [t.to_dict() for t in results],
        "meta": {
            "page": page,
            "per_page": per_page,
            "has_more": len(results) == per_page,
            "query": query,
        }
    }, ensure_ascii=False))
```

Untuk discover — tambahkan `offset` support:
```json
// Request
{ "action": "discover", "data": { "recent_offset": 0, "recent_limit": 15 } }

// Response
{ "recent": [...], "recent_total": 47, "recent_has_more": true }
```

---

### API-10 — MEDIUM: `/health` Tidak Mengembalikan Informasi yang Cukup untuk Load Balancer

**Kategori:** REST Standard · HTTP Status  
**Severity:** MEDIUM

**Masalah:**  
Health check endpoint mengembalikan `{"status": "ok", "db": "connected", "mpv": "not_started"}` dengan status 200 bahkan ketika MPV tidak terkoneksi (`mpv_status = "not_started"`). Load balancer tidak bisa membedakan server yang benar-benar ready untuk melayani playback vs. server yang DB-nya up tapi MPV-nya mati. Juga tidak ada check untuk koneksi internet (diperlukan untuk YouTube streaming).

**Lokasi File:**  
- `server/handlers/http.py` — `health_check()` baris 27–44

**Kode Bermasalah:**
```python
status_val = "ok" if db_status == "connected" else "degraded"
status_code = 200 if status_val == "ok" else 503
# ← MPV not_started = 200 OK — load balancer salah anggap ready
return web.json_response({
    "status": status_val,
    "db": db_status,
    "mpv": mpv_status   # ← "not_started" tapi status 200
}, status=status_code)
```

**Solusi:**  
Implementasikan health check tiered — `liveness` vs `readiness`:

```python
async def health_check(request):
    db = request.app["db"]
    pc = request.app.get("playback_controller")
    state = request.app.get("state")

    db_ok = False
    try:
        if db.conn:
            async with db.conn.execute("SELECT 1") as cur:
                db_ok = bool(await cur.fetchone())
    except Exception:
        pass

    mpv_ok = getattr(getattr(pc, "mpv", None), "is_connected", False)
    online = getattr(state, "is_online", False) if state else False

    checks = {
        "database": "ok" if db_ok else "error",
        "mpv": "ok" if mpv_ok else "degraded",
        "internet": "ok" if online else "degraded",
    }

    # Liveness: minimal db harus ok
    is_live = db_ok
    # Readiness: semua komponen harus ok
    is_ready = db_ok and mpv_ok

    status_val = "ready" if is_ready else ("live" if is_live else "error")
    status_code = 200 if is_live else 503

    return web.json_response({
        "status": status_val,
        "checks": checks,
        "version": "1.0.0",
        "timestamp": time.time(),
    }, status=status_code)
```

---

### API-11 — MEDIUM: Caching Response Header Tidak Konsisten di Stream Endpoint

**Kategori:** Caching  
**Severity:** MEDIUM

**Masalah:**  
`serve_stream()` mengembalikan `Cache-Control: private, max-age=3600` untuk file ter-cache lokal. Namun untuk stream yang di-proxy dari YouTube, header `Cache-Control` yang sama di-set tanpa mempertimbangkan bahwa URL YouTube sudah expired setiap 6 jam (`STREAM_URL_TTL_SEC = 21600`). Browser bisa men-cache URL yang sudah expired, menyebabkan playback gagal setelah 1 jam tapi sebelum URL YouTube expire. Tidak ada `Vary` header untuk stream endpoint. Juga tidak ada `Last-Modified` header untuk file cache lokal.

**Lokasi File:**  
- `server/handlers/http.py` — baris 83–90 dan 158–164

**Kode Bermasalah:**
```python
# Untuk file lokal — OK
return web.FileResponse(
    cache_file,
    headers={
        "Cache-Control": "private, max-age=3600",  # ← terlalu generous untuk stream
        "ETag": etag
    }
)

# Untuk proxy stream — problematik
response = web.StreamResponse(
    headers={
        "Cache-Control": "private, max-age=3600",  # ← proxy stream tidak boleh di-cache browser
    }
)
```

**Solusi:**
```python
# Untuk file cache lokal — boleh cache lebih lama
"Cache-Control": "private, max-age=86400, immutable",  # file tidak berubah
"Last-Modified": formatdate(stat.st_mtime, usegmt=True),

# Untuk proxy stream dari YouTube — JANGAN di-cache browser
"Cache-Control": "no-store, no-cache",  # stream bisa expire
"X-Accel-Buffering": "no",  # untuk NGINX proxy

# Untuk redirect ke YouTube URL
# Redirect seharusnya 307 (Temporary), bukan 302
return web.HTTPTemporaryRedirect(stream_url)  # ← 307 bukan 302/HTTPFound
```

---

### API-12 — MEDIUM: HTTP 302 Digunakan untuk Redirect Stream (Seharusnya 307)

**Kategori:** REST Standard · HTTP Status  
**Severity:** MEDIUM

**Masalah:**  
Ketika `http_session` tidak tersedia, server melakukan redirect ke YouTube stream URL menggunakan `web.HTTPFound(stream_url)` yang mengembalikan **302 Found**. Menurut RFC 7231, 302 memperbolehkan browser mengubah POST menjadi GET, dan tidak semantically correct untuk resource yang berpindah sementara. Untuk audio streaming via `<audio>` tag, seharusnya digunakan **307 Temporary Redirect** yang mempertahankan method dan lebih jelas semantiknya.

**Lokasi File:**  
- `server/handlers/http.py` — baris 118

**Kode Bermasalah:**
```python
return web.HTTPFound(stream_url)   # ← 302, seharusnya 307
```

**Solusi:**
```python
return web.HTTPTemporaryRedirect(stream_url)   # ← 307 Temporary Redirect
# Atau eksplisit:
return web.Response(
    status=307,
    headers={"Location": stream_url, "Cache-Control": "no-store"}
)
```

---

### API-13 — MEDIUM: Tidak Ada Input Validation untuk Artist Name dan Genre Name

**Kategori:** Validation  
**Severity:** MEDIUM

**Masalah:**  
Handler `ENQUEUE_ARTIST_SONGS` dan `ENQUEUE_GENRE_SONGS` menerima string dari klien dan langsung digunakan sebagai parameter query SQL (meskipun via parameterized query — aman dari SQL injection). Namun tidak ada validasi panjang, karakter, atau keberadaan data. String panjang 10.000 karakter bisa dikirim, membuang siklus CPU untuk lookup yang pasti gagal. Tidak ada response error jika artist tidak ditemukan.

**Lokasi File:**  
- `server/handlers/ws/queue_handlers.py` — baris 33–43

**Kode Bermasalah:**
```python
@register_ws_handler(WSAction.ENQUEUE_ARTIST_SONGS)
async def _handle_enqueue_artist_songs(data, ws, state, ytdlp, manager, db, command_bus):
    artist_name = data.get("artist")   # ← tidak ada validasi panjang/format
    if artist_name:
        songs = await db.get_artist_songs_strict(artist=artist_name, limit=10)
        if songs:   # ← silent fail jika artist tidak ada
            # ...
```

**Solusi:**
```python
MAX_NAME_LENGTH = 200

@register_ws_handler(WSAction.ENQUEUE_ARTIST_SONGS)
async def _handle_enqueue_artist_songs(data, ws, state, ytdlp, manager, db, command_bus):
    artist_name = data.get("artist", "").strip()
    
    # Validasi input
    if not artist_name:
        await ws.send_str(json.dumps(make_error("INVALID_INPUT", "Nama artis tidak boleh kosong")))
        return
    if len(artist_name) > MAX_NAME_LENGTH:
        await ws.send_str(json.dumps(make_error("INVALID_INPUT", f"Nama artis terlalu panjang (max {MAX_NAME_LENGTH})")))
        return
    
    songs = await db.get_artist_songs_strict(artist=artist_name, limit=10)
    
    if not songs:
        await ws.send_str(json.dumps(make_error("TRACK_NOT_FOUND", f"Tidak ada lagu dari artis: {artist_name}")))
        return
    
    await db.increment_artist_click(artist_name)
    first_track, rest_tracks = songs[0], songs[1:]
    await command_bus.execute(QueueReplaceCommand(tracks=rest_tracks))
    await command_bus.execute(PlayTrackCommand(track=first_track))
```

---

### API-14 — MEDIUM: WebSocket Actions Menggunakan String Literal, Bukan Enum (Inkonsistensi Naming)

**Kategori:** Naming  
**Severity:** MEDIUM

**Masalah:**  
`WSAction` didefinisikan sebagai class biasa dengan class attributes string. Beberapa handler **tidak menggunakan konstanta** `WSAction` tapi langsung menggunakan string literal:

```python
# settings_handlers.py — MENGABAIKAN WSAction constants
@register_ws_handler("volume_set")     # ← hardcoded string, bukan WSAction.VOLUME_SET
@register_ws_handler("set_mode")       # ← hardcoded string, bukan WSAction.SET_MODE
@register_ws_handler("set_output")     # ← hardcoded string, bukan WSAction.SET_OUTPUT
```

Padahal `WSAction` sudah mendefinisikan:
```python
VOLUME_SET = "volume_set"
SET_MODE = "set_mode"
SET_OUTPUT = "set_output"
```

Inkonsistensi ini rawan typo dan membuat refactoring berbahaya.

**Lokasi File:**  
- `server/handlers/ws/settings_handlers.py` — baris 21, 26, 31

**Solusi:**
```python
# settings_handlers.py — gunakan WSAction constants secara konsisten
from core.ws_actions import WSAction

@register_ws_handler(WSAction.VOLUME_SET)    # ← bukan "volume_set"
async def _handle_volume_set(data, ws, state, ytdlp, manager, db, command_bus):
    ...

@register_ws_handler(WSAction.SET_MODE)      # ← bukan "set_mode"
async def _handle_set_mode(data, ws, state, ytdlp, manager, db, command_bus):
    ...

@register_ws_handler(WSAction.SET_OUTPUT)    # ← bukan "set_output"
async def _handle_set_output(data, ws, state, ytdlp, manager, db, command_bus):
    ...
```

Ubah juga `WSAction` menjadi proper Enum:
```python
# core/ws_actions.py
from enum import StrEnum

class WSAction(StrEnum):
    AUTH = "auth"
    PLAY_TRACK = "play_track"
    VOLUME_SET = "volume_set"
    # ... semua actions
```

---

### API-15 — MEDIUM: Retry Logic Tidak Idempotent untuk `PLAY_TRACK`

**Kategori:** Idempotency · Retry  
**Severity:** MEDIUM

**Masalah:**  
`PLAY_TRACK` command tidak idempotent — jika klien mengirim perintah yang sama dua kali (karena network retry atau bug), lagu akan di-play dua kali (interrupt lagu yang sedang berjalan). Tidak ada deduplication berdasarkan `video_id` atau timestamp. Saat koneksi WS putus dan reconnect, klien tidak memiliki cara untuk mengetahui apakah command terakhir berhasil dieksekusi, sehingga rentan double-execution.

**Lokasi File:**  
- `server/handlers/ws/playback_handlers.py` — baris 8–11  
- `web/static/js/ws.js` — `wsConnect()` reconnect logic

**Solusi:**  
Tambahkan `idempotency_key` opsional di command layer, atau gunakan state check:

```python
# playback_handlers.py
@register_ws_handler(WSAction.PLAY_TRACK)
async def _handle_play_track(data, ws, state, ytdlp, manager, db, command_bus):
    track = TrackInfo.from_client_dict(data)
    if not track:
        return
    
    # Idempotency: jika track yang sama sudah playing, abaikan
    if (state.current_track 
        and state.current_track.video_id == track.video_id
        and state.status.name in ("PLAYING", "LOADING")):
        # Kirim state sekarang — klien mungkin hanya butuh sync
        await ws.send_str(json.dumps({"type": "state", "data": state.to_dict()}))
        return
    
    # Opsi: client kirim idempotency_key
    idem_key = data.get("_idem_key")
    if idem_key and hasattr(state, "_recent_idem_keys"):
        if idem_key in state._recent_idem_keys:
            return  # duplikat, abaikan
        state._recent_idem_keys.add(idem_key)
    
    await command_bus.execute(PlayTrackCommand(track=track))
```

---

### API-16 — MEDIUM: `/metrics` Menggunakan Custom Header `X-Metrics-Token` (Non-Standard)

**Kategori:** Authentication · REST Standard  
**Severity:** MEDIUM

**Masalah:**  
Endpoint `/metrics` menggunakan header custom `X-Metrics-Token` untuk autentikasi, alih-alih standard `Authorization: Bearer <token>`. Hal ini tidak kompatibel dengan sebagian besar monitoring stack (Prometheus, Grafana) yang menggunakan `Authorization` header atau basic auth secara default.

**Lokasi File:**  
- `server/handlers/http.py` — `serve_metrics()` baris 198–210

**Kode Bermasalah:**
```python
has_valid_token = (
    metrics_token
    and request.headers.get("X-Metrics-Token") is not None   # ← non-standard
    and secrets.compare_digest(request.headers.get("X-Metrics-Token"), metrics_token)
)
```

**Solusi:**
```python
# Dukung standard Bearer token
auth_header = request.headers.get("Authorization", "")
bearer_token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""

# Fallback ke X-Metrics-Token untuk backward compat
legacy_token = request.headers.get("X-Metrics-Token", "")
provided_token = bearer_token or legacy_token

has_valid_token = (
    metrics_token
    and provided_token
    and secrets.compare_digest(provided_token, metrics_token)
)
```

Dokumentasikan di `.env.example`:
```bash
# Akses metrics: curl -H "Authorization: Bearer $LUNAWAVE_METRICS_TOKEN" http://localhost:8765/metrics
LUNAWAVE_METRICS_TOKEN=your_secret_token
```

---

### API-17 — MEDIUM: `DELETE_DOWNLOAD` Tidak Mengembalikan Status Sukses/Gagal Terstruktur

**Kategori:** Error Response · REST Standard  
**Severity:** MEDIUM

**Masalah:**  
Handler `DELETE_DOWNLOAD` mengirim hasil operasi sebagai `log` message (string), bukan pesan terstruktur. Klien tidak dapat membedakan antara "berhasil dihapus", "file tidak ditemukan", atau "gagal hapus" secara programatik. Juga tidak ada response jika `track` tidak valid atau tidak ditemukan di DB.

**Lokasi File:**  
- `server/handlers/ws/download_handlers.py` — baris 19–49

**Kode Bermasalah:**
```python
await manager.broadcast({
    "type": "log",         # ← log bukan event terstruktur
    "data": f"Unduhan dihapus: {db_track.title}"
})
# Tidak ada response untuk: track not found, file deletion failure
```

**Solusi:**
```python
# Tambahkan event type baru: download_deleted
await manager.broadcast({
    "type": "download_deleted",
    "data": {
        "video_id": db_track.video_id,
        "title": db_track.title,
        "success": True,
    }
})

# Error case:
if not db_track:
    await ws.send_str(json.dumps(make_error(
        "TRACK_NOT_FOUND", 
        f"Track dengan video_id {track.video_id} tidak ditemukan"
    )))
    return
```

---

### API-18 — LOW: `.env.example` Menggunakan Nama Variable yang Berbeda dari `config.py`

**Kategori:** Naming · REST Standard  
**Severity:** LOW

**Masalah:**  
`.env.example` mendefinisikan `YTGUI_HOST`, `YTGUI_PORT`, `YTGUI_ADMIN_USER`, namun `config.py` membaca `LUNAWAVE_HOST`, `LUNAWAVE_PORT`, `LUNAWAVE_ADMIN_USER`. Nama variable di `.env.example` tidak cocok dengan yang digunakan kode. Developer yang mengikuti `.env.example` akan mendapati konfigurasi mereka tidak ter-load.

**Lokasi File:**  
- `.env.example` — semua baris  
- `config.py` — baris 24–29

**Kode Bermasalah:**
```bash
# .env.example:
YTGUI_HOST=0.0.0.0        # ← tidak dipakai
YTGUI_PORT=8765           # ← tidak dipakai
YTGUI_ADMIN_USER=admin    # ← tidak dipakai

# config.py yang sebenarnya membaca:
WEB_HOST = os.environ.get("LUNAWAVE_HOST", "0.0.0.0")
WEB_PORT = int(os.environ.get("LUNAWAVE_PORT", 8765))
ADMIN_USERNAME = os.environ.get("LUNAWAVE_ADMIN_USER", "admin")
```

**Solusi:**
```bash
# .env.example — sesuaikan dengan config.py
LUNAWAVE_HOST=0.0.0.0
LUNAWAVE_PORT=8765
LUNAWAVE_ADMIN_USER=admin
# LUNAWAVE_ADMIN_PASS=your_secret_password

YT_PLAYER_BASE=.
YT_PLAYER_SOCKET=/tmp/mpv-lunawave.sock
YT_PLAYER_VOLUME=80

TRUSTED_PROXY=false
# LUNAWAVE_METRICS_TOKEN=your_metrics_secret
```

---

## REKAPITULASI TEMUAN

| ID | API / Endpoint | Masalah | Severity |
|---|---|---|---|
| API-01 | WS `play_track` / `queue_add` | `TrackInfo.from_dict()` menerima `stream_url` dan `local_path` dari klien | CRITICAL |
| API-02 | `GET /api/stream/{video_id}` | Tidak ada autentikasi — siapapun bisa trigger stream | CRITICAL |
| API-03 | WS `auth` | Session token 128-bit, disimpan di localStorage | HIGH |
| API-04 | Semua endpoints | Tidak ada API versioning (HTTP maupun WS protocol) | HIGH |
| API-05 | Semua endpoints | 3 format error berbeda, tidak konsisten | HIGH |
| API-06 | WS + HTTP | Dua sistem rate limit tidak sinkron, `/health` tidak ter-rate-limit | HIGH |
| API-07 | `GET /api/stream/` | Tidak ada timeout untuk proxy stream ke YouTube | HIGH |
| API-08 | WS semua actions | Role "client" tidak diimplementasikan di backend — auth model ambigu | HIGH |
| API-09 | WS `search` / `discover` | Tidak ada pagination, tidak ada metadata | HIGH |
| API-10 | `GET /health` | Health check tidak membedakan liveness vs readiness | MEDIUM |
| API-11 | `GET /api/stream/` | Cache-Control header tidak tepat untuk proxy stream | MEDIUM |
| API-12 | `GET /api/stream/` | `302 Found` digunakan, seharusnya `307 Temporary Redirect` | MEDIUM |
| API-13 | WS `enqueue_artist` / `enqueue_genre` | Tidak ada validasi panjang, silent fail jika not found | MEDIUM |
| API-14 | WS settings handlers | String literal alih-alih `WSAction` constants, inkonsistensi naming | MEDIUM |
| API-15 | WS `play_track` | Tidak idempotent — double-send = double play | MEDIUM |
| API-16 | `GET /metrics` | Header `X-Metrics-Token` non-standard, tidak kompatibel Prometheus default | MEDIUM |
| API-17 | WS `delete_download` | Response via `log` message, tidak terstruktur | MEDIUM |
| API-18 | `.env.example` | Nama variable tidak cocok dengan yang dibaca `config.py` | LOW |

---

## PRIORITAS PERBAIKAN

| Prioritas | ID | Effort |
|---|---|---|
| 🔴 SEGERA | API-01 — Reject stream_url/local_path dari klien | 30 menit |
| 🔴 SEGERA | API-02 — Auth untuk /api/stream/ | 1 jam |
| 🟠 MINGGU INI | API-03 — Token entropy + storage | 1 jam |
| 🟠 MINGGU INI | API-04 — API versioning | 2 jam |
| 🟠 MINGGU INI | API-05 — Standardisasi error format | 3 jam |
| 🟠 MINGGU INI | API-06 — Konsolidasi rate limiter | 3 jam |
| 🟠 MINGGU INI | API-07 — Timeout upstream stream | 30 menit |
| 🟠 MINGGU INI | API-08 — Formalisasi role model | 2 jam |
| 🟡 SPRINT INI | API-09 — Pagination | 4 jam |
| 🟡 SPRINT INI | API-10 — Health check tiered | 1 jam |
| 🟡 SPRINT INI | API-11 — Cache-Control fix | 30 menit |
| 🟡 SPRINT INI | API-12 — 307 redirect | 15 menit |
| 🟡 SPRINT INI | API-13 — Input validation | 2 jam |
| 🟡 SPRINT INI | API-14 — WSAction enum + naming | 1 jam |
| 🟡 SPRINT INI | API-15 — Idempotency | 2 jam |
| 🟢 BACKLOG | API-16 — Bearer token metrics | 30 menit |
| 🟢 BACKLOG | API-17 — Structured download events | 1 jam |
| 🟢 BACKLOG | API-18 — Fix .env.example | 15 menit |

---

*Laporan ini mencakup temuan dari: Senior Backend Engineer, Security Engineer, Principal Architect.*

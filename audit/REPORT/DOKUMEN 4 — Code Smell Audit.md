# 🔍 Code Smell Audit Report — LunaWave
**Tim Audit:** Senior Software Architect · Principal Backend Engineer · Senior Frontend Engineer · UI/UX Expert · Product Engineer  
**Tanggal:** 2026-07-06  
**Scope:** Seluruh source code (Python + JavaScript + CSS), dikecualikan `archive/` dan `node_modules/`

---

## Ringkasan Eksekutif

| Kategori | Jumlah Temuan |
|---|---|
| God Class / Large Class | 4 |
| God Function / Long Method | 5 |
| Long Parameter List | 12+ |
| Duplicate Code | 6 |
| Feature Envy | 3 |
| Primitive Obsession | 4 |
| Magic Number | 9 |
| Magic String | 5 |
| Dead Code | 4 |
| Commented Code | 3 |
| Unused Variable / Import | 5 |
| **TOTAL** | **60+** |

---

## CS-001 — God Class: `ServerManagerWindow`

**Lokasi:** `start.py`, kelas `ServerManagerWindow` (baris 1–866, **866 baris total**)  
**Severity:** 🔴 HIGH  

**Alasan:**  
`ServerManagerWindow` adalah kelas Tkinter yang menangani **UI building**, **event handling**, **port detection**, **process management**, **password management**, **dependency checking**, dan **dialog management** sekaligus dalam satu file 866 baris. Ini adalah God Class murni — satu kelas yang tahu dan melakukan segalanya.

**Potongan Kode Bermasalah:**
```python
# start.py — semua ini dalam satu file:
class DependencyChecker: ...         # cek dep
class ServerProcessManager: ...      # kelola proses OS
class ServerReadyDialog: ...         # dialog Tk
class PasswordResetDialog: ...       # dialog Tk
class ServerManagerController: ...   # logic bisnis
class ServerManagerWindow(tk.Tk):    # UI + koordinasi semua
    def _build_window(self): ...
    def _build_ui(self): ...         # 200+ baris UI building
    def update_running_state(self): ...
    def update_conflict_state(self): ...
    def update_stopped_state(self): ...
    def write_log(self): ...
    def clear_log(self): ...
    def show_server_ready_popup(self): ...
    def show_new_password_dialog(self): ...
    # ... 55 total method/fungsi dalam satu file
```

**Cara Refactor:**  
Pecah ke file terpisah dengan tanggung jawab tunggal:

```
start/
├── __main__.py          # entry point only
├── gui/
│   ├── window.py        # ServerManagerWindow (UI only)
│   ├── dialogs.py       # ServerReadyDialog, PasswordResetDialog
│   └── theme.py         # BG, ACCENT, TEXT_1, dll color constants
├── core/
│   ├── process_manager.py   # ServerProcessManager
│   ├── dependency_checker.py
│   └── controller.py        # ServerManagerController
```

---

## CS-002 — God Class: `AppState` (Primitive Obsession + Large Class)

**Lokasi:** `core/state.py`, kelas `AppState`  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
`AppState` menyimpan **player state**, **lyrics state**, **queue state**, **UI state**, **download state**, dan **network state** dalam satu dataclass flat. Ini campuran domain berbeda tanpa pemisahan. Akibatnya, setiap modul yang ingin mengakses satu aspek harus import seluruh `AppState`.

**Potongan Kode Bermasalah:**
```python
@dataclass
class AppState:
    # Player state
    status: PlayerStatus
    playback_mode: PlaybackMode
    audio_output: AudioOutput
    current_track: Optional[TrackInfo]
    position: float
    duration: Duration
    volume: Volume
    sponsorblock_active: bool

    # Queue state
    queue: deque
    radio_queue: deque
    history: deque

    # Lyrics state — kelompok berbeda!
    lyrics_lines: list[str]
    lyrics_timestamps: list[float]
    lyrics_index: int
    lyrics_offset: float
    lyrics_loading: bool

    # UI state — bukan domain player!
    active_tab: str
    error_msg: Optional[str]

    # Network state
    is_online: bool

    # Download state — kelompok lain lagi!
    download_progress: Optional[float]
```

**Cara Refactor:**
```python
@dataclass
class PlaybackState:
    status: PlayerStatus = PlayerStatus.IDLE
    playback_mode: PlaybackMode = PlaybackMode.QUEUE
    audio_output: AudioOutput = AudioOutput.BROWSER
    current_track: Optional[TrackInfo] = None
    position: float = 0.0
    duration: Duration = field(default_factory=lambda: Duration(0))
    volume: Volume = field(default_factory=lambda: Volume(DEFAULT_VOLUME))
    sponsorblock_active: bool = True

@dataclass
class LyricsState:
    lines: list[str] = field(default_factory=list)
    timestamps: list[float] = field(default_factory=list)
    index: int = 0
    offset: float = 0.0
    loading: bool = False

@dataclass
class QueueState:
    queue: deque = field(default_factory=deque)
    radio_queue: deque = field(default_factory=deque)
    history: deque = field(default_factory=lambda: deque(maxlen=50))

@dataclass
class AppState:
    playback: PlaybackState = field(default_factory=PlaybackState)
    lyrics: LyricsState = field(default_factory=LyricsState)
    queue: QueueState = field(default_factory=QueueState)
    active_tab: str = "home"
    error_msg: Optional[str] = None
    is_online: bool = True
    download_progress: Optional[float] = None
```

---

## CS-003 — God Function: `serve_stream`

**Lokasi:** `server/handlers/http.py`, fungsi `serve_stream`, ~130 baris  
**Severity:** 🔴 HIGH  

**Alasan:**  
Satu fungsi mengerjakan: validasi video_id, rate limiting, origin check, path traversal check, ETag caching, stream URL resolution, SSRF validation, HTTP proxy streaming, dan retry logic. Ini adalah God Function — terlalu banyak tanggung jawab.

**Potongan Kode Bermasalah:**
```python
async def serve_stream(request):
    # 1. Validasi video_id
    video_id_str = request.match_info.get("video_id")
    try:
        video_id = VideoId(video_id_str)
    except ValueError: ...

    # 2. Rate limiting (15 baris)
    client_ip = request.remote
    now = time.monotonic()
    history = _stream_rate_limit[client_ip]
    history = [t for t in history if now - t < 60]
    if len(history) >= STREAM_RATE_LIMIT_MAX: ...

    # 3. Origin check
    referer = request.headers.get("Referer", "")
    if host not in referer and ...: ...

    # 4. Path traversal check
    cache_file = CACHE_DIR / f"{video_id}.mp3"
    try:
        if not cache_file.resolve().is_relative_to(CACHE_DIR.resolve()): ...

    # 5. ETag cache
    stat = cache_file.stat()
    etag = f'"{int(stat.st_mtime)}-{stat.st_size}"'
    if request.headers.get("If-None-Match") == etag: ...

    # 6. URL resolution dari DB
    row = await db.get_track(video_id)
    if row and row.stream_url and row.stream_url_ts: ...

    # 7. HTTP redirect path
    if not http_session: ...
        return web.HTTPFound(stream_url)

    # 8. Retry loop dengan proxy streaming (40+ baris)
    for attempt in range(2):
        if not stream_url: ...
        # SSRF validation
        # Proxy stream dengan chunks
        async for chunk in upstream.content.iter_chunked(16384): ...
```

**Cara Refactor:**
```python
# Pisahkan setiap tanggung jawab:

def _check_rate_limit(client_ip: str) -> bool:
    """Returns True jika request diizinkan."""
    ...

def _check_origin(request) -> bool:
    """Returns True jika origin valid."""
    ...

def _validate_stream_url(stream_url: str) -> None:
    """Raises ValueError jika URL tidak aman (SSRF check)."""
    ...

async def _resolve_stream_url(video_id, db, ytdlp) -> str:
    """Fetch stream URL dari DB atau yt-dlp."""
    ...

async def _proxy_stream(request, stream_url: str) -> web.StreamResponse:
    """Proxy audio stream ke client."""
    ...

async def serve_stream(request):
    """Koordinasi semua langkah — hanya 20-30 baris."""
    video_id = _parse_video_id(request)
    if not _check_rate_limit(request.remote): return 429
    if not _check_origin(request): return 403
    cached = await _serve_from_cache(request, video_id)
    if cached: return cached
    stream_url = await _resolve_stream_url(video_id, ...)
    return await _proxy_stream(request, stream_url)
```

---

## CS-004 — Long Method: `handle_auth`

**Lokasi:** `server/handlers/auth.py`, fungsi `handle_auth`  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Satu fungsi handle: session token verification, IP pruning, rate limiting dengan sleep, brute force check, credential comparison, session creation, dan response sending. Terlalu banyak tahap dalam satu alur.

**Potongan Kode Bermasalah:**
```python
async def handle_auth(ws, data, manager, client_ip, db, now):
    async with manager.rl_lock:
        _prune_stale_ips(manager, now)

        # Path 1: Token verification
        token = data.get("token")
        if token and db:
            if await db.verify_session(token):
                manager.authenticated_connections.add(ws)
                await ws.send_str(json.dumps({...}))
                return

        # Path 2: Rate limit check + sleep penalty
        attempts = [t for t in manager.login_attempts.get(client_ip, []) if now - t < 300]
        if attempts:
            import asyncio
            await asyncio.sleep(min(len(attempts), 5))  # asyncio import di dalam fungsi!

        if len(attempts) >= MAX_LOGIN_ATTEMPTS:
            ...
            return

        # Path 3: Credential check
        username = data.get("username", "")
        password = data.get("password", "")
        if secrets.compare_digest(username, ADMIN_USERNAME) and verify_password(...):
            new_token = secrets.token_hex(16)
            ...
        else:
            ...
```

**Masalah Tambahan:** `import asyncio` dilakukan di dalam fungsi (lihat CS-010).

**Cara Refactor:**
```python
async def handle_auth(ws, data, manager, client_ip, db, now):
    """Dispatch ke sub-handler yang sesuai."""
    async with manager.rl_lock:
        _prune_stale_ips(manager, now)
        token = data.get("token")
        if token:
            return await _handle_token_auth(ws, token, manager, db)
        return await _handle_password_auth(ws, data, manager, client_ip, db, now)

async def _handle_token_auth(ws, token, manager, db):
    if db and await db.verify_session(token):
        manager.authenticated_connections.add(ws)
        await _send_auth_success(ws, token)
    # No else needed — silent failure for invalid token reuse

async def _handle_password_auth(ws, data, manager, client_ip, db, now):
    attempts = _get_recent_attempts(manager, client_ip, now)
    if attempts:
        await asyncio.sleep(min(len(attempts), 5))
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        return await _send_auth_failure(ws, "Terlalu banyak percobaan login.")
    username = data.get("username", "")
    password = data.get("password", "")
    if _verify_credentials(username, password):
        return await _create_and_send_session(ws, manager, client_ip, db, now)
    _record_failed_attempt(manager, client_ip, now, attempts)
    await _send_auth_failure(ws, "Username atau Password salah!")
```

---

## CS-005 — Long Parameter List (Systemic): WS Handlers

**Lokasi:** `server/handlers/ws/` — semua handler files  
**Severity:** 🔴 HIGH  

**Alasan:**  
**Setiap** WS handler memiliki signature identik dengan 7 parameter. Ini adalah code smell sistemik yang terjadi di 20+ fungsi. Parameter `ytdlp` dan `manager` sering tidak digunakan oleh handler tertentu, namun tetap dikirim karena dipaksakan oleh interface seragam yang salah.

**Potongan Kode Bermasalah:**
```python
# settings_handlers.py
async def _handle_volume_up(data, ws, state, ytdlp, manager, db, command_bus): ...
async def _handle_volume_down(data, ws, state, ytdlp, manager, db, command_bus): ...
async def _handle_volume_set(data, ws, state, ytdlp, manager, db, command_bus): ...
async def _handle_set_mode(data, ws, state, ytdlp, manager, db, command_bus): ...
async def _handle_set_output(data, ws, state, ytdlp, manager, db, command_bus): ...
async def _handle_set_sponsorblock(data, ws, state, ytdlp, manager, db, command_bus): ...
async def _handle_lyrics_offset(data, ws, state, ytdlp, manager, db, command_bus): ...

# playback_handlers.py
async def _handle_play_track(data, ws, state, ytdlp, manager, db, command_bus): ...
async def _handle_toggle_pause(data, ws, state, ytdlp, manager, db, command_bus): ...
async def _handle_next(data, ws, state, ytdlp, manager, db, command_bus): ...
# ... dan seterusnya untuk 20+ handler
```

**Cara Refactor — Introduce Parameter Object:**
```python
from dataclasses import dataclass

@dataclass
class WSContext:
    """Satu objek context menggantikan 7 parameter terpisah."""
    ws: Any
    state: AppState
    ytdlp: MediaExtractorPort
    manager: ConnectionManager
    db: Database
    command_bus: CommandBus

# Handler menjadi bersih:
async def _handle_volume_up(data: dict, ctx: WSContext) -> None:
    await ctx.command_bus.dispatch(VolumeUpCommand())

async def _handle_play_track(data: dict, ctx: WSContext) -> None:
    track = TrackInfo.from_dict(data)
    if not track:
        return
    await ctx.command_bus.dispatch(PlayTrackCommand(track=track))

# handle_ws_message menjadi:
async def handle_ws_message(msg: dict, ctx: WSContext) -> None:
    action = WSAction(msg.get("action"))
    handler = _ws_handlers.get(action)
    if handler:
        await handler(msg.get("data", {}), ctx)
```

---

## CS-006 — Long Method: `_build_ui` di `ServerManagerWindow`

**Lokasi:** `start.py`, method `_build_ui`, ~180 baris  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Satu method membangun seluruh UI dari header sampai log panel. Tidak ada pemisahan per seksi UI. Perubahan kecil pada satu bagian memerlukan navigasi di seluruh 180 baris.

**Potongan Kode Bermasalah:**
```python
def _build_ui(self):
    # Header section (10 baris)
    header = tk.Frame(...)
    tk.Label(header, text="bagas.fm", ...)
    tk.Label(header, text="Server Manager", ...)

    # Status section (30 baris)
    status_frame = tk.Frame(...)
    self._dot = tk.Canvas(...)
    self._status_label = tk.Label(...)
    port_frame = tk.Frame(...)
    # ... 20 baris lebih

    # Button section (20 baris)
    btn_frame = tk.Frame(...)
    self._btn_start = self._make_btn(...)
    # ... dst

    # Admin section (20 baris)
    # Links section (20 baris)
    # Deps section (15 baris)
    # Log section (30 baris) — semua dalam _build_ui
```

**Cara Refactor:**
```python
def _build_ui(self):
    """Koordinasi saja — delegasi ke builder methods."""
    self._build_header()
    self._build_status_bar()
    self._build_action_buttons()
    self._build_admin_panel()
    self._build_quick_links()
    self._build_deps_panel()
    self._build_log_panel()

def _build_header(self):
    header = tk.Frame(self, bg=BG_SURFACE, pady=14)
    header.pack(fill="x")
    tk.Label(header, text="bagas.fm", bg=BG_SURFACE, fg=ACCENT,
             font=("Segoe UI", 18, "bold")).pack()
    tk.Label(header, text="Server Manager", bg=BG_SURFACE, fg=TEXT_3,
             font=("Segoe UI", 9)).pack()

def _build_status_bar(self):
    # ... hanya status bar
```

---

## CS-007 — Duplicate Code: Validasi `video_id` Regex

**Lokasi:** Terdefinisi di 3 tempat berbeda  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Regex validasi video_id YouTube (`^[a-zA-Z0-9_-]{11}$`) didefinisikan ulang di beberapa lokasi. Jika format berubah (misal 12 karakter), harus diubah di semua tempat — risiko inkonsistensi.

**Potongan Kode Bermasalah:**
```python
# core/value_objects.py
class VideoId(str):
    _RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

# server/handlers/ws/discover_handlers.py
VIDEO_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{11}$")
# ↑ Perhatikan: A-Za-z vs a-zA-Z — urutan berbeda, tapi ekuivalen
# Namun dua definisi terpisah tetap rawan drift

# engine/ytdlp_client.py — validasi manual (implicit regex)
if video_id and not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', video_id):
# ↑ Limit 1–64 vs 11 eksak — INKONSISTEN!
```

**Cara Refactor:**
```python
# core/value_objects.py — single source of truth
class VideoId(str):
    _RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

    def __new__(cls, value: str):
        if not value or not cls._RE.match(str(value)):
            raise ValueError(f"video_id tidak valid: {value!r}")
        return super().__new__(cls, str(value))

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Gunakan method ini daripada mendefinisikan regex baru."""
        return bool(value) and cls._RE.match(str(value)) is not None

# discover_handlers.py — hapus VIDEO_ID_REGEX, gunakan:
from core.value_objects import VideoId

if VideoId.is_valid(str(video_id)):
    ...

# ytdlp_client.py — gunakan VideoId juga:
try:
    vid = VideoId(entry.get("id", ""))
except ValueError:
    vid = f"vid_{abs(hash(entry.get('title', ''))) % 10**10}"
```

---

## CS-008 — Duplicate Code: Password File Logic

**Lokasi:** `start.py` (2 tempat) dan `config.py`  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Logic untuk generate, hash, dan simpan password admin ke file `cache/admin_password.txt` ditulis **3 kali** — di `config.get_admin_password()`, di `ServerManagerController.check_first_run()`, dan di `ServerManagerController.on_reset_password()`. Perubahan path atau behavior harus direplikasi 3 tempat.

**Potongan Kode Bermasalah:**
```python
# config.py — generate password
raw_password = secrets.token_urlsafe(12)
_admin_password = hash_password(raw_password)
_password_file.parent.mkdir(parents=True, exist_ok=True)
with open(_password_file, "w", encoding="utf-8") as f:
    f.write(_admin_password)
try:
    import stat
    _password_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
except OSError:
    pass

# start.py — check_first_run: IDENTIK dengan config.py!
raw_password = secrets.token_urlsafe(12)
hashed_password = hash_password(raw_password)
password_file.parent.mkdir(parents=True, exist_ok=True)
with open(password_file, "w", encoding="utf-8") as f:
    f.write(hashed_password)
try:
    import stat
    password_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
except OSError:
    pass

# start.py — on_reset_password: IDENTIK lagi!
raw_password = secrets.token_urlsafe(12)
hashed_password = hash_password(raw_password)
password_file.parent.mkdir(parents=True, exist_ok=True)
with open(password_file, "w", encoding="utf-8") as f:
    f.write(hashed_password)
```

**Cara Refactor:**
```python
# core/security.py — tambahkan helper:
def generate_and_save_admin_password(password_file: Path) -> str:
    """
    Generate password baru, hash, simpan ke file dengan permission aman.
    Returns raw (plaintext) password untuk ditampilkan ke user.
    """
    raw_password = secrets.token_urlsafe(12)
    hashed = hash_password(raw_password)
    password_file.parent.mkdir(parents=True, exist_ok=True)
    password_file.write_text(hashed, encoding="utf-8")
    try:
        import stat
        password_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return raw_password

# Semua pemanggil cukup:
from core.security import generate_and_save_admin_password
raw = generate_and_save_admin_password(password_file)
```

---

## CS-009 — Duplicate Code: `defaultdict` Rate Limit — 2 Implementasi Berbeda

**Lokasi:** `server/handlers/http.py` vs `server/middleware.py`  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Rate limiting diimplementasikan dua kali dengan mekanisme berbeda: `http.py` menggunakan `collections.defaultdict(list)` global module-level, sementara `middleware.py` menggunakan `manager.command_history` dict yang disimpan di `ConnectionManager`. Keduanya beroperasi dengan sliding window 60 detik tapi dengan kode berbeda.

**Potongan Kode Bermasalah:**
```python
# server/handlers/http.py
_stream_rate_limit = collections.defaultdict(list)
STREAM_RATE_LIMIT_MAX = 20

async def serve_stream(request):
    ...
    history = _stream_rate_limit[client_ip]
    history = [t for t in history if now - t < 60]
    if len(history) >= STREAM_RATE_LIMIT_MAX:
        return web.json_response(..., status=429)
    history.append(now)
    _stream_rate_limit[client_ip] = history

# server/middleware.py — logika SAMA tapi berbeda tempat penyimpanan
async def check_rate_limit(manager, client_ip: str, now: float) -> bool:
    async with manager.rl_lock:
        cmd_history = manager.command_history.get(client_ip, [])
        cmd_history = [t for t in cmd_history if now - t < 60]
        ...
```

**Cara Refactor — Buat `RateLimiter` class:**
```python
# server/rate_limiter.py
import asyncio
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._history: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        async with self._lock:
            history = [t for t in self._history[key] if now - t < self._window]
            if len(history) >= self._max:
                self._history[key] = history
                return False
            history.append(now)
            self._history[key] = history
            return True

    async def prune(self) -> None:
        """Panggil secara periodik untuk mencegah memory leak."""
        now = time.monotonic()
        async with self._lock:
            self._history = {
                k: [t for t in v if now - t < self._window]
                for k, v in self._history.items()
                if any(now - t < self._window for t in v)
            }
```

---

## CS-010 — Primitive Obsession: `is_favorite` sebagai `int` bukan `bool`

**Lokasi:** `core/state.py` (TrackInfo), `cache/db.py`, `cache/repositories/`  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Field `is_favorite` didefinisikan sebagai `Optional[int]` di `TrackInfo` padahal semantiknya boolean. Akibatnya, kode yang menggunakannya harus selalu melakukan konversi manual (`bool(...)`, `int(...)`), dan ada inkonsistensi: kadang nilai `0/1`, kadang `True/False`.

**Potongan Kode Bermasalah:**
```python
# core/state.py — int, bukan bool
@dataclass
class TrackInfo:
    is_favorite: Optional[int] = 0  # ← Seharusnya bool

# state.py to_dict() — perlu konversi manual
"is_favorite": bool(getattr(self, "is_favorite", 0)),

# state.py from_dict() — perlu konversi manual balik
is_favorite=int(data.get("is_favorite", False)),

# discover_handlers.py — pengecekan inkonsisten
is_fav = await db.toggle_favorite(video_id)
# toggle_favorite return int, lalu:
"is_favorite": bool(is_fav)  # konversi lagi

# core/state.py to_dict check
state.current_track.is_favorite = is_fav  # is_fav = int!
```

**Cara Refactor:**
```python
@dataclass
class TrackInfo:
    is_favorite: bool = False  # ← bool dari awal

    def to_dict(self) -> dict:
        return {
            ...
            "is_favorite": self.is_favorite,  # no conversion needed
        }

    @classmethod
    def from_dict(cls, data: dict) -> Optional['TrackInfo']:
        return cls(
            ...
            is_favorite=bool(data.get("is_favorite", False)),  # only here
        )
```

---

## CS-011 — Primitive Obsession: Magic String `"ytgui_*"` di Frontend

**Lokasi:** `web/static/js/ws.js`, `web/static/js/services/auth.js`  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Kunci localStorage menggunakan string literal tersebar seperti `"ytgui_session_token"`, `"ytgui_user_role"`, `"ytgui_audio_output"`. String ini berasal dari nama lama sistem ("ytgui") yang sudah diganti brand menjadi LunaWave. Jika kunci berubah, harus dicari manual di seluruh JS.

**Potongan Kode Bermasalah:**
```javascript
// ws.js
const token = window.safeStorage.get("ytgui_session_token");
window.safeStorage.set("ytgui_user_role", "admin");
window.safeStorage.set("ytgui_session_token", msg.data.token);
const savedOutput = window.safeStorage.get("ytgui_audio_output") || "browser";

// Juga di services/auth.js (belum dibaca lengkap tapi pola sama)
```

**Cara Refactor:**
```javascript
// config.js — tambahkan storage key constants
const STORAGE_KEYS = Object.freeze({
    SESSION_TOKEN: "lunawave_session_token",
    USER_ROLE:     "lunawave_user_role",
    AUDIO_OUTPUT:  "lunawave_audio_output",
    COVER_PREFIX:  "cover_",
});

// ws.js — gunakan constants
const token = window.safeStorage.get(STORAGE_KEYS.SESSION_TOKEN);
window.safeStorage.set(STORAGE_KEYS.USER_ROLE, "admin");
window.safeStorage.set(STORAGE_KEYS.SESSION_TOKEN, msg.data.token);
```

---

## CS-012 — Magic Number: Timeout/Delay Hardcoded

**Lokasi:** Tersebar di seluruh codebase  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Banyak angka timeout, delay, dan limit ditulis langsung tanpa nama konstanta. Bila perlu tuning performa (umum di produksi besar), engineer harus mencari semua `300`, `14400`, `60`, `3000`, dll di seluruh codebase.

**Potongan Kode Bermasalah:**
```python
# server/handlers/auth.py
attempts = [t for t in ... if now - t < 300]  # 300 detik = 5 menit — kenapa?
await asyncio.sleep(min(len(attempts), 5))     # max 5 detik penalty
new_token = secrets.token_hex(16)              # 16 bytes token
await db.create_session(new_token, int(now) + 14400)  # 14400 = 4 jam!

# server/handlers/http.py
history = [t for t in history if now - t < 60]  # 60 detik window
STREAM_RATE_LIMIT_MAX = 20  # ini sudah named, tapi...
async for chunk in upstream.content.iter_chunked(16384)  # chunk size?

# core/state.py
history: deque = field(default_factory=lambda: deque(maxlen=50))  # 50?

# web/static/js/ws.js
wsReconnectTimer = setTimeout(wsConnect, 2000);  # 2 detik?
if (!window.lastToggleTime || Date.now() - window.lastToggleTime > 1000)  # 1 detik?

# web/static/js/render/lyrics.js
scrollTimeout = setTimeout(() => window.isScrollingLyrics = false, 3000);
```

**Cara Refactor:**
```python
# core/constants.py — tambahkan semua:
AUTH_WINDOW_SECONDS       = 300    # 5 menit window rate limit login
AUTH_MAX_PENALTY_SECONDS  = 5      # max sleep penalty per attempt
SESSION_TOKEN_BYTES        = 16    # bytes untuk token hex
SESSION_TTL_SECONDS        = 14400 # 4 jam session lifetime
CMD_RATE_WINDOW_SECONDS    = 60    # sliding window WS commands
STREAM_CHUNK_SIZE          = 16384 # bytes per proxy chunk (16KB)
HISTORY_MAX_SIZE           = 50    # max track history entries
```

```javascript
// config.js
const RECONNECT_DELAY_MS       = 2000;
const TOGGLE_DEBOUNCE_MS       = 1000;
const LYRICS_SCROLL_TIMEOUT_MS = 3000;
const LOG_TOAST_DURATION_MS    = 3000;
const STREAM_CHUNK_SIZE        = 16384;
```

---

## CS-013 — Magic String: Status dan Event Type sebagai Literal

**Lokasi:** `web/static/js/ws.js` — `handleServerMessage`  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Message type dari server seperti `"auth_status"`, `"state"`, `"progress"`, `"lyrics"`, dll ditulis sebagai string literal di switch-case. Jika backend mengubah nama event, akan terjadi silent failure di frontend.

**Potongan Kode Bermasalah:**
```javascript
function handleServerMessage(msg) {
    switch (msg.type) {
        case "auth_status": ...
        case "state": ...
        case "progress": ...
        case "lyrics": ...
        case "search_results": ...
        case "discover_data": ...
        case "favorite_status": ...
        case "log": ...
        case "error": ...
        case "download_progress": ...
    }
}
```

**Cara Refactor:**
```javascript
// config.js
const SERVER_MSG_TYPES = Object.freeze({
    AUTH_STATUS:       "auth_status",
    STATE:             "state",
    PROGRESS:          "progress",
    LYRICS:            "lyrics",
    SEARCH_RESULTS:    "search_results",
    DISCOVER_DATA:     "discover_data",
    FAVORITE_STATUS:   "favorite_status",
    LOG:               "log",
    ERROR:             "error",
    DOWNLOAD_PROGRESS: "download_progress",
});

// ws.js
switch (msg.type) {
    case SERVER_MSG_TYPES.AUTH_STATUS: ...
    case SERVER_MSG_TYPES.STATE: ...
    // ...
}
```

---

## CS-014 — Feature Envy: `discover_handlers.py` Akses Langsung ke `db.conn`

**Lokasi:** `server/handlers/ws/discover_handlers.py`, baris toggle_favorite  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Handler mengakses `db.conn` (implementasi detail aiosqlite) secara langsung, melewati abstraksi repository. Ini mengikat handler ke implementasi database spesifik dan membuat testing sulit.

**Potongan Kode Bermasalah:**
```python
@register_ws_handler(WSAction.TOGGLE_FAVORITE)
async def _handle_toggle_favorite(data, ws, state, ytdlp, manager, db, command_bus):
    ...
    if set_favorite is not None:
        target = 1 if set_favorite else 0
        # ↓ Akses langsung ke db.conn — Feature Envy!
        await db.conn.execute(
            "UPDATE tracks SET is_favorite = ? WHERE video_id = ?",
            (target, video_id)
        )
        await db.conn.commit()
```

**Cara Refactor:**
```python
# cache/repositories/track_repository.py — tambahkan method:
async def set_favorite(self, video_id: str, is_favorite: bool) -> None:
    await self._conn.execute(
        "UPDATE tracks SET is_favorite = ? WHERE video_id = ?",
        (1 if is_favorite else 0, video_id)
    )
    await self._conn.commit()

# discover_handlers.py — handler hanya tahu interface:
if set_favorite is not None:
    await db.set_favorite(video_id, bool(set_favorite))
    is_fav = set_favorite
```

---

## CS-015 — Feature Envy: `on_reset_password` Akses Langsung Database SQLite

**Lokasi:** `start.py`, `ServerManagerController.on_reset_password`  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
GUI controller mengimport dan menggunakan `sqlite3` secara langsung untuk menghapus sessions. Ini adalah Feature Envy — logika database berada di layer yang salah (UI controller).

**Potongan Kode Bermasalah:**
```python
def on_reset_password(self):
    ...
    import sqlite3  # ← import di dalam method, seharusnya di modul khusus
    db_path = BASE_DIR / "data" / "LunaWave.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)  # ← bypass semua abstraksi!
            conn.execute("DELETE FROM sessions")
            conn.commit()
            conn.close()
        except Exception:
            pass
```

**Cara Refactor:**
```python
# core/security.py — tambahkan:
def invalidate_all_sessions(db_path: Path) -> None:
    """Hapus semua session aktif. Dipanggil saat password reset."""
    import sqlite3
    if not db_path.exists():
        return
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("DELETE FROM sessions")
    except Exception:
        pass

# start.py — controller hanya orchestrate:
def on_reset_password(self):
    ...
    from core.security import generate_and_save_admin_password, invalidate_all_sessions
    raw = generate_and_save_admin_password(password_file)
    invalidate_all_sessions(BASE_DIR / "data" / "LunaWave.db")
    self.view.show_new_password_dialog(raw)
```

---

## CS-016 — Feature Envy: `AppState` di Tulis Langsung dari Handler

**Lokasi:** `server/handlers/ws/discover_handlers.py`  
**Severity:** 🟠 MEDIUM  

**Alasan:**  
Handler WebSocket memutasi `state.current_track` secara langsung dari luar domain engine. Ini bypass event-driven architecture yang sudah dibangun, menciptakan side effect tersembunyi.

**Potongan Kode Bermasalah:**
```python
# discover_handlers.py
if state.current_track and state.current_track.video_id == video_id:
    state.current_track.is_favorite = is_fav  # ← mutasi state langsung!
    await manager.broadcast({
        "type": "state",
        "data": state.to_dict()
    })
```

**Cara Refactor:**
```python
# Gunakan command bus:
await command_bus.dispatch(UpdateFavoriteStateCommand(
    video_id=video_id,
    is_favorite=bool(is_fav)
))
# PlaybackController handle event ini dan update state
```

---

## CS-017 — Dead Code: `resumeVisualizerLoop` Tidak Dipanggil

**Lokasi:** `web/static/js/audio.js`  
**Severity:** 🟡 LOW  

**Alasan:**  
Fungsi `resumeVisualizerLoop` terdefinisi namun tidak dipanggil dari mana pun dalam codebase. Visualizer yang sesungguhnya (`startFakeBeatLoop`) adalah pengganti sementara yang tidak memerlukan fungsi ini.

**Potongan Kode Bermasalah:**
```javascript
function resumeVisualizerLoop() {
    // Fungsi ini tidak pernah dipanggil!
    if (analyser && dataArray) {
        ...
    }
}
```

**Cara Refactor:** Hapus fungsi atau implementasikan real visualizer.

---

## CS-018 — Dead Code: `unlockBrowserAudio` Terdefinisi tapi Tidak Dipakai

**Lokasi:** `web/static/js/audio.js`  
**Severity:** 🟡 LOW  

**Alasan:**  
`unlockBrowserAudio(forcePlay)` tidak muncul sebagai pemanggil di file JS manapun selain definisinya sendiri.

**Cara Refactor:** Verifikasi dengan grep menyeluruh; hapus jika memang dead code.

---

## CS-019 — Dead Code: `_last_stdout_line` di `ServerManagerController`

**Lokasi:** `start.py`, `ServerManagerController`  
**Severity:** 🟡 LOW  

**Alasan:**  
Field `self._last_stdout_line` di-assign di `on_start` dan callback `on_log`, tapi tidak pernah dibaca atau digunakan untuk mengambil keputusan apapun.

**Potongan Kode Bermasalah:**
```python
class ServerManagerController:
    def __init__(self, view):
        ...
        self._last_stdout_line = ""  # tidak pernah dibaca!

    def on_start(self):
        ...
        def on_log(line, tag):
            self._last_stdout_line = line  # ditulis, tidak pernah dibaca
            self.view.write_log(line, tag)
```

**Cara Refactor:** Hapus field `_last_stdout_line` dan assignment-nya.

---

## CS-020 — Dead Code: `self.tracks`, `self.sessions`, `self.discover` di `Database`

**Lokasi:** `cache/db.py`  
**Severity:** 🟡 LOW  

**Alasan:**  
`Database.__init__` menginisialisasi `self.tracks = None`, `self.sessions = None`, `self.discover = None`, namun akses ke method-method repository dilakukan via `__getattr__` proxy magic method, bukan via atribut ini secara langsung. Atribut None awal ini menyesatkan.

**Potongan Kode Bermasalah:**
```python
class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self._conn = None
        self.tracks = None    # ← diinit None
        self.sessions = None  # ← diinit None
        self.discover = None  # ← diinit None

    def __getattr__(self, name):
        # Proxy semua akses via magic method
        if self.tracks and hasattr(self.tracks, name):
            return getattr(self.tracks, name)
        ...
```

**Cara Refactor:** Gunakan type hints `Optional[TrackRepository]` dan dokumentasikan bahwa `None` berarti belum terinisialisasi, atau gunakan property.

---

## CS-021 — Unused Import: `import asyncio` di dalam Method Body

**Lokasi:** `server/handlers/auth.py`, baris 43 dan `engine/download_manager.py`  
**Severity:** 🟡 LOW  

**Alasan:**  
`asyncio` diimport di **dalam body fungsi** padahal sudah tersedia di scope modul (atau seharusnya diimport di top-level). Ini adalah anti-pattern Python — setiap call ke fungsi ini memuat (atau lookup) modul `asyncio`.

**Potongan Kode Bermasalah:**
```python
# server/handlers/auth.py
async def handle_auth(ws, data, manager, client_ip, db, now):
    ...
    if attempts:
        import asyncio          # ← import di dalam fungsi!
        await asyncio.sleep(...)

# engine/download_manager.py — _route method
def _route(self, action):
    async def handler(command):
        import asyncio          # ← import di dalam nested function!
        res = action(command.track)
        if asyncio.iscoroutine(res):
            return await res
```

**Cara Refactor:** Pindahkan semua `import asyncio` ke top-level modul.

---

## CS-022 — Unused Variable: `aiohttp` Import di `server/handlers/websocket.py`

**Lokasi:** `server/handlers/websocket.py`, baris 5  
**Severity:** 🟡 LOW  

**Alasan:**  
`import aiohttp` dilakukan di top-level, namun hanya `from aiohttp import web` yang digunakan secara eksplisit. `aiohttp` namespace tidak diakses langsung di file ini.

**Potongan Kode Bermasalah:**
```python
import aiohttp          # ← mana aiohttp.xxx yang dipakai?
import structlog
from aiohttp import web # ini yang dipakai

# ... di seluruh file hanya `web.xxx` yang muncul
```

**Cara Refactor:**
```python
# Hapus baris: import aiohttp
from aiohttp import web  # cukup ini
```

---

## CS-023 — Commented Code: Sisa Komentar PATCH

**Lokasi:** `server/handlers/http.py`, `web/static/js/ws.js`, `engine/mpv_controller.py`  
**Severity:** 🟡 LOW  

**Alasan:**  
Banyak komentar `# PATCH-*` yang menjelaskan "dulu ada bug, sekarang sudah fix" — ini adalah changelog inline, bukan komentar kode. Untuk production, komentar ini seharusnya berada di git commit message atau CHANGELOG, bukan di kode.

**Potongan Kode Bermasalah:**
```python
# server/handlers/http.py
await asyncio.sleep(1) # Backoff before retry
# Jangan retry untuk error selain timeout (misal video tidak ditemukan)

# engine/mpv_controller.py
"""
CRITICAL-03 fix: On Windows, falls back to TCP socket (localhost:port)...
CRITICAL-06 fix: _set_property is now properly defined.
MED-11: Basic reconnection support via is_connected flag.
"""

# web/static/js/ws.js
// PATCH-ANDROID-AUDIO-01: kalau sebelumnya sudah ketauan diblock browser,
// PATCH-ANDROID-AUDIO-01: dipanggil tiap tick (bukan cuma saat statusChanged)
```

**Cara Refactor:** Pindahkan riwayat patch ke `CHANGELOG.md` atau Git history. Komentar yang tersisa di kode hanya boleh menjelaskan **mengapa** sesuatu dilakukan, bukan **apa yang berubah dari versi sebelumnya**.

---

## CS-024 — Primitive Obsession: Session Token sebagai Raw String

**Lokasi:** `server/handlers/auth.py`, `cache/repositories/auth_repository.py`  
**Severity:** 🟡 LOW  

**Alasan:**  
Session token dihandle sebagai `str` biasa di seluruh codebase. Tidak ada validasi format, panjang minimum, atau type yang membedakannya dari string biasa. Jika token format berubah, ada risiko accept token format lama yang tidak valid.

**Cara Refactor:**
```python
# core/value_objects.py
class SessionToken(str):
    """Opaque session token — minimal 32 hex characters."""
    _MIN_LEN = 32

    def __new__(cls, value: str):
        if not value or len(value) < cls._MIN_LEN:
            raise ValueError(f"Token terlalu pendek: {len(value)} < {cls._MIN_LEN}")
        return super().__new__(cls, value)

    @classmethod
    def generate(cls) -> 'SessionToken':
        import secrets
        return cls(secrets.token_hex(16))
```

---

## CS-025 — Magic Number: `MAX_VOLUME = 150` Inkonsisten dengan `Volume(int)` max 100

**Lokasi:** `core/constants.py` vs `core/value_objects.py`  
**Severity:** 🔴 HIGH — Ini adalah BUG, bukan hanya code smell  

**Alasan:**  
`MAX_VOLUME = 150` di `constants.py` berbeda dengan `Volume(int)` yang clamp ke `max(0, min(100, int(value)))`. `MpvController.set_volume` menggunakan `MAX_VOLUME` (150), sementara `Volume` value object tidak bisa merepresentasikan nilai > 100. Nilai antara 100–150 bisa masuk ke mpv tapi tidak bisa direpresentasikan lewat `AppState.volume`.

**Potongan Kode Bermasalah:**
```python
# core/constants.py
MAX_VOLUME = 150  # mpv supports amplification up to 150

# core/value_objects.py
class Volume(int):
    def __new__(cls, value: int):
        return super().__new__(cls, max(0, min(100, int(value))))  # ← clamp ke 100!

# engine/mpv_controller.py
async def set_volume(self, volume: int):
    await self._set_property("volume", max(0, min(MAX_VOLUME, volume)))  # ← pakai 150

# server/handlers/ws/settings_handlers.py
vol = max(0, min(150, int(data.get("volume", DEFAULT_VOLUME))))  # ← hardcode 150!
```

**Cara Refactor:**
```python
# Tentukan: apakah kita support amplifikasi (>100) atau tidak?
# Pilihan A: Support amplifikasi
class Volume(int):
    def __new__(cls, value: int):
        return super().__new__(cls, max(0, min(MAX_VOLUME, int(value))))
    # Jangan lupa update MAX_VOLUME ke satu konstanta di constants.py

# Pilihan B: Tidak support amplifikasi
MAX_VOLUME = 100  # ubah ini
# dan hapus min(150,...) dari settings_handlers.py
```

---

## Ringkasan Prioritas Perbaikan

| Prioritas | ID | Temuan | Effort |
|---|---|---|---|
| 🔴 **Segera** | CS-025 | BUG: MAX_VOLUME inkonsisten (100 vs 150) | Rendah |
| 🔴 **Segera** | CS-005 | Long Parameter List sistemik — 20+ fungsi | Sedang |
| 🔴 **Segera** | CS-003 | God Function `serve_stream` (130 baris) | Sedang |
| 🟠 **Sprint ini** | CS-001 | God Class `start.py` (866 baris) | Tinggi |
| 🟠 **Sprint ini** | CS-007 | Duplikasi video_id regex (inkonsisten 11 vs 64!) | Rendah |
| 🟠 **Sprint ini** | CS-008 | Duplikasi password file logic (3 tempat) | Rendah |
| 🟠 **Sprint ini** | CS-009 | Duplikasi rate limiter (2 implementasi berbeda) | Sedang |
| 🟠 **Sprint ini** | CS-011 | Magic string `"ytgui_*"` — legacy branding di localStorage | Rendah |
| 🟠 **Sprint ini** | CS-014 | Feature Envy: `db.conn` langsung dari handler | Rendah |
| 🟡 **Backlog** | CS-002 | God Class `AppState` (semua state campur) | Tinggi |
| 🟡 **Backlog** | CS-010 | Primitive Obsession `is_favorite` sebagai int | Sedang |
| 🟡 **Backlog** | CS-012 | Magic Numbers tersebar (timeout, TTL) | Rendah |
| 🟡 **Backlog** | CS-013 | Magic Strings event type di WS handler | Rendah |
| 🟡 **Backlog** | CS-017–020 | Dead code (4 item) | Rendah |
| 🟡 **Backlog** | CS-021–022 | Unused import dalam method body | Rendah |
| 🟡 **Backlog** | CS-023 | Commented PATCH notes (sebaiknya di git) | Rendah |

---

*Laporan ini dihasilkan dari analisis statis menyeluruh terhadap semua file source code LunaWave. Setiap temuan disertai lokasi presisi, kode bermasalah, dan contoh refactor yang dapat langsung diimplementasikan.*

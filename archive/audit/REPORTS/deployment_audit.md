# DEPLOYMENT AUDIT — ytgui-main (bagas.fm)
**Source of Truth:** Active source files only — `.backup_patchlog/` dan `*.md` diabaikan  
**Target Environments:** Android/Termux (primary) · Windows Desktop · Linux Desktop/Server  
**Audit Scope:** Docker · CI/CD · Secrets · Build · Release · Rollback · Monitoring · Logging · Alerting · Backup · Disaster Recovery

---

## RINGKASAN EKSEKUTIF

```
DEPLOYMENT MATURITY SCORECARD
═══════════════════════════════════════════════════════════
  Docker           ████░░░░░░░░  TIDAK ADA
  CI/CD            ███░░░░░░░░░  MINIMAL (CI only, no CD)
  Secrets          ███████░░░░░  CUKUP (tapi ada gap)
  Build            ████░░░░░░░░  TIDAK ADA (git archive saja)
  Release          ░░░░░░░░░░░░  TIDAK ADA
  Rollback         ░░░░░░░░░░░░  TIDAK ADA
  Monitoring       █████░░░░░░░  PARSIAL (metrics ada, no backend)
  Logging          ███████░░░░░  CUKUP (structlog, no aggregation)
  Alerting         ░░░░░░░░░░░░  TIDAK ADA
  Backup           ██░░░░░░░░░░  MINIMAL (manual only)
  Disaster Rec.    ░░░░░░░░░░░░  TIDAK ADA
═══════════════════════════════════════════════════════════
  OVERALL          ████░░░░░░░░  ~35% — Personal use OK,
                                  Production: TIDAK SIAP
```

> **Konteks penting**: ytgui adalah aplikasi personal self-hosted, bukan SaaS. Target deployment utama adalah Termux di Android satu device. Temuan di bawah dikalibrasi terhadap konteks ini — bukan enterprise standard.

---

## 1. DOCKER

### Status: ❌ TIDAK ADA

**File yang ada:**
- Tidak ada `Dockerfile`
- Tidak ada `docker-compose.yml` / `docker-compose.yaml`
- Tidak ada `.dockerignore`

**Analisis:**

Ini adalah **keputusan sadar yang valid** untuk target Termux/Android — Docker tidak tersedia di Termux standar dan menambahkan overhead signifikan untuk personal app. Namun untuk deployment di Linux server atau Windows WSL, Docker akan sangat membantu.

**Dependency yang sulit di-containerize:**
1. **MPV** — External process dengan IPC socket. Dalam container, MPV butuh audio device pass-through (`--device /dev/snd`) dan socket volume mount.
2. **yt-dlp** — Python library, mudah di-containerize.
3. **Termux-specific tools** (`termux-notification`, `socat`) — Tidak bisa dipakai dalam container sama sekali.

**Dampak tanpa Docker:**
- Setup berbeda di setiap environment (Termux vs Windows vs Linux) — tidak reproducible
- Tidak ada isolation: kalau `pip install` bentrok dengan global packages, app crash
- Tidak ada resource limit: yt-dlp bisa makan RAM tak terbatas

**Rekomendasi (jika ingin Docker):**
```dockerfile
# Dockerfile (draft konsep — tidak ada dalam repo)
FROM python:3.11-slim
RUN apt-get update && apt-get install -y mpv ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# MPV socket via Unix domain socket di dalam container
ENV YT_PLAYER_SOCKET=/tmp/mpv-ytgui.sock
CMD ["python", "main.py"]
```

---

## 2. CI/CD

### Status: ⚠️ CI ADA — CD TIDAK ADA

### 2.1 CI Pipeline (`.github/workflows/ci.yml`)

```yaml
on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.10"  # ← MASALAH: Python 3.10, bukan 3.11+
        cache: 'pip'
    - run: pip install -r requirements.txt && pip install -r requirements-dev.txt
    - run: pytest tests/ -v
```

**Yang HILANG dari CI:**

| Check | Status | Dampak |
|---|---|---|
| Linting (flake8/ruff) | ❌ Tidak ada | Code style tidak di-enforce |
| Type checking (mypy) | ❌ Tidak ada | Type error bisa lolos ke production |
| Security scan (bandit/safety) | ❌ Tidak ada | Dependency vuln tidak terdeteksi |
| Coverage report | ❌ Tidak ada | Tidak tahu berapa % code di-test |
| Multi-Python version matrix | ❌ Tidak ada | Hanya test di 3.10, tapi code pakai syntax 3.10+ (`X | Y` union types) |
| MPV tidak tersedia di CI | ⚠️ Expected | Test mock MPV — OK, tapi integration test tidak bisa jalan |
| Windows runner | ❌ Tidak ada | `start.bat` tidak pernah di-test |
| Dependency audit | ❌ Tidak ada | `yt-dlp==2026.3.17` — versi pinned tapi tidak di-check untuk CVE |

**Masalah versi Python:**
```yaml
python-version: "3.10"  # CI
```
Sementara `main.py` menggunakan:
```python
from collections import deque
state.queue: deque = field(default_factory=deque)  # OK di 3.10

# engine/mpv_controller.py:
self._pending: dict[int, asyncio.Future] = {}  # built-in generic — OK di 3.9+

# cache/db.py:
async def get_track(self, video_id: str) -> TrackInfo | None:  # ← UNION TYPE — butuh 3.10+
async def get_all_artists(self, kategori: str | None = None) -> list[str]:  # ← 3.10+
```
CI menjalankan Python 3.10 — union type `X | Y` butuh minimum 3.10. Ini OK, tapi CI tidak enforce bahwa **minimum 3.10** adalah requirement. Tidak ada `python_requires` di project config.

### 2.2 CD (Continuous Deployment)

**Tidak ada CD pipeline.** Deployment adalah proses manual:
1. `git pull` di device target
2. Jalankan `./start.sh` atau `python main.py`

Untuk personal app di Termux ini cukup, tapi tidak ada:
- Auto-deploy setelah CI pass
- Staged deployment (dev → staging → prod)
- Deployment verification

---

## 3. SECRETS

### Status: ⚠️ CUKUP — Ada Gap

### 3.1 Secret Inventory

| Secret | Cara Penyimpanan | Penilaian |
|---|---|---|
| Admin password | `cache/admin_password.txt` (hashed pbkdf2) atau ENV `YTGUI_ADMIN_PASS` | ✅ Aman |
| Session token | SQLite `sessions.token` (random hex 32 char) | ✅ OK |
| MPV socket path | Config + ENV `YT_PLAYER_SOCKET` | ✅ OK |
| Metrics token | ENV `YTGUI_METRICS_TOKEN` (opsional) | ✅ OK |
| YouTube API | Tidak ada — pakai yt-dlp scraping | ✅ No key needed |
| SponsorBlock API | Tidak ada key | ✅ No key needed |
| LRCLib API | Tidak ada key | ✅ No key needed |

### 3.2 Password Storage (`config.py`)

```python
# Alur yang benar sudah diimplementasikan:
if "YTGUI_ADMIN_PASS" in os.environ:
    raw = os.environ["YTGUI_ADMIN_PASS"]
    if raw.startswith("pbkdf2:sha256:"):
        ADMIN_PASSWORD = raw          # already hashed
    else:
        ADMIN_PASSWORD = hash_password(raw)  # hash plaintext from ENV
else:
    IS_PASSWORD_AUTO_GENERATED = True
    if _password_file.exists():
        ADMIN_PASSWORD = open(_password_file).read().strip()  # read hash from file
    else:
        raw = secrets.token_urlsafe(12)
        ADMIN_PASSWORD = hash_password(raw)
        # write hash to file, chmod 600
        _password_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
        print(f"PASSWORD ADMIN GENERATED: {raw}")  # ← SEKALI TAMPIL di stdout
```

✅ Benar: Hash PBKDF2-SHA256 dengan 100.000 iterasi, salt random, `secrets.compare_digest` untuk constant-time comparison.

### 3.3 Gap yang Ditemukan

**G-01: Password tercetak ke stdout saat first-run:**
```python
# config.py
print(f"\n=========================================")
print(f"PASSWORD ADMIN GENERATED: {raw}")  # ← plaintext password di stdout
```
Stdout bisa di-capture oleh `start.sh` (yang forward ke log), process manager, atau `start.py` log panel. Password plaintext bisa masuk ke log file. Solusi: print ke stderr hanya saat TTY, atau simpan di file dan hanya beritahu path-nya.

**G-02: `cache/admin_password.txt` berisi hash, bukan plaintext — tapi…**
```bash
# .gitignore sudah benar:
cache/admin_password.txt  # ← di-ignore
```
✅ File tidak akan ke-commit. Tapi jika seseorang melakukan `git add -f cache/admin_password.txt`, hash akan masuk repo. Hash PBKDF2 sulit di-crack tapi tetap sebaiknya ada pre-commit hook yang mencegah ini.

**G-03: Tidak ada `.env.example`:**
```bash
# .gitignore mencantumkan:
.env
*.env
secrets.json
config.local.py
```
File-file ini di-ignore tapi tidak ada contoh/template. Developer baru tidak tahu ENV vars apa yang tersedia. Tidak ada dokumentasi machine-readable untuk:
- `YTGUI_HOST`, `YTGUI_PORT`
- `YTGUI_ADMIN_USER`, `YTGUI_ADMIN_PASS`
- `YT_PLAYER_BASE`, `YT_PLAYER_SOCKET`
- `YT_PLAYER_VOLUME`
- `TRUSTED_PROXY`
- `YTGUI_METRICS_TOKEN`

**G-04: Session tidak di-revoke saat password di-reset:**
```python
# start.py _on_reset_password()
raw_password = secrets.token_urlsafe(12)
hashed_password = hash_password(raw_password)
# Tulis hash baru ke file
# ← TIDAK ada: await db.cleanup_sessions() atau DELETE FROM sessions
```
Setelah password di-reset, semua session token lama masih valid di DB sampai expiry (24 jam). User lama yang session-nya belum expired bisa terus akses.

**G-05: Metrics endpoint — token opsional:**
```python
# server/handlers/http.py
metrics_token = os.environ.get("YTGUI_METRICS_TOKEN")
is_local = client_ip in {"127.0.0.1", "::1", "::ffff:127.0.0.1"}
has_valid_token = metrics_token and request.headers.get("X-Metrics-Token") == metrics_token
if not is_local and not has_valid_token:
    return web.HTTPForbidden()
```
Jika `YTGUI_METRICS_TOKEN` tidak di-set, endpoint `/metrics` **hanya bisa diakses dari localhost**. Ini aman untuk deployment single-machine. Tapi jika app di-expose lewat reverse proxy tanpa X-Forwarded-For stripping, `client_ip` akan selalu jadi IP proxy (lokal) dan metrics terbuka.

---

## 4. BUILD

### Status: ❌ TIDAK ADA sistem build formal

### 4.1 Yang Ada

```bash
# scripts/make_dist.sh (dan make_dist.ps1 untuk Windows)
git archive HEAD -o dist.zip
```

Itu saja. `git archive` menghormati `.gitignore` — DB, log, password, cache tidak masuk ke dist. ✅ Baik untuk prinsipnya.

### 4.2 Yang Tidak Ada

| Komponen | Status | Dampak |
|---|---|---|
| `pyproject.toml` | ❌ | Tidak ada metadata project, tidak bisa `pip install -e .` |
| `setup.py` | ❌ | Tidak bisa di-package sebagai distributable Python package |
| `Makefile` / task runner | ❌ | Tidak ada shorthand untuk dev tasks |
| Dependency locking (`pip-compile`) | ❌ | `requirements.txt` sebagian pin versi, sebagian tidak |
| Virtual env setup automation | ❌ | Developer harus setup manual |
| Asset bundling | ❌ | JS/CSS di `/web/static/` tidak di-minify |
| Version embedding | ❌ | Tidak ada `__version__` di manapun |

### 4.3 Dependency Pinning Analysis

```
# requirements.txt
yt-dlp==2026.3.17          ← EXACT pin ✅ (yt-dlp sering breaking change)
aiosqlite==0.22.1          ← EXACT pin ✅
aiohttp==3.14.1            ← EXACT pin ✅
syncedlyrics==1.0.1        ← EXACT pin ✅
structlog==24.4.0          ← EXACT pin ✅
prometheus_client>=0.20.0  ← RANGE ⚠️ (bisa dapat versi breaking)
opentelemetry-api>=1.25.0  ← RANGE ⚠️
opentelemetry-sdk>=1.25.0  ← RANGE ⚠️

# requirements-dev.txt
pytest>=8.0.0              ← RANGE ⚠️
pytest-asyncio>=0.23.0     ← RANGE ⚠️
pytest-aiohttp>=1.0.5      ← RANGE ⚠️
```

5 dari 10 dependencies menggunakan range (`>=`) tanpa upper bound. Tidak ada `requirements.lock` atau `pip-compile` output. Jika build dilakukan di waktu berbeda, versi bisa berbeda.

**Khusus `yt-dlp==2026.3.17`**: yt-dlp sering update karena YouTube mengubah format extraction. Pin ke versi spesifik mencegah auto-update tapi juga berarti kalau YouTube berubah, app akan broken sampai manual update.

---

## 5. RELEASE

### Status: ❌ TIDAK ADA

**Tidak ada proses release yang terdefinisi:**
- Tidak ada git tags (`v1.0.0`, `v1.2.3`)
- Tidak ada `CHANGELOG` (termasuk tidak ada otomasi seperti conventional commits)
- Tidak ada GitHub Releases
- Tidak ada versioning (`__version__` tidak ditemukan di manapun)
- Tidak ada release notes
- Tidak ada release automation di CI (tidak ada step "on tag push → publish")

**Satu-satunya "release"**: `scripts/make_dist.sh` yang menghasilkan `dist.zip` dari `git archive HEAD`. Output file tidak di-version.

**Dampak praktis**: Untuk personal app ini tidak terlalu masalah — tidak ada user eksternal yang perlu tahu versi. Tapi untuk tracking bug ("versi mana yang ada masalah ini?"), tidak ada cara.

**Rekomendasi minimal:**
```python
# core/__init__.py atau config.py
__version__ = "0.5.0"
```

```yaml
# .github/workflows/release.yml
on:
  push:
    tags: ['v*']
jobs:
  release:
    steps:
      - run: git archive ${{ github.ref_name }} -o dist-${{ github.ref_name }}.zip
      - uses: actions/upload-artifact@v4
```

---

## 6. ROLLBACK

### Status: ❌ TIDAK ADA

**Strategi rollback saat ini**: Manual `git checkout <commit>` + restart.

**Masalah:**

| Skenario | Dampak | Ada Solusi? |
|---|---|---|
| Bug di commit terbaru | Harus `git revert` manual | ❌ |
| DB schema berubah (ALTER TABLE) | Schema sudah ter-apply, tidak bisa di-revert | ❌ KRITIS |
| Config berubah | Harus edit manual | ❌ |
| Dependencies di-upgrade dan breaking | Harus `pip install` versi lama manual | ❌ |

**Schema Rollback — Masalah Paling Serius:**
```python
# cache/db.py
async def init(self):
    # ALTER TABLE tanpa version tracking:
    try:
        await self._conn.execute("ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0")
    except Exception: pass
    try:
        await self._conn.execute("ALTER TABLE artists ADD COLUMN click_count INTEGER DEFAULT 0")
    except Exception: pass
```

SQLite tidak support `DROP COLUMN` di versi lama. Kalau schema berubah di versi baru, rollback ke versi lama akan membuat code tidak match dengan schema yang sudah ter-modify. **Tidak ada down-migration.**

**Rekomendasi minimal:**
```python
# cache/db.py — tambahkan schema versioning
SCHEMA_VERSION = 3

async def _get_schema_version(self) -> int:
    await self._conn.execute("CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)")
    async with self._conn.execute("SELECT value FROM _meta WHERE key='schema_version'") as cur:
        row = await cur.fetchone()
        return int(row[0]) if row else 0

async def _set_schema_version(self, version: int):
    await self._conn.execute(
        "INSERT OR REPLACE INTO _meta (key, value) VALUES ('schema_version', ?)", (str(version),)
    )
    await self._conn.commit()
```

---

## 7. MONITORING

### Status: ⚠️ PARSIAL — Metrics Ada, Backend Tidak Ada

### 7.1 Prometheus Metrics (`core/observability.py`)

```python
COMMAND_COUNT = Counter(
    "ytplayer_commands_total",
    "Total number of commands executed",
    ["command_name", "status"]  # status: "success" | "error"
)

COMMAND_LATENCY = Histogram(
    "ytplayer_command_duration_seconds",
    "Duration of command execution in seconds",
    ["command_name"]
)

EVENT_COUNT = Counter("ytgui_events_total", "Total events published", ["event_type"])

ACTIVE_WEBSOCKETS = Gauge("ytplayer_active_websockets", "Number of active WebSocket connections")
```

**Endpoint**: `GET /metrics` — Prometheus text format ✅

**Yang diekspos:**
- ✅ Command execution count + latency per command
- ✅ Event count per event type
- ✅ Active WebSocket connections
- ✅ Access control (localhost-only atau dengan token)

**Yang TIDAK diekspos:**
- ❌ MPV connection status (connected/disconnected)
- ❌ yt-dlp resolve latency dan error rate
- ❌ Radio queue size
- ❌ Download queue depth dan progress
- ❌ Cache hit rate (stream URL cache)
- ❌ DB query latency
- ❌ Memory usage (psutil ada di log_config tapi tidak diekspos ke Prometheus)
- ❌ Songs played count (ada di `_LOG_STATS.songs_played` tapi tidak ke Prometheus)

### 7.2 OpenTelemetry (`core/observability.py`)

```python
def setup_tracing():
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    return trace.get_tracer("ytplayer.core")

tracer = setup_tracing()
```

**Masalah kritis:**
```python
provider = TracerProvider()
# ← TIDAK ADA SpanProcessor/Exporter yang ditambahkan!
```

`TracerProvider()` tanpa exporter = **semua trace spans dibuang (NoOp)**. Comment di source menyebutkan `BatchSpanProcessor, ConsoleSpanExporter` tapi tidak dipakai. Tracing tidak berfungsi sama sekali. Import opentelemetry-sdk adalah overhead tanpa manfaat.

### 7.3 Health Check (`GET /health`)

```python
async def health_check(request):
    db = request.app["db"]
    db_status = "connected" if db.conn else "disconnected"
    mpv_ok = getattr(getattr(pc, "mpv", None), "is_connected", False)
    mpv_status = "connected" if mpv_ok else "not_started"
    return web.json_response({
        "status": "ok" if db_status == "connected" else "degraded",
        "db": db_status,
        "mpv": mpv_status
    })
```

**Yang dicek:**
- ✅ DB connection (hanya cek `db.conn is not None`, bukan test query)
- ✅ MPV connection (`is_connected` flag)

**Yang tidak dicek:**
- ❌ Network connectivity (`state.is_online` tersedia tapi tidak diekspos)
- ❌ yt-dlp availability (bisa timeout / banned)
- ❌ Disk space untuk cache/mp3
- ❌ Response time (tidak ada latency dalam response)
- ❌ App version

**Masalah**: `db_status = "connected" if db.conn else "disconnected"` — ini hanya cek apakah object ada, bukan apakah DB bisa menerima query. DB bisa "connected" tapi file corrupt.

### 7.4 Status Bar Terminal (`core/log_config.py`)

```python
# Live status bar di terminal:
# [22:15:33] ♫ Never Gonna Give You Up | clients=2 | queue=3 | RAM=145MB | CPU=12%
```

Bagus untuk development/personal use. Tapi:
- Hanya visible saat app berjalan di foreground terminal
- Tidak persisten
- psutil opsional — tanpa psutil, RAM/CPU tidak tampil

---

## 8. LOGGING

### Status: ✅ CUKUP untuk personal use — tapi ada gap

### 8.1 Logging Stack

```
structlog (structured) → custom renderer → stdout (terminal dengan ANSI color)
                                         → logs/app.log (rotating file)
```

**Konfigurasi rotating file (diasumsikan dari `core/log_config.py`):**
- `RotatingFileHandler` diimplementasikan
- Output ke `logs/` directory
- `logs/` di-gitignore ✅

### 8.2 Log Level Usage

| Level | Dipakai? | Contoh |
|---|---|---|
| DEBUG | ✅ | Lyric fetch failed, sponsorblock detail |
| INFO | ✅ | Track connected, database init |
| WARNING | ✅ | MPV reconnect attempt, prefetch fail |
| ERROR | ✅ | MPV not available, download gagal |
| CRITICAL | ❌ | Tidak ada penggunaan CRITICAL |

### 8.3 Yang Baik

- ✅ `structlog` dengan structured logging (key-value pairs)
- ✅ Semua background task exception di-log via `safe_create_task`
- ✅ EventBus handler error tidak silent — di-log sebelum dilanjutkan
- ✅ Command execution error di-log di `CommandBus.execute()`
- ✅ MPV connection/reconnect events di-log
- ✅ WebSocket connect/disconnect di-log dengan count

### 8.4 Gap yang Ditemukan

**L-01: `DiscoverService` swallow semua exception tanpa log:**
```python
# services/discover_service.py
async def get_recent(self, n):
    try:
        ...
    except Exception:  # ← tidak ada logger.error() di sini
        pass           # silent failure
    return tracks
```

**L-02: Tidak ada request logging untuk HTTP endpoints:**
```python
# server/app.py
_l.getLogger('aiohttp.access').setLevel(_l.CRITICAL + 1)  # ← access log di-disable!
runner = web.AppRunner(app, access_log=None)
```
Access log sengaja di-matikan untuk mengurangi noise. Tapi ini berarti tidak ada record kapan `/api/stream/{id}` dipanggil, berapa lama, dari IP mana. Untuk security audit tidak ideal.

**L-03: Log file path:**
```python
# main.py
log_path = BASE_DIR / "ytplayer.log"  # ← root directory
```
Sementara `.gitignore` hanya mengabaikan `logs/`:
```
*.log  # ← ini tangkap ytplayer.log di root ✅
logs/
```
File `.log` di-ignore ✅. Tapi ada dua lokasi logging — `ytplayer.log` di root dan (kemungkinan) `logs/app.log` dari `log_config.py`.

**L-04: Tidak ada log correlation ID:**
Setiap request WebSocket tidak punya unique ID. Jika dua user melakukan operasi bersamaan, log mereka tercampur tanpa cara untuk memfilter per-request. Tidak ada `request_id` atau `correlation_id` di log entries.

**L-05: `scratch/check_db.py` ada di repo:**
```python
# scratch/check_db.py — ini file debug developer
import sqlite3
conn = sqlite3.connect("data/ytgui.db")
rows = conn.execute("SELECT video_id, title, local_path FROM tracks WHERE local_path IS NOT NULL").fetchall()
```
File debug ini harusnya tidak ada di repo production. Tidak ada risiko keamanan langsung tapi menunjukkan kurangnya hygiene untuk deployment.

---

## 9. ALERTING

### Status: ❌ TIDAK ADA

Tidak ada sistem alerting apapun:
- Tidak ada email notification
- Tidak ada Telegram/Discord webhook
- Tidak ada Prometheus AlertManager
- Tidak ada PagerDuty / OpsGenie
- Tidak ada uptime monitoring (UptimeRobot, Better Uptime, dll)

**Konteks**: Untuk personal app di Termux ini bisa acceptable — user adalah developer itu sendiri. Tapi jika app berjalan 24/7 dan dipakai aktif:

| Skenario tanpa alerting | Dampak |
|---|---|
| MPV crash saat malam hari | Musik berhenti, tidak ada yang tahu |
| yt-dlp quota/ban dari YouTube | Semua resolusi gagal, app LOADING terus |
| Disk penuh (cache/mp3) | Download gagal diam-diam |
| Server crash | Tidak ada yang restart otomatis |

**Rekomendasi minimal untuk personal use:**
```bash
# Tambahkan ke crontab di Termux:
# Cek health setiap 5 menit, notif jika down
*/5 * * * * curl -sf http://localhost:8765/health | python3 -c "
import json,sys
d=json.load(sys.stdin)
if d['status']!='ok':
    import subprocess
    subprocess.run(['termux-notification','--title','ytgui DOWN','--content',str(d)])
"
```

---

## 10. BACKUP

### Status: ❌ MINIMAL — Manual Only

### 10.1 Data yang Perlu Dibackup

| Data | Lokasi | Ukuran Estimasi | Kritis? |
|---|---|---|---|
| Main database | `data/ytgui.db` | ~MB | ✅ YES — history, favorites, sessions |
| Artist/song database | `data/library.db` | ~60KB (dari archive) | ✅ YES — seed untuk radio |
| Downloaded MP3s | `cache/mp3/` | ~GB | ⚠️ MEDIUM — bisa re-download |
| User downloads | `downloads/` | ~GB | ✅ YES — user MP3 collection |
| Admin password hash | `cache/admin_password.txt` | bytes | ✅ YES |
| Config | `config.py` + ENV | — | ✅ YES |

### 10.2 Status Backup

**Tidak ada backup otomatis apapun.** Tidak ada:
- Cron job untuk backup DB
- Script backup
- Sinkronisasi ke cloud (rclone, rsync, dll)
- Retention policy untuk backup lama

### 10.3 Risiko Kehilangan Data

```
data/ytgui.db berisi:
  - Semua tracks yang pernah diputar (play_count, last_played)
  - Favorites (is_favorite)
  - Session tokens aktif
  - stream_url cache (TTL 6 jam)

Jika file ini hilang:
  - ❌ Semua riwayat putar hilang
  - ❌ Semua favorites hilang
  - ❌ Cache stream URL hilang (lagu butuh resolve ulang)
  - ✅ Session baru bisa dibuat (tidak fatal)
  - ✅ Artist/song database bisa di-re-import dari data/artists.json
```

### 10.4 WAL Mode dan Backup Consistency

```sql
-- schema.sql
PRAGMA journal_mode=WAL;
```

WAL mode dipakai ✅. Ini berarti backup dengan `cp data/ytgui.db` bisa menghasilkan file inconsistent jika ada transaksi aktif. Backup yang benar harus menggunakan SQLite backup API atau `sqlite3 data/ytgui.db .dump`.

**Rekomendasi backup minimal (sudah ada hook-nya di main.py):**
```python
# main.py — db_cleanup() task sudah ada, tinggal tambah backup:
async def db_cleanup():
    while True:
        await asyncio.sleep(86400)  # sudah ada
        try:
            await db.evict_stale_tracks()
            await db.cleanup_sessions()
            # TAMBAHKAN:
            backup_path = BASE_DIR / "data" / f"ytgui_backup_{int(time.time())}.db"
            async with aiosqlite.connect(backup_path) as backup_conn:
                await db._conn.backup(backup_conn)
            # Keep last 7 backups only
        except Exception as e:
            logger.error(f"DB cleanup/backup failed: {e}")
```

---

## 11. DISASTER RECOVERY

### Status: ❌ TIDAK ADA

### 11.1 Skenario Disaster dan Response

| Skenario | Waktu Recovery Saat Ini | Target | Gap |
|---|---|---|---|
| App crash (python crash) | Manual restart (`./start.sh`) | < 30 detik | Tidak ada auto-restart |
| MPV process crash | Auto-reconnect (3 attempts) lalu stuck | < 5 detik | Reconnect logic ada tapi butuh restart manual jika gagal semua |
| DB corruption | Manual dari backup (tidak ada) | < 5 menit | Tidak ada backup, tidak ada recovery procedure |
| Disk full | App gagal download diam-diam | Immediate alert | Tidak ada monitoring disk |
| `data/ytgui.db` terhapus | Buat ulang dari awal (data hilang) | Restore dari backup | Tidak ada backup |
| `data/library.db` terhapus | Radio mode tidak bisa start | Re-import dari `data/artists.json` | Ada source data-nya ✅ |
| YouTube IP ban / throttle | Semua resolve gagal, LOADING terus | Retry later / VPN | Tidak ada fallback |
| Termux session killed oleh Android | App mati, harus launch manual | Auto-start via Termux:Boot | Tidak ada setup |
| Port sudah dipakai | `start.sh` kill process yang ada → start | < 10 detik | `start.sh` handle ini ✅ |

### 11.2 Auto-Restart

**Tidak ada auto-restart mechanism:**
- Tidak ada `systemd` service file
- Tidak ada Termux:Boot integration
- Tidak ada `supervisor` config
- Tidak ada `pm2` config

**Satu-satunya "recovery"**: `start.py` (GUI) dan `start.sh` menangani port conflict saat *manual* restart.

**Rekomendasi Termux (environment utama):**

**Option A — Termux:Boot (paling mudah):**
```bash
# ~/.termux/boot/start_ytgui.sh
#!/data/data/com.termux/files/usr/bin/bash
cd /data/data/com.termux/files/home/ytgui-main
python main.py >> logs/startup.log 2>&1
```

**Option B — Loop restart di start.sh:**
```bash
# Wrap python main.py dengan restart loop
while true; do
    python main.py
    echo "App exited with code $?. Restarting in 5s..."
    sleep 5
done
```

**Option C — systemd (untuk Linux server):**
```ini
# /etc/systemd/system/ytgui.service
[Unit]
Description=ytgui music player
After=network.target

[Service]
Type=simple
User=bagas
WorkingDirectory=/home/bagas/ytgui-main
ExecStart=/usr/bin/python3 main.py
Restart=on-failure
RestartSec=5
Environment=YTGUI_HOST=0.0.0.0
Environment=YTGUI_PORT=8765

[Install]
WantedBy=multi-user.target
```

### 11.3 Data Recovery Procedure

**Saat ini tidak ada documented procedure.** Jika `data/ytgui.db` hilang:

1. App akan buat DB baru kosong otomatis (`Database.init()`)
2. History dan favorites hilang permanen
3. Artist/song library harus di-re-import:
   ```bash
   python data/export_to_sqlite.py  # re-import dari artists.json
   ```
4. Cache stream URL harus di-rebuild otomatis (6 jam TTL — yt-dlp akan fetch ulang)

---

## 12. RINGKASAN TEMUAN & PRIORITAS

### CRITICAL untuk Personal Use (Segera)

| # | Area | Masalah | Fix |
|---|---|---|---|
| **P-01** | Backup | Tidak ada backup DB otomatis — data favorites/history bisa hilang permanen | Tambah backup harian di `db_cleanup()` |
| **P-02** | Disaster Recovery | Tidak ada auto-restart — kalau app crash saat ditinggal, tidak ada musik | Setup Termux:Boot atau restart loop di `start.sh` |
| **P-03** | Secrets | Password plaintext di-print ke stdout saat first-run | Print ke stderr + hanya tampil jika TTY |
| **P-04** | Secrets | Password reset tidak revoke session lama | Tambah `db.cleanup_sessions()` saat reset |

### HIGH (Perlu Fix)

| # | Area | Masalah |
|---|---|---|
| **H-01** | Monitoring | OpenTelemetry configured tapi tidak ada exporter — tracing NON-FUNCTIONAL, dependency overhead percuma |
| **H-02** | CI | Python 3.10 di CI tapi tidak ada `python_requires` — environment mismatch tidak terdeteksi |
| **H-03** | Rollback | Tidak ada schema versioning/migration — rollback app version bisa break DB |
| **H-04** | Build | `prometheus_client>=0.20.0`, `opentelemetry-api>=1.25.0` tidak di-pin — bisa dapat breaking version |
| **H-05** | Secrets | Tidak ada `.env.example` — 9 ENV vars tidak terdokumentasi machine-readable |

### MEDIUM (Tech Debt)

| # | Area | Masalah |
|---|---|---|
| **M-01** | Monitoring | Health check `/health` tidak test DB query — "connected" bisa false positive |
| **M-02** | Monitoring | Key metrics tidak diekspos: cache hit rate, yt-dlp latency, radio queue size |
| **M-03** | Logging | `DiscoverService` exception swallow tanpa logging |
| **M-04** | Logging | HTTP access log di-disable total — tidak ada request audit trail |
| **M-05** | CI | Tidak ada linting, type check, security scan di pipeline |
| **M-06** | CI | Tidak ada test coverage report |
| **M-07** | Build | Tidak ada version number di manapun (`__version__`) |
| **M-08** | Backup | `cp data/ytgui.db` tidak aman dengan WAL mode — butuh SQLite backup API |
| **M-09** | Repo hygiene | `scratch/check_db.py` file debug ada di repo |
| **M-10** | Monitoring | `STATS.songs_played` di `log_config.py` tidak diekspos ke Prometheus |

### LOW (Improvement)

| # | Area | Masalah |
|---|---|---|
| **L-01** | Release | Tidak ada git tags / versioning |
| **L-02** | Release | `make_dist.sh` output tidak di-version |
| **L-03** | Docker | Tidak ada Dockerfile untuk Linux deployment |
| **L-04** | Alerting | Tidak ada notif jika app down |
| **L-05** | Logging | Tidak ada request correlation ID |
| **L-06** | CI | Tidak ada Windows runner test untuk `start.bat` |

---

## 13. QUICK WINS (Bisa dilakukan hari ini)

### QW-01: Backup DB harian — 10 baris kode

```python
# main.py — tambahkan ke db_cleanup():
async def db_cleanup():
    while True:
        await asyncio.sleep(86400)
        try:
            await db.evict_stale_tracks()
            await db.cleanup_sessions()
            
            # Backup DB
            import aiosqlite
            ts = int(time.time())
            backup_path = BASE_DIR / "data" / f"ytgui_backup_{ts}.db"
            async with aiosqlite.connect(backup_path) as bconn:
                await db._conn.backup(bconn)
            structlog.get_logger(__name__).info(f"DB backup saved: {backup_path}")
            
            # Hapus backup > 7 hari
            for old in sorted((BASE_DIR / "data").glob("ytgui_backup_*.db"))[:-7]:
                old.unlink()
        except Exception as e:
            structlog.get_logger(__name__).error(f"DB cleanup failed: {e}")
```

### QW-02: Auto-restart via start.sh — 3 baris

```bash
# start.sh — ganti baris terakhir:
# python main.py
while true; do
    python main.py
    echo -e "${YELLOW}[!] App exited. Restarting in 5s... (Ctrl+C to stop)${RESET}"
    sleep 5
done
```

### QW-03: Fix password print ke stderr + TTY check

```python
# config.py — ganti print() dengan:
import sys as _sys
if _sys.stderr.isatty():
    _sys.stderr.write(f"\n⚠  Admin password: {raw_password}\n")
    _sys.stderr.write(f"   Tersimpan di: {_password_file}\n\n")
else:
    _sys.stderr.write(f"[YTGUI] Admin password disimpan di: {_password_file}\n")
```

### QW-04: Session revoke saat password reset

```python
# start.py _on_reset_password():
# Setelah tulis password baru:
# Perlu cleanup sessions — tapi start.py tidak punya DB handle
# Solusi: tambah flag file yang dibaca saat start
flag = BASE_DIR / "cache" / ".sessions_invalidated"
flag.touch()

# main.py db_cleanup() atau startup:
if (BASE_DIR / "cache" / ".sessions_invalidated").exists():
    await db.cleanup_sessions()  # DELETE FROM sessions WHERE ...
    (BASE_DIR / "cache" / ".sessions_invalidated").unlink()
```

### QW-05: Fix OpenTelemetry — hapus atau aktifkan

```python
# core/observability.py — opsi A: hapus OTel yang tidak berfungsi
# Cukup pakai Prometheus saja.

# opsi B: aktifkan ConsoleSpanExporter untuk debugging lokal
def setup_tracing():
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    return trace.get_tracer("ytplayer.core")
```

### QW-06: Tambah .env.example

```bash
# .env.example (buat file baru ini)
# ytgui — Environment Variables Reference
# Copy ke .env dan sesuaikan

YTGUI_HOST=0.0.0.0
YTGUI_PORT=8765

# Admin credentials (opsional — jika tidak di-set, password di-generate otomatis)
# YTGUI_ADMIN_USER=admin
# YTGUI_ADMIN_PASS=your_secret_password_here

# Path kustom (opsional)
# YT_PLAYER_BASE=/path/to/ytgui-main
# YT_PLAYER_SOCKET=/path/to/mpv.sock
# YT_PLAYER_VOLUME=80

# Security
# TRUSTED_PROXY=false          # Set true jika di belakang nginx/reverse proxy
# YTGUI_METRICS_TOKEN=secret   # Token untuk akses /metrics dari non-localhost
```

### QW-07: Pin semua dependencies

```
# requirements.txt — ganti range dengan exact:
prometheus_client==0.21.0
opentelemetry-api==1.27.0
opentelemetry-sdk==1.27.0

# requirements-dev.txt
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-aiohttp==1.0.5
```

### QW-08: Tambah versi

```python
# config.py — tambahkan satu baris:
__version__ = "0.5.0"

# main.py startup output — tambahkan:
sys.stderr.write(f"  Version: ytgui v{__version__}\n")
```

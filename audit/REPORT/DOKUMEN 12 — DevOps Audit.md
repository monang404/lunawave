# Lunawave — Laporan Audit DevOps
**Tim Audit:** Senior Software Architect · DevOps Engineer · Security Engineer · Performance Engineer  
**Tanggal:** 2026-07-07  
**Scope:** Docker · CI/CD · Secrets · Build · Release · Rollback · Monitoring · Logging · Alerting · Backup · Disaster Recovery

---

## Ringkasan Eksekutif

Project Lunawave memiliki fondasi DevOps yang **sebagian terbentuk tetapi kritis dalam kelemahan produksi**. CI/CD dasar sudah ada, Docker tersedia, dan logging sudah dikonfigurasi. Namun terdapat **cacat fatal** yang akan menyebabkan kegagalan operasional jika di-deploy ke production: container berjalan sebagai root, Dockerfile mereferensikan file yang tidak ada (`run.py`), backup hanya satu file tanpa rotasi, tidak ada alerting, tidak ada disaster recovery, dan inkonsistensi penamaan env var yang bisa menyebabkan silent misconfiguration.

| Domain | Status | Skor |
|---|---|---|
| Docker | ⚠️ Parsial — cacat kritis | 4/10 |
| CI/CD | ⚠️ Parsial — tidak ada CD | 5/10 |
| Secrets Management | ⚠️ Sedang — naming chaos | 5/10 |
| Build | ✅ Berfungsi dasar | 6/10 |
| Release | ❌ Tidak ada proses formal | 2/10 |
| Rollback | ⚠️ Manual, tidak aman | 3/10 |
| Monitoring | ⚠️ Parsial — Prometheus ada tapi tidak tersambung | 4/10 |
| Logging | ✅ Baik untuk skala kecil | 7/10 |
| Alerting | ❌ Tidak ada sama sekali | 0/10 |
| Backup | ⚠️ Ada tapi berbahaya | 3/10 |
| Disaster Recovery | ❌ Tidak ada rencana | 1/10 |

---

## 1. DOCKER

---

### DEVOPS-001 — Dockerfile Mereferensikan `run.py` yang Tidak Ada
**Severity:** 🔴 KRITIS  
**Dampak:** `docker compose up` akan build sukses tapi container **langsung crash** saat start karena `run.py` tidak ada di repository. Deployment production gagal total.

**Lokasi:** `Dockerfile`, baris 28

**Kode bermasalah:**
```dockerfile
CMD ["python", "run.py"]
```

**Realita di repo:**
```bash
$ ls *.py
config.py  main.py  start.py
# run.py TIDAK ADA
```

**Solusi:**
```dockerfile
CMD ["python", "main.py"]
```

---

### DEVOPS-002 — Container Berjalan Sebagai Root
**Severity:** 🔴 KRITIS  
**Dampak:** Tidak ada direktif `USER` di Dockerfile. Container berjalan sebagai `root` (UID 0). Jika ada RCE melalui yt-dlp atau aiohttp, attacker mendapatkan akses root di container yang bisa digunakan untuk eskalasi ke host. Ini adalah pelanggaran prinsip least-privilege yang fundamental.

**Lokasi:** `Dockerfile` (keseluruhan)

**Solusi:**
```dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends mpv ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Buat user non-root khusus untuk aplikasi
RUN groupadd -r lunawave && useradd -r -g lunawave -m -d /home/lunawave lunawave

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=lunawave:lunawave . .

# Buat direktori yang dibutuhkan dengan ownership yang benar
RUN mkdir -p /app/data /app/cache/mp3 /app/cache/sockets /app/logs \
    && chown -R lunawave:lunawave /app

USER lunawave

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8765/health || exit 1

CMD ["python", "main.py"]
```

---

### DEVOPS-003 — Tidak Ada `HEALTHCHECK` di Dockerfile
**Severity:** 🟡 TINGGI  
**Dampak:** Docker tidak bisa mendeteksi apakah container dalam keadaan sehat atau stuck. `docker ps` akan menampilkan `Up` meskipun server sudah crash secara internal. Orchestrator (Swarm, ECS) tidak bisa melakukan automatic restart berdasarkan health status.

**Lokasi:** `Dockerfile`

**Solusi:** Tambahkan ke Dockerfile (lihat contoh di DEVOPS-002 di atas):
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8765/health || exit 1
```

---

### DEVOPS-004 — Volume Docker Hanya Mount `/app/data`, Cache dan Logs Hilang Saat Restart
**Severity:** 🔴 KRITIS  
**Dampak:** `docker-compose.yml` hanya mount `./data:/app/data`. Direktori berikut tidak di-persist dan **hilang setiap container restart**:
- `cache/mp3/` — file MP3 yang sudah di-download (data berharga, proses download ulang mahal)
- `cache/sockets/` — tidak kritis, tapi socket path perlu konsisten
- `logs/` — log hilang, tidak bisa post-mortem
- `cache/admin_password.txt` — password admin hilang, trigger auto-generate baru setiap restart

**Lokasi:** `docker-compose.yml`

**Kode bermasalah:**
```yaml
volumes:
  - ./data:/app/data   # hanya ini yang di-persist!
```

**Solusi:**
```yaml
services:
  lunawave:
    build: .
    container_name: lunawave
    ports:
      - "127.0.0.1:8765:8765"   # Bind ke localhost, bukan 0.0.0.0
    volumes:
      - lunawave_data:/app/data
      - lunawave_cache:/app/cache
      - lunawave_logs:/app/logs
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
      - LUNAWAVE_ADMIN_PASS=${LUNAWAVE_ADMIN_PASS}
      - LUNAWAVE_METRICS_TOKEN=${LUNAWAVE_METRICS_TOKEN}
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8765/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

volumes:
  lunawave_data:
  lunawave_cache:
  lunawave_logs:
```

---

### DEVOPS-005 — Port Binding ke `0.0.0.0` Tanpa Firewall Layer
**Severity:** 🟡 TINGGI  
**Dampak:** Port `8765` di-bind ke semua interface (`0.0.0.0:8765:8765`). Jika host memiliki public IP, endpoint `/health`, `/metrics`, dan bahkan WebSocket login terbuka ke internet. Untuk aplikasi yang didesain sebagai personal server, ini berisiko.

**Lokasi:** `docker-compose.yml`, baris `ports`

**Solusi:**
```yaml
ports:
  - "127.0.0.1:8765:8765"   # Hanya localhost, akses via reverse proxy
```

Untuk akses publik, gunakan Nginx sebagai reverse proxy dengan TLS.

---

### DEVOPS-006 — Layer Caching Dockerfile Tidak Optimal
**Severity:** 🟢 SEDANG  
**Dampak:** `COPY . .` dilakukan sebelum `npm` build. Setiap perubahan source code (termasuk perubahan Python satu baris) akan invalida seluruh layer termasuk `npm install`. Build lambat.

**Solusi — Optimasi layer order:**
```dockerfile
WORKDIR /app

# Layer 1: Python deps (jarang berubah)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Layer 2: Node deps (jarang berubah)
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Layer 3: Build assets (berubah saat frontend diubah)
COPY web/ ./web/
RUN npm run build

# Layer 4: Application source (sering berubah)
COPY --chown=lunawave:lunawave . .
```

---

## 2. CI/CD

---

### DEVOPS-007 — Tidak Ada Continuous Deployment (CD)
**Severity:** 🟡 TINGGI  
**Dampak:** CI pipeline hanya melakukan test dan lint. Tidak ada otomasi deployment. Release ke production adalah proses manual yang tidak terdokumentasi, berisiko human error.

**Lokasi:** `.github/workflows/ci.yml`

**Solusi — Tambahkan CD job:**
```yaml
# .github/workflows/cd.yml
name: CD

on:
  push:
    tags:
      - 'v*.*.*'   # Trigger saat tag release dibuat

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.ref_name }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

### DEVOPS-008 — Windows CI Job Tidak Menjalankan Tests
**Severity:** 🟡 TINGGI  
**Dampak:** Job `test-windows` di CI hanya mengecek apakah `start.bat` bisa diparsing. Tidak ada unit test yang dijalankan di Windows. Bug yang hanya muncul di Windows (path separator, encoding, win32 subprocess) tidak akan terdeteksi.

**Lokasi:** `.github/workflows/ci.yml`

**Kode bermasalah:**
```yaml
test-windows:
  steps:
    # ... install deps
    - name: Test start.bat syntax
      run: cmd.exe /c "start.bat --help" || exit 0
    # TIDAK ADA pytest di sini!
```

**Solusi:**
```yaml
test-windows:
  runs-on: windows-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"
        cache: 'pip'
    - run: pip install -r requirements.txt -r requirements-dev.txt
    - name: Run tests on Windows
      run: pytest tests/ -v --ignore=tests/integration -k "not slow"
      # Exclude integration tests yang butuh MPV
```

---

### DEVOPS-009 — CI Coverage Threshold Terlalu Rendah (40%)
**Severity:** 🟢 SEDANG  
**Dampak:** `--cov-fail-under=40` adalah threshold yang sangat rendah untuk production code. Ini memberikan false sense of security — CI hijau meskipun 60% kode tidak diuji.

**Lokasi:** `.github/workflows/ci.yml`, baris 41

**Kode bermasalah:**
```yaml
run: pytest tests/ -v --cov=. --cov-report=term-missing --cov-fail-under=40
```

**Solusi — Naikkan bertahap:**
```yaml
# Fase 1 (sekarang): 40% → 50%
# Fase 2 (+1 sprint): 50% → 60%
# Fase 3 (+2 sprint): 60% → 75%
# Target production: 80%
run: pytest tests/ -v --cov=core --cov=engine --cov=cache --cov=server --cov=plugins \
     --cov-report=term-missing --cov-report=html --cov-fail-under=50
```

---

### DEVOPS-010 — Tidak Ada CI Job untuk Frontend JavaScript
**Severity:** 🟡 TINGGI  
**Dampak:** `package.json` mendefinisikan `"test": "echo \"Error: no test specified\" && exit 1"`. CI tidak pernah menjalankan JS lint atau test. Bug JavaScript tidak akan terdeteksi di CI.

**Lokasi:** `.github/workflows/ci.yml`, `package.json`

**Solusi — Tambahkan frontend CI:**
```yaml
# Tambahkan ke ci.yml
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm run build        # Pastikan bundle build berhasil
      - run: npm test             # Setelah Vitest di-setup
      - run: npx eslint web/static/js/  # Lint JS
```

---

### DEVOPS-011 — Tidak Ada Artifact Pinning / Reproducible Build
**Severity:** 🟢 SEDANG  
**Dampak:** CI menggunakan `actions/checkout@v4` tanpa SHA pinning. Jika action di-hijack (supply chain attack), CI bisa disusupi. Untuk production, pin ke SHA spesifik.

**Solusi:**
```yaml
# Ganti:
- uses: actions/checkout@v4

# Dengan SHA-pinned:
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

---

## 3. SECRETS MANAGEMENT

---

### DEVOPS-012 — Inkonsistensi Prefix Environment Variable (3 Skema Berbeda)
**Severity:** 🔴 KRITIS  
**Dampak:** Project menggunakan **tiga prefix berbeda** secara bersamaan untuk env var yang saling terkait:
- `YTGUI_*` — dipakai di `start.sh`, `start.bat`, `.env.example`
- `LUNAWAVE_*` — dipakai di `config.py` (untuk HOST, PORT, ADMIN_PASS)
- `YT_PLAYER_*` — dipakai di `config.py` (untuk BASE, SOCKET, VOLUME)
- `LunaWave_PORT` (mixed-case!) — di `start.py`

Seorang operator yang membaca `.env.example` dan mengatur `YTGUI_ADMIN_PASS` tidak akan berhasil karena `config.py` membaca `LUNAWAVE_ADMIN_PASS`. **Password tidak akan terbaca, app menggunakan auto-generated password tanpa tahu mengapa.**

**Lokasi:** `config.py`, `.env.example`, `start.sh`, `start.py`

**Bukti inkonsistensi:**
```bash
# .env.example mengajarkan user:
YTGUI_ADMIN_PASS=your_password       # ← prefix YTGUI

# config.py membaca:
os.environ.get("LUNAWAVE_ADMIN_PASS")  # ← prefix LUNAWAVE (TIDAK TERBACA!)
```

**Solusi — Standarisasi ke `LUNAWAVE_`:**
```python
# config.py — unified constants
WEB_HOST    = os.environ.get("LUNAWAVE_HOST",         "0.0.0.0")
WEB_PORT    = int(os.environ.get("LUNAWAVE_PORT",     8765))
ADMIN_USER  = os.environ.get("LUNAWAVE_ADMIN_USER",   "admin")
BASE_DIR    = Path(os.environ.get("LUNAWAVE_BASE_DIR", Path(__file__).parent))
MPV_SOCKET  = os.environ.get("LUNAWAVE_MPV_SOCKET",   ...)
DEFAULT_VOL = int(os.environ.get("LUNAWAVE_VOLUME",   80))
```

```bash
# .env.example — setelah unifikasi
LUNAWAVE_HOST=0.0.0.0
LUNAWAVE_PORT=8765
LUNAWAVE_ADMIN_USER=admin
LUNAWAVE_ADMIN_PASS=your_secret_password
LUNAWAVE_BASE_DIR=.
LUNAWAVE_MPV_SOCKET=/tmp/lunawave-mpv.sock
LUNAWAVE_VOLUME=80
LUNAWAVE_METRICS_TOKEN=your_metrics_secret
```

---

### DEVOPS-013 — `admin_password.txt` Disimpan dalam Plaintext Hash Tanpa Enkripsi Tambahan
**Severity:** 🟡 TINGGI  
**Dampak:** `cache/admin_password.txt` menyimpan PBKDF2 hash. Jika seseorang mendapat akses read ke file system (misalnya path traversal atau backup exposure), mereka bisa melakukan offline dictionary attack terhadap hash tersebut. File ini juga dalam direktori `cache/` yang mungkin ter-expose jika backup dikonfigurasi salah.

**Lokasi:** `config.py`, baris 66–69

**Catatan:** File sudah di-chmod 600 (baik), tapi path-nya di dalam `cache/` yang bersebelahan dengan MP3 files.

**Solusi — Pindahkan ke direktori terpisah dengan permission lebih ketat:**
```python
# Simpan di luar cache/ directory
_password_file = BASE_DIR / ".secrets" / "admin_password_hash"
_password_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
# chmod 600 seperti sebelumnya
```

---

### DEVOPS-014 — `docker-compose.yml` Tidak Meneruskan Secrets dari Environment
**Severity:** 🟡 TINGGI  
**Dampak:** `docker-compose.yml` hanya meneruskan `PYTHONUNBUFFERED=1`. Variabel seperti `LUNAWAVE_ADMIN_PASS` dan `LUNAWAVE_METRICS_TOKEN` tidak diteruskan ke container. Container akan selalu menggunakan auto-generated password, yang artinya password baru setiap restart container (jika volume cache tidak di-mount — lihat DEVOPS-004).

**Lokasi:** `docker-compose.yml`

**Kode bermasalah:**
```yaml
environment:
  - PYTHONUNBUFFERED=1
  # LUNAWAVE_ADMIN_PASS tidak ada!
```

**Solusi:**
```yaml
environment:
  - PYTHONUNBUFFERED=1
  - LUNAWAVE_ADMIN_PASS=${LUNAWAVE_ADMIN_PASS:-}
  - LUNAWAVE_METRICS_TOKEN=${LUNAWAVE_METRICS_TOKEN:-}
  - LUNAWAVE_HOST=0.0.0.0
  - LUNAWAVE_PORT=8765
env_file:
  - .env   # Load dari file .env jika ada
```

---

### DEVOPS-015 — Password Admin Tercetak ke `stderr` di TTY
**Severity:** 🟡 TINGGI  
**Dampak:** Saat auto-generate password pertama kali, password raw (sebelum di-hash) ditulis ke `sys.stderr`. Jika stderr di-redirect ke log file (seperti di `termux_boot.sh`: `./start.sh >> logs/startup.log 2>&1`), password plaintext masuk ke log file. Log file tidak selalu di-protect dengan baik.

**Lokasi:** `config.py`, baris 76–79

**Kode bermasalah:**
```python
if sys.stderr.isatty():
    sys.stderr.write(f"PASSWORD ADMIN GENERATED: {raw_password}\n")
```

**Masalah:** `termux_boot.sh` melakukan `2>&1`, yang berarti stderr di-redirect ke stdout, lalu ke log file. `isatty()` akan return `False` dalam kasus ini, sehingga password tidak dicetak. Namun jika ada kasus lain di mana TTY terdeteksi tapi output masih di-log, password bocor.

**Solusi — Tulis ke file terpisah yang aman, bukan ke stderr:**
```python
# Tulis ke file one-time credentials, bukan stderr
_first_run_hint = BASE_DIR / ".secrets" / "FIRST_RUN_PASSWORD.txt"
with open(_first_run_hint, "w", encoding="utf-8") as f:
    f.write(f"Password pertama Lunawave: {raw_password}\n")
    f.write("Hapus file ini setelah login pertama.\n")
_first_run_hint.chmod(0o600)

# Tampilkan HANYA path file, bukan password-nya
sys.stderr.write(f"[LUNAWAVE] Password tersimpan di: {_first_run_hint}\n")
```

---

## 4. BUILD

---

### DEVOPS-016 — JS Bundle Tidak Di-build dalam Docker Image
**Severity:** 🔴 KRITIS  
**Dampak:** `Dockerfile` tidak menjalankan `npm run build`. Jika `web/static/js/bundle.js` tidak ada di repo (karena `.gitignore` seharusnya mengabaikan build artifacts), container akan serve halaman tanpa JavaScript yang ter-bundle. App tidak akan berfungsi.

**Lokasi:** `Dockerfile`

**Verifikasi:**
```bash
# bundle.js ada di repo atau tidak?
# Jika bundle.js di-gitignore, container akan serve blank app
```

**Solusi:**
```dockerfile
# Tambahkan ke Dockerfile sebelum COPY . .
COPY package.json package-lock.json ./
RUN npm ci --only=production

COPY web/ ./web/
RUN npm run build   # Generate bundle.js dan bundle.css

COPY --chown=lunawave:lunawave . .
```

---

### DEVOPS-017 — `requirements.txt` dan `pyproject.toml` Tidak Sinkron
**Severity:** 🟡 TINGGI  
**Dampak:** `pyproject.toml` mendefinisikan dependencies project, dan `requirements.txt` adalah file terpisah. Tidak ada mekanisme untuk memastikan keduanya sinkron. Versi bisa berbeda, menyebabkan environment yang inconsistent antara `pip install -r requirements.txt` (untuk Docker) dan `pip install -e .` (untuk dev).

**Lokasi:** `requirements.txt`, `pyproject.toml`

**Solusi — Gunakan satu sumber kebenaran:**
```toml
# pyproject.toml adalah sumber utama
# requirements.txt di-generate dari pyproject.toml:
# pip-compile pyproject.toml -o requirements.txt

# Atau gunakan uv:
# uv pip compile pyproject.toml -o requirements.txt
```

Tambahkan ke CI:
```yaml
- name: Check requirements.txt is up to date
  run: |
    pip-compile pyproject.toml -o requirements.check.txt
    diff requirements.txt requirements.check.txt || \
      (echo "requirements.txt tidak sync dengan pyproject.toml!" && exit 1)
```

---

### DEVOPS-018 — `make_dist.sh` Menggunakan `git archive` Tanpa Verifikasi Integritas
**Severity:** 🟢 SEDANG  
**Dampak:** `scripts/make_dist.sh` membuat `dist.zip` via `git archive HEAD`. Tidak ada:
- Checksum (SHA256) untuk verifikasi integritas
- Version tagging otomatis
- Verifikasi bahwa bundle.js sudah ter-build sebelum packaging

**Solusi:**
```bash
#!/bin/bash
set -euo pipefail

VERSION=$(git describe --tags --always --dirty)
OUTPUT="dist/lunawave-${VERSION}.zip"

mkdir -p dist

# Pastikan JS sudah di-build
npm run build

# Package
git archive HEAD -o "$OUTPUT"

# Tambahkan bundle.js (tidak di-track git tapi diperlukan runtime)
zip -u "$OUTPUT" web/static/js/bundle.js web/static/css/bundle.css

# Generate checksum
sha256sum "$OUTPUT" > "${OUTPUT}.sha256"
echo "Distributable: $OUTPUT"
echo "SHA256: $(cat ${OUTPUT}.sha256)"
```

---

## 5. RELEASE

---

### DEVOPS-019 — Tidak Ada Proses Release Formal
**Severity:** 🟡 TINGGI  
**Dampak:** Tidak ada `CHANGELOG.md`, tidak ada release tagging convention, tidak ada GitHub Releases. Versi di `main.py` adalah hardcoded `__version__ = "1.0.0"` dan tidak terhubung ke `pyproject.toml` yang memiliki `version = "0.1.0"` (inkonsisten!).

**Lokasi:** `main.py` baris 1, `pyproject.toml`

**Inkonsistensi versi:**
```python
# main.py
__version__ = "1.0.0"

# pyproject.toml
version = "0.1.0"
```

**Solusi — Single source of truth untuk versi:**
```toml
# pyproject.toml
[project]
version = "0.1.0"

[tool.setuptools.dynamic]
version = {attr = "lunawave.__version__"}
```

```bash
# scripts/release.sh
#!/bin/bash
VERSION=$1
git tag -s "v${VERSION}" -m "Release v${VERSION}"
git push origin "v${VERSION}"
# CD pipeline otomatis build dan push Docker image
```

---

## 6. ROLLBACK

---

### DEVOPS-020 — Rollback via `git checkout` Berbahaya di Environment Produksi
**Severity:** 🔴 KRITIS  
**Dampak:** `scripts/rollback.sh` menggunakan `git checkout <target>` untuk rollback. Ini sangat berbahaya:
1. `git checkout` pada working tree yang kotor bisa gagal atau corrupt
2. Tidak ada stop server sebelum rollback — database bisa corrupt jika server masih berjalan saat kode diubah
3. Tidak ada rollback untuk **skema database** — hanya ada comment "you may need to manually revert DB schema"
4. Tidak ada verifikasi bahwa rollback berhasil
5. `git checkout` bisa meninggalkan detached HEAD state

**Lokasi:** `scripts/rollback.sh`

**Kode bermasalah:**
```bash
echo "Rolling back to $TARGET..."
git checkout "$TARGET"   # ← Tidak stop server dulu!
# Tidak ada DB migration rollback
# Tidak ada health check setelah rollback
```

**Solusi — Rollback yang aman berbasis Docker image:**
```bash
#!/bin/bash
# rollback.sh — Production-safe rollback
set -euo pipefail

TARGET_VERSION=$1
BACKUP_DIR="backups/rollback_$(date +%Y%m%d_%H%M%S)"

echo "[1/5] Membuat backup state saat ini..."
mkdir -p "$BACKUP_DIR"
docker exec lunawave python -c "
from cache.db import Database; import asyncio
db = Database(); asyncio.run(db.init())
asyncio.run(db.backup('$BACKUP_DIR/pre_rollback.db'))
" || echo "WARN: DB backup gagal, lanjut dengan caution"

echo "[2/5] Menghentikan container..."
docker compose stop lunawave

echo "[3/5] Tarik image versi target..."
docker pull "ghcr.io/monang404/lunawave:$TARGET_VERSION"

echo "[4/5] Update compose ke versi target..."
LUNAWAVE_IMAGE="ghcr.io/monang404/lunawave:$TARGET_VERSION" \
  docker compose up -d lunawave

echo "[5/5] Verifikasi health..."
sleep 10
STATUS=$(curl -sf http://localhost:8765/health | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
if [ "$STATUS" = "ok" ]; then
    echo "✅ Rollback ke $TARGET_VERSION berhasil"
else
    echo "❌ Rollback GAGAL. Status: $STATUS"
    echo "Jalankan: docker compose logs lunawave"
    exit 1
fi
```

---

### DEVOPS-021 — Tidak Ada Database Migration Framework
**Severity:** 🟡 TINGGI  
**Dampak:** Skema DB diubah dengan `ALTER TABLE` di `db.init()` secara ad-hoc. Tidak ada versioning migrasi (Alembic, flyway, dll). Rollback ke versi lama bisa menyebabkan skema tidak kompatibel dengan kode lama.

**Contoh masalah nyata:**
```python
# db.py — migrasi ad-hoc tanpa versioning
await add_column_if_not_exists("tracks", "is_favorite", "INTEGER DEFAULT 0")
await add_column_if_not_exists("artists", "click_count", "INTEGER DEFAULT 0")
```

**Solusi minimal — Version tracking di DB:**
```sql
-- schema.sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER DEFAULT (strftime('%s', 'now'))
);
```

```python
# db.py
MIGRATIONS = [
    (1, "ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0"),
    (2, "ALTER TABLE artists ADD COLUMN click_count INTEGER DEFAULT 0"),
    (3, "CREATE INDEX idx_favorites ON tracks(is_favorite) WHERE is_favorite=1"),
]

async def _run_migrations(self):
    async with self._conn.execute(
        "SELECT MAX(version) as v FROM schema_migrations"
    ) as cursor:
        row = await cursor.fetchone()
        current = row["v"] or 0

    for version, sql in MIGRATIONS:
        if version > current:
            await self._conn.execute(sql)
            await self._conn.execute(
                "INSERT INTO schema_migrations(version) VALUES (?)", (version,)
            )
    await self._conn.commit()
```

---

## 7. MONITORING

---

### DEVOPS-022 — Prometheus Metrics Ada Tapi Tidak Terhubung ke Sistem Monitoring
**Severity:** 🟡 TINGGI  
**Dampak:** `core/observability.py` mendefinisikan Counter, Gauge, dan Histogram Prometheus. Endpoint `/metrics` tersedia. Namun tidak ada `prometheus.yml`, tidak ada Grafana, tidak ada Alertmanager. Metrics ada tapi tidak ada yang membacanya — monitoring theater.

**Lokasi:** `docker-compose.yml`, `core/observability.py`

**Solusi — Tambahkan monitoring stack ke docker-compose:**
```yaml
# docker-compose.monitoring.yml (opsional, jalankan terpisah)
services:
  prometheus:
    image: prom/prometheus:v2.51.0
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
    ports:
      - "127.0.0.1:9090:9090"

  grafana:
    image: grafana/grafana:10.4.0
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    ports:
      - "127.0.0.1:3000:3000"

volumes:
  prometheus_data:
  grafana_data:
```

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'lunawave'
    static_configs:
      - targets: ['lunawave:8765']
    metrics_path: '/metrics'
    bearer_token: '${LUNAWAVE_METRICS_TOKEN}'
```

---

### DEVOPS-023 — Metrics yang Terdefinisi Tidak Mencukupi untuk Production Monitoring
**Severity:** 🟢 SEDANG  
**Dampak:** Hanya ada 4 metric: `ytplayer_commands_total`, `ytplayer_command_duration_seconds`, `ytgui_events_total`, `ytplayer_active_websockets`. Tidak ada metric untuk:
- Error rate
- Playback failure rate
- DB query latency
- YtDlp resolve latency
- Radio mode health
- Memory usage per komponen

**Lokasi:** `core/observability.py`

**Solusi:**
```python
# core/observability.py — tambahkan metrics penting
from prometheus_client import Counter, Gauge, Histogram, Summary

# Existing
COMMAND_COUNT = Counter("ytplayer_commands_total", "...", ["command_name", "status"])
COMMAND_LATENCY = Histogram("ytplayer_command_duration_seconds", "...", ["command_name"])
EVENT_COUNT = Counter("ytgui_events_total", "...", ["event_type"])
ACTIVE_WEBSOCKETS = Gauge("ytplayer_active_websockets", "...")

# TAMBAHAN — critical untuk production
PLAYBACK_ERRORS = Counter(
    "ytplayer_playback_errors_total",
    "Total playback failures",
    ["error_type"]  # ytdlp_timeout, mpv_disconnect, stream_expired
)

YTDLP_RESOLVE_LATENCY = Histogram(
    "ytplayer_ytdlp_resolve_duration_seconds",
    "Time to resolve stream URL via yt-dlp",
    buckets=[1, 5, 10, 20, 30, 60]
)

DB_QUERY_LATENCY = Histogram(
    "ytplayer_db_query_duration_seconds",
    "Database query duration",
    ["operation"]  # upsert, get, backup, cleanup
)

TRACKS_IN_CACHE = Gauge("ytplayer_tracks_cached_total", "Total tracks in DB cache")
ACTIVE_DOWNLOADS = Gauge("ytplayer_active_downloads", "Number of ongoing downloads")
MPV_CONNECTED = Gauge("ytplayer_mpv_connected", "1 if MPV is connected, 0 otherwise")
RADIO_MODE_ACTIVE = Gauge("ytplayer_radio_mode_active", "1 if radio mode is running")
```

---

## 8. LOGGING

---

### DEVOPS-024 — Log Hanya ke File Lokal, Tidak Ada Centralized Logging
**Severity:** 🟡 TINGGI  
**Dampak:** Log ditulis ke `logs/app.log` dengan RotatingFileHandler (5MB × 3 backup = max 20MB). Untuk production multi-instance atau container environment:
- Log hilang saat container restart jika volume tidak di-mount
- Tidak ada cara aggregate log dari multiple instances
- Tidak ada structured log shipping ke ELK/Loki

**Lokasi:** `core/log_config.py`

**Solusi — Tambahkan JSON handler untuk container environment:**
```python
# core/log_config.py
def setup_logging():
    import structlog

    is_container = os.environ.get("LUNAWAVE_CONTAINER", "").lower() == "true"

    if is_container:
        # Container: JSON ke stdout (di-collect oleh Docker logging driver)
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),   # JSON untuk Loki/ELK
            ],
            logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        )
    else:
        # Local: compact ANSI + rotating file (existing behavior)
        # ... existing setup ...
```

---

### DEVOPS-025 — Log File Tidak Di-mount di Docker Container
**Severity:** 🟡 TINGGI  
**Dampak:** Sesuai temuan DEVOPS-004, `logs/` tidak di-mount sebagai volume. Saat container restart, seluruh riwayat log hilang. Tidak bisa melakukan post-mortem analysis setelah crash.

**Solusi:** Sudah tercakup dalam DEVOPS-004 (mount `lunawave_logs:/app/logs`).

---

### DEVOPS-026 — Structlog Tidak Menyertakan Correlation ID / Request ID
**Severity:** 🟢 SEDANG  
**Dampak:** Log tidak memiliki correlation ID. Saat ada error, tidak bisa trace log dari satu request/WebSocket session ke seluruh pipeline (WS handler → command bus → engine → MPV). Debugging sangat sulit.

**Solusi:**
```python
# server/middleware.py — tambahkan request ID
import uuid
import structlog

async def request_id_middleware(app, handler):
    async def middleware(request):
        request_id = str(uuid.uuid4())[:8]
        # Bind ke structlog context untuk request ini
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await handler(request)
        response.headers["X-Request-ID"] = request_id
        structlog.contextvars.unbind_contextvars("request_id")
        return response
    return middleware
```

---

## 9. ALERTING

---

### DEVOPS-027 — Tidak Ada Sistem Alerting Sama Sekali
**Severity:** 🔴 KRITIS  
**Dampak:** Seluruh sistem tidak memiliki alerting. Jika server crash, MPV disconnect, DB korup, atau memory leak terjadi di malam hari, tidak ada notifikasi. Operator hanya bisa tahu dari `monitor_health.sh` yang harus dijalankan secara manual atau via cron.

**Yang ada hanyalah:**
- `scripts/monitor_health.sh` — script manual/cron, hanya cek `/health`
- `termux-notification` — hanya berfungsi jika device tidak sleep

**Solusi 1 — Alerting via Prometheus Alertmanager:**
```yaml
# monitoring/alerting_rules.yml
groups:
  - name: lunawave
    rules:
      - alert: LunawaveDown
        expr: up{job="lunawave"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Lunawave server down"

      - alert: HighPlaybackErrorRate
        expr: rate(ytplayer_playback_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Playback error rate tinggi: {{ $value | humanize }} errors/sec"

      - alert: MPVDisconnected
        expr: ytplayer_mpv_connected == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "MPV terputus selama > 2 menit"
```

**Solusi 2 — Alerting sederhana untuk Termux/self-hosted:**
```python
# plugins/alerting.py — minimal alerting via webhook
import aiohttp
import structlog

class AlertManager:
    def __init__(self, webhook_url: str | None):
        self._webhook_url = webhook_url

    async def send(self, title: str, message: str, level: str = "warning"):
        if not self._webhook_url:
            return
        payload = {
            "content": f"**[{level.upper()}] {title}**\n{message}"
        }
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self._webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=5))
        except Exception as e:
            structlog.get_logger(__name__).error(f"Alert failed to send: {e}")
```

```bash
# .env
LUNAWAVE_ALERT_WEBHOOK=https://discord.com/api/webhooks/xxx/yyy
# atau Slack: https://hooks.slack.com/services/xxx
# atau Telegram bot API
```

---

### DEVOPS-028 — `monitor_health.sh` Tidak Memeriksa MPV Status
**Severity:** 🟡 TINGGI  
**Dampak:** `monitor_health.sh` hanya mengecek apakah `/health` dapat dijangkau dan `status == "ok"`. Namun `/health` mengembalikan `"ok"` bahkan jika MPV disconnect (`mpv: "not_started"`). Kondisi degraded (DB connected tapi MPV mati) tidak terdeteksi.

**Lokasi:** `scripts/monitor_health.sh`

**Kode bermasalah:**
```bash
STATUS=$(echo "$RES" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))")
if [ "$STATUS" != "ok" ]; then  # ← "ok" bahkan saat MPV mati!
```

**Solusi:**
```bash
#!/bin/bash
PORT=${LUNAWAVE_PORT:-8765}
RES=$(curl -sf "http://localhost:$PORT/health") || {
    send_alert "LUNAWAVE DOWN" "Server tidak dapat dijangkau"
    exit 1
}

STATUS=$(echo "$RES" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('status',''))")
MPV=$(echo "$RES" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('mpv',''))")
DB=$(echo "$RES" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('db',''))")

[ "$DB" != "connected" ] && send_alert "LUNAWAVE DEGRADED" "Database disconnected"
[ "$MPV" = "not_started" ] && send_alert "LUNAWAVE DEGRADED" "MPV tidak terhubung"
[ "$STATUS" != "ok" ] && send_alert "LUNAWAVE DEGRADED" "Status: $STATUS"
echo "[+] Health OK: db=$DB mpv=$MPV"
```

---

## 10. BACKUP

---

### DEVOPS-029 — Backup Database Hanya Satu File `.bak` (Overwrite Setiap 24 Jam)
**Severity:** 🔴 KRITIS  
**Dampak:** `core/background_tasks.py` membuat backup ke `lunawave.db.bak` setiap 24 jam. File ini **selalu di-overwrite**, tidak ada rotasi. Jika corruption terjadi tepat sebelum backup run berikutnya, backup `.bak` sudah corrupt juga karena sudah overwrite yang lama.

**Lokasi:** `core/background_tasks.py`, baris 32

**Kode bermasalah:**
```python
await db.backup(Path(str(DB_PATH) + ".bak"))  # Selalu overwrite file yang sama!
```

**Solusi — Rotasi backup dengan timestamp:**
```python
async def _db_cleanup(db):
    while True:
        await asyncio.sleep(86400)
        try:
            from config import DB_PATH, BASE_DIR
            backup_dir = BASE_DIR / "backups" / "db"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup dengan timestamp
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"lunawave_{ts}.db"
            await db.backup(backup_path)
            logger.info("Database backed up", path=str(backup_path))

            # Pertahankan hanya 7 backup terakhir
            backups = sorted(backup_dir.glob("lunawave_*.db"), key=lambda p: p.stat().st_mtime)
            for old_backup in backups[:-7]:
                old_backup.unlink()
                logger.info("Old backup removed", path=str(old_backup))

            await db.evict_stale_tracks()
            await db.cleanup_sessions()
        except Exception as e:
            logger.error(f"DB backup/cleanup failed: {e}")
```

---

### DEVOPS-030 — Tidak Ada Backup untuk File MP3 Download
**Severity:** 🟡 TINGGI  
**Dampak:** File MP3 yang sudah di-download ke `cache/mp3/` tidak di-backup. Jika disk failure atau container volume corrupt, semua MP3 yang pernah di-download hilang. Re-download dari YouTube memerlukan waktu dan bandwidth.

**Solusi — Tambahkan backup MP3 ke external storage (opsional untuk personal server):**
```python
# Minimal: tambahkan manifest file yang bisa dipakai untuk re-download
async def _backup_download_manifest(db, base_dir):
    """Generate manifest semua track yang punya local_path."""
    manifest_path = base_dir / "backups" / "download_manifest.json"
    tracks = await db.get_all_downloaded_tracks()
    manifest = [{"video_id": t.video_id, "title": t.title} for t in tracks]
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
```

---

### DEVOPS-031 — Backup Tidak Diverifikasi Setelah Dibuat
**Severity:** 🟡 TINGGI  
**Dampak:** `db.backup()` menggunakan SQLite's backup API yang biasanya reliable, tapi tidak ada verifikasi bahwa backup file valid dan tidak corrupt setelah dibuat.

**Solusi:**
```python
async def backup(self, backup_path):
    """Creates a verified backup of the database."""
    if not self._conn:
        return

    async with aiosqlite.connect(backup_path) as dest:
        await self._conn.backup(dest)

    # Verifikasi integritas backup
    async with aiosqlite.connect(backup_path) as verify_conn:
        async with verify_conn.execute("PRAGMA integrity_check") as cursor:
            result = await cursor.fetchone()
            if result[0] != "ok":
                raise RuntimeError(f"Backup integrity check failed: {result[0]}")

    logger.info("Database backup verified", path=str(backup_path))
```

---

## 11. DISASTER RECOVERY

---

### DEVOPS-032 — Tidak Ada Rencana Disaster Recovery
**Severity:** 🔴 KRITIS  
**Dampak:** Tidak ada dokumentasi tentang:
- RTO (Recovery Time Objective) — berapa lama sistem boleh down?
- RPO (Recovery Point Objective) — berapa data yang boleh hilang?
- Prosedur recovery saat disk failure
- Prosedur recovery saat database corrupt
- Prosedur recovery saat server di-compromise

**Solusi — Dokumentasikan minimal DR playbook:**
```markdown
# DISASTER_RECOVERY.md

## Skenario 1: Server Crash / Restart Normal
RTO: < 30 detik (restart: unless-stopped)
RPO: 0 (tidak ada data loss)
Prosedur: Otomatis via Docker restart policy

## Skenario 2: Database Corrupt
RTO: < 5 menit
RPO: Max 24 jam (interval backup)
Prosedur:
1. `docker compose stop lunawave`
2. `ls backups/db/` — pilih backup terakhir yang valid
3. `cp backups/db/lunawave_YYYYMMDD_HHMMSS.db data/lunawave.db`
4. `docker compose up -d lunawave`
5. Verifikasi: `curl http://localhost:8765/health`

## Skenario 3: Disk Penuh
Prosedur:
1. `find cache/mp3/ -name "*.mp3" -mtime +30 -delete`
2. `docker compose restart lunawave`

## Skenario 4: Container Image Corrupt
Prosedur:
1. `docker compose pull lunawave`  # atau pull versi sebelumnya
2. `docker compose up -d lunawave`
```

---

### DEVOPS-033 — Termux Boot Script Tidak Menangani Kegagalan Startup
**Severity:** 🟡 TINGGI  
**Dampak:** `scripts/termux_boot.sh` menjalankan `./start.sh >> logs/startup.log 2>&1 &` tanpa memeriksa apakah startup berhasil. Jika server gagal start (misalnya karena Python dependency hilang setelah update), script tetap exit 0 dan tidak ada notifikasi.

**Lokasi:** `scripts/termux_boot.sh`

**Kode bermasalah:**
```bash
termux-wake-lock
cd ~/ytgui-main || cd ~/ytgui-project || exit
./start.sh >> logs/startup.log 2>&1 &  # ← background, tidak ada health check!
```

**Solusi:**
```bash
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock

cd ~/lunawave-main || {
    termux-notification --title "LunaWave Boot Fail" --content "Directory tidak ditemukan"
    exit 1
}

mkdir -p logs
./start.sh >> logs/startup.log 2>&1 &
SERVER_PID=$!

# Tunggu server ready (max 30 detik)
for i in $(seq 1 30); do
    sleep 1
    if curl -sf http://localhost:8765/health > /dev/null 2>&1; then
        termux-notification --title "LunaWave" --content "Server started (PID $SERVER_PID)"
        exit 0
    fi
done

termux-notification --title "LunaWave Boot Fail" --content "Server tidak ready setelah 30 detik. Cek logs/startup.log"
exit 1
```

---

## 12. Temuan Tambahan

---

### DEVOPS-034 — `opentelemetry` Disebut di Dependency Check Tapi Tidak di requirements.txt
**Severity:** 🟡 TINGGI  
**Dampak:** `start.sh` dan `start.bat` memeriksa `import opentelemetry` sebagai dependency yang dibutuhkan, tapi `requirements.txt` dan `pyproject.toml` tidak mencantumkannya. Dependency check menunjukkan "missing" padahal sebenarnya tidak dibutuhkan (atau sebaliknya, dibutuhkan tapi tidak akan ter-install).

**Lokasi:** `start.sh` (baris `DEPS="... opentelemetry"`), `requirements.txt`

**Solusi:** Hapus `opentelemetry` dari dependency check di `start.sh` jika memang tidak digunakan, atau tambahkan ke `requirements.txt` jika digunakan.

---

### DEVOPS-035 — `/tmp` Socket Path di `.env.example` Berbahaya di Shared Environment
**Severity:** 🟢 SEDANG  
**Dampak:** `.env.example` menganjurkan `YT_PLAYER_SOCKET=/tmp/mpv-ytgui.sock`. Pada sistem multi-user atau container tanpa namespace isolasi, file di `/tmp` bisa diakses user lain. Socket MPV yang terbuka bisa dieksploitasi untuk mengirim command ke MPV instance.

**Lokasi:** `.env.example`, baris 11

**Solusi:**
```bash
# .env.example
# Gunakan path di dalam project, bukan /tmp global
LUNAWAVE_MPV_SOCKET=./cache/sockets/lunawave-mpv.sock
```

Config.py sudah memiliki validasi path yang baik, tapi default di `.env.example` sebaiknya menggunakan path yang lebih aman.

---

## Ringkasan Prioritas Perbaikan

### 🔴 Kritis — Harus Diperbaiki Sebelum Production Release

| ID | Temuan | Estimasi |
|---|---|---|
| DEVOPS-001 | `run.py` tidak ada, Docker langsung crash | 5 menit |
| DEVOPS-002 | Container berjalan sebagai root | 30 menit |
| DEVOPS-004 | Volume Docker tidak persist cache/logs | 30 menit |
| DEVOPS-012 | Inkonsistensi prefix env var (YTGUI vs LUNAWAVE) | 2 jam |
| DEVOPS-016 | JS bundle tidak di-build di Docker | 1 jam |
| DEVOPS-020 | Rollback via git checkout berbahaya | 2 jam |
| DEVOPS-027 | Tidak ada alerting sama sekali | 3 jam |
| DEVOPS-029 | Backup DB overwrite setiap 24 jam (no rotation) | 1 jam |
| DEVOPS-032 | Tidak ada Disaster Recovery plan | 4 jam |

### 🟡 Tinggi — Perlu Diperbaiki Sprint Berikutnya

| ID | Temuan | Estimasi |
|---|---|---|
| DEVOPS-003 | Tidak ada HEALTHCHECK di Dockerfile | 15 menit |
| DEVOPS-005 | Port binding ke 0.0.0.0 | 15 menit |
| DEVOPS-007 | Tidak ada CD pipeline | 3 jam |
| DEVOPS-008 | Windows CI tidak menjalankan tests | 1 jam |
| DEVOPS-010 | Tidak ada CI untuk JavaScript | 2 jam |
| DEVOPS-013 | admin_password.txt path di cache/ | 30 menit |
| DEVOPS-014 | docker-compose tidak meneruskan secrets | 15 menit |
| DEVOPS-015 | Password tercetak ke stderr/log | 1 jam |
| DEVOPS-021 | Tidak ada DB migration framework | 4 jam |
| DEVOPS-022 | Prometheus tidak terhubung ke monitoring stack | 3 jam |
| DEVOPS-024 | Log tidak centralized (hilang saat restart) | 2 jam |
| DEVOPS-028 | monitor_health.sh tidak cek MPV | 30 menit |
| DEVOPS-030 | Tidak ada backup untuk MP3 downloads | 1 jam |
| DEVOPS-031 | Backup tidak diverifikasi integrity-nya | 1 jam |
| DEVOPS-033 | Termux boot script tidak menangani gagal startup | 30 menit |
| DEVOPS-034 | opentelemetry di dependency check tapi tidak di requirements | 15 menit |

### 🟢 Sedang — Backlog

| ID | Temuan | Estimasi |
|---|---|---|
| DEVOPS-006 | Layer caching Dockerfile tidak optimal | 30 menit |
| DEVOPS-009 | CI coverage threshold terlalu rendah (40%) | 15 menit |
| DEVOPS-011 | Tidak ada SHA pinning untuk GitHub Actions | 30 menit |
| DEVOPS-017 | requirements.txt dan pyproject.toml tidak sinkron | 1 jam |
| DEVOPS-018 | make_dist.sh tanpa checksum | 30 menit |
| DEVOPS-019 | Tidak ada release process formal | 2 jam |
| DEVOPS-023 | Metrics tidak cukup untuk production | 2 jam |
| DEVOPS-026 | Tidak ada correlation ID di log | 1 jam |
| DEVOPS-035 | Socket path di /tmp di .env.example | 10 menit |

---

*Total estimasi untuk semua Kritis: ~14 jam kerja. Temuan ini berdasarkan static analysis source code dan konfigurasi tanpa akses ke environment runtime.*

# 🔍 DEPENDENCY AUDIT REPORT — LunaWave
**Audit Tim:** Senior Software Architect · Principal Backend Engineer · Senior Frontend Engineer · DevOps Engineer · Security Engineer  
**Tanggal Audit:** 2026-07-07  
**Scope:** requirements.txt · requirements-dev.txt · pyproject.toml · package.json · package-lock.json · CDN dependencies  
**Status:** ⚠️ **TIDAK SIAP PRODUCTION** — Ditemukan 14 temuan kritis/major

---

## RINGKASAN EKSEKUTIF

| Kategori | Jumlah Temuan |
|---|---|
| 🔴 Critical | 3 |
| 🟠 Major | 6 |
| 🟡 Minor | 5 |
| **Total** | **14** |

---

## TEMUAN #1 — VERSION CONFLICT: aiosqlite Berbeda di Dua File

**Severity:** 🔴 CRITICAL  
**Kategori:** Version Conflict  

**Dampak:**  
Jika developer install dari `requirements.txt` (0.20.0) dan production deploy dari `pyproject.toml` (0.22.1), behavior database akan berbeda. aiosqlite 0.22.x memperbaiki bug context manager dan connection handling yang ada di 0.20.0. Bug ini bisa muncul di production namun tidak terreproduksi di development, atau sebaliknya.

**Penyebab:**  
Dua file dependency yang tidak disinkronkan. Developer memperbarui `pyproject.toml` namun lupa memperbarui `requirements.txt`.

**Lokasi File:**
- `requirements.txt` baris 2
- `pyproject.toml` baris 8

**Kode Bermasalah:**
```
# requirements.txt
aiosqlite==0.20.0          ← versi lama

# pyproject.toml
"aiosqlite==0.22.1",       ← versi lebih baru
```

**Solusi Lengkap:**  
Tetapkan satu sumber kebenaran. Karena `pyproject.toml` adalah standar modern Python packaging, jadikan ia sebagai master dan hapus duplikasi di `requirements.txt`.

**Implementasi:**
```
# requirements.txt — selaraskan ke versi pyproject.toml
aiosqlite==0.22.1          ← ubah dari 0.20.0
```

Atau, lebih baik lagi, hapus `requirements.txt` dan generate otomatis dari pyproject.toml:
```bash
# generate requirements.txt dari pyproject.toml (untuk Docker/CI compatibility)
pip-compile pyproject.toml --output-file requirements.txt
```

---

## TEMUAN #2 — CRITICAL: node_modules Tidak Ada di .gitignore

**Severity:** 🔴 CRITICAL  
**Kategori:** Dependency Problem · Repository Hygiene  

**Dampak:**  
`node_modules/` ikut di-commit ke Git dan terbawa dalam zip distribution. Ini menyebabkan:
1. Repository bloat (puluhan MB untuk binary platform-specific)
2. Binary platform yang salah masuk ke production (zip berisi `@esbuild/win32-x64` binary, bukan Linux)
3. Pengguna yang clone dan langsung pakai binary yang committed bisa crash di runtime
4. Security: binary yang di-commit tidak bisa diverifikasi integrity-nya via package-lock

**Penyebab:**  
`.gitignore` tidak menyertakan `node_modules/` sama sekali.

**Lokasi File:**
- `.gitignore` — tidak ada entry `node_modules`
- `node_modules/@esbuild/win32-x64/esbuild.exe` — Windows binary ikut ke repository

**Kode Bermasalah:**
```gitignore
# .gitignore — TIDAK ADA baris berikut:
node_modules/    ← HILANG
```

**Solusi Lengkap:**

```gitignore
# .gitignore — tambahkan:
node_modules/
npm-debug.log*
yarn-error.log*
.npm/
```

Kemudian bersihkan dari Git history:
```bash
git rm -r --cached node_modules/
git commit -m "chore: remove node_modules from tracking"
echo "node_modules/" >> .gitignore
git add .gitignore
git commit -m "chore: add node_modules to .gitignore"
```

---

## TEMUAN #3 — CRITICAL: CDN External tanpa Subresource Integrity (SRI)

**Severity:** 🔴 CRITICAL  
**Kategori:** Security Vulnerability · External Dependency  

**Dampak:**  
Tabler Icons dimuat dari jsDelivr CDN tanpa hash SRI. Jika CDN dicompromise (supply chain attack), attacker bisa menyuntikkan JavaScript arbitrer ke semua user LunaWave. Ini adalah vektor serangan nyata (lihat: Polyfill.io incident 2024). Selain itu, jika CDN down, seluruh UI kehilangan semua icon — karena icon dipakai untuk navigasi, play/pause, queue, dan semua kontrol utama.

**Penyebab:**  
Pengembang menambahkan CDN link tanpa menggunakan SRI generator.

**Lokasi File:**
- `web/static/index.html` baris 17-18

**Kode Bermasalah:**
```html
<!-- TIDAK ADA integrity hash = Supply Chain Attack Risk -->
<link rel="stylesheet" 
  href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.33.0/dist/tabler-icons.min.css"
  media="print" onload="this.media='all'">
<noscript>
  <link rel="stylesheet" 
    href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.33.0/dist/tabler-icons.min.css">
</noscript>
```

**Solusi Lengkap — Opsi A (Self-hosted, Recommended untuk Production):**  
Download dan bundle Tabler Icons secara lokal, hilangkan dependency CDN sama sekali.

```bash
# Download ke local assets
npm install @tabler/icons-webfont@3.33.0 --save-dev
cp -r node_modules/@tabler/icons-webfont/dist web/static/vendor/tabler-icons/
```

```html
<!-- index.html — gunakan lokal -->
<link rel="stylesheet" href="/static/vendor/tabler-icons/tabler-icons.min.css">
```

**Solusi — Opsi B (SRI Hash, minimum acceptable):**
```html
<link rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.33.0/dist/tabler-icons.min.css"
  integrity="sha384-[HASH_DARI_SRI_GENERATOR]"
  crossorigin="anonymous"
  media="print" onload="this.media='all'">
```

Generate hash via: https://www.srihash.org atau `openssl dgst -sha384 -binary tabler-icons.min.css | openssl base64 -A`

---

## TEMUAN #4 — MAJOR: Package Name Mismatch antara package.json dan package-lock.json

**Severity:** 🟠 MAJOR  
**Kategori:** Version Conflict · Maintainability  

**Dampak:**  
`package.json` punya nama `"lunawave-project"` namun `package-lock.json` masih menggunakan nama lama `"ytgui-project"`. Ini menandakan lock file tidak pernah di-regenerate setelah rename. Jika ada tools yang membandingkan nama antara kedua file (npm ci di beberapa versi), install bisa gagal atau menghasilkan warning yang menyesatkan di CI/CD.

**Lokasi File:**
- `package.json` baris 2
- `package-lock.json` baris 2

**Kode Bermasalah:**
```json
// package.json
{ "name": "lunawave-project" }

// package-lock.json
{ "name": "ytgui-project" }   ← nama lama, tidak konsisten
```

**Solusi:**
```bash
# Regenerate lock file
rm package-lock.json
npm install
# Verifikasi kedua file sekarang konsisten
```

---

## TEMUAN #5 — MAJOR: Python Version Inconsistency di Tiga Tempat

**Severity:** 🟠 MAJOR  
**Kategori:** Version Conflict · Breaking Change Risk  

**Dampak:**  
Tiga lokasi berbeda mendefinisikan versi Python berbeda, menyebabkan behavior berbeda antara development, CI, dan production Docker:

| Lokasi | Python Version |
|---|---|
| `pyproject.toml` `requires-python` | `>=3.10` |
| `pyproject.toml` `[tool.mypy]` | `3.10` |
| `.github/workflows/ci.yml` | `3.11` |
| `Dockerfile` | `python:3.12-slim` |

Code yang lulus CI (Python 3.11) bisa berbeda behavior di Docker (3.12). Python 3.12 menghapus beberapa stdlib deprecated yang mungkin masih digunakan. Python 3.10 sintaks type hints (`X | Y`) tidak kompatibel penuh dengan 3.10 tanpa `from __future__ import annotations`.

**Lokasi File:**
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `Dockerfile`

**Solusi Lengkap:**  
Pilih satu versi Python, gunakan di semua tempat. Rekomendasi: **Python 3.12** (LTS roadmap, performance improvements).

```toml
# pyproject.toml
[project]
requires-python = ">=3.12"

[tool.mypy]
python_version = "3.12"
```

```yaml
# .github/workflows/ci.yml
python-version: "3.12"
```

```dockerfile
# Dockerfile
FROM python:3.12-slim
```

---

## TEMUAN #6 — MAJOR: Dockerfile Merujuk File yang Tidak Ada (run.py)

**Severity:** 🟠 MAJOR  
**Kategori:** Breaking Change Risk · Deployment Failure  

**Dampak:**  
`Dockerfile` baris terakhir menjalankan `CMD ["python", "run.py"]` namun file `run.py` tidak ada di project. File yang ada adalah `main.py` dan `start.py`. Docker image akan build berhasil namun **crash langsung saat container distart** dengan `ModuleNotFoundError` atau `FileNotFoundError`. Deployment akan gagal total.

**Lokasi File:**
- `Dockerfile` baris 24

**Kode Bermasalah:**
```dockerfile
CMD ["python", "run.py"]    ← run.py tidak ada di project!
```

**File yang ada:**
```
main.py      ← kemungkinan entry point yang benar
start.py     ← GUI launcher dengan tkinter
```

**Solusi:**
```dockerfile
# Verifikasi entry point yang benar (main.py berdasarkan struktur project)
CMD ["python", "main.py"]

# Atau dengan argumen server mode jika ada flag:
CMD ["python", "main.py", "--headless"]
```

Tambahkan juga healthcheck ke Dockerfile:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/health')"
```

---

## TEMUAN #7 — MAJOR: Dev Dependencies Sangat Jauh dari Latest (Outdated)

**Severity:** 🟠 MAJOR  
**Kategori:** Deprecated Package · Breaking Change Risk  

**Dampak:**  
Semua dev dependencies dalam `requirements-dev.txt` sudah sangat tertinggal dari versi terbaru, beberapa dengan breaking changes di intermediate versions:

| Package | Pinned | Latest | Gap |
|---|---|---|---|
| `pytest` | 8.0.0 | **9.1.1** | +1 major, +1 minor |
| `pytest-asyncio` | 0.23.0 | **1.4.0** | +1 major version |
| `pytest-aiohttp` | 1.0.5 | **1.1.1** | +1 minor |
| `ruff` | 0.1.0 | **0.15.20** | +14 minor versions |
| `mypy` | 1.8.0 | **2.1.0** | +1 major version |
| `bandit` | 1.7.5 | **1.9.4** | +2 minor versions |
| `pip-audit` | 2.7.0 | **2.10.1** | +3 minor versions |

**Breaking changes penting:**
- `pytest-asyncio` 0.23.0 → 1.x: Mode handling berubah drastis. `asyncio_mode = "auto"` di pyproject.toml mungkin tidak lagi valid di 1.x.
- `mypy` 1.8.0 → 2.x: Strict mode defaults berubah, banyak type errors baru muncul.
- `ruff` 0.1.0 → 0.15.x: Rules baru ditambahkan yang mungkin mengubah lint output.

**Lokasi File:** `requirements-dev.txt`

**Solusi:**
```
# requirements-dev.txt — versi yang diupdate
pytest==9.1.1
pytest-asyncio==1.4.0
pytest-aiohttp==1.1.1
ruff==0.15.20
mypy==2.1.0
bandit==1.9.4
pip-audit==2.10.1
```

Lakukan update bertahap dengan testing di setiap step:
```bash
# Update pytest ecosystem dulu
pip install pytest==9.1.1 pytest-asyncio==1.4.0 pytest-aiohttp==1.1.1
pytest tests/ -v   # pastikan lulus sebelum lanjut

# Update static analysis tools
pip install ruff==0.15.20 mypy==2.1.0 bandit==1.9.4 pip-audit==2.10.1
```

---

## TEMUAN #8 — MAJOR: Production Dependencies Tertinggal dari Latest

**Severity:** 🟠 MAJOR  
**Kategori:** Deprecated Package · Security Vulnerability Risk  

**Dampak:**  
Beberapa production dependency tertinggal dari versi terbaru dengan potensi security fixes yang terlewat:

| Package | Pinned | Latest | Keterangan |
|---|---|---|---|
| `structlog` | 24.4.0 | **26.1.0** | 2 major versions, API processor changes |
| `prometheus_client` | 0.20.0 | **0.25.0** | 5 minor versions, multiprocess mode fix |
| `yt-dlp` | 2026.3.17 | **2026.7.4** | 4 releases, YouTube API changes |

**yt-dlp khusus:** Ini adalah library yang **paling sering butuh update**. YouTube secara aktif memperbarui mekanisme streaming mereka. Pinning ke 2026.3.17 sementara latest adalah 2026.7.4 berarti kemungkinan besar ada format yang sudah tidak bisa diextract atau ada bug yang sudah diperbaiki di versi terbaru. Ini langsung berdampak pada fungsionalitas inti aplikasi.

**Lokasi File:** `requirements.txt`

**Solusi untuk yt-dlp — gunakan range version:**
```
# requirements.txt
yt-dlp>=2026.7.4,<2027.0.0    ← lebih fleksibel untuk patch updates
```

**Solusi untuk structlog dan prometheus_client:**
```
structlog==26.1.0
prometheus_client==0.25.0
```

Untuk yt-dlp, pertimbangkan auto-update strategy:
```python
# Di startup, check dan warn jika yt-dlp outdated
import yt_dlp
import subprocess
result = subprocess.run(['pip', 'index', 'versions', 'yt-dlp'], capture_output=True, text=True)
# Parse dan log warning jika versi installed != latest
```

---

## TEMUAN #9 — MAJOR: Ruff Configuration — Terlalu Banyak Rules yang Di-ignore

**Severity:** 🟠 MAJOR  
**Kategori:** Technical Debt · Maintainability  

**Dampak:**  
`pyproject.toml` mengignore 9 Ruff rules penting, termasuk beberapa yang merupakan best practice dan security concern:

```toml
ignore = ["E501", "E722", "E731", "E402", "F841", "E712", "E741", "E701", "E702", "I001"]
```

Rule yang berbahaya di-ignore:
- **E722** (`bare except`): `except:` tanpa exception type — menyembunyikan error, anti-pattern yang serius
- **F841** (unused variable): Variable dibuat tapi tidak dipakai — potensi logic error tersembunyi
- **E712** (comparison to True/False): `if x == True` — semantic bug risk
- **I001** (import sorting): Import tidak terurut — maintainability issue

**Lokasi File:** `pyproject.toml` seksi `[tool.ruff.lint]`

**Kode Bermasalah:**
```toml
ignore = ["E501", "E722", "E731", "E402", "F841", "E712", "E741", "E701", "E702", "I001"]
#                  ^^^^                           ^^^^   ^^^^
#              bare except               unused var  == True/False
```

**Solusi:**
```toml
# pyproject.toml — kurangi ignore, perbaiki kode yang melanggar
[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "S"]  # tambah bugbear dan security rules
ignore = [
    "E501",   # line too long — acceptable dengan line-length = 120
    "E402",   # module level import not at top — legacy, perbaiki bertahap
]
# Hapus: E722, F841, E712, I001 dari ignore — fix kodenya, bukan ignore rulenya
```

---

## TEMUAN #10 — MAJOR: Mypy Dikonfigurasi Terlalu Permissif

**Severity:** 🟠 MAJOR  
**Kategori:** Technical Debt · Maintainability  

**Dampak:**  
Konfigurasi mypy hampir non-functional. Dengan semua option dimatikan, mypy hanya menemukan error yang paling jelas saja. Type checking tidak memberikan nilai proteksi yang berarti untuk codebase ini.

**Lokasi File:** `pyproject.toml` seksi `[tool.mypy]`

**Kode Bermasalah:**
```toml
[tool.mypy]
ignore_missing_imports = true      # external lib errors diabaikan
follow_imports = "skip"            # import chain tidak difollow
check_untyped_defs = false         # fungsi tanpa type hint tidak dicek
disallow_untyped_defs = false      # fungsi tanpa type hint diizinkan
disallow_incomplete_defs = false   # definisi incomplete diizinkan
```

**Solusi — perbaiki bertahap:**
```toml
[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true    # pertahankan untuk third-party
follow_imports = "normal"        # ubah dari "skip"
check_untyped_defs = true        # aktifkan pengecekan
disallow_untyped_defs = false    # biarkan false dulu, naikkan bertahap
disallow_incomplete_defs = true  # aktifkan ini dulu
warn_return_any = true           # tambahkan
warn_unused_configs = true       # tambahkan
```

---

## TEMUAN #11 — MINOR: esbuild Hanya di devDependencies tapi Dibutuhkan untuk Build

**Severity:** 🟡 MINOR  
**Kategori:** Dependency Problem  

**Dampak:**  
`esbuild` ada di `devDependencies` yang secara semantik benar, namun build script (`npm run build`) adalah bagian dari deployment pipeline. Jika ada sistem yang menginstall hanya `--production` (tanpa dev dependencies), build akan gagal. Selain itu, tidak ada script `prepare` atau `prebuild` yang memastikan esbuild tersedia sebelum bundle dihasilkan.

**Lokasi File:** `package.json`

**Kode Bermasalah:**
```json
{
  "devDependencies": {
    "esbuild": "^0.28.1"    ← build tool, tapi bundle.js harus ada sebelum deploy
  },
  "scripts": {
    "build": "npm run build:js && npm run build:css"
    // tidak ada "prepare" atau CI build hook
  }
}
```

**Solusi:**
```json
{
  "scripts": {
    "build": "npm run build:js && npm run build:css",
    "prepare": "npm run build",    // otomatis build setelah npm install
    "ci": "npm ci && npm run build"  // untuk CI pipeline
  }
}
```

Pastikan `bundle.js` dan `bundle.css` ada di `.gitignore` atau sebaliknya selalu di-commit (pilih satu strategi):
```gitignore
# Jika build di CI:
web/static/js/bundle.js
web/static/css/bundle.css
```

---

## TEMUAN #12 — MINOR: syncedlyrics 1.0.1 — Potensi Breaking API

**Severity:** 🟡 MINOR  
**Kategori:** Deprecated Package · Breaking Change Risk  

**Dampak:**  
`syncedlyrics` 1.0.1 adalah versi major 1.x terbaru. Ini library kecil yang mengandalkan scraping dari Musixmatch, NetEase, dan provider lain. Provider-provider ini sering mengubah API mereka tanpa notifikasi, dan update library mungkin dibutuhkan tanpa perubahan versi yang signifikan. Library ini juga digunakan sebagai fallback dari lrclib, artinya jika gagal, lyrics tidak tersedia — namun saat ini tidak ada monitoring untuk kasus ini.

**Lokasi File:** `requirements.txt`, `plugins/lyrics.py`

**Solusi:**  
Tambahkan monitoring untuk syncedlyrics failures:
```python
# plugins/lyrics.py — tambahkan metric
from core.observability import LYRICS_SOURCE_COUNTER

try:
    lrc = await asyncio.wait_for(...)
    LYRICS_SOURCE_COUNTER.labels(source="syncedlyrics", status="success").inc()
except TimeoutError:
    LYRICS_SOURCE_COUNTER.labels(source="syncedlyrics", status="timeout").inc()
    logger.warning("syncedlyrics timeout (5.0s)")
```

---

## TEMUAN #13 — MINOR: Bandit Mengskip Rules Keamanan Penting

**Severity:** 🟡 MINOR  
**Kategori:** Security Vulnerability  

**Dampak:**  
Bandit dikonfigurasi untuk skip 3 rules dengan justifikasi yang perlu dikaji ulang:

```toml
skips = ["B101", "B104", "B108"]
#         assert  0.0.0.0  /tmp
```

- **B104** (bind to all interfaces `0.0.0.0`): Skip ini oke untuk intentional server binding, tapi perlu dipastikan tidak ada binding tak-sengaja
- **B108** (hardcoded `/tmp` path): Path `/tmp` rentan terhadap symlink attacks dan race conditions di multi-user environment

**Lokasi File:** `pyproject.toml`

**Solusi untuk B108:**
```python
# Ganti hardcoded /tmp dengan tempfile module
import tempfile
import os

# JANGAN:
path = "/tmp/lunawave_cache"

# GUNAKAN:
path = os.path.join(tempfile.gettempdir(), "lunawave_cache")
# atau lebih aman:
with tempfile.TemporaryDirectory() as tmpdir:
    path = os.path.join(tmpdir, "lunawave_cache")
```

---

## TEMUAN #14 — MINOR: CI Pipeline Menginstall requirements.txt di Ubuntu tapi Tidak di Windows

**Severity:** 🟡 MINOR  
**Kategori:** Dependency Problem · Breaking Change Risk  

**Dampak:**  
CI job `test-windows` menginstall dependencies (`pip install -r requirements.txt`) namun tidak menjalankan test suite, hanya mengtest `start.bat` syntax. Ini berarti test coverage hanya untuk Linux/Ubuntu. Bug spesifik Windows (path separator, `asyncio` event loop policy, `aiohttp` connector behavior) tidak akan terdeteksi.

**Lokasi File:** `.github/workflows/ci.yml`

**Kode Bermasalah:**
```yaml
test-windows:
  steps:
    - name: Install dependencies
      run: pip install -r requirements.txt && pip install -r requirements-dev.txt
    - name: Test start.bat syntax
      run: cmd.exe /c "start.bat --help" || exit 0
      # ← tidak ada pytest run untuk Windows!
```

**Solusi:**
```yaml
test-windows:
  steps:
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests on Windows
      run: pytest tests/ -v -x --ignore=tests/integration  # skip integration yang butuh mpv
      env:
        PYTHONASYNCIODEBUG: 1
```

---

## MATRIKS PRIORITAS PERBAIKAN

| # | Temuan | Severity | Effort | Priority |
|---|---|---|---|---|
| 2 | node_modules tidak di .gitignore | 🔴 Critical | Rendah | **P0 — Fix Sekarang** |
| 6 | Dockerfile CMD merujuk run.py (tidak ada) | 🔴 Critical | Rendah | **P0 — Fix Sekarang** |
| 1 | aiosqlite version conflict | 🔴 Critical | Rendah | **P0 — Fix Sekarang** |
| 3 | CDN tanpa SRI hash | 🔴 Critical | Sedang | **P1 — Sprint Ini** |
| 4 | package.json/lock name mismatch | 🟠 Major | Rendah | **P1 — Sprint Ini** |
| 5 | Python version inconsistency | 🟠 Major | Sedang | **P1 — Sprint Ini** |
| 8 | Production deps outdated (yt-dlp) | 🟠 Major | Rendah | **P1 — Sprint Ini** |
| 7 | Dev deps outdated (major versions) | 🟠 Major | Sedang | **P2 — Sprint Berikut** |
| 9 | Ruff ignore terlalu banyak | 🟠 Major | Sedang | **P2 — Sprint Berikut** |
| 10 | Mypy terlalu permissif | 🟠 Major | Tinggi | **P2 — Sprint Berikut** |
| 11 | esbuild di devDeps, build required | 🟡 Minor | Rendah | **P3** |
| 12 | syncedlyrics tanpa monitoring | 🟡 Minor | Rendah | **P3** |
| 13 | Bandit skip B108 (/tmp) | 🟡 Minor | Sedang | **P3** |
| 14 | CI Windows tanpa test suite | 🟡 Minor | Sedang | **P3** |

---

## DEPENDENCY INVENTORY FINAL

### Python Production (`requirements.txt` / `pyproject.toml`)

| Package | Pinned | Latest | Status | Action |
|---|---|---|---|---|
| `yt-dlp` | 2026.3.17 | 2026.7.4 | ⚠️ Outdated | Update segera |
| `aiosqlite` | 0.20.0 / 0.22.1 | 0.22.1 | 🔴 Conflict | Selaraskan ke 0.22.1 |
| `aiohttp` | 3.14.1 | 3.14.1 | ✅ Latest | OK |
| `syncedlyrics` | 1.0.1 | 1.0.1 | ✅ Latest | OK |
| `structlog` | 24.4.0 | 26.1.0 | ⚠️ Outdated | Plan upgrade |
| `prometheus_client` | 0.20.0 | 0.25.0 | ⚠️ Outdated | Plan upgrade |

### Python Dev (`requirements-dev.txt`)

| Package | Pinned | Latest | Status | Action |
|---|---|---|---|---|
| `pytest` | 8.0.0 | 9.1.1 | ⚠️ Outdated | Update |
| `pytest-asyncio` | 0.23.0 | 1.4.0 | 🔴 Major drift | Update + test |
| `pytest-aiohttp` | 1.0.5 | 1.1.1 | ⚠️ Outdated | Update |
| `ruff` | 0.1.0 | 0.15.20 | 🔴 Very outdated | Update |
| `mypy` | 1.8.0 | 2.1.0 | ⚠️ Major drift | Update |
| `bandit` | 1.7.5 | 1.9.4 | ⚠️ Outdated | Update |
| `pip-audit` | 2.7.0 | 2.10.1 | ⚠️ Outdated | Update |

### JavaScript (`package.json`)

| Package | Pinned | Latest | Status | Action |
|---|---|---|---|---|
| `esbuild` | ^0.28.1 | 0.28.1 | ✅ Latest | OK |

### Frontend CDN

| Resource | Version | SRI | Status | Action |
|---|---|---|---|---|
| `@tabler/icons-webfont` | 3.33.0 (jsDelivr) | N/A | 🔴 No SRI | Self-host atau tambah SRI |

---

## REKOMENDASI AKHIR

**Sebelum Production Release, wajib diselesaikan:**

1. Fix `Dockerfile` CMD dari `run.py` ke `main.py`
2. Tambah `node_modules/` ke `.gitignore` dan hapus dari Git
3. Selaraskan `aiosqlite` ke `0.22.1` di kedua file
4. Tambah SRI hash untuk Tabler Icons CDN atau self-host
5. Update `yt-dlp` ke `2026.7.4` (fungsi inti tergantung ini)

**Technical debt yang harus dijadwalkan:**

6. Seragamkan Python version ke 3.12 di semua environment
7. Update semua dev dependencies ke versi terbaru
8. Perbaiki Ruff dan mypy configuration agar efektif
9. Tambahkan Windows test suite ke CI

---

*Laporan ini dihasilkan oleh tim audit software LunaWave. Seluruh temuan diverifikasi manual terhadap source code aktual.*

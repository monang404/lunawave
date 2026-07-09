# Audit Dependency & Import Regression — LunaWave
**Scope:** Import/Module/Symbol/Package/DI resolution only (business logic tidak disentuh)
**Metode:** Static AST/symtable analysis + subprocess import test (seluruh modul non-test berhasil di-import setelah third-party stub dipasang — jadi tidak ada `ModuleNotFoundError`/circular import yang crash saat import; sisa temuan adalah **runtime symbol/attribute resolution** dan **missing dependency declaration**).

---

## 🔴 KRITIS

### 1. `WSAction.SETTINGS_UPDATE` — symbol tidak pernah didefinisikan
- **Lokasi:** `server/handlers/websocket.py:139`
- **Penyebab:** `core/ws_actions.py` mendefinisikan 26 konstanta `WSAction.*`, tapi `SETTINGS_UPDATE` tidak ada di antaranya. Referensi tertinggal dari refactor.
- **Dampak:** Baris `ADMIN_ONLY_ACTIONS = {..., WSAction.SETTINGS_UPDATE}` berada di dalam function (bukan module-level), jadi **tidak** meledak saat import — tapi meledak dengan `AttributeError` setiap kali function tersebut dieksekusi, yaitu **setiap pesan WS masuk yang perlu dicek admin-only**. Secara praktis seluruh dispatcher WS command rusak.
- **Cara memperbaiki:** Tambahkan `SETTINGS_UPDATE = "settings_update"` di `core/ws_actions.py`, atau hapus referensinya dari `ADMIN_ONLY_ACTIONS` bila memang sudah tidak dipakai.
- **File terdampak:** `server/handlers/websocket.py`, `core/ws_actions.py`

---

### 2. `STATIC_DIR` dipakai tanpa import di `server/handlers/http.py`
- **Lokasi:** `server/handlers/http.py:21` (fungsi `serve_index`)
- **Penyebab:** `STATIC_DIR` didefinisikan di `server/routes.py:14`, tapi `http.py` tidak meng-import-nya. Terverifikasi via analisis symtable: nama `STATIC_DIR` referenced tapi tidak assigned/imported di scope manapun dalam file ini.
- **Dampak:** `NameError: name 'STATIC_DIR' is not defined` di setiap request `GET /`. Halaman utama tidak bisa diakses (500).
- **Cara memperbaiki:** `from server.routes import STATIC_DIR` di bagian import `http.py`.
- **File terdampak:** `server/handlers/http.py`, `server/routes.py`

---

### 3. `Database.get_recent_tracks` / `Database.get_favorites` dipanggil tapi tidak ada forwarding
- **Lokasi:** `server/handlers/event_listeners.py:62-63`
- **Penyebab:** `cache/db.py` (`class Database`) hanya expose `self.tracks`, `self.sessions`, `self.discover`, `self.pool` — tidak ada method `get_recent_tracks()`/`get_favorites()` langsung di object `Database`. Method sebenarnya ada di `TrackRepository` (`get_recent_tracks`, `get_favorite_tracks`), diakses lewat `db.tracks.*`. Forwarding method di `Database` tidak pernah dibuat saat refactor repository pattern.
- **Dampak:** `AttributeError` setiap kali callback `_on_download_complete`/event listener jalan → broadcast data discover ke client gagal.
- **Cara memperbaiki:** Tambahkan method forwarding di `cache/db.py`:
```python
async def get_recent_tracks(self, limit: int):
    return await self.tracks.get_recent_tracks(limit)

async def get_favorites(self, limit: int = 50):
    return await self.tracks.get_favorite_tracks(limit)
```
- **File terdampak:** `cache/db.py`, `server/handlers/event_listeners.py`, `cache/repositories/track_repository.py`

---

### 4. `self.db.conn` — attribute yang tidak ada di object dependency `Database`
- **Lokasi:** `engine/radio_engine.py:83` dan `engine/radio_engine.py:287`
- **Penyebab:** `Database` (dependency yang di-inject ke `RadioMode`) hanya punya attribute `self.pool` (lihat `cache/db.py:53`), tidak pernah punya `self.conn`. `conn` adalah attribute milik `PoolContext` (inner helper class), bukan `Database`.
- **Dampak:** Guard `if self.db and self.db.conn:` selalu raise `AttributeError` → tertangkap `except Exception` generik → silent failure. `_ensure_artists_loaded()` dan `_gather_batch()` selalu gagal fetch data dari DB.
- **Cara memperbaiki:** Ganti kedua guard menjadi `if self.db and self.db.pool:`.
- **File terdampak:** `engine/radio_engine.py`, `cache/db.py`

---

## 🟠 TINGGI

### 5. Dependency `aiofiles` dipakai tapi tidak dideklarasikan di `requirements.txt`
- **Lokasi:** `core/state.py:14` (`import aiofiles`, dipakai baris 166 & 179)
- **Penyebab:** `requirements.txt` hanya berisi `yt-dlp`, `aiosqlite`, `aiohttp`, `syncedlyrics`, `structlog`, `prometheus_client` — `aiofiles` tidak ada di daftar.
- **Dampak:** Fresh install via `pip install -r requirements.txt` akan menyebabkan `ModuleNotFoundError: No module named 'aiofiles'` saat `core/state.py` (dependency inti, dipakai `bootstrap.py`) di-import.
- **Cara memperbaiki:** Tambahkan `aiofiles==<versi>` ke `requirements.txt`.
- **File terdampak:** `requirements.txt`, `core/state.py`

---

### 6. Konfigurasi environment variable tidak konsisten antara `gui_manager.py` dan `config.py`
- **Lokasi:** `gui_manager.py:16, 259-260` vs `config.py:30-31`
- **Penyebab:** `config.py` membaca `LUNAWAVE_HOST` / `LUNAWAVE_PORT` (huruf besar semua), tapi `gui_manager.py` membaca/menulis `LunaWave_HOST` / `LunaWave_PORT` (mixed-case). Ini adalah dependency injection lewat environment variable yang casing-nya salah.
- **Dampak:** Server yang di-spawn oleh GUI tidak pernah menerima override port/host dari GUI karena nama env var berbeda case (env var di Linux/macOS case-sensitive) — server selalu start dengan default `config.py`.
- **Cara memperbaiki:** Samakan semua referensi di `gui_manager.py` menjadi `LUNAWAVE_PORT` / `LUNAWAVE_HOST`.
- **File terdampak:** `gui_manager.py`, `config.py`

---

## 🟡 SEDANG

### 7. `psutil` dipakai tapi tidak dideklarasikan sebagai dependency
- **Lokasi:** `core/cli_ui.py` (`import psutil`)
- **Penyebab:** Tidak ada di `requirements.txt` maupun `requirements-dev.txt`.
- **Dampak:** `ModuleNotFoundError` bila `core/cli_ui.py` di-import di environment yang hanya install dari `requirements.txt`.
- **Cara memperbaiki:** Tambahkan `psutil` ke `requirements.txt`.
- **File terdampak:** `requirements.txt`, `core/cli_ui.py`

---

### 8. Registrasi WS handler pakai string literal, bypass konstanta `WSAction` (registry/DI fragile)
- **Lokasi:** `server/handlers/ws/settings_handlers.py:24, 32, 38`
```python
@register_ws_handler("volume_set")
@register_ws_handler("set_mode")
@register_ws_handler("set_output")
```
- **Penyebab:** Handler lain di file yang sama sudah konsisten pakai `WSAction.VOLUME_UP`, `WSAction.SET_SPONSORBLOCK`, dll., tapi 3 handler ini masih pakai string literal hardcoded.
- **Dampak:** Saat ini masih bekerja (nilainya sama), tapi ini **dependency wiring yang rapuh**: kalau value `WSAction.VOLUME_SET`/`SET_MODE`/`SET_OUTPUT` diubah di `core/ws_actions.py`, handler ini **diam-diam tidak akan pernah terpanggil** tanpa error apapun (silent breakage pada registry pattern).
- **Cara memperbaiki:** Ganti ke `@register_ws_handler(WSAction.VOLUME_SET)`, dst.
- **File terdampak:** `server/handlers/ws/settings_handlers.py`, `core/ws_actions.py`

---

## 🟢 RENDAH (code smell / latent, tidak crash saat ini)

### 9. Circular import laten: `gui_manager.py` ⇄ `start.py`
- **Lokasi:** `gui_manager.py:30` (`from start import DependencyChecker, ServerProcessManager`, top-level) dan `start.py:196` (`from gui_manager import ServerManagerWindow`, hanya di dalam blok `if __name__ == "__main__"`).
- **Penyebab:** Dua modul saling import. Tidak crash sekarang karena import balik di `start.py` dilindungi guard `__main__`, jadi tidak tereksekusi saat modul diimport sebagai library.
- **Dampak:** Aman untuk alur eksekusi normal (`python start.py`), tapi rapuh untuk tooling/test yang meng-import kedua modul di luar konteks `__main__`.
- **Cara memperbaiki:** Ekstrak `DependencyChecker` dan `ServerProcessManager` ke modul netral, misal `core/server_utils.py`.
- **File terdampak:** `gui_manager.py`, `start.py`

### 10. Import statement di dalam class body (`DiscoverService`)
- **Lokasi:** `server/services/discover_service.py:31`
```python
class DiscoverService:
    from core.ports import DatabasePort
    def __init__(self, track_repo: DatabasePort, discover_repo: DatabasePort):
```
- **Penyebab:** `DatabasePort` diimport di class body, sehingga menjadi class attribute `DiscoverService.DatabasePort`, bukan module-level type reference. Simbol tetap resolve dengan benar (tidak error), tapi pola ini tidak idiomatik dan membingungkan linter/type checker.
- **Dampak:** Tidak fungsional, hanya code-quality/tooling issue.
- **Cara memperbaiki:** Pindahkan `from core.ports import DatabasePort` ke bagian import di atas, di luar class.
- **File terdampak:** `server/services/discover_service.py`

### 11. Dead import: `collections` tidak dipakai
- **Lokasi:** `server/handlers/http.py:4`
- **Dampak:** Tidak fungsional, indikasi refactor tidak bersih.
- **Cara memperbaiki:** Hapus baris `import collections`.
- **File terdampak:** `server/handlers/http.py`

### 12. Dead import: `AUTH_MAX_LIMIT` tidak dipakai
- **Lokasi:** `server/handlers/auth.py:7` (`from core.constants import AUTH_TIMEOUT, AUTH_MAX_LIMIT, TOKEN_TTL, MAX_LOGIN_ATTEMPTS`)
- **Dampak:** Tidak fungsional, hanya dead import.
- **Cara memperbaiki:** Hapus `AUTH_MAX_LIMIT` dari import bila memang tidak dipakai di file ini.
- **File terdampak:** `server/handlers/auth.py`, `core/constants.py`

---

## Ringkasan Prioritas

| # | Prioritas | Kategori Dependency | File Utama |
|---|-----------|---------------------|------------|
| 1 | 🔴 KRITIS | Symbol tidak ada (moved/removed) | `server/handlers/websocket.py` |
| 2 | 🔴 KRITIS | Absolute import hilang | `server/handlers/http.py` |
| 3 | 🔴 KRITIS | Function dipindahkan tanpa forwarding | `cache/db.py`, `event_listeners.py` |
| 4 | 🔴 KRITIS | Dependency injection rusak (attr salah) | `engine/radio_engine.py` |
| 5 | 🟠 TINGGI | Package/config dependency hilang | `requirements.txt` |
| 6 | 🟠 TINGGI | Config dependency (env var) tidak sinkron | `gui_manager.py` / `config.py` |
| 7 | 🟡 SEDANG | Package dependency hilang | `requirements.txt` |
| 8 | 🟡 SEDANG | DI/registry rapuh (string vs const) | `settings_handlers.py` |
| 9 | 🟢 RENDAH | Circular import (laten) | `gui_manager.py` / `start.py` |
| 10 | 🟢 RENDAH | Import placement tidak idiomatik | `discover_service.py` |
| 11 | 🟢 RENDAH | Dead import | `http.py` |
| 12 | 🟢 RENDAH | Dead import | `auth.py` |

**Catatan:** Tidak ditemukan `ModuleNotFoundError`/circular-import yang benar-benar crash saat import (diverifikasi dengan menjalankan import test terhadap seluruh modul non-test setelah third-party package di-stub). Klaim di laporan lama terkait `core/background_tasks.py` ⇄ `core/bootstrap.py` circular import **tidak terverifikasi** — `core/bootstrap.py` tidak meng-import `background_tasks` sama sekali (yang meng-import adalah `main.py`, secara lokal di dalam fungsi), jadi tidak ada circular import di sana.

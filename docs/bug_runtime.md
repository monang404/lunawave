# Laporan Bug Runtime — LunaWave

Metode: instalasi dependency sesuai `requirements.txt`/`requirements-dev.txt`, menjalankan `pytest` penuh (230 pass / 9 fail), menelusuri call stack tiap failure, dikonfirmasi silang dengan `ruff --select F821` (undefined name) di seluruh source (non-test).

---

## BUG #1 (KRITIS) — NameError: `STATIC_DIR` tidak terdefinisi

**Lokasi bug**
`server/handlers/http.py:21`, fungsi `serve_index()`
```python
async def serve_index(request):
    resp = web.FileResponse(STATIC_DIR / "index.html")
```

**Root cause**
`STATIC_DIR` didefinisikan di `server/routes.py` dan di-import secara lokal di `server/app.py` (`from server.routes import ... STATIC_DIR`), tetapi **tidak pernah di-import** ke dalam module `server/handlers/http.py`. Saat `serve_index` dieksekusi, Python mencari nama `STATIC_DIR` di scope lokal → global module `http.py` → builtins, dan tidak ditemukan di manapun dalam module tersebut.

Route `"/"` (halaman utama aplikasi) didaftarkan ke `serve_index` di `server/app.py`:
```python
app.router.add_get(ROUTE_INDEX, serve_index)
```
Artinya **setiap kali user membuka halaman utama**, handler ini akan crash dengan:
```
NameError: name 'STATIC_DIR' is not defined
```
Bug ini tidak tertangkap oleh test suite karena tidak ada satupun test yang melakukan request ke route `"/"`.

**Solusi minimal**
Tambahkan import `STATIC_DIR` di `server/handlers/http.py`:
```python
from server.routes import STATIC_DIR
```
(atau import langsung dari sumber definisinya, tanpa mengubah struktur/refactor lain.)

**File terdampak**
- `server/handlers/http.py` (lokasi error)
- `server/routes.py` (sumber definisi `STATIC_DIR`)
- `server/app.py` (yang mendaftarkan route ke handler bermasalah)

---

## BUG #2 (KRITIS) — AttributeError: `WSAction` tidak punya `SETTINGS_UPDATE`

**Lokasi bug**
`server/handlers/websocket.py:139`, fungsi `handle_ws_message()`
```python
ADMIN_ONLY_ACTIONS = {WSAction.SET_OUTPUT, WSAction.SET_SPONSORBLOCK, WSAction.DELETE_DOWNLOAD, WSAction.STOP, WSAction.SETTINGS_UPDATE}
```

**Root cause**
Class `WSAction` di `core/ws_actions.py` tidak memiliki atribut `SETTINGS_UPDATE` (tidak ada di daftar action apapun — Auth/Playback/Queue/Radio/Settings/Download/Discover). Baris ini dieksekusi **secara tidak bersyarat setiap kali** ada pesan `"cmd"` masuk (setelah pengecekan `AUTH`/`LOGOUT`), sehingga hampir semua command (`search`, `play_track`, `stop`, dll.) langsung melempar:
```
AttributeError: type object 'WSAction' has no attribute 'SETTINGS_UPDATE'
```
Exception ini tertangkap oleh `except Exception as e:` di `ws_handler()` (baris ~112), yang men-log error lalu **menutup koneksi WebSocket**. Dampaknya: fitur real-time seperti play track, search, queue, radio, dll semua gagal total setelah client login.

Terverifikasi lewat 3 test yang gagal karena efek berantai ini:
- `tests/integration/test_critical_paths.py::test_critical_path_ws_play_track_to_command_bus`
- `tests/integration/test_e2e.py::test_e2e_websocket_search`
- `tests/integration/test_e2e.py::test_e2e_websocket_unauthenticated_command_rejected`

**Solusi minimal**
Tambahkan konstanta yang hilang di `core/ws_actions.py`:
```python
SETTINGS_UPDATE = "settings_update"
```
Ditempatkan di bagian "Settings Actions" agar konsisten dengan action lain yang sudah ada.

**File terdampak**
- `core/ws_actions.py` (lokasi penambahan konstanta)
- `server/handlers/websocket.py` (lokasi error dilempar & call stack crash)

---

## BUG #3 (MINOR / laten) — AttributeError: `'StringPayload' object has no attribute 'decode'`

**Lokasi bug**
`server/handlers/http.py:232`, fungsi `serve_metrics()`
```python
content, content_type = get_metrics_content()
...
return web.Response(body=content, content_type=ct)
```

**Root cause**
`web.Response(body=...)` mengharapkan `bytes`, bukan `str`. Saat ini `get_metrics_content()` (di `core/observability.py`) selalu mengembalikan `bytes` dari `prometheus_client.generate_latest()`, sehingga di jalur normal tidak crash. Namun begitu `content` berupa `str` (skenario ini terjadi nyata di test `test_metrics_auth_bearer` yang mem-patch `get_metrics_content` mengembalikan string), aiohttp membungkusnya sebagai `StringPayload`, dan akses `resp.text` di lapisan lain memanggil `.decode()` pada objek yang tidak punya method itu → `AttributeError`. Ini adalah bug fragilitas tipe: kode tidak menjamin `content` selalu `bytes` sebelum diteruskan ke `body=`.

**Solusi minimal**
Gunakan parameter yang sesuai dengan tipe data, misalnya paksa encode agar konsisten:
```python
if isinstance(content, str):
    content = content.encode("utf-8")
return web.Response(body=content, content_type=ct)
```

**File terdampak**
- `server/handlers/http.py` (lokasi error)
- `core/observability.py` (sumber `get_metrics_content`, kontrak tipe kembalian tidak dijamin)

---

## Ringkasan Prioritas
| # | Severity | Jenis | File utama | Trigger |
|---|----------|-------|------------|---------|
| 1 | Kritis | NameError | `server/handlers/http.py` | Buka halaman utama `/` |
| 2 | Kritis | AttributeError | `server/handlers/websocket.py` | Kirim command WS apapun setelah login |
| 3 | Minor/laten | AttributeError | `server/handlers/http.py` | `get_metrics_content()` mengembalikan `str`, bukan `bytes` |

Tidak ada saran refactor — solusi di atas adalah perbaikan minimal (menambah 1 import, 1 konstanta, 1 pengecekan tipe) sesuai lokasi akar penyebab masing-masing bug.

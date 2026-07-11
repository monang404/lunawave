# PATCH_TRACING_OVERHEAD_AUTH_BLOCKING.md

Baca `AI_CONTEXT.md` dulu. Belum di-apply — rencana implementasi dari sesi
hunting lanjutan (setelah `PATCH_DB_MAINTENANCE_LYRICS_PAYLOAD.md`).

Dua bug di dokumen ini levelnya beda kepercayaan diri saya:

- **Task 2 (PBKDF2 blocking)** — sudah dibenchmark langsung, angkanya
  konkret, fix-nya jelas dan minim risiko. Confidence tinggi.
- **Task 1 (OTel span overhead)** — root cause & fakta (span dibuat,
  tidak ada exporter) itu pasti benar, tapi saya TIDAK punya angka
  benchmark overhead-per-span di device kalian (gak ada akses jaringan
  buat install opentelemetry-sdk di sandbox ini). Jangan anggap ini
  "signifikan dalam milidetik" — overhead per span kemungkinan besar di
  level mikrodetik, bukan mendekati PBKDF2. Yang membuat ini tetap layak
  di-patch: kerjanya 100% sia-sia (zero benefit, karena hasil span tidak
  pernah diexport kemanapun) dan dieksekusi di jalur ter-panas di seluruh
  aplikasi (tiap command). Baca bagian "TINGKAT KEYAKINAN" di Task 1
  sebelum apply.

---

## RINGKASAN

| # | Bug | File | Confidence | Dampak |
|---|-----|------|-----------|--------|
| 1 | OTel span dibuat tiap command, tidak ada exporter (zero benefit) | `core/command_bus.py`, `core/observability.py` | Sedang (root cause pasti, magnitude belum terukur) | Kecil-sedang per call, tapi di jalur paling sering dipakai |
| 2 | `verify_password()` (PBKDF2 100k iter) jalan sinkron di event loop | `server/handlers/auth.py` | Tinggi (sudah dibenchmark) | Tinggi saat terjadi — blokir SEMUA client selama proses login |

Tidak ada file baru. Tidak ada perubahan arsitektur inti — Task 1 opsi B
menambah 1 env var baru (pola yang sudah dipakai di `config.py` untuk
`LUNAWAVE_METRICS_TOKEN` dkk), bukan komponen baru.

---

## TASK 1 — Hentikan OTel span di command_bus (tidak ada exporter terpasang)

### ROOT CAUSE

`core/command_bus.py`:
```python
with tracer.start_as_current_span(f"CommandBus.execute:{command}") as span:
    span.set_attribute("command", command)
    try:
        ...
    except Exception as e:
        status = "error"
        span.record_exception(e)
        ...
```

Ini jalan di **setiap** `command_bus.execute()` — setiap play, pause,
next, prev, seek, volume up/down/set, queue add/remove/reorder/select,
radio randomize, lyrics offset. Semua command tanpa kecuali.

`core/observability.py`:
```python
def setup_tracing():
    provider = TracerProvider()
    # processor = BatchSpanProcessor(ConsoleSpanExporter())
    # provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return trace.get_tracer("ytplayer.core")
```

`BatchSpanProcessor` (yang bertugas mengirim span ke exporter — di sini
`ConsoleSpanExporter`, biasanya dipakai buat debug lokal, bukan
production) sengaja di-comment. Saya cek seluruh codebase — tidak ada
processor lain yang di-attach di tempat lain. Artinya: `tracer` yang
dipakai di `command_bus.py` menghasilkan span yang **tidak pernah
diproses atau diexport kemanapun**. Data telemetrinya hilang begitu span
selesai (`__exit__` dari context manager) — tidak berguna untuk debugging,
monitoring, ataupun apapun saat ini.

### TINGKAT KEYAKINAN (baca sebelum apply)

- **Yang pasti benar (fakta, sudah diverifikasi):** span dibuat setiap
  command, tidak ada exporter terpasang, jadi span tersebut memang tidak
  memberi manfaat apapun sekarang.
- **Yang TIDAK saya klaim:** saya tidak punya angka "X ms per command"
  atau "X% CPU" dari overhead span ini di device kalian — sandbox saya
  tidak punya akses jaringan buat install `opentelemetry-sdk` dan
  benchmark langsung. Berdasarkan pengalaman umum dengan OTel SDK,
  overhead per span (tanpa exporter, cuma AlwaysOnSampler default) biasanya
  di kisaran mikrodetik per call, BUKAN milidetik — jauh lebih kecil dari
  Task 2 (PBKDF2, ~58ms terukur langsung).
- **Alasan tetap layak di-patch:** bukan karena "pasti kerasa lag", tapi
  karena ini kerja CPU yang 100% terbuang percuma (bikin objek Span,
  attach/detach context var, generate ID) di jalur yang paling sering
  dieksekusi di seluruh aplikasi. Kalau nanti diukur ternyata dampaknya
  kecil sekali, minimal ini "bersih-bersih dead weight", bukan regresi.
- **Rekomendasi:** kalau kalian punya cara profiling di device asli
  (Termux/Android), ukur dulu command latency sebelum & sesudah patch
  ini untuk konfirmasi besarannya sebelum yakin 100% ini "signifikan".
  Saya taruh cara sederhana untuk itu di bagian VERIFIKASI.

### PERUBAHAN — pilih salah satu opsi

#### OPSI A — Hapus span dari hot path (paling sederhana, direkomendasikan untuk fase stabilisasi)

Tracing OTel saat ini tidak dipakai untuk apapun (tidak ada exporter),
jadi hapus saja pemakaiannya dari `command_bus.py`. Kalau nanti mau
tracing beneran, tinggal tambahkan lagi span + exporter sekaligus dalam
satu paket kerja (bukan setengah-setengah kayak sekarang).

**File: `core/command_bus.py`**

**Cari:**
```python
from core.observability import COMMAND_COUNT, COMMAND_LATENCY, tracer
```
**Ganti dengan:**
```python
from core.observability import COMMAND_COUNT, COMMAND_LATENCY
```

**Cari:**
```python
        with tracer.start_as_current_span(f"CommandBus.execute:{command}") as span:
            span.set_attribute("command", command)
            try:
                if asyncio.iscoroutinefunction(handler):
                    return await handler(data)
                else:
                    return handler(data)
            except Exception as e:
                status = "error"
                span.record_exception(e)
                logger.error(f"Command execution error for '{command}': {e}", exc_info=True)
                raise
            finally:
                duration = time.perf_counter() - start_time
                COMMAND_LATENCY.labels(command_name=command).observe(duration)
                COMMAND_COUNT.labels(command_name=command, status=status).inc()
```
**Ganti dengan:**
```python
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(data)
            else:
                return handler(data)
        except Exception as e:
            status = "error"
            logger.error(f"Command execution error for '{command}': {e}", exc_info=True)
            raise
        finally:
            duration = time.perf_counter() - start_time
            COMMAND_LATENCY.labels(command_name=command).observe(duration)
            COMMAND_COUNT.labels(command_name=command, status=status).inc()
```

**File: `core/observability.py`** — `setup_tracing()`, `tracer`, dan
import OpenTelemetry-nya jadi tidak dipakai di manapun lagi setelah ini.
Boleh dihapus sekalian biar tidak ada dead code, ATAU dibiarkan (tidak
mengganggu, cuma tidak dipanggil). Kalau mau dihapus:

**Cari:**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
```
**Ganti dengan:**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
```

**Cari:**
```python
# --- OpenTelemetry Tracing ---
def setup_tracing():
    provider = TracerProvider()
    # processor = BatchSpanProcessor(ConsoleSpanExporter())
    # provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return trace.get_tracer("ytplayer.core")

tracer = setup_tracing()

def get_metrics_content():
```
**Ganti dengan:**
```python
def get_metrics_content():
```

Cek juga `requirements.txt` — `opentelemetry-api` dan `opentelemetry-sdk`
jadi tidak dipakai di manapun kalau opsi ini diambil penuh. Boleh
dibiarkan di requirements (jaga-jaga mau dipakai lagi nanti) atau dihapus
— keputusan kalian, bukan bagian wajib dari fix ini.

#### OPSI B — Future-proof lewat env var (kalau masih mau ada opsi nyalain tracing tanpa edit kode lagi nanti)

Kalau kalian merasa tracing ini memang mau dipakai suatu saat (bukan
cuma dead code kebetulan kelewat), opsi ini lebih matang: span cuma
dibuat kalau memang di-enable, dan begitu di-enable, exporter-nya juga
otomatis aktif (gak ada lagi kondisi "setengah nyala" seperti sekarang).

**File: `core/observability.py`**

**Cari:**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
```
**Ganti dengan:**
```python
import os
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
```

**Cari:**
```python
# --- OpenTelemetry Tracing ---
def setup_tracing():
    provider = TracerProvider()
    # processor = BatchSpanProcessor(ConsoleSpanExporter())
    # provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return trace.get_tracer("ytplayer.core")

tracer = setup_tracing()
```
**Ganti dengan:**
```python
# --- OpenTelemetry Tracing ---
# Nonaktif secara default (LUNAWAVE_ENABLE_TRACING tidak di-set) — span
# yang dibuat tanpa exporter cuma buang CPU tanpa manfaat. Set env var ini
# ke "1" untuk mengaktifkan tracing + exporter sekaligus (satu paket, tidak
# ada lagi kondisi "span dibuat tapi tidak diexport").
_TRACING_ENABLED = os.environ.get("LUNAWAVE_ENABLE_TRACING", "0") == "1"

def setup_tracing():
    if not _TRACING_ENABLED:
        return trace.NoOpTracer()
    provider = TracerProvider()
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return trace.get_tracer("ytplayer.core")

tracer = setup_tracing()
```

`trace.NoOpTracer()` dari OpenTelemetry API adalah tracer resmi yang
`start_as_current_span()`-nya jadi no-op murah (tidak generate span ID,
tidak ada context attach beneran) — jadi `command_bus.py` **tidak perlu
diubah sama sekali** di opsi ini, cukup ganti file ini.

`core/command_bus.py` **tidak perlu disentuh** untuk Opsi B.

### RISIKO & CATATAN

- Opsi A menghilangkan kemampuan tracing sepenuhnya sampai ada yang
  menambahkannya lagi secara sengaja (kode + exporter sekaligus).
  Cocok kalau tracing memang belum pernah benar-benar dipakai/dilihat
  siapapun.
- Opsi B mempertahankan opsi tracing tapi default mati — cocok kalau
  kalian menduga akan butuh tracing nanti dan tidak mau nulis ulang.
- Baik Opsi A maupun B **tidak mengubah** `COMMAND_COUNT` dan
  `COMMAND_LATENCY` (metric Prometheus) — keduanya tetap jalan seperti
  biasa, cuma span OTel yang dihilangkan/dijadikan opsional.
- Cek dulu apakah `docs/` atau `scripts/architecture_lint.py` punya
  referensi ke `tracer`/OpenTelemetry yang perlu disesuaikan kalau pilih
  Opsi A (grep `tracer` dan `opentelemetry` di seluruh repo, termasuk
  `docs/`, sebelum apply).

### VERIFIKASI

```bash
python -m pytest tests/ -x -q
```

Manual test:
1. Jalankan semua command dasar (play, pause, next, prev, seek, volume,
   queue add/remove) → pastikan semua tetap berfungsi normal, tidak ada
   `AttributeError` soal `span`/`tracer` yang hilang.
2. Cek endpoint `/metrics` → `ytplayer_commands_total` dan
   `ytplayer_command_duration_seconds` tetap muncul dan increment normal
   (memastikan Prometheus metric tidak ikut ke-hapus, cuma OTel span-nya).
3. **Kalau mau ukur dampak nyata** (opsional tapi disarankan sebelum
   yakin 100% ini "signifikan"): sebelum patch, jalankan sesuatu seperti
   ```python
   import time
   start = time.perf_counter()
   for _ in range(1000):
       await command_bus.execute(CMD_VOLUME_UP)
   print((time.perf_counter() - start) / 1000)
   ```
   di device asli (Termux), lalu bandingkan dengan setelah patch. Kalau
   perbedaannya di bawah margin noise, berarti dampaknya memang kecil —
   tetap boleh di-apply (zero benefit tetap zero benefit), tapi jangan
   ekspektasi ini jadi solusi utama masalah performa.

---

## TASK 2 — `verify_password()` jangan blokir event loop

### ROOT CAUSE

`server/handlers/auth.py`:
```python
username = data.get("username", "")
password = data.get("password", "")
if username == ADMIN_USERNAME and verify_password(password, ADMIN_PASSWORD):
```

`core/security.py::verify_password()`:
```python
key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, int(iterations))
```
100.000 iterasi PBKDF2-SHA256, dipanggil **langsung** (bukan lewat
`run_in_executor`) di dalam `handle_auth()`, yang berjalan di dalam
`async with manager.rl_lock:` sebagai bagian dari coroutine WS handler
biasa.

**Dibenchmark langsung di sandbox ini:**
```
PBKDF2 100k iter time (mesin sandbox): 0.0585 detik (~58ms)
```
Di device dengan CPU lebih lemah (HP low-end / Termux di Android), bisa
1.5-3x lebih lambat → perkiraan **90-180ms per verifikasi**.

Karena LunaWave berjalan di satu event loop asyncio (aiohttp, single
process), selama 100k iterasi SHA256 ini berjalan, **seluruh event loop
berhenti total** — bukan cuma request login itu. Semua hal lain yang
biasanya jalan bersamaan (mpv observer loop yang menerima `time-pos`
event, broadcast progress ke semua client, command lain, dst) semuanya
menunggu giliran CPU sampai hashing selesai. Efeknya: setiap kali ada
yang mencoba login admin — termasuk percobaan gagal (sampai 5x per IP
per 5 menit sebelum kena rate limit) — **semua orang yang sedang
mendengarkan lewat LunaWave** (kalau multi-client) bisa merasakan
stutter/freeze singkat di audio/UI.

### PERUBAHAN

**File:** `server/handlers/auth.py`

**Cari (bagian import atas file):**
```python
import json
import time
import secrets
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from core.security import verify_password
```

**Ganti dengan:**
```python
import asyncio
import json
import time
import secrets
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from core.security import verify_password
```

**Cari:**
```python
        username = data.get("username", "")
        password = data.get("password", "")
        if username == ADMIN_USERNAME and verify_password(password, ADMIN_PASSWORD):
```

**Ganti dengan:**
```python
        username = data.get("username", "")
        password = data.get("password", "")
        # PBKDF2 100k iterasi adalah kerja CPU berat (~60-180ms tergantung
        # device) — kalau dijalankan sinkron di sini, seluruh event loop
        # (termasuk broadcast progress ke client lain & observer mpv) ikut
        # berhenti selama itu. Jalankan di thread executor agar event loop
        # tetap responsif untuk client lain selagi verifikasi berjalan.
        loop = asyncio.get_running_loop()
        password_ok = (
            username == ADMIN_USERNAME
            and await loop.run_in_executor(None, verify_password, password, ADMIN_PASSWORD)
        )
        if password_ok:
```

**Catatan penyesuaian indentasi:** blok kode setelah `if username ==
ADMIN_USERNAME and verify_password(...):` di file asli (pembuatan
`new_token`, dst.) tetap sama persis, cuma kondisi `if`-nya yang diganti
jadi `if password_ok:` dengan indentasi yang sama seperti sebelumnya.
Baris `else:` di bagian bawah (kredensial salah) juga tidak berubah.

### RISIKO & CATATAN

- **Lock tetap dipegang selama executor call** — `handle_auth()` masih
  jalan di dalam `async with manager.rl_lock:` yang membungkus seluruh
  fungsi. Ini artinya percobaan auth **lain** (dari IP berbeda sekalipun)
  akan antre menunggu lock ini selesai, TAPI — ini beda jauh dari sebelum
  patch: yang menunggu cuma percobaan auth lain, bukan seluruh event loop
  (mpv, progress broadcast, command lain tetap jalan normal). Ini
  perbaikan besar dibanding kondisi sekarang meski belum sempurna.
- **Penyempurnaan lanjutan (opsional, tidak wajib di task ini):** kalau
  mau menghilangkan antrian auth-vs-auth sepenuhnya, `rl_lock` bisa
  dipersempit supaya hanya membungkus akses ke `manager.login_attempts`
  (baca/tulis dict), bukan seluruh `verify_password()`. Ini perubahan
  lebih invasif (mengubah scope locking), jadi saya sarankan **tidak**
  dilakukan di fase stabilisasi ini kecuali kalian memang sering punya
  banyak percobaan login bersamaan — cukup jalankan Task 2 versi
  sederhana ini dulu.
- `ThreadPoolExecutor` default (`None` sebagai executor pertama di
  `run_in_executor`) dipakai di sini — ini executor bawaan Python
  (`concurrent.futures.ThreadPoolExecutor` default), terpisah dari
  `self._executor` yang dipakai `YtDlpClient`. Tidak ada konflik resource
  antara keduanya.

### VERIFIKASI

```bash
python -m pytest tests/ -x -q
```

Manual test:
1. Login admin dengan password benar → berhasil seperti biasa, token
   diterima.
2. Login admin dengan password salah 5x berturut-turut → tetap kena
   rate limit "Terlalu banyak percobaan login" setelah percobaan ke-6,
   sama seperti sebelum patch.
3. **Test dampak nyata:** sambil ada 1 client yang sedang play musik
   (audio_output browser, progress jalan tiap detik), buka tab/koneksi
   WS kedua dan coba login admin (boleh sengaja salah password) →
   sebelum patch, seharusnya ada jeda kecil di progress bar client
   pertama tepat saat proses login berjalan; setelah patch, seharusnya
   progress bar client pertama tetap mulus tanpa hentakan.
4. Cek `python scripts/doctor.py` (kalau ada checker terkait blocking
   call) tetap lolos.

---

## URUTAN PENERAPAN YANG DISARANKAN

1. **Task 2 dulu** — confidence tinggi, sudah dibenchmark, risiko kecil,
   manfaat jelas dan langsung terasa (kalau kalian sering multi-client).
2. **Task 1 (Opsi A atau B)** — root cause pasti benar (zero-benefit
   work), tapi ukur dulu di device asli kalau mau tau seberapa besar
   dampaknya sebelum memutuskan mana yang lebih penting dibanding
   pekerjaan stabilisasi lain di ledger.

---

## UPDATE UNTUK `BUG_LEDGER.md`

Tambahkan baris berikut setelah task-task ini direview:

```markdown
| 011 | OTel span setiap command tanpa exporter (zero benefit) | core/command_bus.py, core/observability.py | found | 2026-07-11 | PATCH_TRACING_OVERHEAD_AUTH_BLOCKING.md — magnitude belum diukur di device asli |
| 012 | verify_password (PBKDF2 100k iter) blocking event loop | server/handlers/auth.py | found | 2026-07-11 | PATCH_TRACING_OVERHEAD_AUTH_BLOCKING.md — sudah dibenchmark (~58ms di sandbox) |
```

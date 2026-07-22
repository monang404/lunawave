---

title: LunaWave Patch Log

latest_patch_id: PATCH-2026-07-22-175

total_entries: 175

---



# PATCHLOG.md — LunaWave



> **Format:** Prepend-only (terbaru di atas). Jangan hapus entri sebelumnya.

> **Versi format:** v2 (field-based) — bermigrasi dari v1 (prosa bebas) pada 2026-07-20. Entry hasil migrasi bertanda `Status: Unclassified` dan menyimpan isi Ringkasan v1 apa adanya, utuh, di field `Notes` -- tidak ada fakta teknis yang hilang atau diringkas saat migrasi.

> **ID:** setiap entri wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit), sekarang jadi heading `## PATCH-...` -- satu-satunya sumber judul per entry.

> **Field:** Tanggal, Timestamp, Git Branch, Git Commit, Type, Area, Priority, Title, Reason, Root Cause, Solution, Changed Files, Changed Symbols, Tests, Breaking Change, Regression Risk, Related Patch, Status, Notes -- urutan selalu sama di semua entry. Lihat `automation/patchlog.py` untuk definisi & CLI lengkap.

---

## PATCH-2026-07-22-175

**Tanggal:** 2026-07-22
**Timestamp:** 11:36
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend/Observability
**Priority:** Medium
**Title:** Finalisasi observability_log_baseline: ADR-0010 Accepted, STATUS.md, FILE_INDEX/REPORT regen

**Reason:** Sesi 5 (finalisasi) task_breakdown_observability.yaml: tandai fitur selesai, sinkronkan docs, verifikasi end-to-end

**Root Cause:**
Fitur observability_log_baseline (ADR-0010) sudah melewati sesi 1-4
(modul dependency-free, metric Prometheus, wiring middleware/app.py/
connection_manager, /health + task periodik [STATUS]) plus gap-fix
wiring log_session_start()/log_session_end() ke main.py (PATCH-174),
tapi ADR-0010 masih berstatus Proposed, docs/STATUS.md belum mencatat
ringkasan fitur ini, docs/FILE_INDEX.md belum mengenal 3 file baru
(core/mem_stats.py, core/server_clock.py, server/middleware/traffic.py)
maupun perubahan server/middleware.py -> package, dan belum ada
verifikasi end-to-end nyata (bukan cuma unit test) bahwa server benar-
benar berjalan tanpa crash dan menghasilkan output sesuai RFC.

**Solution:**
python automation/generate_file_index.py dan python automation/
generate_report.py dijalankan -- FILE_INDEX.md dan REPORT.md kini
mengenal core/mem_stats.py, core/server_clock.py, server/middleware/
traffic.py, dan server/middleware/__init__.py (package), menghilangkan
FAIL verify_docs FILE_INDEX yang persisten sejak sesi 3. docs/STATUS.md:
tambah 1 seksi ringkas di atas (tabel file+perubahan untuk seluruh 5
sesi + gap-fix, mengikuti format entri lain di file ini). docs/adr/
0010-observability-log-baseline.md: status diubah dari "Proposed" ke
"Accepted". Verifikasi manual end-to-end dijalankan langsung (bukan
cuma baca kode): python main.py di lingkungan non-tty/tanpa TERM
(mensimulasikan kondisi non-interaktif ala Termux -- stdout dipipe,
tidak ada terminal berwarna) -- server start bersih (mpv graceful
"not available" karena tidak ter-install di sandbox, sesuai desain
fail-safe, bukan crash), GET /health mengembalikan memory_mb dan
uptime_seconds terisi (bukan null), lunawave.log memuat baris "====
SESSION START ... ====" dan "==== SESSION END ... ====" yang benar,
grep -aP '\x1b\[' lunawave.log tetap bersih tanpa ANSI byte, shutdown
(SIGINT) bersih tanpa task tersisa (log "Shutdown complete." muncul
sebelum SESSION END). Jalur Windows (ctypes+psapi di core/mem_stats.py)
tidak bisa diverifikasi end-to-end karena tidak ada mesin Windows di
lingkungan eksekusi ini -- tetap tervalidasi lewat unit test dengan
mock ctypes yang sudah ada sejak sesi 1.

**Changed Files:**
- `docs/adr/0010-observability-log-baseline.md`
- `docs/STATUS.md`
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** doctor.py --json: overall FAIL 80 (hanya verify_security .gitignore, pre-existing, tidak ada FAIL baru); verify_docs/architecture_lint/verify_structure/event_graph semua PASS 100; verifikasi manual end-to-end: python main.py non-tty -- SESSION START/END banner benar, /health memory_mb & uptime_seconds terisi, lunawave.log bersih dari ANSI, shutdown bersih

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-22-174

**Status:** Draft

**Notes:**
Sesi 5 (final) dari task_breakdown_observability.yaml, task O5.1,
patchlog: own. Seluruh 5 sesi (O1.1/O1.2, O2.1/O2.2, O3.1/O3.2/O3.3,
O4.1/O4.2) + 1 gap-fix (PATCH-2026-07-22-174, wiring log_session_start/
end ke main.py yang terlewat dari sesi 2) kini selesai. doctor.py --json
akhir: overall_status FAIL, aggregate_score 80 -- HANYA 1 checker FAIL
tersisa (verify_security: .gitignore tidak ada sejak arsip awal,
dikonfirmasi berulang di sesi 3/4/5 bukan disebabkan/disentuh oleh
perubahan fitur ini, di luar scope observability_log_baseline). Semua
checker lain (verify_docs, architecture_lint, verify_structure,
event_graph) PASS 100. TIDAK ADA FAIL BARU dibanding baseline sesi
3/4. Metric WS_MESSAGES_TOTAL (dideklarasikan sesi 2) tetap belum
di-wiring -- dikonfirmasi ulang ini bukan gap: tidak ada task manapun
di O1-O5 yang menugaskan wiring-nya (websocket.py locked, hanya boleh
dibaca), didesain untuk dipakai fitur lain di masa depan. Locked files
(engine/playback/controller.py, server/handlers/websocket.py,
web/static/index.html) tidak pernah disentuh di sesi manapun. Tidak ada
env var atau dependency pip baru ditambahkan di sepanjang fitur ini.

---

## PATCH-2026-07-22-174

**Tanggal:** 2026-07-22
**Timestamp:** 11:33
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Backend/Observability
**Priority:** Medium
**Title:** main.py: wiring log_session_start()/log_session_end() (sesi 2, belum pernah dipanggil)

**Reason:** ADR-0010 mensyaratkan banner SESSION START/END di lunawave.log; fungsi sudah ada sejak sesi 2 tapi tidak pernah dipanggil dari main.py

**Root Cause:**
core/log_config.py (sesi 2, O2.2, PATCH-2026-07-22-171) menambahkan
log_session_start()/log_session_end() untuk menulis baris pemisah
"==== SESSION START/END ... ====" ke lunawave.log dan console, sesuai
contoh output di RFC observability_logging.md §Bentuk Output. Fungsi ini
sudah diuji sendiri (tests/unit/core/test_log_config.py) tapi tidak pernah
dipanggil dari main.py atau modul lain manapun -- dod O2.2 hanya menuntut
test unit untuk fungsinya sendiri, bukan wiring ke entrypoint, dan tidak
ada task eksplisit lain di task_breakdown_observability.yaml yang
menyebut pemanggilannya. Akibatnya lunawave.log tidak pernah benar-benar
memuat banner sesi di kondisi jalan sebenarnya, walau fiturnya sudah
"selesai" menurut patchlog sesi 2.

**Solution:**
main.py: import log_session_start/log_session_end dari core.log_config
(disatukan dengan import setup_logging yang sudah ada). Di run_server():
pid = os.getpid() dihitung sebelum blok try (supaya tersedia juga di
finally), log_session_start(pid, host=host, port=port) dipanggil setelah
host/port diketahui dan tepat sebelum await _web_run_server(...) --
sehingga banner "==== SESSION START ... ====" tercatat begitu server
benar-benar mulai listen. log_session_end(pid) dipanggil di baris
terakhir blok finally, setelah "Shutdown complete." di-log dan semua
cleanup (task cancel, mpv.close, repos.close, dst) selesai -- menandai
shutdown benar-benar selesai. Kedua pemanggilan fail-safe di sisi
core/log_config.py sendiri (try/except di _emit_banner_line), jadi tidak
menambah risiko crash startup/shutdown. Tidak ada perubahan pada
log_session_start()/log_session_end() itu sendiri, hanya wiring
pemanggilannya. tests/unit/test_main.py: tambah patch
"main.log_session_start"/"main.log_session_end" ke test_main_smoke plus
assert_called_once() untuk keduanya, supaya wiring ini tidak regresi diam-
diam lagi di masa depan.

**Changed Files:**
- `main.py`
- `tests/unit/test_main.py`

**Changed Symbols:**
- `run_server()`

**Tests:** tests/unit/test_main.py (2 test, 1 updated dgn assertion baru) - passed; tests/unit (753 test, exclude launcher/gui) - passed; architecture_lint.py --json PASS 0 new_violations

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-22-173

**Status:** Draft

**Notes:**
Gap-fix sebelum sesi 5 dari task_breakdown_observability.yaml, ditemukan
saat verifikasi eksplisit user bahwa hasil sesi 2 sudah wiring ke main
sebelum melanjutkan sesi 5. Bukan task O5.1 itu sendiri dan tidak
mengubah scope-nya -- O5.1 tetap dikerjakan terpisah setelah ini.
patchlog: own (bukan bagian patchlog_group manapun, karena bukan task
eksplisit di yaml). Tidak menyentuh file locked (main.py dan
core/log_config.py bukan locked_files_global). Tidak ada env var atau
dependency pip baru. Verifikasi manual: python -c import core.log_config;
setup_logging(); log_session_start(1234, host="0.0.0.0", port=8765);
log_session_end(1234) -- baris banner muncul benar di lunawave.log,
grep -aP '\x1b\[' lunawave.log tetap bersih (tidak ada ANSI). Verifikasi
otomatis: pytest tests/unit/test_main.py (2 passed, termasuk assertion
baru log_session_start/end called once); pytest tests/unit (753 test,
exclude launcher/gui -- ModuleNotFoundError tkinter, pre-existing
environment gap) - semua passed; architecture_lint.py --json: PASS, 0
new_violations. Metric WS_MESSAGES_TOTAL (dideklarasikan sesi 2, O2.1)
dicek juga: memang belum dipakai/wiring di kode manapun sampai saat ini,
tapi ini BUKAN gap -- tidak ada task manapun di
task_breakdown_observability.yaml (O3.x/O4.x) yang menugaskan wiring-nya,
websocket.py locked (hanya boleh dibaca), jadi metric ini didekralasikan
untuk dipakai nanti di luar scope fitur ini, sesuai desain.

---

## PATCH-2026-07-22-173

**Tanggal:** 2026-07-22
**Timestamp:** 11:23
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend/Observability
**Priority:** Medium
**Title:** /health tambah uptime/RAM/koneksi aktif + task periodik [STATUS] ke log

**Reason:** ADR-0010 butuh /health yang lebih informatif untuk monitoring dasar dan ringkasan log berkala yang human-readable tanpa harus scrape /metrics

**Root Cause:**
/health hanya melaporkan status DB dan mpv, tidak ada uptime, RAM, atau
jumlah koneksi aktif (ADR-0010 poin 4 & 6). Tidak ada juga ringkasan
berkala ke log yang bisa dibaca manusia untuk memantau server tanpa harus
scrape /metrics -- padahal PROCESS_RSS_MB (gauge, ditambah di sesi 2) belum
pernah diisi/diperbarui sama sekali sejak dibuat.

**Solution:**
server/handlers/http.py: health_check() ditambah try/except independen per
field baru -- server_clock.uptime_seconds (via get_server_clock(request),
AppKey baru dari sesi 3), core.mem_stats.get_rss_mb() (sudah fail-safe
sendiri), dan len(manager.active_connections) (via get_manager(request)
existing) -- kalau salah satu gagal, field itu jadi null tanpa menggagalkan
field lain atau response 200-nya. Field status/db/mpv tidak diubah sama
sekali. Tambah accessor get_server_clock() di server/handlers/__init__.py
mengikuti pola get_conn/get_manager/get_playback_controller yang sudah ada
(file ini tidak locked, hanya tidak disebut eksplisit di files: task O4.1 --
diperlukan supaya http.py tidak perlu raw request.app[SERVER_CLOCK] yang
memutus konsistensi pola accessor bertipe di modul ini).

bootstrap/maintenance.py: status_log_task() -- while True + asyncio.sleep(15
menit), lalu baca 4 sumber data secara independen (masing-masing try/except
sendiri): ServerClock.uptime_seconds, ACTIVE_WEBSOCKETS gauge (_value.get()),
total request lewat helper baru _sum_counter_total() (menjumlahkan semua
sample '_total' dari Counter HTTP_REQUESTS_TOTAL lintas semua kombinasi
label method/path/status -- exact count, bukan pendekatan), dan
core.mem_stats.get_rss_mb() (dibungkus try/except tambahan di call site
juga, defense-in-depth walau get_rss_mb() sendiri sudah fail-safe). RAM yang
berhasil dibaca dipakai untuk PROCESS_RSS_MB.set() -- gauge diisi/diperbarui
untuk pertama kalinya sejak dibuat di sesi 2, sebelumnya cuma dideklarasikan.
Baris log final "[STATUS] uptime=Xm aktif=Y req=Z ram=WMB" (atau "n/a" per
komponen yang gagal) ditulis lewat try/except terluar sendiri supaya
kegagalan format string pun tidak mematikan loop. schedule_status_log()
mengikuti pola schedule_db_maintenance()/start_mpv_watchdog() persis
(context.tasks.append(safe_create_task(...))), sehingga otomatis ikut
ter-cancel bersih oleh loop shutdown main.py yang sudah ada tanpa perubahan
apa pun ke logic shutdown itu sendiri.

main.py: tambah 1 baris pemanggilan schedule_status_log() di main(), sejajar
dengan schedule_db_maintenance()/start_mpv_watchdog() yang sudah ada --
tanpa ini task baru tidak akan pernah dijadwalkan/berjalan sama sekali.
File ini bukan locked_files_global, hanya tidak eksplisit disebut di
files: O4.2 -- perubahan minimal, tidak mengubah urutan/logic startup atau
shutdown yang sudah ada.

**Changed Files:**
- `server/handlers/http.py`
- `server/handlers/__init__.py`
- `bootstrap/maintenance.py`
- `main.py`
- `tests/unit/server/handlers/test_http.py`
- `tests/unit/bootstrap/test_maintenance.py`

**Changed Symbols:**
- `health_check()`
- `get_server_clock()`
- `status_log_task()`
- `schedule_status_log()`
- `_sum_counter_total()`

**Tests:** tests/unit/server/handlers/test_http.py (9 test, 2 updated + 2 new), tests/unit/bootstrap/test_maintenance.py (7 test, 3 new) - semua passed; tests/unit (753 test, exclude launcher/gui) - semua passed; tests/integration (4 skipped, tidak ada regresi); architecture_lint.py --json PASS 0 new_violations

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-22-172

**Status:** Draft

**Notes:**
Sesi 4 dari task_breakdown_observability.yaml (task O4.1 + O4.2, patchlog_group
OG-3). Tidak ada env var atau dependency pip baru. server/handlers/websocket.py
tidak disentuh (locked_files_global dihormati). Dua file disentuh di luar
`files:` yang tertulis literal di task tapi BUKAN locked file dan diperlukan
supaya dod terpenuhi: server/handlers/__init__.py (tambah get_server_clock(),
konsistensi pola accessor -- O4.1) dan main.py (tambah 1 baris
schedule_status_log() -- O4.2, tanpa ini task periodik tidak pernah berjalan
maupun ter-cancel bersih saat shutdown seperti diminta dod).

Verifikasi: pytest tests/unit (exclude tests/unit/launcher/gui yang gagal
collect karena ModuleNotFoundError: No module named 'tkinter' -- tkinter
tidak ter-install di sandbox eksekusi ini, pre-existing environment gap,
tidak terkait fitur ini): 753 passed. pytest tests/integration: 4 skipped
(tidak ada regresi). architecture_lint.py --json: PASS, 0 new_violations.
doctor.py --json: overall_status FAIL, aggregate_score 77 -- IDENTIK dengan
hasil sesi 3 (2 FAIL yang sama persis: verify_docs FILE_INDEX karena
core/mem_stats.py, core/server_clock.py, server/middleware/traffic.py
belum tercatat dan server/middleware.py masih tercatat padahal sudah jadi
package -- regenerasi dijadwalkan sesi 5 (O5.1); verify_security karena
.gitignore tidak ada sejak arsip awal, di luar scope fitur ini) -- TIDAK ADA
FAIL BARU dibanding sesi 3.

---

## PATCH-2026-07-22-172

**Tanggal:** 2026-07-22
**Timestamp:** 11:17
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend/Observability
**Priority:** Medium
**Title:** server/middleware/traffic.py + wiring app.py + connection_manager.py durasi sesi WS

**Reason:** ADR-0010 butuh middleware traffic terpusat (req_id, HTTP_REQUESTS_TOTAL/HTTP_BYTES_TOTAL) dan durasi sesi WS aktif (ACTIVE_USER_SESSION_SECONDS)

**Root Cause:**
ADR-0010 butuh titik instrumentasi HTTP terpusat (bukan tersebar di tiap
handler), correlation id per request, dan durasi sesi WebSocket aktif --
belum ada satu pun dari ketiganya sebelum sesi ini. server/middleware.py
juga masih berupa modul tunggal (bukan package), sehingga tidak ada tempat
alami untuk menambah traffic.py tanpa mencampurnya dengan logic rate-limit
WS yang sudah ada di sana.

**Solution:**
server/middleware.py dikonversi jadi package server/middleware/ (__init__.py
tetap berisi check_rate_limit tidak berubah, plus re-export traffic_middleware)
-- import path lama "from server.middleware import check_rate_limit" tetap
valid, tidak ada call site yang perlu diubah. traffic.py: middleware aiohttp
tunggal (@web.middleware) yang assign req_id 8-hex via
structlog.contextvars.bind_contextvars() lalu reset_contextvars() di
finally, increment HTTP_REQUESTS_TOTAL(method,path,status) dan
HTTP_BYTES_TOTAL(direction=in|out) best-effort (try/except per metric,
tidak pernah menggagalkan request), dan log satu baris ringkas per request
selesai. web.HTTPException tetap di-raise ulang dengan status aslinya
(bukan disamarkan jadi 500). server/app.py: tambah web.AppKey SERVER_CLOCK
mengarah ke singleton core.server_clock.server_clock (pola sama dengan
AppKey lain di file ini), daftarkan traffic_middleware ke
web.Application(middlewares=[...]) tanpa mengubah urutan/isi middleware
lain (memang belum ada middleware lain terdaftar di level Application --
rate-limit WS tetap dipanggil manual di handle_ws_message, tidak diubah).
server/connection_manager.py: tambah dict connected_at (ws -> time.monotonic()
saat connect()), disconnect() menghitung durasi, mengamati ke
ACTIVE_USER_SESSION_SECONDS, dan menulis log
"WebSocket disconnected duration=...s total_clients=..." -- dibungkus
try/except supaya kegagalan observasi metric tidak pernah menggagalkan
disconnect() itu sendiri; juga aman dipanggil pada ws yang belum pernah
connect() (connected_at.pop(ws, None) tidak KeyError). server/handlers/
websocket.py TIDAK disentuh sama sekali -- ia sudah memanggil
manager.connect(ws)/manager.disconnect(ws) apa adanya, cukup untuk
instrumentasi baru ini bekerja tanpa refactor apa pun di file itu.

**Changed Files:**
- `server/middleware/__init__.py`
- `server/middleware/traffic.py`
- `server/app.py`
- `server/connection_manager.py`
- `tests/unit/server/middleware/test_traffic.py`
- `tests/unit/server/test_app.py`
- `tests/unit/server/test_connection_manager.py`

**Changed Symbols:**
- `traffic_middleware()`
- `_short_req_id()`
- `SERVER_CLOCK`
- `ConnectionManager.connected_at`
- `ConnectionManager.connect()`
- `ConnectionManager.disconnect()`

**Tests:** tests/unit/server/middleware/test_traffic.py (5 test baru), tests/unit/server/test_app.py (updated, 2 test), tests/unit/server/test_connection_manager.py (3 test baru + 3 existing) - semua passed; tests/unit (748 test, exclude launcher/gui) - semua passed

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-22-171

**Status:** Draft

**Notes:**
Sesi 3 dari task_breakdown_observability.yaml (task O3.1 + O3.2 + O3.3,
patchlog_group OG-2). Tidak ada env var atau dependency pip baru
ditambahkan. server/handlers/websocket.py tidak disentuh (locked_files_global
dihormati -- hanya dipanggil apa adanya). doctor.py --json setelah sesi ini:
overall_status FAIL, aggregate_score 77 -- KEDUANYA PRE-EXISTING, bukan
regresi baru dari sesi ini: (1) verify_docs FILE_INDEX FAIL karena
core/mem_stats.py, core/server_clock.py, server/middleware/traffic.py belum
tercatat dan server/middleware.py (dihapus, jadi package) masih tercatat --
regenerasi FILE_INDEX memang dijadwalkan di sesi 5 (O5.1), bukan tugas sesi
ini; (2) verify_security FAIL karena .gitignore tidak ada sama sekali di
repo yang di-upload untuk sesi ini -- dikonfirmasi manual file itu memang
tidak ada di arsip sejak awal, tidak disentuh atau dihapus oleh perubahan
apa pun di sesi ini, dan di luar scope observability_log_baseline.
architecture_lint.py --json: PASS, tidak ada NotAppKeyWarning baru.
pytest tests/unit (748 test, exclude tests/unit/launcher/gui yang gagal
collect karena ModuleNotFoundError: No module named 'tkinter' -- tkinter
tidak ter-install di sandbox eksekusi ini, pre-existing environment gap,
tidak disentuh oleh perubahan sesi ini): semua 748 passed.

---

## PATCH-2026-07-22-171

**Tanggal:** 2026-07-22
**Timestamp:** 11:03
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend/Observability
**Priority:** Medium
**Title:** core/log_config.py: split renderer file(plain)/console(auto-color) + correlation id + session banner

**Reason:** ADR-0010 butuh log human-readable/traceable: warna console auto-detect tanpa env var, req_id per request/sesi WS lewat structlog.contextvars, dan baris pemisah SESSION START/END

**Root Cause:**
simple_renderer lama satu jalur untuk file dan console (selalu plain), tidak ada correlation id per request/sesi, dan tidak ada baris pemisah sesi di log. Ditemukan juga: structlog.stdlib.ProcessorFormatter yang dipakai untuk render berbeda per-handler tidak kompatibel langsung dengan QueueHandler stdlib bawaan -- QueueHandler.prepare() men-stringify record.msg sebelum ProcessorFormatter di sisi QueueListener sempat memprosesnya sebagai dict, menyebabkan AttributeError saat runtime.

**Solution:**
simple_renderer dipecah jadi file_renderer (perilaku identik, plain ASCII selalu) dan console_renderer (menambah ANSI color berdasar _console_color_enabled() = sys.stdout.isatty() AND TERM tidak dumb/kosong -- auto-detect murni, tanpa env var baru). Ditambah structlog.contextvars.merge_contextvars di processor chain untuk req_id. Log routing memakai structlog.stdlib.ProcessorFormatter per-handler (file/console beda formatter), dipasang lewat _StructlogQueueHandler (subclass QueueHandler yang meng-override prepare() supaya TIDAK men-stringify record -- aman karena queue cuma dipakai lintas-thread dalam proses yang sama, bukan lintas proses). Tambah log_session_start()/log_session_end() yang menulis banner '==== SESSION START/END ... ====' langsung ke kedua handler (bypass processor chain, selalu plain, fail-safe try/except).

**Changed Files:**
- `core/log_config.py`
- `tests/unit/core/test_log_config.py`

**Changed Symbols:**
- `file_renderer()`
- `console_renderer()`
- `_console_color_enabled()`
- `simple_renderer`
- `log_session_start()`
- `log_session_end()`
- `_StructlogQueueHandler`

**Tests:** tests/unit/core/test_log_config.py (19 test, termasuk smoke test end-to-end req_id + no-ANSI-leak) - semua passed; full suite tests/unit/core/ (105 test) - semua passed; doctor.py --json overall_status WARN (pre-existing, tidak ada FAIL baru)

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** PATCH-2026-07-22-170

**Status:** Draft

**Notes:**
Sesi 2 task O2.2 dari task_breakdown_observability.yaml, patchlog: own. Backward-compat: simple_renderer = file_renderer (alias), semua 4 test lama untuk simple_renderer masih lulus tanpa perubahan assertion. Verifikasi manual: console_renderer menghasilkan ANSI hanya saat isatty()=True dan TERM valid (dicek dengan mock); file_renderer di kondisi sama tetap 100% plain. Belum ada wiring req_id assignment per-request (itu tugas middleware di sesi 3, O3.1) -- di sesi ini baru dipastikan contextvars ikut terbawa ke log line kalau di-bind manual.

---

## PATCH-2026-07-22-170

**Tanggal:** 2026-07-22
**Timestamp:** 10:58
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend/Observability
**Priority:** Medium
**Title:** core/observability.py: tambah 5 metric Prometheus traffic/RAM/uptime sesi

**Reason:** ADR-0010 butuh instrumentasi traffic HTTP/WS, RAM proses, dan durasi sesi user aktif untuk monitoring dasar

**Root Cause:**
Belum ada metric Prometheus untuk traffic HTTP/WS, RAM proses, dan durasi sesi user aktif - hanya ada metric command/event/websocket count dan resolve latency.

**Solution:**
Tambah Counter HTTP_REQUESTS_TOTAL(method,path,status), Counter HTTP_BYTES_TOTAL(direction), Counter WS_MESSAGES_TOTAL(direction), Gauge PROCESS_RSS_MB, Histogram ACTIVE_USER_SESSION_SECONDS. Metric lama (COMMAND_COUNT, COMMAND_LATENCY, EVENT_COUNT, ACTIVE_WEBSOCKETS, RESOLVE_LATENCY) tidak diubah sama sekali.

**Changed Files:**
- `core/observability.py`

**Changed Symbols:**
- `HTTP_REQUESTS_TOTAL`
- `HTTP_BYTES_TOTAL`
- `WS_MESSAGES_TOTAL`
- `PROCESS_RSS_MB`
- `ACTIVE_USER_SESSION_SECONDS`

**Tests:** python automation/doctor.py --json (WARN pre-existing FILE_INDEX, tidak ada FAIL baru); verifikasi manual get_metrics_content() memuat 5 metric baru + 5 metric lama tidak berubah

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-22-169

**Status:** Draft

**Notes:**
Sesi 2 task O2.1 dari task_breakdown_observability.yaml, patchlog: own. Metric belum dipakai di kode manapun (wiring middleware/connection_manager menyusul sesi 3). doctor.py melaporkan WARN (bukan FAIL) karena FILE_INDEX.md belum di-regenerate - ini memang dijadwalkan di sesi 5 finalisasi (generate_file_index.py), bukan regresi baru.

---

## PATCH-2026-07-22-169

**Tanggal:** 2026-07-22
**Timestamp:** 10:57
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend/Observability
**Priority:** Medium
**Title:** Modul dependency-free: core/mem_stats.py dan core/server_clock.py

**Reason:** ADR-0010: butuh baca RAM proses dan uptime server tanpa dependency pip baru (psutil pernah gagal install di Termux) dan tanpa env var baru

**Root Cause:**
Belum ada cara baca RSS proses maupun uptime server yang cross-platform (Termux/Android + Windows) tanpa dependency native compile (psutil gagal di Termux).

**Solution:**
mem_stats.py: baca /proc/self/status (VmRSS) di Linux/Termux, ctypes+psapi.GetProcessMemoryInfo di Windows, None fallback di platform lain/kegagalan apa pun, try/except menyeluruh. server_clock.py: kelas ServerClock berbasis time.monotonic() untuk uptime_seconds yang monoton, time.time() untuk start_time (wall clock), method init() untuk reset eksplisit dari main.py.

**Changed Files:**
- `core/mem_stats.py`
- `core/server_clock.py`
- `tests/unit/core/test_mem_stats.py`
- `tests/unit/core/test_server_clock.py`

**Changed Symbols:**
- `get_rss_mb()`
- `_get_rss_mb_proc()`
- `_get_rss_mb_windows()`
- `ServerClock`
- `ServerClock.uptime_seconds`

**Tests:** tests/unit/core/test_mem_stats.py (8 test), tests/unit/core/test_server_clock.py (4 test) - 12 passed

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-22-168

**Status:** Draft

**Notes:**
Sesi 1 dari task_breakdown_observability.yaml (task O1.1 + O1.2, patchlog_group OG-1). Dependency-free, tidak import layer lain. Belum di-wiring ke server/app.py (menyusul sesi 2-3). get_rss_mb() diverifikasi manual: mengembalikan 9.59 (float) di lingkungan Linux saat ini.

---

## PATCH-2026-07-22-168

**Tanggal:** 2026-07-22
**Timestamp:** 13:22
**Git Branch:** develop
**Git Commit:** 3f1e77f
**Type:** Docs
**Area:** AI_CONTEXT.md, README.md
**Priority:** Medium
**Title:** Docs audit lanjutan: update AI_CONTEXT.md dan README.md

**Reason:** AI_CONTEXT.md masih referensi cache/admin_password.txt (tidak ada lagi), ADR list hanya sampai 0006, contoh find_owner.py pakai file lama, heading duplikat. README.md referensi cache/library.db dan cache/<video_id>.mp3 (path lama), link MANUAL_BOOK.md (tidak ada), link CONTRIBUTING.md salah, fitur baru (EBU R128, discover personalization, bandit) belum disebut

**Root Cause:**
Kedua file tidak diupdate seiring sprint Phase 8. README.md masih deskripsi database path versi lama (sebelum migrasi persistence/ split). MANUAL_BOOK.md tidak pernah dibuat. AI_CONTEXT.md ADR list hanya 6 entry padahal sudah ada 9 ADR.

**Solution:**
AI_CONTEXT.md: hapus cache/admin_password.txt dari freeze list, tambah web.AppKey dan hash_token sebagai batasan wajib, update ADR list (0007-0009), fix contoh find_owner, fix duplikat heading, update last_verified. README.md: fix path database/cache, ganti MANUAL_BOOK.md ref dengan link docs/INDEX.md, tambah EBU R128 dan Discover Personalization ke fitur unggulan, tambah 4 cara menjalankan, fix CONTRIBUTING.md link

**Changed Files:**
- `AI_CONTEXT.md`
- `README.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
doctor.py tetap PASS 100/100 setelah update. Tidak ada perubahan source code.

---

## PATCH-2026-07-22-167

**Tanggal:** 2026-07-22
**Timestamp:** 13:19
**Git Branch:** develop
**Git Commit:** 3f1e77f
**Type:** Docs
**Area:** docs/INDEX.md, docs/architecture/folder_structure.md, docs/architecture/backend.md, docs/security/security.md, docs/security/threat_model.md, docs/backend/persistence.md, docs/backend/api.md, docs/backend/services.md
**Priority:** Medium
**Title:** Docs audit: update 8 file .md yang informasinya sudah usang dibanding source code

**Reason:** Source code jauh lebih maju dari dokumentasi. Banyak referensi file tidak ada, modul baru tidak terdokumentasi, dan beberapa informasi salah (FastAPI vs aiohttp, format command WS, token format, SECURITY.md status)

**Root Cause:**
Dokumentasi tidak diupdate seiring sprint Phase 8 + Hardening. Gap terbesar: bootstrap/, failure_ops, discover_repo, stream_cache, audio_stream_handler, ws_cache, semua automation tools baru tidak terdokumentasi. server/app.py masih disebut FastAPI. Token format dan CSWSH belum tercatat di security docs.

**Solution:**
Rewrite 3 file kritis (INDEX, folder_structure, backend.md). Update 5 file lain dengan tambalan spesifik: schema tracks (kolom unavailable), sessions (SHA-256 note), API format (type/action/data), CSWSH protection, logout action, radio_config constants baru, failure_ops, search_tracks method

**Changed Files:**
- `docs/INDEX.md`
- `docs/architecture/folder_structure.md`
- `docs/architecture/backend.md`
- `docs/security/security.md`
- `docs/security/threat_model.md`
- `docs/backend/persistence.md`
- `docs/backend/api.md`
- `docs/backend/services.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Docs tetap PASS 100/100 di doctor.py setelah update. File auto-generated (FILE_INDEX, REPORT, PATCHLOG) tidak disentuh.

---

## PATCH-2026-07-22-166

**Tanggal:** 2026-07-22
**Timestamp:** 13:07
**Git Branch:** develop
**Git Commit:** 3f1e77f
**Type:** Security
**Area:** core.security, persistence.session_repo, server.handlers.websocket, server.app, server.handlers
**Priority:** Medium
**Title:** Security hardening: session token hashing, CSWSH protection, web.AppKey migration

**Reason:** Token sesi disimpan plaintext di DB; WS handler tidak cek Origin header (CSWSH); app state pakai string keys (NotAppKeyWarning)

**Root Cause:**
Session repo tidak hash token sebelum INSERT; ws_handler tidak validasi Origin; app.py memakai pola app[string] yang deprecated

**Solution:**
Tambah hash_token/verify_token (SHA-256) di core.security; session_repo hash semua token sebelum DB ops; tambah check_ws_origin() di ws_handler; migrasi 7 app keys ke web.AppKey constants

**Changed Files:**
- `core/security.py`
- `persistence/session_repo.py`
- `server/handlers/websocket.py`
- `server/app.py`
- `server/handlers/__init__.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Sesi lama (plaintext token) otomatis invalid setelah restart — user perlu login ulang sekali. Klien non-browser (Termux/curl, tanpa Origin header) tetap diizinkan connect WS.

---

## PATCH-2026-07-22-165

**Tanggal:** 2026-07-22
**Timestamp:** 13:00
**Git Branch:** develop
**Git Commit:** 3f1e77f
**Type:** Fix
**Area:** Core
**Priority:** High
**Title:** Fixed head-of-line blocking in rate limit lock during PBKDF2 hashing

**Reason:** Identified deadlock pattern where rl_lock was held during CPU-heavy PBKDF2 hashing, blocking all other clients from sending commands because check_rate_limit also requires rl_lock.

**Root Cause:**
The asyncio.Lock (manager.rl_lock) was held across the entire login and setup process, including the loop.run_in_executor call for PBKDF2 (100k iterations).

**Solution:**
Narrowed the scope of the critical section by releasing rl_lock right before the hashing operation and re-acquiring it afterward to update rate limits or register the session.

**Changed Files:**
- `server/handlers/auth.py`
- `server/handlers/setup.py`

**Changed Symbols:**
- `handle_auth`
- `handle_setup_admin`

**Tests:** Code analysis and concurrency reproduction

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
Race conditions safely mitigated by re-fetching attempt lists upon re-entry and relying on sqlite3.IntegrityError for dual setup submissions.

---

## PATCH-2026-07-22-164

**Tanggal:** 2026-07-22
**Timestamp:** 12:34
**Git Branch:** develop
**Git Commit:** b503b4b
**Type:** Refactor
**Area:** Player
**Priority:** Medium
**Title:** Uniform crossfade duration via single constant across frontend and backend

**Reason:** User reported crossfade overlap wasn't noticeable because hardcoded fetch trigger remained at 2.0s even when fade-out was adjusted.

**Root Cause:**
Hardcoded 2.0 seconds existed in three separate places (fade-out duration, early fetch trigger, and fade-in duration), breaking overlap timing when modified individually.

**Solution:**
Extracted the constant to CROSSFADE_DURATION = 5.0 in playback-sync.js and synced the backend trigger (controller.py) and loops (crossfade.py) to 5.0 seconds.

**Changed Files:**
- `web/static/js/audio/playback-sync.js`
- `engine/playback/controller.py`
- `engine/playback/crossfade.py`

**Changed Symbols:**
- `apply_crossfade_in`
- `apply_crossfade_out`
- `ontimeupdate`

**Tests:** Manual validation

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
Included reverting a failed attempt to apply loudness normalization in the browser using Web Audio API due to cross-origin resource sharing mutes.

---

## PATCH-2026-07-22-163

**Tanggal:** 2026-07-22
**Timestamp:** 11:44
**Git Branch:** develop
**Git Commit:** b503b4b
**Type:** Feature
**Area:** Frontend
**Priority:** Medium
**Title:** PATCH-2026-07-22-163: True overlapping crossfade for browser audio

**Reason:** Previous crossfade implementation failed due to timing desync with MPV and single audio element limitation

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/audio/playback-sync.js`
- `web/static/js/render/player.js`
- `web/static/js/events/transport-events.js`

**Changed Symbols:**
- `audioPool`
- `syncBrowserAudio`
- `_fadeVolume`

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
-

---

## PATCH-2026-07-22-162

**Tanggal:** 2026-07-22
**Timestamp:** 11:34
**Git Branch:** develop
**Git Commit:** 3b8eb2d
**Type:** Fix
**Area:** Playback
**Priority:** Medium
**Title:** PATCH-2026-07-22-162: Fix crossfade and volume race condition

**Reason:** Fake crossfade-out behavior and volume change overwrite during fade

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `core/events.py`
- `engine/volume_service.py`
- `engine/playback/crossfade.py`
- `engine/playback/controller.py`
- `tests/unit/engine/playback/test_crossfade.py`

**Changed Symbols:**
- `VolumeChangedEvent`
- `apply_crossfade_out`
- `PlaybackController._on_volume_changed`

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
-

---

## PATCH-2026-07-22-161

**Tanggal:** 2026-07-22
**Timestamp:** 11:22
**Git Branch:** develop
**Git Commit:** 3b8eb2d
**Type:** Security
**Area:** Server
**Priority:** High
**Title:** Fix event loop starvation and rate limiting bypass in initial setup

**Reason:** Pembuatan hash password secara sinkron memblokir event loop utama, dan validasi rate limiting gagal mencatat percobaan gagal pada edge case tertentu.

**Root Cause:**
Fungsi hash_password dieksekusi sinkron di dalam websocket handler, serta rate limit increment hanya dilakukan pada error validasi input dasar.

**Solution:**
Bungkus hash_password dengan loop.run_in_executor dan buat fungsi helper _record_failure yang dipanggil di semua cabang kegagalan sebelum return.

**Changed Files:**
- `server/handlers/setup.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Mencegah event loop freeze ~100ms dan serangan DoS via submit credential saat setup.

---

## PATCH-2026-07-22-160

**Tanggal:** 2026-07-22
**Timestamp:** 11:13
**Git Branch:** develop
**Git Commit:** 3b8eb2d
**Type:** Refactor
**Area:** automation
**Priority:** Medium
**Title:** Remove unused dead code in generate_report.py

**Reason:** Merapikan basis kode dengan menghapus fungsi usang yang sudah tidak dipanggil sama sekali.

**Root Cause:**
Fungsi count_files_by_ext merupakan helper peninggalan lama yang tertinggal karena evolusi script reporting.

**Solution:**
Menghapus definisi fungsi count_files_by_ext dari file.

**Changed Files:**
- `automation/generate_report.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Trivial cleanup, confirmed unused.

---

## PATCH-2026-07-22-159

**Tanggal:** 2026-07-22
**Timestamp:** 11:11
**Git Branch:** develop
**Git Commit:** 3b8eb2d
**Type:** Performance
**Area:** radio
**Priority:** Medium
**Title:** Fix race condition in RadioPrefetcher.build_standby

**Reason:** Mengatasi eksekusi ganda yang sia-sia pada gather_batch akibat double-trigger saat user melakukan interaksi beruntun.

**Root Cause:**
Pengecekan _fetch_lock.locked() berada di luar context manager lock, menimbulkan TOCTOU yang membuat eksekusi mahal terjalankan 2x.

**Solution:**
Menerapkan double-checked locking secara tepat dengan re-check _standby di dalam blok self._fetch_lock.

**Changed Files:**
- `engine/radio/prefetcher.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Menghemat network call & DB queries ketika user menekan 'Acak' saat antrean lagu juga sedang tipis (memanggil build_standby secara bersamaan).

---

## PATCH-2026-07-22-158

**Tanggal:** 2026-07-22
**Timestamp:** 11:08
**Git Branch:** develop
**Git Commit:** 3b8eb2d
**Type:** Security
**Area:** server
**Priority:** Medium
**Title:** Invalidate session on logout

**Reason:** Mencegah token tetap valid setelah user menekan tombol Keluar.

**Root Cause:**
Fungsi logout di sisi client sebelumnya hanya menghapus token dari localStorage tanpa memberi tahu server untuk menghapus sesi dari database.

**Solution:**
Menambahkan pesan 'logout' via WebSocket yang akan memanggil sessions.delete_session(token) di server sebelum client menghapus token lokal.

**Changed Files:**
- `web/static/js/services/auth.js`
- `server/handlers/websocket.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Sekarang token benar-benar mati ketika user logout, mencegah penyalahgunaan token bekas (replay attack/curian via eksploitasi).

---

## PATCH-2026-07-22-157

**Tanggal:** 2026-07-22
**Timestamp:** 11:04
**Git Branch:** develop
**Git Commit:** 3b8eb2d
**Type:** Security
**Area:** server
**Priority:** Medium
**Title:** Implement silent token refresh and reduce TTL to 1 hour

**Reason:** Mitigasi resiko XSS dengan memperpendek usia token idle dan memperpanjang token otomatis di background.

**Root Cause:**
Token sesi sebelumnya tersimpan 24 jam di localStorage, yang merupakan single point of failure jika terdapat celah XSS.

**Solution:**
Mengubah TTL token baru menjadi 3 jam dan menambahkan mekanisme refresh interval di ws.js yang mengirim ulang perintah auth untuk memperpanjang sesi di DB secara senyap.

**Changed Files:**
- `core/ports.py`
- `persistence/session_repo.py`
- `server/handlers/auth.py`
- `web/static/js/ws.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Front-end audit confirms all external data currently uses escapeHtml() correctly, mitigating current immediate XSS risks.

---

## PATCH-2026-07-22-156

**Tanggal:** 2026-07-22
**Timestamp:** 11:00
**Git Branch:** develop
**Git Commit:** 3b8eb2d
**Type:** Fix
**Area:** bootstrap
**Priority:** Medium
**Title:** Fix 15-second delay on startup when mpv is not installed

**Reason:** User was forced to wait 15 seconds watching a loading screen before being told mpv is missing.

**Root Cause:**
mpv.connect() attempts to connect to the unix/pipe socket in a loop with 10 attempts and timeouts, without checking if the executable is available first.

**Solution:**
Add a shutil.which('mpv') guard clause in _init_mpv() to immediately set error state if mpv is not found.

**Changed Files:**
- `bootstrap/services.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Resolves a UX issue where startup seemed frozen when the primary dependency was missing.

---

## PATCH-2026-07-22-155

**Tanggal:** 2026-07-22
**Timestamp:** 10:49
**Git Branch:** develop
**Git Commit:** 3b8eb2d
**Type:** Feature
**Area:** Frontend
**Priority:** Medium
**Title:** Tambahkan token komponen RGB untuk dukungan warna alpha-blend

**Reason:** Mengatasi keterbatasan sistem CSS variabel yang sebelumnya tidak memiliki nilai RGB dasar, sehingga elemen yang butuh transparansi alpha (seperti starfield ambient background) terpaksa memakai RGB hardcode

**Root Cause:**
tokens.css versi awal hanya menyediakan token dalam format hex statis (#9AA0AA), sehingga rgba(var(--text-2), 0.3) mustahil dilakukan via CSS native

**Solution:**
Membuat varian RGB untuk background, text, dan accent (contoh: --text-2-rgb: 154, 160, 170) di tokens.css, dan memigrasikan nilai RGB hardcode pada efek radial-gradient di app-shell.css

**Changed Files:**
- `web/static/css/tokens.css`
- `web/static/css/layout/app-shell.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Solusi ini meminimalisir drift sekaligus memberikan keleluasaan pada developer untuk memakai modifier opacity menggunakan token standar (e.g. rgba(var(--text-1-rgb), 0.5))

---

## PATCH-2026-07-22-154

**Tanggal:** 2026-07-22
**Timestamp:** 10:47
**Git Branch:** develop
**Git Commit:** 3b8eb2d
**Type:** Cleanup
**Area:** Frontend
**Priority:** Medium
**Title:** Hilangkan sisa nilai hex warna hardcode pada player-bar.css dan cards.css

**Reason:** Mencegah drift pada styling elemen lencana dan ikon mood jika palet warna aplikasi diperbarui di masa depan

**Root Cause:**
Ada 3 nilai literal CSS (#60a5fa dan #f59e0b) yang tertinggal dan tidak tersinkronisasi dengan variabel warna utama pada tokens.css

**Solution:**
Mengganti literal #60a5fa menjadi var(--fm-blue) dan literal #f59e0b menjadi var(--fm-warn)

**Changed Files:**
- `web/static/css/components/player-bar.css`
- `web/static/css/components/cards.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Pembersihan warna ini menargetkan file CSS komponen (cards, player-bar) yang sebelumnya tidak terdeteksi dalam proses audit portal.css

---

## PATCH-2026-07-22-153

**Tanggal:** 2026-07-22
**Timestamp:** 10:24
**Git Branch:** develop
**Git Commit:** 2d463d4
**Type:** Cleanup
**Area:** Frontend
**Priority:** Medium
**Title:** Hilangkan nilai hardcode CSS di portal.css agar patuh pada design tokens

**Reason:** Mencegah drift diam-diam karena portal.css memuat nilai warna dan radius statis yang tidak sinkron bila token diubah di masa depan

**Root Cause:**
Developer lupa mengacu pada var() saat menambahkan styling layar admin di portal.css (misal #60a5fa dan 10px)

**Solution:**
Mengubah deklarasi statis menjadi referensi token murni: #60a5fa -> var(--fm-blue) dan 10px -> var(--r-sm)

**Changed Files:**
- `web/static/css/portal.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Memastikan seluruh nilai UI penting bersumber pada satu tempat tunggal yaitu tokens.css, layar pertama aplikasi kini lebih patuh design system

---

## PATCH-2026-07-22-152

**Tanggal:** 2026-07-22
**Timestamp:** 10:19
**Git Branch:** develop
**Git Commit:** 2d463d4
**Type:** Refactor
**Area:** Frontend
**Priority:** Medium
**Title:** Migrasi ikon custom SVG ke font Tabler di index.html

**Reason:** Mengatasi inkonsistensi bobot visual dan mengurangi duplikasi aset ikon

**Root Cause:**
Lima ikon persisten (nav bar & transport control) memakai inline SVG, sementara 41 ikon lain menggunakan font Tabler (stroke 2px) sehingga tidak harmonis

**Solution:**
Mengganti 5 SVG custom menjadi tag Tabler yang setara (ti-home, ti-radio, dll)

**Changed Files:**
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Font Tabler sudah diload, sehingga 0-cost network dan sepenuhnya menyelesaikan isu bobot ikon

---

## PATCH-2026-07-22-151

**Tanggal:** 2026-07-22
**Timestamp:** 10:16
**Git Branch:** develop
**Git Commit:** 2d463d4
**Type:** Docs
**Area:** Docs
**Priority:** Medium
**Title:** Tambahkan ADR-0009 untuk keputusan tipografi Radio Mode

**Reason:** Mengisi gap dokumentasi: Keputusan penggunaan font eksternal di Radio Mode belum memiliki ADR resmi sebagai referensi tetap

**Root Cause:**
Keputusan sebelumnya mengenai font Fraunces/Space Grotesk hanya tercatat di RFC yang bersifat working document, menimbulkan kecurigaan bahwa ini adalah 'drift' tak organik bagi yang tak membaca RFC penuh

**Solution:**
Membuat ADR permanen (0009) yang merangkum keputusan self-hosted & subsetting font eksternal untuk momen editorial Radio Mode

**Changed Files:**
- `docs/adr/0009-radio-mode-typography.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Sekarang pengembang baru dapat langsung merujuk ke ADR untuk menghindari perombakan tipografi secara tak sengaja

---

## PATCH-2026-07-22-150

**Tanggal:** 2026-07-22
**Timestamp:** 10:15
**Git Branch:** develop
**Git Commit:** 2d463d4
**Type:** Cleanup
**Area:** Frontend
**Priority:** Medium
**Title:** Tuntaskan migrasi token radius dan hapus dead code radius app

**Reason:** Migrasi alias radius ke canonical (--r-sm dkk) sudah selesai di semua komponen lain, tinggal menyisakan token sampah yang tidak terpakai

**Root Cause:**
Token --fm-radius-app (36px) sama sekali tidak dipakai, dan --fm-radius-sm hanya tersisa 2 penggunaan lama di settings-sheet.css

**Solution:**
Mengganti sisa --fm-radius-sm menjadi --r-sm di settings-sheet.css, dan menghapus seluruh blok alias --fm-radius-* dari tokens.css

**Changed Files:**
- `web/static/css/tokens.css`
- `web/static/css/components/settings-sheet.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Menuntaskan satu babak tech debt desain radius tanpa mengubah UI sama sekali

---

## PATCH-2026-07-22-149

**Tanggal:** 2026-07-22
**Timestamp:** 10:13
**Git Branch:** develop
**Git Commit:** 2d463d4
**Type:** Fix
**Area:** Frontend
**Priority:** Medium
**Title:** Tingkatkan kontras warna --fm-text-5 agar lolos standar WCAG AA

**Reason:** Nilai sebelumnya (#4A5060) memiliki rasio kontras 2.11:1 melawan --bg-elevated, gagal uji aksesibilitas

**Root Cause:**
Token text-5 yang digunakan untuk sub-label atau teks sekunder memiliki luminance terlalu rendah terhadap semua surface background (bg-primary, bg-surface, bg-elevated)

**Solution:**
Menaikkan brightness token ke #6b7280 yang memberikan rasio setidaknya ~4.6:1 terhadap background tergelap/terterang sekalipun

**Changed Files:**
- `web/static/css/tokens.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Warna baru tetap memberikan kesan muted/secondary tanpa mengorbankan keterbacaan (accessibility)

---

## PATCH-2026-07-22-148

**Tanggal:** 2026-07-22
**Timestamp:** 10:11
**Git Branch:** develop
**Git Commit:** 2d463d4
**Type:** Fix
**Area:** Frontend
**Priority:** Medium
**Title:** Hapus redundansi deklarasi .ss-action-btn di settings-sheet.css

**Reason:** Mencegah override senyap akibat deklarasi ganda dengan spesifisitas setara

**Root Cause:**
Grup selector di bagian atas file menetapkan radius var(--fm-radius-sm) (8px), sementara di bawah ada deklarasi var(--r-sm) (12px) yang menimpa secara senyap

**Solution:**
Menghapus .ss-action-btn dari grup selector gabungan di atas dan menjadikan blok spesifik di bawah sebagai satu-satunya single source of truth

**Changed Files:**
- `web/static/css/components/settings-sheet.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Menghilangkan kebingungan bagi developer yang membaca bagian atas file dan berharap style tersebut efektif

---

## PATCH-2026-07-22-147

**Tanggal:** 2026-07-22
**Timestamp:** 10:08
**Git Branch:** develop
**Git Commit:** 2d463d4
**Type:** Cleanup
**Area:** Frontend
**Priority:** Medium
**Title:** Remove dead token aliases and fix --fm-radius-sm drift

**Reason:** Beberapa alias CSS tidak pernah dipakai dan ada satu alias yang hardcoded nilai salah

**Root Cause:**
Desain sistem menyisakan alias lama dan hardcode --fm-radius-sm ke 8px alih-alih var(--r-sm)

**Solution:**
Menghapus 4 token yang tidak terpakai dan mengubah --fm-radius-sm menjadi referensi canonical var(--r-sm)

**Changed Files:**
- `web/static/css/tokens.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Tidak ada regresi visual karena token lama benar-benar dead code

---

## PATCH-2026-07-22-146

**Tanggal:** 2026-07-22
**Timestamp:** 10:01
**Git Branch:** develop
**Git Commit:** c0e4dac
**Type:** Performance
**Area:** Backend
**Priority:** Medium
**Title:** In-memory caching untuk artist reward stats pada radio bandit

**Reason:** Radio mode memanggil get_reward_stats (full-table scan) setiap refill batch

**Root Cause:**
get_reward_stats selalu query ke database meskipun data bisa di-cache

**Solution:**
Menambahkan dict _reward_cache in-memory yang menyimpan tuple alpha dan beta, serta meng-update-nya langsung di record_completion dan record_skip

**Changed Files:**
- `persistence/artist_repo.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
-

---

## PATCH-2026-07-22-145

**Tanggal:** 2026-07-22
**Timestamp:** 09:42
**Git Branch:** develop
**Git Commit:** c0e4dac
**Type:** Performance
**Area:** Backend
**Priority:** High
**Title:** Implementasi LRU Cache Eviction dan perbaikan IO blocking

**Reason:** Folder downloads/ bisa tumbuh tanpa batas dan pembacaan folder cache di ws_cache.py memblokir event loop

**Root Cause:**
Tidak ada background job eviction, dan I/O filesystem dipanggil sinkron di event loop utama

**Solution:**
Menambah batas MAX_CACHE_SIZE_BYTES (1GB), background job eviction berdasarkan LRU last_played, serta memindahkan I/O ke run_in_executor

**Changed Files:**
- `config.py`
- `server/handlers/ws_cache.py`
- `bootstrap/startup_tasks.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Clear cache via UI kini menghapus local_path dari DB

---

## PATCH-2026-07-22-144

**Tanggal:** 2026-07-22
**Timestamp:** 09:35
**Git Branch:** develop
**Git Commit:** c0e4dac
**Type:** Performance
**Area:** Backend
**Priority:** High
**Title:** Migrasi pencarian Discover ke FTS5 dan eksekusi paralel

**Reason:** Pencarian lambat di Termux karena full table scan linear dengan ukuran library

**Root Cause:**
Penggunaan kondisi LIKE pada pencarian membuat index SQLite B-Tree tidak bisa dipakai dan query sekuensial

**Solution:**
Membuat virtual table FTS5 tracks_fts dan songs_fts yang sinkron via triggers, mengganti query dengan MATCH dan bm25(). Fetch ke kedua sumber menggunakan asyncio.gather()

**Changed Files:**
- `persistence/schema.sql`
- `persistence/db.py`
- `persistence/discover_repo.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
FTS5 di-backfill otomatis saat startup pertama kali

---

## PATCH-2026-07-22-143

**Tanggal:** 2026-07-22
**Timestamp:** 09:30
**Git Branch:** develop
**Git Commit:** c0e4dac
**Type:** Fix
**Area:** Backend
**Priority:** High
**Title:** Terapkan decay pada Radio Bandit Thompson Sampling

**Reason:** Bandit membeku ke histori lama karena tidak ada cap atau peluruhan

**Root Cause:**
Varians distribusi Beta mengecil saat alpha+beta sangat besar karena update record_completion/record_skip tidak memiliki mekanisme decay, membuat eksplorasi mati

**Solution:**
Menambahkan faktor decay (0.98) pada kedua nilai alpha dan beta sebelum di-increment. Serta mengubah return type dari dict stats menjadi float.

**Changed Files:**
- `persistence/artist_repo.py`
- `core/ports.py`
- `docs/backend/persistence.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Mengubah return type dari get_reward_stats menjadi dict[str, tuple[float, float]]

---

## PATCH-2026-07-22-142

**Tanggal:** 2026-07-22
**Timestamp:** 09:21
**Git Branch:** develop
**Git Commit:** b94c0a5
**Type:** Fix
**Area:** Launcher
**Priority:** Medium
**Title:** Fix launcher not finding main.py

**Reason:** Server process failed to start because it looked for main.py in the launcher folder

**Root Cause:**
BASE_DIR in gui/app.py resolved to launcher directory instead of project root, causing subprocess to look for main.py in the wrong directory

**Solution:**
Updated BASE_DIR path resolution by appending an extra .parent to correctly point to the project root

**Changed Files:**
- `launcher/gui/app.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
-

---

## PATCH-2026-07-22-141

**Tanggal:** 2026-07-22
**Timestamp:** 09:16
**Git Branch:** develop
**Git Commit:** b94c0a5
**Type:** Fix
**Area:** engine.radio
**Priority:** Medium
**Title:** Fix Thompson Sampling dilution in radio mode

**Reason:** Radio mode was only personalizing 25% of songs and SQL query was extremely slow.

**Root Cause:**
gather_batch requested 1 artist from bandit but filled 4 slots. SQL query used ORDER BY RANDOM() on the entire table.

**Solution:**
Introduced BANDIT_QUOTA and EXPLORE_QUOTA. Sample multiple artists from bandit. Update get_random_songs to filter by artists if provided to prevent full table scan.

**Changed Files:**
- `engine/radio/radio_config.py`
- `engine/radio/artist_selector.py`
- `persistence/library_repo.py`
- `tests/unit/engine/radio/test_artist_selector.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Draft

**Notes:**
Radio batches now accurately reflect Thompson Sampling learning.

---

## PATCH-2026-07-21-140

**Tanggal:** 2026-07-21
**Timestamp:** 12:50
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Backend
**Priority:** High
**Title:** Fix blocking call di charging-gate loudness (regresi dari PATCH-139/PD-6)

**Reason:** Review teknis pasca-PATCH-139 (baca langsung ke source, bukan cuma klaim teks) menemukan `_is_charging_or_unknown()` yang baru ditambahkan di PD-6 dipanggil secara sinkron dari path async, berpotensi freeze seluruh server.

**Root Cause:**
`_is_charging_or_unknown()` (engine/loudness/service.py, ditambahkan di PATCH-139/PD-6) memanggil `subprocess.run([...], timeout=5)` secara blocking. Fungsi ini dipanggil langsung (tanpa `run_in_executor`) di dalam `analyze_and_store()` yang async, padahal baris tepat setelahnya sudah punya pola yang benar (`loop.run_in_executor(self._executor, self.analyzer.measure_sync, uri)`). Karena LunaWave single-process asyncio dan `analyze_and_store()` dijadwalkan fire-and-forget lewat `safe_create_task()` di event loop utama, kalau `termux-battery-status` lambat/hang, bukan cuma task loudness yang freeze -- WS, HTTP, dan broadcast progress ikut berhenti sampai 5 detik, persis di device (Termux/Android) yang jadi target fix PATCH-139.

**Solution:**
`_is_charging_or_unknown()` sekarang dipanggil lewat `await loop.run_in_executor(self._executor, _is_charging_or_unknown)`, mengikuti pola `measure_sync` di baris berikutnya, sebelum `get_running_loop()` dipindah ke atas gate. Tidak ada perubahan behavior/signature fungsi itu sendiri -- murni titik pemanggilannya yang dipindah keluar dari event loop utama.

**Changed Files:**
- `engine/loudness/service.py`

**Changed Symbols:**
- `LoudnessService.analyze_and_store()`

**Tests:** pytest -q tests/unit/engine/loudness/test_service.py (7 passed, termasuk test_skips_when_not_charging & test_proceeds_when_charging yang mem-patch `_is_charging_or_unknown` langsung); full suite pytest -q (716 passed, 4 skipped -- 2 test GUI tkinter di-skip karena environment sandbox review, tidak terkait fix ini); npx vitest run (20/20 passed, tidak tersentuh perubahan ini); repro manual: charging-check disimulasikan lambat 1s -> heartbeat loop lain tetap tick ~20x selama window itu (sebelum fix, event loop freeze total 1s).

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-21-139

**Status:** Merged

**Notes:**
Verifikasi manual di device Termux asli (memastikan charging-gate benar-benar tidak memblokir playback/WS saat `termux-battery-status` lambat) tetap perlu dilakukan langsung di perangkat, sama seperti catatan belum-terverifikasi di PATCH-139.

---

## PATCH-2026-07-21-139

**Tanggal:** 2026-07-21
**Timestamp:** 11:50
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Backend
**Priority:** High
**Title:** Background/battery survival Termux: notifikasi persistent, wake-lock, rAF stop saat hidden, WS backo

**Reason:** temuan.md: server LunaWave mati/baterai boros saat layar Android mati -- 7 temuan performa (PERF-1..7) dikonsolidasi jadi satu batch eksekusi (sesi 0-7) per task_breakdown_perf.yaml

**Root Cause:**
temuan.md (audit langsung ke source) mengidentifikasi 7 temuan performa/baterai (PERF-1..7) di LunaWave pada Termux/Android:
(1) notifikasi termux-notification tidak persistent (--ongoing absen), memudahkan user/OS menghapus notifikasi lalu Android membekukan proses;
(2) tidak ada wake-lock apapun (grep termux-wake-lock kosong), proses dibekukan Doze/HyperOS saat layar mati;
(3) tiga loop requestAnimationFrame independen (progress clock di player.js, visualizer FFT glow, radio moon phase) terus jalan walau tab/layar disembunyikan -- hanya satu listener visibilitychange existing di playback-sync.js dan itu pun tidak punya cabang document.hidden===true;
(4) WS client reconnect (ws.js onclose) retry flat setTimeout 2000ms tanpa backoff maupun kesadaran document.hidden;
(5) ConnectionManager.broadcast() kirim progress 1Hz ke SEMUA klien termasuk yang backgrounded (PERF-5, deferred -- lihat Notes);
(6) subprocess ffmpeg (loudness analyzer) dan worker thread yt-dlp (search/extract/resolve/download, shared ThreadPoolExecutor) jalan di prioritas default OS, bersaing CPU/IO dengan playback MPV, dan loudness batch analysis tidak charging-aware;
(7) persistence/db.py hanya set PRAGMA journal_mode=WAL, synchronous masih default FULL sehingga fsync per-commit lebih sering dari perlu.

**Solution:**
Dieksekusi mengikuti docs/rfc/performa/task_breakdown_perf.yaml (sesi 0-7, PD-1..PD-7 + PD-6b):
PD-1: tambah "--ongoing" + "--priority high" ke args termux-notification (_render(), plugins/notifications.py) -- persistent notification.
PD-2: modul baru bootstrap/power.py (acquire_wake_lock(), fail-safe, no-op Windows/binary hilang) diwire sebagai background task non-blocking di bootstrap/startup_tasks.py; didesain sebagai lapisan SEKUNDER -- lapisan PRIMER wajib tetap setup manual HyperOS/MIUI (Autostart, battery saver No restrictions, lock recent-apps), didokumentasikan di docs/CONSTRAINTS.md karena custom OEM power policy bisa mengabaikan wake-lock/notification API standar.
PD-3: extend listener visibilitychange existing di playback-sync.js jadi satu titik kontrol -- cabang hidden panggil stopProgressClock() (player.js), cabang visible panggil startProgressClock()/resumeVisualizerLoop()/setRadioHeroAnimState() ulang dari state DOM yang sudah dimiliki modul lain (read-only, tidak menulis store baru). visualizer.js dan radio-hero-moon.js (stepCycle/stepTween) masing-masing hanya dapat guard document.hidden self-terminating di titik reschedule rAF, tidak listener baru.
PD-4: exponential backoff 2s->4s->8s->16s->30s (cap, reset di ws.onopen) di ws.js onclose; listener visibilitychange KEDUA (sengaja terpisah dari PD-3, scope beda) untuk retry instan begitu tab kembali visible saat reconnect pending -- dibungkus typeof document !== "undefined" supaya tidak crash di test environment:node (vitest).
PD-5: PERF-5 (broadcast progress per-visibility, menyentuh server/handlers/websocket.py yang governed) SENGAJA DITUNDA -- lihat Notes.
PD-6/PD-6b: engine/loudness/analyzer.py bungkus subprocess ffmpeg dengan nice -n 10 + ionice -c2 -n7 (fail-safe, cek shutil.which terpisah); engine/loudness/service.py tambah _is_charging_or_unknown() (cek termux-battery-status field "status"=="CHARGING", fail-open kalau binary/field tidak dikenali) yang men-skip analisis loudness batch saat tidak charging; adapters/ytdlp/__init__.py tambah ThreadPoolExecutor initializer _set_worker_priority() yang panggil os.setpriority(PRIO_PROCESS, 0, 10) SEKALI per worker thread lifetime -- absolut (bukan os.nice() yang relatif/kumulatif dan akan starvation karena executor reuse lintas job) -- charging-gate SENGAJA TIDAK diterapkan ke yt-dlp karena search/download harus tetap responsif seketika (PD-6).
PD-7: tambah PRAGMA synchronous=NORMAL tepat setelah PRAGMA journal_mode=WAL di persistence/db.py.
QA (sesi 6): pytest -q 718 passed/6 skipped/0 failed (termasuk fix regresi test_run_startup_checks_schedules_three_background_tasks: 3->4 task setelah wake_lock_acquire ditambah, dan test baru tests/unit/engine/loudness/test_service.py 7 test untuk charging-gate); npx vitest run 20/20 passed; doctor.py --strict WARN->PASS setelah FILE_INDEX.md diregenerasi (bootstrap/power.py baru).

**Changed Files:**
- `plugins/notifications.py`
- `persistence/db.py`
- `bootstrap/power.py`
- `bootstrap/startup_tasks.py`
- `web/static/js/audio/playback-sync.js`
- `web/static/js/audio/visualizer.js`
- `web/static/js/render/radio-hero-moon.js`
- `web/static/js/ws.js`
- `engine/loudness/analyzer.py`
- `engine/loudness/service.py`
- `adapters/ytdlp/__init__.py`
- `docs/CONSTRAINTS.md`
- `docs/STATUS.md`
- `CHANGELOG.md`
- `tests/unit/bootstrap/test_startup_tasks.py`
- `tests/unit/engine/loudness/test_service.py`

**Changed Symbols:**
- `acquire_wake_lock()`
- `_render()`
- `_is_charging_or_unknown()`
- `_set_worker_priority()`
- `stepCycle()`
- `stepTween()`
- `startVisualizerLoop()`

**Tests:** pytest -q (718 passed, 6 skipped, 0 failed); npx vitest run (20/20 passed); doctor.py --strict (WARN->PASS setelah FILE_INDEX regen)

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
PERF-5 (F1.1, broadcast progress adaptif per-visibility klien) SENGAJA TIDAK termasuk patch ini -- deferred, butuh sign-off eksplisit terpisah karena menyentuh server/handlers/websocket.py yang governed di AI_CONTEXT.md. Didesain sebagai blok future_work terpisah di docs/rfc/performa/task_breakdown_perf.yaml, tidak masuk execution_order sesi 1-7. Tercatat eksplisit di docs/STATUS.md dan CHANGELOG.md supaya tidak terlihat seperti item yang lupa dikerjakan.
Referensi: temuan.md (sumber standalone, diberikan terpisah dari repo) dan docs/rfc/performa/task_breakdown_perf.yaml (PD-1, PD-2, PD-3, PD-4, PD-5, PD-6, PD-6b, PD-7).
Verifikasi manual di device Termux asli (notifikasi persistent, wake-lock aktif, niceness proses via ps/top, charging-gate loudness) belum dilakukan dari sandbox eksekusi ini -- perlu dicoba langsung di perangkat.

---

## PATCH-2026-07-21-138

**Tanggal:** 2026-07-21
**Timestamp:** 05:51
**Git Branch:** -
**Git Commit:** -
**Type:** Security
**Area:** Backend
**Priority:** Medium
**Title:** Log silent-except di 3 titik + tambah gate CI bandit/pip-audit/ruff

**Reason:** Follow-up audit teknis: try/except/pass menelan error tanpa jejak, dan bandit/pip-audit/ruff sudah ada di requirements-dev.txt tapi belum pernah jadi gate wajib di CI

**Root Cause:**
Audit codebase menemukan 3 titik except Exception: pass (plugins/notifications.py x2, server/handlers/websocket.py, server/handlers/ws_download.py) yang menelan error best-effort cleanup tanpa logging sama sekali, menyulitkan debugging kalau error sebenarnya bukan kasus benign yang diharapkan. Terpisah, CI (.github/workflows/ci.yml) hanya menjalankan doctor.py/patchlog verify/import-linter/pytest/vitest -- bandit, pip-audit, dan ruff sudah terpasang di requirements-dev.txt tapi tidak pernah dieksekusi otomatis, jadi regresi lint/security bisa lolos ke main tanpa terdeteksi.

**Solution:**
3 except Exception: pass diganti logger.debug() dengan pesan spesifik per lokasi (notifikasi Termux, cleanup fifo/action path, balasan error ke ws, hapus file legacy) -- tetap best-effort/non-fatal, tapi sekarang ada jejak log. Tambah job security-and-lint baru di ci.yml: ruff check ., bandit -r . -c pyproject.toml, pip-audit -r requirements.txt, sebagai gate wajib terpisah dari job health-checks yang sudah ada. Sempat salah duplikasi [tool.bandit] section di pyproject.toml karena run bandit pertama tidak pakai -c pyproject.toml (pakai profil default, bukan config project yang sudah skip B104/B608/B110 dkk dengan alasan yang sudah dipertimbangkan) -- sudah dikoreksi, section asli dipertahankan, tidak ada perubahan config bandit yang sebenarnya diperlukan.

**Changed Files:**
- `plugins/notifications.py`
- `server/handlers/websocket.py`
- `server/handlers/ws_download.py`
- `.github/workflows/ci.yml`

**Changed Symbols:**
- `-`

**Tests:** pytest -q (711 passed, 6 skipped), doctor.py --strict (100/100 x5), ruff check . (clean), bandit -r . -c pyproject.toml (clean), pip-audit -r requirements.txt (no known vulnerabilities)

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
Tidak ada perubahan pyproject.toml final -- draft penambahan [tool.bandit] baru sempat dibuat lalu di-revert setelah ketahuan section itu sudah ada dan lebih lengkap dari draft saya.

---

## PATCH-2026-07-21-137

**Tanggal:** 2026-07-21
**Timestamp:** 04:03
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Backend
**Priority:** High
**Title:** Fallback resilience streaming: bot-check/rate-limit/unavailable/prebuffer/prefetch-retry

**Reason:** Gap-analysis fallback skenario streaming diminta user: internet mati/lambat, YouTube limit/restrict butuh login, dan skenario lain yang bikin app gagal muter lagu tanpa fallback jelas

**Root Cause:**
Gap-analysis fallback-skenario streaming (diminta user) menemukan 5 klaim awal yang lolos verifikasi kode langsung (bukan asumsi): (1) adapters/ytdlp/resolver.py sebelumnya cuma punya 3 except generik (TimeoutError/RuntimeError/Exception) -- core/exceptions.py sudah punya TrackResolutionError/DownloadError tapi 0 pemakaian di seluruh repo (dead code), jadi bot-check/rate-limit/video-hilang semua jatuh ke RuntimeError generik yang sama, tidak bisa dibedakan strateginya. (2) server/handlers/audio_stream_handler.py: response.prepare() lalu langsung iter_chunked(16384) proxy ke client tanpa buffer sama sekali -- upstream lambat di detik pertama langsung bikin client stutter. (3) services/stream_prefetch.py: kegagalan cuma logger.warning() sekali, tidak ada retry sama sekali. (4) Tidak ada mekanisme menandai video yang sudah dikonfirmasi dihapus/private permanen -- video begitu akan terus dicoba resolve ulang selamanya tiap kali diputar/diprefetch (grep unavailable|is_private|is_deleted|blacklist ke persistence/engine/adapters = 0 hasil).

Investigasi awal juga sempat salah 4 kali sebelum sesi patch ini (dicabut setelah dibuktikan lewat pembacaan kode): retry_count diklaim bocor lintas-track (ternyata reset di sukses), mpv reconnect diklaim tanpa circuit breaker (ternyata ada RECONNECT_MAX_ATTEMPTS di adapters/mpv/observer.py), race prefetch-vs-ondemand diklaim berbahaya (ternyata cuma last-write-wins benign), dan yang paling signifikan: "tidak ada circuit breaker lintas-track" (klaim #5) juga salah -- controller._retry_count SUDAH berfungsi sebagai itu sejak awal (setiap kegagalan play_track APAPUN tracknya selalu _advance_to_next() dengan backoff naik, berhenti total tanpa advance setelah 3x beruntun), cuma lokasinya salah dicari (dicek di queue_controller.py, padahal yang relevan ada di play_track()'s except block sendiri).

Patch ini pertama dikerjakan+diuji di branch/rilis 1.5.1 (tests/unit 701/701 lulus), lalu di-port ke develop. Saat porting, ditemukan 2 hal: (a) engine/playback/controller.py di develop identik byte-for-byte dengan baseline pra-patch 1.5.1/1.5.2 (bukan refactor independen), jadi aman ditimpa; (b) sesi kerja sebelumnya di 1.5.1 ternyata sudah mengekstrak logic except play_track() ke engine/playback/failure_ops.py (LARGE_FILE_THRESHOLD 500 LOC, pola sama seperti track_ended_ops.py) yang sempat lupa ikut disalin ke develop, ketahuan lewat ModuleNotFoundError saat test run pertama di develop -- sudah diperbaiki dengan menyalin file tersebut.

**Solution:**
(1) core/exceptions.py: 3 exception baru VideoUnavailableError/BotCheckError/RateLimitedError (subclass TrackResolutionError). adapters/ytdlp/resolver.py: classify_ytdlp_error() cocokkan regex pesan yt-dlp ke 3 tipe; bot-check retry SEKALI dengan YDL_OPTS_INFO_FALLBACK (player_client=android, adapters/ytdlp/ydl_options.py) sebelum menyerah; error tak dikenal tetap RuntimeError generik (perilaku lama tidak berubah). engine/playback/failure_ops.py (FailureOps, dipanggil dari controller.py): handle_video_unavailable() skip TANPA backoff + mark_unavailable() ke DB; handle_bot_check_or_rate_limited() tetap backoff seperti error generik; keduanya + handle_generic_error() bermuara ke advance_after_track_failure() yang sama, memakai counter controller._retry_count yang SUDAH ADA sebagai circuit breaker lintas-track (bukan mekanisme baru).

(2) server/handlers/audio_stream_handler.py + config.py STREAM_PREBUFFER_BYTES=65536: buffer ~64KB pertama dari upstream SEBELUM mulai response.write() ke client. Range request pendek (<64KB sisa) tetap jalan wajar (loop berhenti begitu upstream habis).

(3) services/stream_prefetch.py: retry PREFETCH_RETRY_ATTEMPTS=2x dengan backoff PREFETCH_RETRY_BACKOFF_SEC sebelum menyerah.

(4) Kolom tracks.unavailable/unavailable_reason: schema.sql (DB baru) + migrasi ALTER TABLE di persistence/__init__.py (DB lama, lokasi canonical -- BUKAN persistence/db.py, sempat salah taruh di sana dulu di sesi 1.5.1 sampai ketahuan lewat test real-DB migrasi yang gagal). persistence/track_repo.py: mark_unavailable() pakai UPSERT bukan UPDATE polos (row belum tentu ada kalau resolve gagal di percobaan pertama). persistence/stream_cache.py (CacheResolver.resolve()) + audio_stream_handler.serve_stream(): Rule 0 cek flag ini duluan, skip yt-dlp kalau video sudah pernah gagal permanen. core/ports.py: TrackRepositoryPort Protocol diupdate agar kontraknya eksplisit.

(5) TIDAK ada patch baru untuk "circuit breaker lintas-track" -- lihat Root Cause, klaim ini dicabut, cuma menyambungkan exception baru ke mekanisme _retry_count yang sudah ada.

Bug tambahan yang ditemukan+diperbaiki selama proses (bukan direncanakan): 8 test lama tests/unit/server/handlers/test_audio_stream_handler.py pakai AsyncMock() polos yang auto-truthy -- Rule 0 baru bikin semua gagal sampai ditambah get_unavailable_reason.return_value=None eksplisit di semuanya. tests/fakes/fake_track_repository.py tidak punya record_completion()/record_skip() sama sekali (dipanggil queue_controller.advance_to_next(), AttributeError SINKRON sebelum sempat reach queue_mode.next() -- bukan di background task) -- ditambahkan no-op minimal. Migrasi kolom unavailable sempat ditaruh di persistence/db.py (lokasi yang ternyata TIDAK dipakai Repositories.init()) -- dipindah ke persistence/__init__.py yang canonical setelah test real-DB migrasi gagal.

**Changed Files:**
- `core/exceptions.py`
- `adapters/ytdlp/ydl_options.py`
- `adapters/ytdlp/resolver.py`
- `engine/playback/controller.py`
- `engine/playback/failure_ops.py`
- `persistence/schema.sql`
- `persistence/__init__.py`
- `persistence/track_repo.py`
- `persistence/stream_cache.py`
- `core/ports.py`
- `server/handlers/audio_stream_handler.py`
- `services/stream_prefetch.py`
- `config.py`
- `tests/fakes/fake_track_repository.py`
- `tests/unit/adapters/ytdlp/test_resolver.py`
- `tests/unit/engine/playback/test_controller.py`
- `tests/unit/persistence/test_track_repo.py`
- `tests/unit/persistence/test_stream_cache.py`
- `tests/unit/server/handlers/test_audio_stream_handler.py`
- `tests/unit/services/test_stream_prefetch.py`

**Changed Symbols:**
- `classify_ytdlp_error()`
- `VideoUnavailableError`
- `BotCheckError`
- `RateLimitedError`
- `FailureOps`
- `mark_unavailable()`
- `get_unavailable_reason()`
- `STREAM_PREBUFFER_BYTES`
- `advance_after_track_failure()`

**Tests:** 709/709 unit test develop lulus (255 di area yang disentuh langsung); ruff check bersih

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
Porting dari branch 1.5.1 (sudah punya PATCH-2026-07-21-135 di sana dengan format PATCHLOG v1/prosa) ke develop yang sudah bermigrasi ke format v2 field-based (PATCH-2026-07-20-135) -- entry ini ditulis langsung dalam format v2, bukan hasil migrasi otomatis. Semua file yang disentuh (11 file produksi + 1 file baru engine/playback/failure_ops.py + 7 file test) diverifikasi identik dengan baseline pra-patch develop sebelum ditimpa, jadi tidak ada risiko menghapus pekerjaan develop-specific lain (docs update PATCH-136, patchlog migration PATCH-135, pause-race PATCH-134 -- semua di area frontend/docs, tidak bersinggungan). Verifikasi akhir: 709/709 unit test develop lulus (255 di area yang disentuh langsung), ruff check bersih di semua file .py yang diubah.

---

## PATCH-2026-07-21-136

**Tanggal:** 2026-07-21
**Timestamp:** 09:12
**Git Branch:** develop
**Git Commit:** 5c580cf
**Type:** Docs
**Area:** Docs
**Priority:** Low
**Title:** Update dokumentasi inti (status, changelog, ai_context) agar sinkron dengan proyek

**Reason:** Informasi sprint dan status proyek sudah outdate

**Root Cause:**
Dokumentasi belum di-update pasca penyelesaian Fitur B dan C, menyebabkan mismatch timeline.

**Solution:**
Perbarui last_verified, sinkronisasi nama sprint, tambahkan Fitur C ke CHANGELOG, reformat tabel Fitur di STATUS.md

**Changed Files:**
- `docs/STATUS.md`
- `CHANGELOG.md`
- `AI_CONTEXT.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** N/A

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
Tabel Status Fitur yang semula acak-acakan karena paragraf yang terlalu panjang diubah formatnya agar mudah dibaca.

---

## PATCH-2026-07-20-135

**Tanggal:** 2026-07-20
**Timestamp:** 22:54
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Tooling
**Priority:** High
**Title:** Migrasi PATCHLOG.md ke format v2 field-based + refactor patchlog.py

**Reason:** Format v1 (prosa bebas per-entry) sulit di-grep presisi, duplikasi heading vs Ringkasan, tidak ada field terstruktur (Type/Area/Priority/Changed Symbols/dst.) -- lihat evaluasi di PATCHLOG_REDESIGN.md.

**Root Cause:**
Format v1 menjejalkan seluruh alasan/root-cause/proses investigasi/fix/hasil-test/edge-case ke dalam satu field Ringkasan prosa bebas, sekaligus diulang di heading -- rata-rata 684 karakter per entry, ~45% dari total isi file, tidak bisa di-query per kategori (mis. grep root cause tanpa noise), dan tidak ada field terstruktur (Type/Area/Priority/Changed Symbols/Breaking Change/Regression Risk/Status/Related Patch) walau info itu kadang disebut naratif.

**Solution:**
Ganti ke format v2: heading per-ID (## PATCH-...) sebagai satu-satunya sumber judul, diikuti field eksplisit (Tanggal/Timestamp/Git Branch/Git Commit -- auto; Type/Area/Priority -- semi-otomatis; Title/Reason/Root Cause/Solution/Changed Symbols/Tests/Breaking Change/Regression Risk/Related Patch/Status/Notes -- manual). Migrasi 134 entry v1 dikerjakan mekanis lewat automation/migrate_patchlog_v2.py (skrip sekali-jalan, dibuang setelah dipakai): Title = kalimat pertama Ringkasan lama (potong di '.'/'—' pertama, <=100 char), seluruh Ringkasan lama dipindah verbatim ke Notes (tidak dipecah otomatis ke Root Cause/Solution -- itu butuh pemahaman makna, berisiko salah kalau dikerjakan mesin), Type/Area/Priority/Status/Breaking Change/Regression Risk diisi 'Unclassified' (jujur menandakan belum diklasifikasi, bukan ditebak). Diverifikasi 0 mismatch antara 134 entry v1 vs v2 (ID/tanggal/files/isi Ringkasan-ke-Notes identik). patchlog.py direfactor: parsing regex generik FIELD_RE (satu pola untuk semua field, bukan regex per-field), _split_into_chunks() dipertahankan apa adanya (sudah teruji), CLI add baru dengan flag lengkap + fallback $EDITOR untuk field panjang, subcommand symbol baru untuk query Changed Symbols, verify() ditambah pengecekan enum. doc_parsing_utils.PATCH_ID_RE & checks_docs.py diupdate mengikuti heading baru.

**Changed Files:**
- `docs/PATCHLOG.md`
- `automation/patchlog.py`
- `automation/verify_docs/doc_parsing_utils.py`
- `automation/verify_docs/checks_docs.py`
- `tests/unit/automation/test_patchlog.py`
- `tests/unit/automation/test_find_owner_and_context_pack.py`

**Changed Symbols:**
- `parse_entry_fields()`
- `ENTRY_HEADING_RE`
- `FIELD_RE`
- `ENUM_FIELDS`
- `render_entry()`
- `suggest_area()`
- `PATCH_ID_RE`

**Tests:** pytest tests/unit/automation (33/33), python automation/doctor.py --strict (5/5 PASS 100), python automation/patchlog.py verify (134/134 parsed, 0 invalid enum)

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
hotspot.py dan context_pack.py (consumer parse_entries()) tidak diubah -- kontrak id+files dipertahankan. Test fixture di test_find_owner_and_context_pack.py diupdate ke format v2. Field Git Branch/Git Commit/Timestamp untuk 134 entry migrasi diisi '-' (tidak tersedia untuk histori lama, bukan ditebak).

---

## PATCH-2026-07-20-134

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Frontend
**Priority:** High
**Title:** pause_race_condition_fix — auto-play lagi sendiri di jaringan jelek

**Reason:** Dilaporkan user, dikonfirmasi lewat eksekusi kode asli sebelum patch.

**Root Cause:**
Optimistic UI update dilindungi grace-window waktu TETAP yang tujuannya menolak update status server yang datang sebelum server sempat memproses toggle kita. Di jaringan flaky, RTT sering > grace-window, jadi progress broadcast basi lolos dan menimpa balik status yang baru diset, memicu audio autoplay (FIX-RADIO-08 di ws.js).

**Solution:**
Ganti grace-window berbasis waktu dengan pending-target tracking (`markPendingToggle` + `isPendingToggleActive` di `store.js`). Client melacak status apa yang ditunggu konfirmasinya, dengan safety-valve 8 detik. `wsSend()` clear `pendingToggleTarget` pada navigasi track.

**Changed Files:**
- `web/static/js/store.js`
- `web/static/js/ws.js`
- `web/static/js/events/transport-events.js`
- `web/static/js/audio/playback-sync.js`
- `tests/frontend/pause-race.test.js`

**Changed Symbols:**
- `markPendingToggle`
- `isPendingToggleActive`

**Tests:** Regression test baru `tests/frontend/pause-race.test.js` (4 test). Suite lengkap 20/20 lulus.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-20-133

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI
**Priority:** Medium
**Title:** starfield_and_discover_scrollbar — ambient starfield pure-CSS site-wide + theming scrollbar Discover tab

**Reason:** Peningkatan visual: background site-wide statis dan scrollbar khusus tema gelap di Discover tab.

**Root Cause:**
Scrollbar Discover tidak flush ke tepi browser karena constraint lebar diterapkan ke `#tab-discover` (parent) bukan ke children-nya.

**Solution:**
(1) Tambahkan `background-image` radial-gradient ke `#content-area` untuk starfield statis. (2) Tambahkan CSS `::-webkit-scrollbar` ke `#tab-discover`. (3) Pindah constraint max-width/margin dari `#tab-discover` ke `#tab-discover > *` agar scrollbar mentok ke tepi layar.

**Changed Files:**
- `web/static/css/layout/app-shell.css`
- `web/static/css/components/discover-cards.css`
- `web/static/css/platform/desktop.css`
- `web/static/css/platform/landscape.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** Review manual cascade CSS. Cek ulang di browser nyata disarankan.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-20-132

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** UI/CSS
**Priority:** High
**Title:** radio_toggle_redesign — HOTFIX: .radio-hero collapse saat Radio ON

**Reason:** Bug report dari real-device (disertai screenshot): `.radio-hero` mengecil ke ~50px saat Radio ON dan daftar 'All Stations' terisi.

**Root Cause:**
Bug flexbox: `.radio-hero` adalah flex item di dalam `.tab-panel` (height:100%). Saat isi list melebihi tinggi container, flexbox mengecilkan children sesuai `flex-shrink` (default: 1) SEBELUM `#content-area` sempat scroll.

**Solution:**
Tambahkan `flex-shrink:0` dan `min-height:322px` (sebagai backstop) ke `.radio-hero` di `radio-hero.css`. Update comment R2.1 menjelaskan root cause baru.

**Changed Files:**
- `web/static/css/components/radio-hero.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** Playwright headless (chromium). Diuji pada mobile (400x700) dan desktop (1366x660) dengan state off/on dan kosong/terisi (4 kombinasi). Tinggi `.radio-hero` konsisten di 322px, scroll tetap normal. `doctor.py --strict` -> PASS 100.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-20-131

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** UI/CSS
**Priority:** Medium
**Title:** radio_toggle_redesign — Sesi 7 (PENUTUP): Cleanup CSS lama

**Reason:** Menutup seluruh fitur "Night Dial" (Sesi 1-7) dan membersihkan sisa kode lama.

**Root Cause:**
-

**Solution:**
Hapus 233 baris CSS lama (`.radio-featured`, `.centerpiece-*`, `.radio-live-badge` beserta keyframes terkait) dari `cards.css`. Regenerasi `FILE_INDEX.md` dan `REPORT.md`.

**Changed Files:**
- `web/static/css/components/cards.css`
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** `doctor.py --strict` PASS/100. Grep-ulang dependency untuk memastikan safe deletion.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-20-130

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-20-130

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** UI/JS
**Priority:** Medium
**Title:** radio_toggle_redesign — Sesi 6 (QA & Fix reduced-motion)

**Reason:** Tahap QA fitur Night Dial menemukan bug animasi untuk pengguna prefers-reduced-motion.

**Root Cause:**
Loop `requestAnimationFrame` tidak berhenti meskipun `prefers-reduced-motion` aktif.

**Solution:**
Update `radio-hero-moon.js`: Fallback ke render statis tanpa `rAF` sama sekali jika `prefers-reduced-motion` terdeteksi.

**Changed Files:**
- `web/static/js/render/radio-hero-moon.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** QA headless browser: rAF isolation stress-test (60x spam toggle) bersih, guard-role berfungsi. `doctor.py` PASS/100.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-20-129

**Status:** Merged

**Notes:**
Bug ditemukan namun belum difix: starfield overflow di viewport kecil (320/360px) dan landscape pendek.

---

## PATCH-2026-07-20-129

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/JS
**Priority:** Medium
**Title:** radio_toggle_redesign — Sesi 5: Wiring radio-tab.js

**Reason:** Implementasi hook animasi radio pada state on/off.

**Root Cause:**
-

**Solution:**
Hook `setRadioHeroAnimState(isRadio)` dipanggil dari `renderRadio()` dengan sinkronisasi `aria-pressed`. `radio-tab.js` tetap satu-satunya pemilik state on/off.

**Changed Files:**
- `web/static/js/render/radio-tab.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-20-128

**Status:** Merged

**Notes:**
Menutup Sesi 1-5 fitur "Night Dial" (font, CSS, modul JS animasi, markup index.html, wiring).

---

## PATCH-2026-07-20-128

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/HTML
**Priority:** Medium
**Title:** radio_toggle_redesign — Sesi 4: Update markup index.html

**Reason:** Pembaruan markup untuk mengaktifkan desain "Night Dial".

**Root Cause:**
-

**Solution:**
Markup `#radio-toggle-btn` diganti total ke desain "Night Dial" (`id`/`data-on`/`rt-sub` dipertahankan). Menambahkan `<link>` `radio-hero.css` dan `<script>` `radio-hero-moon.js`.

**Changed Files:**
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** `doctor.py` & `architecture_lint.py` tetap PASS 100.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-20-127

**Status:** Merged

**Notes:**
Gate governance-locked, dieksekusi setelah konfirmasi eksplisit user.

---

## PATCH-2026-07-20-127

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/JS
**Priority:** Medium
**Title:** radio_toggle_redesign — Sesi 3: Modul animasi radio-hero-moon.js

**Reason:** Implementasi modul animasi astronomi fase bulan untuk radio hero.

**Root Cause:**
-

**Solution:**
Pembuatan modul baru `radio-hero-moon.js` yang mengelola fase bulan, state machine rAF cycling/tweening, dan ekspos API publik `setRadioHeroAnimState(isOn)`.

**Changed Files:**
- `web/static/js/render/radio-hero-moon.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** Self-audit isolasi RFC §5.4 penuh lolos (tidak ada bocor state global, tidak ada coupling ke `playback-sync.js`/`player.js`).

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-20-126

**Status:** Merged

**Notes:**
Self-contained, module-scoped. Klik & subtitle tetap milik file lain sesuai RFC §5.3. Belum dapat diakses dari UI (menunggu sesi 4).

---

## PATCH-2026-07-20-126

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/CSS
**Priority:** Medium
**Title:** radio_toggle_redesign — Sesi 2: radio-hero.css

**Reason:** Implementasi gaya CSS untuk komponen radio hero yang baru ("Night Dial").

**Root Cause:**
-

**Solution:**
Pembuatan komponen `radio-hero.css` (container height:322px fixed, starfield, moon SVG + tuner ticks, badge status 2-state selalu-visible sesuai R-D2, hero-name/hero-sub). Semua animasi menggunakan transform/opacity/filter/stroke/fill (tidak ada reflow).

**Changed Files:**
- `web/static/css/components/radio-hero.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-20-125

**Status:** Merged

**Notes:**
Belum dapat diakses dari UI (menunggu integrasi modul JS animasi di sesi 3).

---

## PATCH-2026-07-20-125

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Asset
**Priority:** Medium
**Title:** radio_toggle_redesign — Sesi 1: Self-host fonts & skeleton CSS

**Reason:** Kebutuhan aset font dan fondasi awal untuk fitur "Night Dial".

**Root Cause:**
-

**Solution:**
Menambahkan font self-host (Fraunces italic 500, Space Grotesk 400/500/600) agar tidak bergantung pada CDN Google Fonts. Membuat skeleton awal `radio-hero.css` berisi `@font-face` dan CSS variable yang di-scope ke `.radio-hero`.

**Changed Files:**
- `web/static/fonts/fraunces/fraunces-latin-500-italic.woff2`
- `web/static/fonts/space-grotesk/space-grotesk-latin-400-normal.woff2`
- `web/static/fonts/space-grotesk/space-grotesk-latin-500-normal.woff2`
- `web/static/fonts/space-grotesk/space-grotesk-latin-600-normal.woff2`
- `web/static/fonts/LICENSE.md`
- `web/static/css/components/radio-hero.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
Belum dapat diakses dari UI manapun, fondasi awal.

---

## PATCH-2026-07-19-124

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Backend
**Priority:** Medium
**Title:** Doc cleanup (di luar task_breakdown_agent)

**Reason:** Memperbaiki drift dokumentasi vs kode aktual di `docs/backend/persistence.md` dan `docs/backend/services.md` hasil temuan audit pasca T-B19.

**Root Cause:**
-

**Solution:**
`persistence.md`: Update skema yang akurat untuk 7 tabel (termasuk `artist_genres` & `songs` yang baru ditambahkan). Perbaiki method Repository API yang fiktif. Pindah seksi Inisialisasi Database ke `DatabaseConnection+Repositories` aktual.
`services.md`: Update handlers dict fiktif ke `CommandRouter.register()`, update alur radio fiktif ke alur nyata `RadioMode`, update operasi queue ke `QueueOps`, perbaiki contoh kode di `volume_service.py` dan `discover_service.py`.

**Changed Files:**
- `docs/backend/persistence.md`
- `docs/backend/services.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** `doctor.py --strict` PASS 100. (Semua path test yang direferensikan diverifikasi ada di disk).

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-123

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-19-123

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Core
**Priority:** Medium
**Title:** T-B19 (lanjutan): finalisasi entry CHANGELOG

**Reason:** Fitur B (login_redesign) telah selesai, entry `CHANGELOG.md` perlu di-finalisasi.

**Root Cause:**
-

**Solution:**
Finalisasi entry di `CHANGELOG.md`: hapus status draft, tambahkan poin launcher tanpa auth (K5), env var override (K4), dan tautkan Dampak Upgrade (K3) ke `ADR-0008` (menggantikan link langsung ke `threat_model.md`).

**Changed Files:**
- `CHANGELOG.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-122

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-19-122

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Core
**Priority:** Medium
**Title:** T-B19: dokumentasi akhir Fitur B (login_redesign) & regenerasi index

**Reason:** Mendokumentasikan akhir Fitur B (login_redesign) untuk konsistensi dokumentasi.

**Root Cause:**
-

**Solution:**
`api.md`: Update alur HTTP basi ke alur nyata WS setup_admin/auth, gate `require_auth()` per-action, koreksi tabel error.
`persistence.md`: Tambah skema `admin_account` dan `AdminAccountRepository`.
`STATUS.md`: Set status Fitur B menjadi selesai.
`README.md`: Update bagian Mengakses Antarmuka Web (upgrade = logout paksa + wajib re-setup, kredensial lama tidak dimigrasikan). Regenerasi indeks dan laporan.

**Changed Files:**
- `docs/backend/api.md`
- `docs/backend/persistence.md`
- `docs/STATUS.md`
- `README.md`
- `docs/PATCHLOG.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** `doctor.py --strict` PASS penuh; `patchlog.py verify` tanpa entry rusak.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-121

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-19-121

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Security
**Priority:** High
**Title:** T-B18: ADR-0008 — kredensial admin di SQLite

**Reason:** Merekam keputusan arsitektural (ADR) untuk penyimpanan kredensial admin di SQLite tanpa migrasi otomatis.

**Root Cause:**
-

**Solution:**
Terbitkan `ADR-0008` yang menyatukan keputusan K3 (tidak ada migrasi otomatis), K4 (env var override), dan K5 (launcher tanpa mekanisme auth sendiri). Mencatat alternatif dan alasan penolakan. `threat_model.md` diupdate agar menunjuk ke ADR yang sudah terbit.

**Changed Files:**
- `docs/adr/0008-admin-credentials-in-sqlite.md`
- `docs/security/threat_model.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Yes

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-120

**Status:** Merged

**Notes:**
Konsekuensi eksplisit: user existing wajib re-setup (logout paksa) saat upgrade.

---

## PATCH-2026-07-19-120

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Launcher
**Priority:** Medium
**Title:** T-B16 — Launcher tanpa mekanisme auth sendiri

**Reason:** Kebutuhan implementasi K5 (launcher redirect fitur auth ke web browser).

**Root Cause:**
-

**Solution:**
T-B16.1: Hapus `launcher/auth_service.py`.
T-B16.2: Tulis ulang `auth_panel.py` agar `on_reset_password()` membuka browser (`webbrowser.open`), tidak ada generate/simpan password lokal. `app.py`: hapus `handle_first_run`. `ui_builder.py`: sederhanakan callback.
Test unit diupdate: `test_auth_panel.py` (assert webbrowser.open) dan `test_app.py` (hapus monkeypatch).

**Changed Files:**
- `launcher/auth_service.py`
- `launcher/gui/auth_panel.py`
- `launcher/gui/app.py`
- `launcher/gui/ui_builder.py`
- `tests/unit/launcher/gui/test_auth_panel.py`
- `tests/unit/launcher/gui/test_app.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Manual QA end-to-end (simulasi boot instalasi baru vs WS nyata). Regresi penuh: 667 passed, 6 skipped. `verify_security.py` PASS 100/100.

**Breaking Change:** Yes

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-119

**Status:** Merged

**Notes:**
Review `.gitignore`: pola `cache/admin_password.txt` & `instance/` dipertahankan selama masa transisi.

---

## PATCH-2026-07-19-119

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Core
**Priority:** Medium
**Title:** T-B15 — Bersih-bersih pasca cut-over kredensial

**Reason:** Pembersihan kode pasca penerapan mekanisme kredensial admin baru di SQLite.

**Root Cause:**
-

**Solution:**
T-B15.1: Verifikasi tidak ada konsumen `config_security.py`.
T-B15.2: Hapus `config_security.py` dan tes terkaitnya. Regenerasi `FILE_INDEX.md`.
T-B15.3: Pengujian akhir regresi dan e2e boot manual dengan SQLite nyata.

**Changed Files:**
- `config_security.py`
- `tests/unit/test_config_security.py`
- `docs/FILE_INDEX.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** Full suite regresi: 665 passed, 4 skipped. 3 skenario e2e boot manual. `doctor.py --strict` PASS 100.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-118

**Status:** Merged

**Notes:**
Instalasi lama dengan `cache/admin_password.txt` diabaikan, dan env var override `LUNAWAVE_ADMIN_PASS` berfungsi seed.

---

## PATCH-2026-07-19-118

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Core
**Priority:** High
**Title:** T-B14 — Hapus mekanisme legacy auto-generated admin password

**Reason:** Migrasi ke penyimpanan admin_account (SQLite) sebagai sumber kredensial login.

**Root Cause:**
-

**Solution:**
Hapus mekanisme lama auto-generated admin password di `config.py` dan blok banner di `main.py`. Tambahkan override `LUNAWAVE_ADMIN_PASS` / `YTGUI_ADMIN_PASS` lewat `config.ADMIN_PASSWORD_OVERRIDE` (dikonsumsi oleh `_seed_admin_account_from_env`). Hapus workaround di test suite.

**Changed Files:**
- `config.py`
- `bootstrap/services.py`
- `main.py`
- `tests/unit/test_config.py`
- `tests/unit/bootstrap/test_services.py`
- `tests/conftest.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Tambah 3 test baru untuk `_seed_admin_account_from_env`. 666 passed, 4 skipped. `doctor.py --strict` PASS.

**Breaking Change:** Yes

**Regression Risk:** Medium

**Related Patch:** PATCH-2026-07-19-117

**Status:** Merged

**Notes:**
Env var tidak akan meng-overwrite akun existing jika tabel sudah tidak kosong.

---

## PATCH-2026-07-19-117

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Auth
**Priority:** High
**Title:** T-B13 — Cut-over sumber kredensial login ke admin_account_repo

**Reason:** Transisi endpoint autentikasi menggunakan sumber kredensial baru berbasis SQLite.

**Root Cause:**
-

**Solution:**
Ubah `handle_auth` agar menggunakan `admin_account_repo` dan menerima objek `repos` utuh. Mitigasi timing side-channel dipertahankan via dummy PBKDF2 hash. Di `websocket.py`, pemanggilan `handle_auth` meneruskan objek `repos`.

**Changed Files:**
- `server/handlers/auth.py`
- `server/handlers/websocket.py`
- `tests/unit/server/handlers/test_auth.py`
- `tests/unit/server/handlers/test_websocket.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Yes

**Regression Risk:** High

**Related Patch:** PATCH-2026-07-19-116

**Status:** Merged

**Notes:**
Instalasi baru dan instalasi lama kini identik, wajib Initial Setup ulang, tidak ada migrasi otomatis (K3).

---

## PATCH-2026-07-19-116

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/JS
**Priority:** High
**Title:** Fitur B (login_redesign) — Sesi 6, T-B10..T-B12.2: CSS #setup-screen + wiring JS

**Reason:** Membangun antarmuka dan interaktivitas Initial Setup (Setup Admin).

**Root Cause:**
-

**Solution:**
T-B10: Styling `#setup-screen` (mirror `#portal-screen`) dan field Confirm Password di `portal.css`.
T-B11: JS `initSetupCheck()` (GET `/api/setup-required`) sebelum menampilkan screen. Fail-open saat fetch gagal.
T-B12: Logika verifikasi kecocokan password di `updateSetupSubmitState()`. `submitSetup()` memanggil `wsSend('setup_admin')`. Handle respons `setup_status` dari server untuk beralih layar.

**Changed Files:**
- `web/static/css/portal.css`
- `web/static/js/portal.js`
- `web/static/js/main.js`
- `web/static/js/dom.js`
- `web/static/js/events/index.js`
- `web/static/js/services/auth.js`
- `web/static/js/ws.js`
- `tests/frontend/ws-routing.test.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** 2 test baru di `ws-routing.test.js` (total 16 passed vitest). Regresi backend lengkap (663 passed, 6 skipped). `doctor.py --strict` PASS 100.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** PATCH-2026-07-19-115

**Status:** Merged

**Notes:**
Pengujian end-to-end tidak dapat dijalankan di sandbox karena pembatasan lingkungan.

---

## PATCH-2026-07-19-115

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/HTML
**Priority:** Medium
**Title:** Fitur B (login_redesign) — Sesi 5, T-B9.1..T-B9.2: Gate index.html #2

**Reason:** Implementasi struktur dasar halaman (markup HTML) untuk layar setup akun admin.

**Root Cause:**
-

**Solution:**
Tambahkan `#setup-screen` ke `index.html` dengan pola komponen yang sama dari `#portal-screen` existing. Tambah elemen ID baru (setup-form, setup-username, dll). Field Confirm Password memiliki elemen validasi tersendiri.

**Changed Files:**
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** Regresi penuh 663 passed, 6 skipped. `doctor.py --strict` PASS 100.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-114

**Status:** Merged

**Notes:**
Markup ini belum terlihat karena tidak ada styling CSS `display` di sesi ini, sesuai pendekatan pengembangan inkremental.

---

## PATCH-2026-07-19-114

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend
**Priority:** High
**Title:** Fitur B (login_redesign) — Sesi 4, T-B8: Routing setup_admin ke whitelist

**Reason:** Membuka akses untuk fitur `setup_admin` dari websocket client dan `GET /api/setup-required` dari HTTP client.

**Root Cause:**
-

**Solution:**
T-B8: Di `websocket.py`, action `setup_admin` di-special-case di `handle_ws_message()` SEBELUM `require_auth()` (mirror pola `auth`). Endpoint HTTP `GET /api/setup-required` didaftarkan di `server/app.py`. Unit test baru ditambah di `test_websocket.py` dan `test_app.py`.

**Changed Files:**
- `server/handlers/websocket.py`
- `server/app.py`
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/test_app.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Regresi WS lengkap: 663 passed, 2 skipped. `doctor.py --strict` PASS 100.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** PATCH-2026-07-19-113

**Status:** Merged

**Notes:**
`setup_admin` & `GET /api/setup-required` kini reachable end-to-end dari WS/HTTP client.

---

## PATCH-2026-07-19-113

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Security
**Priority:** High
**Title:** Fitur B (login_redesign) — Sesi 3, T-B6..T-B7: Dok K3 & fallback kegagalan setup

**Reason:** Mendokumentasikan keputusan keamanan (K3) dan menangani kegagalan sistem saat setup admin.

**Root Cause:**
-

**Solution:**
T-B6: Tambah section 'Kredensial Admin Tidak Dimigrasikan Otomatis (K3)' di `threat_model.md`. Draft catatan upgrade ditambah ke `CHANGELOG.md`.
T-B7: Di `setup.py`, tambah try/except di 3 titik (admin_account_exists, create_admin_account, setup_required HTTP endpoint). Kegagalan di-log eksplisit tanpa bocor ke client. HTTP 503 dikembalikan alih-alih 500.

**Changed Files:**
- `docs/security/threat_model.md`
- `CHANGELOG.md`
- `server/handlers/setup.py`
- `tests/unit/server/handlers/test_setup.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** 3 skenario fallback ditambah ke test unit. Regresi penuh: 661 passed, 2 skipped. `verify_security.py` PASS 100.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** PATCH-2026-07-19-112

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-19-112

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend
**Priority:** High
**Title:** Fitur B (login_redesign) — Sesi 2, T-B5.1..T-B5.6: Handler setup_admin lengkap

**Reason:** Menyediakan backend logic untuk menerima, memvalidasi, dan menyimpan setup admin_account.

**Root Cause:**
-

**Solution:**
Buat `server/handlers/setup.py` dengan fungsi `handle_setup_admin()`: validasi username wajib + password min 8 karakter, hashing via `hash_password`, simpan ke `admin_account`. Menangani race condition dengan 2 lapis cek (exists & IntegrityError). Tambah rate limit 5x/5menit di `connection_manager.py` (state `setup_attempts`). Fungsi `setup_required(request)` disediakan untuk HTTP.

**Changed Files:**
- `server/handlers/setup.py`
- `server/connection_manager.py`
- `tests/unit/server/handlers/test_setup.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** 11 skenario unit test baru di `test_setup.py` (semua hijau). Regresi penuh: 658 passed, 2 skipped.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** PATCH-2026-07-19-111

**Status:** Merged

**Notes:**
Belum reachable dari client (belum ada whitelist di websocket.py).

---

## PATCH-2026-07-19-111

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** DB
**Priority:** High
**Title:** Fitur B (login_redesign) — Sesi 1, T-B1..T-B4: Infrastruktur admin_account

**Reason:** Pembuatan infrastruktur DB tabel `admin_account` yang diperlukan untuk login redesign.

**Root Cause:**
-

**Solution:**
Tabel `admin_account` ditambah ke `schema.sql`. Buat repositori baru `AdminAccountRepository` (`persistence/admin_account_repo.py`) dengan fungsi create/get/exists. Repositori didaftarkan di `persistence/__init__.py`.

**Changed Files:**
- `persistence/schema.sql`
- `persistence/admin_account_repo.py`
- `persistence/__init__.py`
- `tests/unit/persistence/test_admin_account_repo.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** 4 skenario unit test baru di `test_admin_account_repo.py` (semua hijau). `doctor.py --strict` PASS 100.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-110

**Status:** Merged

**Notes:**
Belum reachable dari client.

---

## PATCH-2026-07-19-110

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** UI/JS
**Priority:** Medium
**Title:** T-A9: registrasi elemen DOM baru Quick Search Discover ke dom

**Reason:** Setup referensi elemen DOM agar fitur Quick Search Discover bisa menggunakan `dom.*`.

**Root Cause:**
-

**Solution:**
Registrasikan 10 elemen baru untuk Quick Search Discover di `dom.js` (beserta fungsi filterScopeHint & rowUnheardLabel). Update `discover-search-events.js` dan `render/discover-search.js` agar menggunakan referensi `dom.*`.

**Changed Files:**
- `web/static/js/dom.js`
- `web/static/js/events/discover-search-events.js`
- `web/static/js/render/discover-search.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** `doctor.py --strict` PASS 100.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-109

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-19-109

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/JS
**Priority:** Medium
**Title:** T-A8: file baru web/static/js/render/discover-search

**Reason:** Kebutuhan logic frontend untuk me-render hasil pencarian Quick Search Discover.

**Root Cause:**
-

**Solution:**
Buat `web/static/js/render/discover-search.js` dengan me-reuse `.sr-item`. Terdapat 5 state lengkap dengan toggle blok personalisasi dan guard request basi. Tambahkan container dan script di `index.html`. Sedikit wiring di `ws.js` dan `discover-search-events.js`.

**Changed Files:**
- `web/static/js/render/discover-search.js`
- `web/static/index.html`
- `web/static/js/ws.js`
- `web/static/js/events/discover-search-events.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** `doctor.py --strict` PASS 100.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** PATCH-2026-07-19-108

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-19-108

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/JS
**Priority:** Medium
**Title:** T-A7: file baru web/static/js/events/discover-search-events

**Reason:** Event handling untuk Quick Search Discover di frontend.

**Root Cause:**
-

**Solution:**
Buat `web/static/js/events/discover-search-events.js`. Event trigger `wsSend('discover_search')` dipanggil dengan debounce 500ms atau tombol Enter. Tombol clear mereset filter. Didaftarkan ke `initEvents()` di `events/index.js` dan script dimuat di `index.html`.

**Changed Files:**
- `web/static/js/events/discover-search-events.js`
- `web/static/js/events/index.js`
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** `doctor.py --strict` PASS 100.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** PATCH-2026-07-19-107

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-19-107

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/CSS
**Priority:** Medium
**Title:** T-A6: CSS baru web/static/css/components/discover-search

**Reason:** Styling untuk fitur Quick Search Discover.

**Root Cause:**
-

**Solution:**
Tambahkan `web/static/css/components/discover-search.css` menggunakan token spacing project-wide. `.filter-bar`/`.segmented`/`.custom-dropdown` di-reuse. Dimuat di `index.html`.

**Changed Files:**
- `web/static/css/components/discover-search.css`
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** `verify_structure.py` & `doctor.py --strict` PASS 100.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-106

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-19-106

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/HTML
**Priority:** Medium
**Title:** T-A5: markup Quick Search Discover di web/static/index

**Reason:** Struktur DOM (markup) untuk search bar dan filter row Quick Search Discover.

**Root Cause:**
-

**Solution:**
Tambahkan markup `.discover-search-wrap` dan filter row ke `#tab-discover` (sebelum `.taste-block`) di `index.html`. Reuse class yang sudah ada.

**Changed Files:**
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-105

**Status:** Merged

**Notes:**
Belum ada JS wiring.

---

## PATCH-2026-07-19-105

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend
**Priority:** Medium
**Title:** T-A4: tambah 'discover_search' ke DISCOVERY_CMDS

**Reason:** Endpoint websocket `discover_search` butuh di-whitelist.

**Root Cause:**
-

**Solution:**
Tambah `discover_search` ke `DISCOVERY_CMDS` di `server/handlers/websocket.py`.

**Changed Files:**
- `server/handlers/websocket.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** `doctor.py --strict` PASS 100.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-104

**Status:** Merged

**Notes:**
Belum ditest manual di browser sungguhan.

---

## PATCH-2026-07-19-104

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** DB
**Priority:** Medium
**Title:** Quick Search Discover (T-A1..T-A3)

**Reason:** Logika filter dan pencarian database untuk Quick Search Discover.

**Root Cause:**
-

**Solution:**
Tambahkan `search_tracks()` di `discover_repo.py` dengan pencarian LIKE title/artist dan subquery filter kategori/dekade. Tambah branch `discover_search` di `ws_discovery.py`.

**Changed Files:**
- `persistence/discover_repo.py`
- `tests/unit/persistence/test_discover_repo_search.py`
- `server/handlers/ws_discovery.py`
- `tests/unit/server/handlers/test_ws_discovery.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Unit test baru.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-19-103

**Status:** Merged

**Notes:**
Belum reachable dari client -- menunggu izin T-A4 (DISCOVERY_CMDS).

---

## PATCH-2026-07-18-103

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Cleanup
**Area:** Core
**Priority:** Low
**Title:** Rename nama generik: adapters/ytdlp/common

**Reason:** Memperbaiki penamaan file agar lebih spesifik dan menghindari nama generik seperti `common.py` atau `helpers.py`.

**Root Cause:**
-

**Solution:**
Rename `adapters/ytdlp/common.py` -> `ydl_options.py`, `engine/radio/common.py` -> `radio_config.py`, `automation/verify_docs/helpers.py` -> `doc_parsing_utils.py`. Perbaiki docstring 'Depends on' yang usang.

**Changed Files:**
- `adapters/ytdlp/ydl_options.py`
- `adapters/ytdlp/searcher.py`
- `adapters/ytdlp/resolver.py`
- `adapters/ytdlp/downloader.py`
- `engine/radio/radio_config.py`
- `engine/radio/artist_selector.py`
- `engine/radio/engine.py`
- `engine/radio/prefetcher.py`
- `automation/verify_docs/doc_parsing_utils.py`
- `automation/verify_docs/render.py`
- `automation/verify_docs/checks_files.py`
- `automation/verify_docs/checks_coverage.py`
- `automation/verify_docs/checks_docs.py`
- `automation/verify_docs.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-102

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Test
**Area:** Testing
**Priority:** Low
**Title:** Rename file test yang menyimpang konvensi penamaan

**Reason:** Menjaga konsistensi penamaan file test agar dikenali test runner.

**Root Cause:**
-

**Solution:**
Rename file `test_store.test.js`, `test_ws-routing.test.js`, `test_app_lifecycle.py`. Konsolidasi `test_ytdlp.py` dan `test_ytdlp_client.py` menjadi satu file (menggunakan suffix `ViaYtDlpClient` agar tidak bentrok).

**Changed Files:**
- `tests/frontend/store.test.js`
- `tests/frontend/ws-routing.test.js`
- `tests/unit/launcher/gui/test_app.py`
- `tests/unit/adapters/ytdlp/test_ytdlp.py`
- `docs/testing/README.md`
- `docs/testing/frontend_testing.md`
- `docs/architecture/folder_structure.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** Verified: 620 passed tetap sama.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
Semua 42 assertion/test case dipertahankan di file konsolidasi.

---

## PATCH-2026-07-18-101

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Docs
**Priority:** Low
**Title:** Rename ADR 003-Crossfade

**Reason:** Standardisasi penamaan file ADR (Architecture Decision Record).

**Root Cause:**
-

**Solution:**
Rename `003-Crossfade.md` menjadi `0007-crossfade.md` dan samakan judul internal menjadi `ADR-0007`.

**Changed Files:**
- `docs/adr/0007-crossfade.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
Entri historis di PATCHLOG.md sengaja dibiarkan.

---

## PATCH-2026-07-18-100

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Build
**Area:** Tooling
**Priority:** Medium
**Title:** Perluas aturan importlinter

**Reason:** Mempertegas batasan impor antar modul agar tidak ada coupling yang salah.

**Root Cause:**
-

**Solution:**
Perluas `.importlinter`: `automation` dan `data` dijadikan root package terisolasi (`automation` tidak boleh diimpor produksi, `data` hanya boleh diimpor `automation`). Konfirmasi `cache/` sudah bukan package Python.

**Changed Files:**
- `.importlinter`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-099

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Backend
**Priority:** Medium
**Title:** Tambahkan accessor get_*() bertipe di server/handlers/__init__

**Reason:** Memberikan pengetikan (type hint) untuk akses atribut di dalam `request.app`.

**Root Cause:**
-

**Solution:**
Tambahkan helper `get_*()` bertipe untuk semua key `request.app[...]` (seperti `repos`, `tracks`, `conn`, dll). Helper ini menggantikan akses dictionary mentah agar kode lebih type-safe.

**Changed Files:**
- `server/handlers/__init__.py`
- `server/handlers/http.py`
- `server/handlers/websocket.py`
- `server/handlers/audio_stream_handler.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
`get_db()` sudah tidak relevan dan diganti akses per-repo.

---

## PATCH-2026-07-18-098

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Backend
**Priority:** Low
**Title:** Tambahkan type hint DatabasePort

**Reason:** Menambahkan anotasi tipe pada dependency injection layer engine.

**Root Cause:**
-

**Solution:**
Tambahkan type hint `DatabasePort` ke constructor engine yang menerima dependensi database.

**Changed Files:**
- `core/ports.py`
- `engine/radio/artist_selector.py`
- `engine/radio/engine.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-097

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Data
**Priority:** Low
**Title:** Audit data/: artists_enriched1

**Reason:** Mengevaluasi keberadaan file `artists_enriched1.json` pasca perbaikan database.

**Root Cause:**
-

**Solution:**
Didokumentasikan di `STATUS.md` bahwa file `artists_enriched1.json` (854 artis) bukan duplikat dari versi 100 artis, sehingga tidak dihapus. Konfirmasi `export_to_sqlite.py` tetap berada di `data/`.

**Changed Files:**
- `docs/STATUS.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-096

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Backend
**Priority:** Medium
**Title:** Pisah serve_stream (range-request) ke audio_stream_handler

**Reason:** Memisahkan logika handler stream audio dari HTTP handler umum untuk kerapian.

**Root Cause:**
-

**Solution:**
Ekstrak fungsionalitas `serve_stream` (dukungan HTTP range-request) ke `server/handlers/audio_stream_handler.py`.

**Changed Files:**
- `server/handlers/audio_stream_handler.py`
- `server/handlers/http.py`
- `server/app.py`
- `tests/unit/server/handlers/test_audio_stream_handler.py`
- `tests/unit/server/handlers/test_http.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-095

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Backend
**Priority:** Medium
**Title:** Pisah skor rekomendasi ke services/discover_ranking

**Reason:** Memisahkan logika komputasi skor rekomendasi yang murni fungsional dari lapisan DB.

**Root Cause:**
-

**Solution:**
Ekstrak logika komputasi probabilitas skor (`compute_match_pct`, taste spectrum) ke `services/discover_ranking.py`. Fungsi ini kini murni dan independen dari operasi database.

**Changed Files:**
- `services/discover_ranking.py`
- `persistence/discover_repo.py`
- `services/discover_service.py`
- `tests/unit/services/test_discover_ranking.py`
- `tests/unit/persistence/test_discover_repo.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-094

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** UI/Launcher
**Priority:** Low
**Title:** Ekstrak auth_service

**Reason:** Memisahkan logika autentikasi dari komponen UI.

**Root Cause:**
-

**Solution:**
Ekstrak `auth_service.py` dari `auth_panel.py`, memisahkan logika backend-facing dari presentasi UI.

**Changed Files:**
- `launcher/auth_service.py`
- `launcher/gui/auth_panel.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-093

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** UI/Launcher
**Priority:** Low
**Title:** Pecah build_ui() jadi 4 method privat di ui_builder

**Reason:** Memecah method `build_ui()` yang terlalu besar agar lebih modular dan mudah dipelihara.

**Root Cause:**
-

**Solution:**
Pecah fungsi `build_ui()` menjadi 4 method privat di dalam `ui_builder.py`.

**Changed Files:**
- `launcher/gui/ui_builder.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-092

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** UI/Launcher
**Priority:** Low
**Title:** Ekstrak ServerLifecycle dari ServerManager

**Reason:** Melepaskan dependensi logika lifecycle server dari komponen antarmuka (Tkinter).

**Root Cause:**
-

**Solution:**
Ekstrak `ServerLifecycle` dari `ServerManager` di `launcher/gui/app.py` agar tidak memiliki dependensi Tkinter.

**Changed Files:**
- `launcher/gui/app.py`
- `launcher/server_lifecycle.py`
- `launcher/gui/log_view.py`
- `tests/unit/launcher/test_server_lifecycle.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-091

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Docs
**Priority:** Low
**Title:** Perbaiki typo/leftover text di docs/STATUS

**Reason:** Membersihkan sisa teks draf yang tidak sengaja ter-commit.

**Root Cause:**
-

**Solution:**
Perbaiki typo/leftover text di `docs/STATUS.md` pada baris `services/stream_prefetch.py`.

**Changed Files:**
- `docs/STATUS.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-090

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Backend
**Priority:** Medium
**Title:** T2.7: Satukan services/ dan server/services/

**Reason:** Menyederhanakan struktur direktori services.

**Root Cause:**
-

**Solution:**
Pindahkan `stream_prefetch.py` ke `services/`. Pindahkan `broadcast_service.py` ke `server/broadcast_service.py` (bukan root `services/` karena dependensi pada web layer, menghindari pelanggaran kontrak `importlinter`). Hapus folder `server/services/`. Update importer dan tes terkait. Dokumentasi diperbarui (STATUS, INDEX, backend/services.md, dll).

**Changed Files:**
- `services/stream_prefetch.py`
- `server/broadcast_service.py`
- `server/handlers/event_listeners.py`
- `server/app.py`
- `tests/unit/services/test_stream_prefetch.py`
- `tests/unit/server/test_broadcast_service.py`
- `docs/backend/services.md`
- `docs/backend/background_jobs.md`
- `docs/testing/unit_testing.md`
- `docs/INDEX.md`
- `docs/architecture/backend.md`
- `docs/architecture/data_flow.md`
- `docs/adr/0005-websocket-single-channel.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** pytest 594 passed. `lint-imports` 7 kept 0 broken. `architecture_lint` PASS, `doctor.py` PASS. Wiring `server/app.py` dicek manual.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-089

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Tooling
**Priority:** High
**Title:** Perbaiki bug syntax .importlinter

**Reason:** Memperbaiki bug linting di mana 6 dari 7 kontrak importlinter sebelumnya tidak tereksekusi.

**Root Cause:**
`forbidden_modules`/`source_modules` menggunakan format koma-satu-baris yang tidak di-parse oleh `import-linter`.

**Solution:**
Ubah format file `.importlinter` menjadi list per-baris, karena parser `import-linter` (SetField) membagi berdasarkan baris, bukan koma.

**Changed Files:**
- `.importlinter`

**Changed Symbols:**
- (tidak ada)

**Tests:** Baseline lint-imports pasca-perbaikan: 7 kept, 0 broken (genuinely verified).

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-088

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Testing
**Priority:** Low
**Title:** Perbaiki assertion salah di test_handle_playback_command

**Reason:** Assertion yang salah mengenai data yang dikirim pada `CMD_PREV`.

**Root Cause:**
-

**Solution:**
Koreksi test `test_handle_playback_command_other_commands` untuk memvalidasi bahwa `CMD_PREV` memang dikirim beserta data (mendukung guard `video_id` opsional di `_on_prev`), alih-alih tanpa argumen.

**Changed Files:**
- `tests/unit/server/handlers/test_ws_playback.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Baseline test suite sekarang 594 passed, 0 failed.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-087

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Backend
**Priority:** Medium
**Title:** Gabungkan cache/resolver

**Reason:** Konsolidasi file cache ke layer persistence dan penghapusan folder yang tidak perlu.

**Root Cause:**
-

**Solution:**
Gabungkan `cache/resolver.py` ke dalam `persistence/stream_cache.py`. Hapus folder `cache/`. File statis `pb_html.txt` dipindah ke `data/`. File handler `ws_cache.py` tidak di-rename karena bukan terkait stream cache.

**Changed Files:**
- `persistence/stream_cache.py`
- `data/pb_html.txt`
- `bootstrap/services.py`
- `tests/integration/conftest.py`
- `tests/unit/test_main.py`
- `tests/unit/persistence/test_stream_cache.py`
- `tests/unit/engine/playback/test_track_loader.py`
- `tests/unit/engine/conftest.py`
- `tests/unit/bootstrap/test_services.py`
- `server/handlers/ws_cache.py`
- `docs/backend/caching.md`
- `cache/resolver.py`
- `cache/__init__.py`
- `cache/pb_html.txt`
- `tests/unit/cache/test_resolver.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-086

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Backend
**Priority:** Medium
**Title:** Pecah main

**Reason:** Memecah logika startup monolith di `main.py`.

**Root Cause:**
-

**Solution:**
Pecah isi `main.py` menjadi modul di dalam `bootstrap/` (`services`, `startup_tasks`, `maintenance`). `main()` kini menjadi orkestrasi 4 langkah yang lebih bersih.

**Changed Files:**
- `main.py`
- `bootstrap/__init__.py`
- `bootstrap/services.py`
- `bootstrap/startup_tasks.py`
- `bootstrap/maintenance.py`
- `tests/unit/test_main.py`
- `tests/unit/bootstrap/__init__.py`
- `tests/unit/bootstrap/test_services.py`
- `tests/unit/bootstrap/test_startup_tasks.py`
- `tests/unit/bootstrap/test_maintenance.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-085

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Core
**Priority:** Medium
**Title:** Pecah PlaybackController

**Reason:** Mengurai `PlaybackController` agar fokus dan tanggung jawab terbagi secara jelas.

**Root Cause:**
-

**Solution:**
Ekstrak fungsionalitas queue ke `QueueController` dan setelan ke `SettingsController` dari `PlaybackController`. Wiring delegasi dilakukan menggunakan `command_router`.

**Changed Files:**
- `engine/playback/controller.py`
- `engine/playback/queue_controller.py`
- `engine/playback/settings_controller.py`
- `tests/unit/engine/playback/test_controller.py`
- `tests/unit/engine/playback/test_queue_controller.py`
- `tests/unit/engine/playback/test_settings_controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-084

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** DB
**Priority:** High
**Title:** T2.2e: Hapus facade Database (God Facade) dari persistence

**Reason:** Membuang "God Facade" untuk koneksi DB dan memisahkan setiap area domain ke repositorinya sendiri.

**Root Cause:**
-

**Solution:**
Hapus `Database` dari `persistence/__init__.py`. Gunakan `Repositories` sebagai container untuk koneksi. Wiring ulang `main.py` menggunakan `ResolverDbCompat`. Perbaiki aplikasi utama (`server/app.py`, `http.py`, `websocket.py`) untuk menyuntikkan `repos` bukan `db` penuh. Ubah tes untuk menggunakan `db.<repo>.<method>`.

**Changed Files:**
- `persistence/__init__.py`
- `main.py`
- `cache/resolver.py`
- `server/app.py`
- `server/handlers/http.py`
- `server/handlers/websocket.py`
- `server/handlers/ws_download.py`
- `scratch/check_db.py`
- `tests/conftest.py`
- `tests/integration/conftest.py`
- `tests/unit/core/test_ports.py`
- `tests/unit/persistence/test_db.py`
- `tests/unit/persistence/test_track_repo.py`
- `tests/unit/persistence/test_session_repo.py`
- `tests/unit/persistence/test_artist_repo.py`
- `tests/unit/persistence/test_genre_repo.py`
- `tests/unit/persistence/test_discover_repo.py`
- `tests/unit/services/test_discover_service.py`
- `tests/unit/test_main.py`
- `tests/unit/server/test_app.py`
- `tests/unit/server/handlers/test_http.py`
- `tests/unit/server/handlers/test_ws_download.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** 558 passed, import-linter 7 kept.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-083

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Backend
**Priority:** Medium
**Title:** T2.2d: Migrasi discover_service dan ws_discovery ke DiscoverRepository langsung

**Reason:** Bagian dari inisiatif untuk melepaskan dependensi penuh dari "God Facade" Database.

**Root Cause:**
-

**Solution:**
`DiscoverService` sekarang menerima `DiscoverRepository` langsung. `ws_discovery.py` disesuaikan. `websocket.py` disesuaikan untuk meneruskan `db.discover`. Beberapa file lain seperti `event_listeners.py` dan `ws_download.py` juga turut disesuaikan agar tidak error saat runtime.

**Changed Files:**
- `services/discover_service.py`
- `server/handlers/ws_discovery.py`
- `server/handlers/websocket.py`
- `server/handlers/event_listeners.py`
- `server/handlers/ws_download.py`
- `persistence/discover_repo.py`
- `core/ports.py`
- `tests/unit/services/test_discover_service.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-082

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** DB
**Priority:** Medium
**Title:** T2.2c: Migrasi konsumen domain ke repo session/artist/genre/library

**Reason:** Melanjutkan de-coupling "God Facade" Database.

**Root Cause:**
-

**Solution:**
Tambahkan akses ke repo spesifik (`sessions`, `artists`, `genres`, `library`) ke facade Database. Modifikasi konsumen (misal `auth.py`, `ws_queue.py`, `artist_selector.py`) untuk memanggil repo spesifik ketimbang menggunakan keseluruhan instance `Database`. Tambahkan properti `conn` publik di beberapa repo untuk pengecekan *liveness*.

**Changed Files:**
- `persistence/__init__.py`
- `persistence/artist_repo.py`
- `persistence/library_repo.py`
- `engine/radio/artist_selector.py`
- `engine/radio/engine.py`
- `server/handlers/auth.py`
- `server/handlers/ws_queue.py`
- `server/handlers/websocket.py`
- `main.py`
- `tests/integration/conftest.py`
- `tests/unit/engine/radio/test_artist_selector.py`
- `tests/unit/engine/radio/test_engine.py`
- `tests/unit/server/handlers/test_ws_queue.py`
- `tests/unit/server/handlers/test_websocket.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-081

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** DB
**Priority:** Medium
**Title:** T2.2b: Migrasi konsumen domain track ke TrackRepository

**Reason:** Inisiatif pembongkaran "God Facade" Database untuk track domain.

**Root Cause:**
-

**Solution:**
Migrasikan pengguna domain track yang aman (`StreamPrefetchService`, `serve_stream` di `http.py`) agar menggunakan `TrackRepository` secara langsung melalui properti `db.tracks` baru di facade Database.

**Changed Files:**
- `persistence/__init__.py`
- `server/services/stream_prefetch.py`
- `server/app.py`
- `server/handlers/http.py`
- `tests/unit/server/handlers/test_http.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
Beberapa file seperti `resolver.py` tidak disempitkan karena masih digunakan secara silang-domain (cross-domain).

---

## PATCH-2026-07-18-080

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** DB
**Priority:** Medium
**Title:** T2.2a: Ekstrak lifecycle koneksi Database ke persistence/db.py

**Reason:** Memisahkan logika pengelolaan (lifecycle) koneksi dari kelas facade.

**Root Cause:**
-

**Solution:**
Pindahkan manajemen koneksi `DatabaseConnection` dan metode internal seperti `_migrate_songs_unique_constraint` ke `persistence/db.py`. Facade `Database` sekarang lebih ringan (tipis).

**Changed Files:**
- `persistence/db.py`
- `persistence/__init__.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-079

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Cleanup
**Area:** Core
**Priority:** Low
**Title:** Hapus 6 file alias backward-compat

**Reason:** Pembersihan pasca-refactor setelah semua pemanggil diperbarui ke sumber aslinya.

**Root Cause:**
-

**Solution:**
Hapus 6 file yang hanya berfungsi sebagai alias backward-compat (mis. `engine/radio_engine.py`, `cache/db.py`, dsb.) karena sudah tidak digunakan.

**Changed Files:**
- `scratch/check_db.py`
- `tests/conftest.py`
- `tests/integration/conftest.py`
- `tests/unit/core/test_ports.py`
- `tests/unit/test_main.py`
- `engine/radio_engine.py`
- `engine/mpv_controller.py`
- `engine/ytdlp_client.py`
- `cache/db.py`
- `plugins/lyrics.py`
- `launcher/gui.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-078

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Cleanup
**Area:** Core
**Priority:** Low
**Title:** Luruskan import di main

**Reason:** Pembaruan path impor yang sesuai dengan file yang telah dipindahkan/di-refactor.

**Root Cause:**
-

**Solution:**
Sesuaikan jalur *import* pada `main.py` dan `controller.py` agar mengarah ke sumber aslinya (di `persistence`, `adapters.mpv`, dll.).

**Changed Files:**
- `main.py`
- `engine/playback/controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-077

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Security
**Priority:** Medium
**Title:** Pindahkan admin_password

**Reason:** Menghindari komit informasi sensitif seperti kata sandi ke sistem kontrol versi.

**Root Cause:**
-

**Solution:**
Pindahkan `admin_password.txt` ke direktori `instance/` dan pastikan telah diabaikan (ignore) oleh Git dengan memperluas file `.gitignore`.

**Changed Files:**
- `.gitignore`
- `launcher/gui/auth_panel.py`
- `tests/unit/launcher/gui/test_auth_panel.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-076

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Docs
**Priority:** Low
**Title:** Fase 0 selesai: catat baseline pytest

**Reason:** Mendokumentasikan *milestone* refactor Fase 0 dan kondisi dasar pengujian (baseline) di STATUS.md.

**Root Cause:**
-

**Solution:**
Catat metrik dari `pytest` (558 passed, 1 pre-existing failed) dan `lint-imports` (7 kept, 0 broken) di `docs/STATUS.md`.

**Changed Files:**
- `docs/STATUS.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-18-075

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Tooling
**Priority:** Low
**Title:** Fix bug patchlog failed to increment ID

**Reason:** Perbaikan pada alat patchlog agar tidak keliru saat memberi penomoran patch baru.

**Root Cause:**
Tool `patchlog.py` gagal mengurutkan *patch* dengan benar sehingga alih-alih menambah ID eksisting, dia kembali menghasilkan ID `001`.

**Solution:**
Perbaiki logika pengurutan dan penambahan ID dalam `patchlog.py` agar meneruskan dari nomor terakhir yang ada.

**Changed Files:**
- `patchlog.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-17-074

**Tanggal:** 2026-07-17
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Docs
**Priority:** Low
**Title:** Merapikan dokumen patchlog

**Reason:** Merapikan format dan entri pada dokumen patchlog.

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `PATCHLOG.MD`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-17-073

**Tanggal:** 2026-07-17
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/JS
**Priority:** High
**Title:** UI/UX revamp tab discover

**Reason:** Memperbarui antarmuka pengguna pada tab Discover.

**Root Cause:**
-

**Solution:**
Revamp fitur tab Discover meliputi progressive disclosure untuk hashtag/list, pengaturan role-gate access, keyboard accessibility, dan scope filter pencarian.

**Changed Files:**
- `server/handlers/ws_discovery.py`
- `web/static/js/render/discover-tab.js`
- `web/static/js/events/click-delegation-events.js`
- `web/static/index.html`
- `web/static/css/components/discover-cards.css`
- `web/static/js/render/discover-personalize.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-17-072

**Tanggal:** 2026-07-17
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Cleanup
**Area:** Tooling
**Priority:** Low
**Title:** Rename scripts/ menjadi automation/

**Reason:** Menyelaraskan nama direktori agar lebih representatif dengan fungsinya.

**Root Cause:**
-

**Solution:**
Ganti nama direktori internal `scripts/` menjadi `automation/` pada seluruh docstring, instruksi, dan dokumentasi. Hapus blok peringatan migrasi di `AI_CONTEXT.md`.

**Changed Files:**
- `AI_CONTEXT.md`
- `automation/**/*.py`
- `automation/shared/skip_dirs.py`
- `automation/shared/arch_rules.py`
- `automation/find_owner.py`
- `docs/*.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-17-071

**Tanggal:** 2026-07-17
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/JS
**Priority:** High
**Title:** Implementasi frontend discover tab personalisasi

**Reason:** Menerapkan UI untuk data personalisasi yang telah dikirim oleh backend di patch 070.

**Root Cause:**
-

**Solution:**
Modifikasi frontend untuk merender data personalisasi Discover. Tambahkan state default ke `store.js`. Pada `ws.js`, render personalisasi saat `discover_data` tiba dan tangani aksi `artist_detail`. Tambahkan berbagai elemen DOM baru (`dom.js`, `discover-personalize.js`) termasuk *taste bar* dan baris *artist card*. `index.html` ditambahkan elemen markup baru. Modifikasi `websocket.py` untuk mengizinkan `get_artist_detail`.

**Changed Files:**
- `server/handlers/websocket.py`
- `web/static/js/store.js`
- `web/static/js/ws.js`
- `web/static/js/dom.js`
- `web/static/js/render/discover-personalize.js`
- `web/static/css/components/discover-cards.css`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/events/index.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** PATCH-2026-07-17-070

**Status:** Merged

**Notes:**
File `discover-tab.js` tidak disentuh, fungsi lama dipertahankan.

---

## PATCH-2026-07-17-070

**Tanggal:** 2026-07-17
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend
**Priority:** High
**Title:** Eksekusi backend untuk discover tab v2

**Reason:** Membangun API backend untuk personalisasi pengguna di tab discover.

**Root Cause:**
-

**Solution:**
Tambahkan helper `enrich_artists` di `discover_enrich.py`. Buat `DiscoverRepository` mandiri (`discover_repo.py`) untuk kueri berbasis riwayat pengguna (`get_bandit_ranked_artists`, `get_taste_spectrum`, dll). Implementasi delegasi `discover_service.py` untuk membungkus endpoint. Hubungkan aksi di `ws_discovery.py` untuk mengeksekusi 9 query paralel saat inisialisasi discover.

**Changed Files:**
- `persistence/discover_enrich.py`
- `persistence/discover_repo.py`
- `persistence/__init__.py`
- `services/discover_service.py`
- `server/handlers/ws_discovery.py`
- `tests/unit/persistence/test_discover_repo.py`
- `tests/unit/services/test_discover_service.py`
- `tests/unit/server/handlers/test_ws_discovery.py`
- `docs/STATUS.md`
- `docs/discover-tab-frontend-handoff.md`
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`
- `server/handlers/websocket.py`
- `web/static/js/dom.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** 522 passed. Coverage unit test ditambah luas untuk `discover_repo.py` (14 skenario) dan wrapper (12 skenario).

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** PATCH-2026-07-17-071

**Status:** Merged

**Notes:**
Frontend tidak disentuh di patch ini. Terdapat *guard* di `websocket.py` yang dibiarkan menunggu (akan diselesaikan di patch frontend).

---

## PATCH-2026-07-16-069

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Core
**Priority:** High
**Title:** Eksekusi implementation-plan (Bug Fix Batch)

**Reason:** Menangani berbagai bug dan utang teknis dari rencana implementasi (CI hang, database connection leak, memory leak).

**Root Cause:**
-

**Solution:**
Terapkan solusi untuk beberapa isu:
1. Zombie non-daemon threads saat teardown test: fix timing pada iterasi test, tambah `pytest-timeout`.
2. Connection thread leak: pindahkan `shutil.which("mpv")` sebelum start `db.init()`.
3. Side-channel enumerasi pengguna: `verify_password` kini selalu dipanggil bahkan jika username salah.
4. Bug LRC parsing `lyrics_parser.py`: tangani multi-timestamp per baris dan lewati metadata.
5. Handler leak `controller.py`: tambah `dispose()` dan pembatalan closure dengan safe memory handling.
6. Performa Regex di `patchlog.py`: ubah string parsing dari DOTALL ke per chunk.

**Changed Files:**
- `pytest.ini`
- `requirements-dev.txt`
- `main.py`
- `adapters/mpv/observer.py`
- `tests/integration/conftest.py`
- `persistence/db.py`
- `tests/unit/persistence/test_db.py`
- `server/handlers/auth.py`
- `tests/unit/server/handlers/test_auth.py`
- `engine/radio/prefetcher.py`
- `plugins/sponsorblock.py`
- `tests/unit/plugins/test_sponsorblock.py`
- `plugins/lyrics_parser.py`
- `tests/unit/plugins/test_lyrics_parser.py`
- `core/command_bus.py`
- `tests/unit/core/test_command_bus.py`
- `engine/playback/controller.py`
- `tests/unit/engine/playback/test_controller.py`
- `tests/unit/engine/playback/test_track_ended_ops.py`
- `automation/patchlog.py`
- `docs/PATCHLOG.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** Unit + Integrasi: 508 passed, coverage 88%.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-16-068

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Adapters
**Priority:** High
**Title:** Ganti MPV IPC dari TCP Sockets ke Named Pipes

**Reason:** Meningkatkan keandalan koneksi lokal dengan MPV di Windows. Menghilangkan socket exhaustion dan latensi.

**Root Cause:**
Penggunaan soket TCP pada Windows menimbulkan kelemahan flakiness dan interupsi pada saat intensitas IPC tinggi.

**Solution:**
Ubah inisialisasi MPV menggunakan Windows Named Pipes (`\\.\pipe\mpv-lunawave`) melalui class `MpvConnection` dan `MpvObserver`. Perbaiki test integrations yang berbenturan saat berurutan. Perbarui ID YouTube pada test integrasi yang tidak restriksi geografi.

**Changed Files:**
- `adapters/mpv/connection.py`
- `adapters/mpv/ipc.py`
- `adapters/mpv/observer.py`
- `adapters/ytdlp/__init__.py`
- `tests/integration/conftest.py`
- `tests/integration/test_download_flow.py`
- `tests/integration/test_playback_flow.py`
- `tests/integration/test_radio_flow.py`
- `tests/integration/test_websocket_flow.py`
- `tests/unit/adapters/mpv/test_connection.py`
- `tests/unit/adapters/mpv/test_ipc.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Suite tes integrasi diperbaiki.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-16-067

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Core
**Priority:** High
**Title:** Tiga perbaikan startup latency

**Reason:** Mempercepat durasi mulai server di Windows hingga maksimal ~25 detik pada case terburuk.

**Root Cause:**
Resume stream memblokir server start. Connect ke MPV lewat TCP blocking dan sleep asal.

**Solution:**
Pindahkan "resume last playback" ke task latar belakang (`safe_create_task`) sehingga tidak memblok `run_server()`. Pindahkan `mpv.connect()` ke background dan gunakan polling event TCP di Windows ketimbang `sleep(1.0)` statis.

**Changed Files:**
- `main.py`
- `adapters/mpv/connection.py`
- `tests/unit/adapters/mpv/test_connection.py`
- `tests/unit/test_main.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Update 4 test, tambah 3 test baru. Total 11 pass.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-16-066

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** UI/JS
**Priority:** High
**Title:** Audit JavaScript Frontend (6 Confirmed Bug Fixes)

**Reason:** Memperbaiki fungsionalitas UI yang macet atau berpotensi XSS akibat logic lama.

**Root Cause:**
Ada panggilan yang salah (localStorage properties vs objek map), error di reference DOM, XSS, dan callback event cancel yang tidak tertangani.

**Solution:**
1. Tambahkan `#vol-slider` di `dom.js` agar volume berfungsi.
2. Perbaiki fungsi get pada search history sehingga tidak throw TypeError dan fitur Search berfungsi.
3. Gunakan `getOrInitAudio()` (bukan global audio tak terdefinisikan) untuk efek crossfade di player.
4. Perbaiki shortcut navigasi via keyboard arrow.
5. Perbaiki Stored XSS pada render histori pencarian lewat HTML encoding.
6. Tambahkan event listener `pointercancel` pada seekBar drag handling di UI.

**Changed Files:**
- `web/static/js/dom.js`
- `web/static/js/events/search-input-events.js`
- `web/static/js/render/player.js`
- `web/static/js/platform/keyboard.js`
- `web/static/js/events/progress-events.js`
- `web/static/js/ws.js`
- `web/static/sw.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** Vitest run (14 pass).

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
Beberapa dead code (seperti audio visualizer mati) tidak dihapus agar menghindari komplikasi tanpa desain baru.

---

## PATCH-2026-07-16-065

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Core
**Priority:** High
**Title:** Fix race condition di ConnectionManager.broadcast

**Reason:** Klien sehat kadang terputus saat broadcast due to concurrent connection lists.

**Root Cause:**
Panggilan iterator `list()` pada set client teraktif setelah panggilan asinkron yang menahan I/O, sehingga urutan zip salah pasangan.

**Solution:**
Snapshop `list(active_connections)` satu kali saja dan disematkan sebelum `asyncio.gather` sehingga indeks callback tidak pernah melenceng dari urutan target websocket yang sesungguhnya.

**Changed Files:**
- `server/connection_manager.py`
- `tests/unit/server/test_connection_manager.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Reproduksi testing gagal 3/3 pada kode lama telah stabil.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-16-064

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** UI/Launcher
**Priority:** High
**Title:** Audit GUI Server Manager: Perbaikan kontrak admin password dan race condition thread

**Reason:** Terjadi lockout admin saat reset password dan potensi crash saat launcher ditutup (race destroy vs thread).

**Root Cause:**
1. Ada ketidaksinkronan kontrak `admin_password.txt`, GUI menulis hash tetapi `config.py` membacanya sebagai plaintext lalu di-hash lagi, memicu lockout karena mismatch. 2. Handler UI/Thread mengeksekusi callback I/O yang tertinggal (`self.after()`) saat GUI loop ditutup.

**Solution:**
Tulis raw password langsung ke `admin_password.txt`. Tambahkan guard penanda status shutdown (`ServerManager._closing`) yang mereset semua siklus callback background thread agar I/O berhenti saat menutup window GUI.

**Changed Files:**
- `launcher/gui/auth_panel.py`
- `launcher/gui/app.py`
- `launcher/gui/controller.py`
- `tests/unit/launcher/gui/test_auth_panel.py`
- `tests/unit/launcher/gui/test_app_lifecycle.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Direproduksi lewat Xvfb headless, status test passed pasca fix.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-16-063

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** DB
**Priority:** High
**Title:** Fix unique constraint pada kolom youtube_id di tabel songs

**Reason:** Mencegah kehilangan lagu kolaborasi di database SQLite yang sama-sama memiliki youtube_id.

**Root Cause:**
`songs.youtube_id` memiliki constraint `UNIQUE` global. Lagu kolaborasi/duet sah dimiliki lebih dari satu artis, tapi akan dibuang saat export jika ID-nya sama.

**Solution:**
Ganti constraint jadi composite `UNIQUE(artist_id, youtube_id)` di `persistence/schema.sql`. Lakukan rebuild tabel lama dengan logic migrasi `_migrate_songs_unique_constraint` di `persistence/__init__.py`. Update logic `data/export_to_sqlite.py` untuk menggunakan komposit ID.

**Changed Files:**
- `persistence/schema.sql`
- `persistence/__init__.py`
- `data/export_to_sqlite.py`
- `tests/unit/persistence/test_db.py`
- `tests/unit/data/test_export_to_sqlite.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-16-062

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Adapters
**Priority:** Low
**Title:** Perbaiki binding port untuk MPV Connection

**Reason:** Test suite gagal karena dynamic port assignment menimpa pinned port.

**Root Cause:**
Pada OS Windows, constructor menimpa tcp_port yang sudah ditentukan eksplisit dengan binding port 0 yang dinamis.

**Solution:**
Tambahkan boolean flag `_port_pinned` ke constructor untuk mencegah port dinamis digunakan saat port secara eksplisit telah disediakan. Tingkatkan kejelasan pada pesan error `MpvConnectionError` untuk memakai `self.tcp_port` terbaru.

**Changed Files:**
- `adapters/mpv/connection.py`
- `tests/unit/adapters/mpv/test_connection.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** `test_mpv_connection_connect_windows` kembali pass.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-061

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Backend
**Priority:** High
**Title:** Menghubungkan fitur backend orphan ke frontend (Loudness, Queue, dll)

**Reason:** Beberapa fitur yang diimplementasikan di backend tidak dapat dijangkau oleh pengguna dari antarmuka klien (UI).

**Root Cause:**
Action tidak didaftarkan di WS routing, delegasi DOM tidak diimplementasikan, state di store dan response payload mengabaikan beberapa key.

**Solution:**
1. Tambahkan `set_loudness_normalization` ke WS routing dan Settings UI.
2. Tambahkan aksi `queue_select` untuk `.qi-remove` di queue UI.
3. Tambahkan layout UI untuk drag handle di Queue list (meskipun masih dinonaktifkan).
4. Tambahkan `favorites` ke payload WS action `discover` dan tambahkan tab Favorit di discover page.
5. Tambahkan container `#discover-recent` di index HTML untuk fitur History.

**Changed Files:**
- `server/handlers/websocket.py`
- `server/handlers/ws_playback.py`
- `server/handlers/ws_discovery.py`
- `server/handlers/ws_download.py`
- `web/static/index.html`
- `web/static/js/dom.js`
- `web/static/js/store.js`
- `web/static/js/ws.js`
- `web/static/js/events/settings-events.js`
- `web/static/js/events/queue-events.js`
- `web/static/js/render/queue.js`
- `web/static/js/render/discover-tab.js`
- `tests/unit/server/handlers/test_ws_playback.py`
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/handlers/test_ws_discovery.py`
- `tests/unit/server/handlers/test_ws_download.py`
- `tests/frontend/test_ws-routing.test.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** pytest: 456 passed, vitest: 14/14 passed.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-060

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Test
**Area:** Testing
**Priority:** Low
**Title:** Tambah test suite pasca PATCH-058/059

**Reason:** Memastikan perbaikan dan penambahan fungsionalitas di patch sebelumnya tertangkap test suite.

**Root Cause:**
-

**Solution:**
Tambahkan unit test untuk aksi pemutaran baru dan serialize keys di `test_websocket.py` (5 actions) dan `test_serializers.py`.

**Changed Files:**
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/test_serializers.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-15-058, PATCH-2026-07-15-059

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-059

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Core
**Priority:** High
**Title:** Sinkronisasi toggle client dengan websocket payload

**Reason:** Nilai opsi kecepatan pemutaran, crossfade, dan mode loop tidak direfleksikan dari backend ke frontend.

**Root Cause:**
Payload state yang diserialisasi tidak berisi variabel tersebut.

**Solution:**
Tambahkan `playback_speed`, `loop_mode`, dan `crossfade_enabled` ke serialisasi payload WS `state_to_dict`. Edit audio `.playbackRate` ke object DOM sehingga kecepatan audio bisa dirubah juga. Tambahkan counter durasi timer ke timer pop UI.

**Changed Files:**
- `server/serializers.py`
- `web/static/js/render/full-state.js`
- `web/static/js/events/settings-events.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** PATCH-2026-07-15-058

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-058

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** UI/JS
**Priority:** High
**Title:** Audit dan Perbaikan Bug UI untuk Fitur Baru T1-T16

**Reason:** Fitur baru dari T1-T16 tidak berfungsi di frontend akibat kelalaian dalam integrasi WS dan UI state.

**Root Cause:**
-

**Solution:**
1. Daftarkan 5 action websocket (stop, set_sleep_timer, set_speed, set_loop, set_crossfade).
2. Daftarkan key `crossfade_enabled` di js store.
3. Ganti case mapping loopmode menjadi `loop_mode` dari `loopMode` untuk sinkronisasi format dengan state server.
4. Hapus code pass queue idle loop dan duplikat properti di dataclass.
5. Hapus binding listener click dobel di UI sponsorblock.

**Changed Files:**
- `server/handlers/websocket.py`
- `web/static/js/store.js`
- `web/static/js/events/transport-events.js`
- `engine/queue_manager.py`
- `core/state.py`
- `web/static/js/events/settings-events.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-057

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Core
**Priority:** Medium
**Title:** T16: Implementasi efek crossfade eksperimental

**Reason:** Transisi lagu yang lebih mulus dengan fading suara pada ujung akhir.

**Root Cause:**
-

**Solution:**
Tambahkan pengaturan crossfade (`crossfade_enabled`) beserta efek fade (memperlahan suara di akhir durasi via `controller.py` dan `crossfade.py`) untuk BROWSER dan DEVICE outputs. Integrasikan command-nya ke UI.

**Changed Files:**
- `core/state.py`
- `core/commands.py`
- `engine/command_router.py`
- `engine/playback/mode_ops.py`
- `engine/playback/controller.py`
- `engine/playback/crossfade.py`
- `server/handlers/ws_playback.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/render/player.js`
- `web/static/js/dom.js`
- `docs/ADR/003-Crossfade.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-056

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/JS
**Priority:** Low
**Title:** T15: Penambahan real-time metrics untuk antrean putar

**Reason:** Membantu user melihat total waktu tempuh seluruh antrean beserta isinya.

**Root Cause:**
-

**Solution:**
Tambahkan informasi kalkulasi durasi estimasi secara real-time dan jumlah lagu di footer panel UI.

**Changed Files:**
- `web/static/js/render/queue.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-055

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend
**Priority:** Low
**Title:** T14: Log Message Event saat stream upstream mati

**Reason:** Memberikan notifikasi UI apabila stream dilarang oleh hulu/upstream YouTube (error 403 atau 410).

**Root Cause:**
-

**Solution:**
Ekspos respons error `/stream/<video_id>` ke dalam payload WS `LogMessageEvent`.

**Changed Files:**
- `server/handlers/http.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-054

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Core
**Priority:** Medium
**Title:** T13: Menambahkan fitur Loop Mode (off/track/queue)

**Reason:** Memungkinkan pengguna untuk mengulang satu lagu terus menerus atau mengulang seluruh antrean lagu.

**Root Cause:**
-

**Solution:**
Tambahkan opsi loop mode ke state aplikasi (off/track/queue) dan implementasikan logika loop di `queue_manager.py` (methode `next()`). Tambahkan WS command `CMD_SET_LOOP` dan binding ke UI.

**Changed Files:**
- `core/state.py`
- `core/commands.py`
- `engine/queue_manager.py`
- `engine/playback/mode_ops.py`
- `server/handlers/ws_playback.py`
- `web/static/js/store.js`
- `web/static/js/dom.js`
- `web/static/js/render/player.js`
- `web/static/js/events/transport-events.js`
- `web/static/css/components/player-bar.css`
- `tests/unit/engine/test_queue_manager.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-053

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/JS
**Priority:** Low
**Title:** T12: SafeStorage riwayat pencarian terkini

**Reason:** Menyimpan daftar pencarian terakhir pengguna di sisi client.

**Root Cause:**
-

**Solution:**
Menerapkan penyimpanan client-side menggunakan objek `safeStorage` untuk history pencarian di tab search. Fitur ini disertai dengan dukungan UI untuk penghapusan entri historis maupun perbaikan hapus item pada queue.

**Changed Files:**
- `web/static/js/events/search-input-events.js`
- `web/static/js/render/queue.js`
- `web/static/js/events/queue-events.js`
- `server/handlers/ws_playback.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-052

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Core
**Priority:** Low
**Title:** T11: Fitur kontrol kecepatan pemutaran

**Reason:** Memungkinkan pengguna memutar lagu lebih cepat atau lebih lambat.

**Root Cause:**
-

**Solution:**
Tambahkan dropdown kecepatan di layar Pengaturan (UI). Hubungkan melalui koneksi WebSocket untuk merubah rate secara *real-time* ke MPV (`mpv.set_property("speed", value)`).

**Changed Files:**
- `core/state.py`
- `core/commands.py`
- `engine/playback/mode_ops.py`
- `server/handlers/ws_playback.py`
- `web/static/js/store.js`
- `web/static/js/render/player.js`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-051

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Core
**Priority:** Medium
**Title:** T10: Implementasi mode Sleep Timer

**Reason:** User ingin server bisa auto-stop playback setelah rentang durasi tertentu untuk menemani saat tidur.

**Root Cause:**
-

**Solution:**
Tambahkan opsi *Sleep Timer* yang memungkinkan user mengatur countdown tidur. Mengintegrasikan background loop di `engine/sleep_timer.py` yang akan memicu command stop lewat command bus saat timer habis.

**Changed Files:**
- `core/commands.py`
- `engine/sleep_timer.py`
- `engine/command_router.py`
- `server/handlers/ws_playback.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/render/player.js`
- `tests/unit/engine/test_sleep_timer.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Ditambahkan unit test.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-050

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend
**Priority:** Low
**Title:** T9: Penambahan handler ws_cache.py (Manajemen Ukuran Cache)

**Reason:** Menyediakan fungsionalitas bagi admin UI untuk mengukur dan mengosongkan cache MP3.

**Root Cause:**
-

**Solution:**
Buat handler `ws_cache.py` untuk mengukur besaran direktori cache MP3 (`config.CACHE_DIR`) dan endpoint untuk menghapusnya secara aman tanpa menghapus file statis. Tambahkan display di UI Settings tab.

**Changed Files:**
- `server/handlers/ws_cache.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `tests/unit/server/handlers/test_ws_cache.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Unit test untuk `ws_cache.py` ditambahkan.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-049

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Core
**Priority:** High
**Title:** T8: Resume posisi playback setelah restart server

**Reason:** Menjamin *seamless listening* di mana playback yang terjeda/berjalan tetap dapat dilanjutkan setelah restart tanpa mulai ulang dari awal.

**Root Cause:**
-

**Solution:**
Simpan secara periodik `last_position` dari current track (tiap 10 detik di `_on_track_progress`). Tambahkan skema SQLite kolom `last_position`, CRUD fungsi di repository, dan baca state waktu awal server dihidupkan di `main.py`.

**Changed Files:**
- `core/state.py`
- `persistence/schema.sql`
- `persistence/track_repo.py`
- `persistence/__init__.py`
- `engine/playback/controller.py`
- `tests/unit/engine/playback/test_controller.py`
- `main.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Tambah tes di `test_controller.py` untuk start_paused.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-048

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Core
**Priority:** High
**Title:** Eksekusi T1-T7 Tier 1 (Bug Fix dan Performa Lirik, Regex, Rate Limit)

**Reason:** Kumpulan perbaikan ketahanan, stabilitas, dan data integrity.

**Root Cause:**
-

**Solution:**
T1-T7 Tier 1 dijalankan meliputi:
1. Fix data integrity hash fallback.
2. Precompile Regex pada ytdlp searcher.
3. Perbaikan Lirik Parser agar support variasi metadata LRC.
4. Optimasi regex noise pada lyrics fetcher.
5. Fix HTTP handler.
6. Ganti tipe penyimpanan limit antrean rate limit ke `collections.deque` pada middleware demi O(1).
7. Menambahkan constraint `UNIQUE` untuk nama artist di DB.

**Changed Files:**
- `adapters/ytdlp/searcher.py`
- `tests/unit/adapters/ytdlp/test_searcher.py`
- `persistence/schema.sql`
- `plugins/lyrics_parser.py`
- `tests/unit/plugins/test_lyrics_parser.py`
- `plugins/lyrics_fetcher.py`
- `tests/unit/plugins/test_lyrics_fetcher.py`
- `server/handlers/http.py`
- `tests/unit/server/handlers/test_http.py`
- `server/middleware.py`
- `tests/unit/server/test_middleware.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-047

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Testing
**Priority:** Low
**Title:** Diagnosa hang 1 jam 54 menit pada CI pytest

**Reason:** CI test run mandek/menggantung lama.

**Root Cause:**
Terdapat *zombie process* dari `yt-dlp` pada tes integrasi karena gagal di-kill pada sesi teardown saat YouTube memblokir IP dari server GitHub Actions.

**Solution:**
Tambahkan pedoman ke `integration_testing.md` tentang bagaimana melakukan teardown yang benar untuk menge-kill explicit proses eksternal. (Semua 435 unit test dipastikan *green*).

**Changed Files:**
- `docs/testing/integration_testing.md`
- `log.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-046

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Test
**Area:** Testing
**Priority:** Low
**Title:** Menambah unit test untuk error handling WS dan Radio

**Reason:** Memenuhi target coverage test yang telah dicatat (P3 & P4).

**Root Cause:**
-

**Solution:**
Tambah unit tests validasi route ws dan penanganan exception di `test_websocket.py` & `test_ws_playback.py`. Tambah test fallback engine radio pada `test_engine.py` & `test_prefetcher.py`.

**Changed Files:**
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/handlers/test_ws_playback.py`
- `tests/unit/engine/radio/test_engine.py`
- `tests/unit/engine/radio/test_prefetcher.py`
- `tests/unit/engine/radio/test_artist_selector.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-045

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Test
**Area:** Testing
**Priority:** Low
**Title:** Menambah unit test untuk loop event async di MPV observer

**Reason:** Memenuhi target coverage P2.

**Root Cause:**
-

**Solution:**
Menuliskan skenario unit test mengenai event async property changes, proses cleanup, dan koneksi ulang soket MPV. Total coverage unit test melonjak.

**Changed Files:**
- `tests/unit/adapters/mpv/test_observer.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Unit test `test_observer.py` selesai dibuat.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-044

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Test
**Area:** Testing
**Priority:** Low
**Title:** Menambah unit test state machine di playback controller

**Reason:** Menutup target tes prioritas utama (P1) mengenai error status pada controller.

**Root Cause:**
-

**Solution:**
Tulis skenario edge-case test: queue_empty, race condition, track_error, state fallback pada `test_controller.py`. Overall coverage naik ke 77.48%.

**Changed Files:**
- `tests/unit/engine/playback/test_controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Coverage unit test untuk controller naik.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-043

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Test
**Area:** Testing
**Priority:** Low
**Title:** Menambahkan unit test untuk fungsi serve_stream()

**Reason:** Memenuhi target coverage P0 untuk handler stream.

**Root Cause:**
-

**Solution:**
Menulis skenario tes stream untuk `server/handlers/http.py`. Coverage unit test naik.

**Changed Files:**
- `tests/unit/server/handlers/test_http.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Unit test `test_http.py` diperbarui.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-15-042

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Core
**Priority:** High
**Title:** Eksekusi 3 fitur besar serentak: Bandit Radio, Loudness, Latency Window

**Reason:** Mematuhi larangan two-stage refactoring untuk arsitektur.

**Root Cause:**
-

**Solution:**
Eksekusi langsung Thompson Sampling Bandit (Artist Radio), EBU R128 Loudness Normalization, dan Adaptive Network Prefetch (Latency Window). Fitur dipisah ke service/kelas baru dan diintegrasikan pada controller menggunakan Dependency Injection.

**Changed Files:**
- `persistence/schema.sql`
- `core/state.py`
- `persistence/artist_repo.py`
- `core/latency_window.py`
- `config.py`
- `cache/resolver.py`
- `engine/radio/prefetcher.py`
- `engine/loudness/gain_calculator.py`
- `engine/playback/track_loader.py`
- `adapters/mpv/__init__.py`
- `engine/command_router.py`
- `server/serializers.py`
- `main.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** High

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-14-041

**Tanggal:** 2026-07-14
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Core
**Priority:** High
**Title:** Eksekusi P0-P2 dari IMPLEMENTATION_PLAN untuk Stable Release v1.0.0

**Reason:** Menyiapkan rilis versi 1 yang stabil dan menyelesaikan task yang belum tercover.

**Root Cause:**
-

**Solution:**
Menerapkan perbaikan di config, download manager, ci actions, serta metadata packaging untuk v1.0.0 (banner password, path downloads, DB migration logging, `shell=False` pada subproses probe network, CI gate block).

**Changed Files:**
- `main.py`
- `config.py`
- `README.md`
- `docs/INDEX.md`
- `engine/download_manager.py`
- `server/handlers/ws_download.py`
- `persistence/__init__.py`
- `launcher/network.py`
- `package.json`
- `.importlinter`
- `.github/workflows/ci.yml`
- `pyproject.toml`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-14-040

**Tanggal:** 2026-07-14
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Docs
**Priority:** Low
**Title:** Finalisasi "stable baseline version" v1

**Reason:** Persiapan repositori menuju rilis 1.0.0 secara resmi.

**Root Cause:**
-

**Solution:**
Mengubah item tertunda menjadi Frozen di STATUS.md. Menambahkan CHANGELOG, CONTRIBUTING, dan SECURITY (standar Open Source Readiness). Melakukan tag versi.

**Changed Files:**
- `docs/STATUS.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-14-039

**Tanggal:** 2026-07-14
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Core
**Priority:** Low
**Title:** Menyeragamkan format docstring pada 145 file menggunakan AST

**Reason:** Merapikan standar kelengkapan field dokumentasi fungsi dan kelas dalam codebase.

**Root Cause:**
-

**Solution:**
Gunakan analisis AST secara dinamis untuk mengoreksi docstring pada 145 file secara seragam.

**Changed Files:**
- (tidak ada)

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-14-038

**Tanggal:** 2026-07-14
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Build
**Area:** Tooling
**Priority:** Low
**Title:** Automation - all tests and linters passing

**Reason:** Sinkronisasi laporan eksekusi automation.

**Root Cause:**
-

**Solution:**
Perbarui `PATCHLOG.md` untuk mencatat status clean dari pipeline.

**Changed Files:**
- `docs/PATCHLOG.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-037

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Test
**Area:** Testing
**Priority:** High
**Title:** Membangun test/integration/conftest.py dan E2E test flows

**Reason:** Dibutuhkan infrastruktur test integrasi end-to-end yang solid.

**Root Cause:**
-

**Solution:**
Bangun `conftest.py` dengan EventBus, DB, yt-dlp asli. Tambah test integrasi (IT-01 sampai IT-04). Refactor `generate_file_index.py` untuk dinamis. Atasi masalah crash unicode CP1252 pada terminal Windows di test script.

**Changed Files:**
- `tests/integration/__init__.py`
- `tests/integration/conftest.py`
- `tests/integration/test_websocket_flow.py`
- `tests/integration/test_playback_flow.py`
- `tests/integration/test_radio_flow.py`
- `tests/integration/test_download_flow.py`
- `scripts/generate_file_index.py`
- `scripts/generate_report.py`
- `scripts/run_all.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** Integration tests berhasil.

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-036

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Docs
**Priority:** Medium
**Title:** Memindahkan dokumen kompas ke root

**Reason:** Migrasi telah selesai dan dokumentasi di kompas/ menjadi standar utama arsitektur.

**Root Cause:**
-

**Solution:**
Pindahkan seluruh dokumentasi arsitektur dari `docs/kompas/` ke `docs/`. Hapus folder kompas, perbarui referensi path pada `AI_CONTEXT.md` dan berbagai tools otomatis.

**Changed Files:**
- `docs/kompas/*`
- `docs/Blueprint.md`
- `AI_CONTEXT.md`
- `CONTRIBUTING.md`
- `docs/MIGRATION_GUIDE.md`
- `docs/PATCHLOG.md`
- `docs/STATUS.md`
- `docs/FILE_INDEX.md`
- `scripts/architecture_lint.py`
- `scripts/find_owner.py`
- `scripts/verify_structure.py`
- `tests/conftest.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-035

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Build
**Area:** Tooling
**Priority:** Medium
**Title:** Menyelesaikan checklist Tahap 13

**Reason:** Memastikan seluruh dependency contract terpenuhi tanpa pelanggaran sebelum open source readiness.

**Root Cause:**
-

**Solution:**
Lakukan evaluasi import-linter. Tambahkan `requirements-dev.txt`, standar LICENSE, CHANGELOG, pull request & issue template, editorconfig.

**Changed Files:**
- `.importlinter`
- `requirements-dev.txt`
- `LICENSE`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `.editorconfig`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** import-linter clean (0 pelanggaran).

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-034

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Test
**Area:** Testing
**Priority:** Medium
**Title:** Melengkapi unit tests Prioritas 2

**Reason:** Memastikan layer adapter/plugin/server ter-cover dengan mocks/fakes.

**Root Cause:**
-

**Solution:**
Tambahkan unit testing menggunakan mocks untuk layer eksternal. Tambahkan `services/__init__.py` yang hilang sehingga test suit bisa dieksekusi penuh. Total 295 tes sukses berjalan.

**Changed Files:**
- `tests/unit/launcher/gui/test_dep_checker.py`
- `tests/unit/server/test_connection_manager.py`
- `tests/unit/server/test_middleware.py`
- `tests/unit/server/test_serializers.py`
- `tests/unit/engine/radio/test_artist_selector.py`
- `tests/unit/engine/radio/test_prefetcher.py`
- `tests/unit/engine/radio/test_engine.py`
- `tests/unit/plugins/test_lyrics_parser.py`
- `tests/unit/plugins/test_lyrics_sync.py`
- `services/__init__.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** 295 unit tests success.

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-033

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Test
**Area:** Testing
**Priority:** Medium
**Title:** Melengkapi unit tests Prioritas 1

**Reason:** Modul-modul dengan logika core butuh coverage test penuh.

**Root Cause:**
-

**Solution:**
Tambah 16 unit tests untuk logika core dan I/O bebas di test_library_repo, test_track_interleaver, test_queue_ops, test_mode_ops.

**Changed Files:**
- `tests/unit/persistence/test_library_repo.py`
- `tests/unit/engine/radio/test_track_interleaver.py`
- `tests/unit/engine/playback/test_queue_ops.py`
- `tests/unit/engine/playback/test_mode_ops.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** 16 passed

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-032

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Test
**Area:** Testing
**Priority:** Medium
**Title:** Setup folder struktur testing dan pembuatan fakes

**Reason:** Standardisasi dan kelancaran eksekusi tes dengan object replika yang dikontrol.

**Root Cause:**
-

**Solution:**
Persiapkan fakes untuk LyricsProvider dan SponsorBlockProvider dan setup struktur unit test folder. Modifikasi fixture db memory.

**Changed Files:**
- `tests/unit/adapters/mpv/`
- `tests/unit/engine/radio/`
- `tests/unit/engine/playback/`
- `tests/unit/server/handlers/`
- `tests/unit/server/services/`
- `tests/unit/plugins/`
- `tests/unit/launcher/gui/`
- `tests/integration/`
- `tests/frontend/utils/`
- `tests/fakes/fake_lyrics_provider.py`
- `tests/fakes/fake_sponsorblock_provider.py`
- `tests/conftest.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-031

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** CI
**Area:** Tooling
**Priority:** Low
**Title:** Setup file konfigurasi DevOps/Tooling

**Reason:** Memastikan CI dan lint rule terstandardisasi.

**Root Cause:**
-

**Solution:**
Menambah workflow GitHub, aturan linter pre-commit, dan dependensi dev di `pyproject.toml`.

**Changed Files:**
- `pyproject.toml`
- `.importlinter`
- `.pre-commit-config.yaml`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-030

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** UI/JS
**Priority:** Medium
**Title:** Memecah monolith frontend js

**Reason:** Script frontend menjadi satu file besar yang susah di-maintain.

**Root Cause:**
-

**Solution:**
Ekstrak event handler, fungsi utilitas, dan logic audio/render ke dalam file-file terpisah di `web/static/js/`.

**Changed Files:**
- `web/static/js/events/*`
- `web/static/js/audio/*`
- `web/static/js/utils/*`
- `web/static/js/render/*`
- `web/static/js/ws.js`
- `web/static/index.html`
- `scripts/verify_docs/checks_docs.py`
- `scripts/architecture_lint.py`
- `scripts/generate_file_index.py`
- `docs/CONSTRAINTS.md`
- `docs/rfc/.keep`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-029

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Core
**Priority:** Low
**Title:** Merapikan struktur folder sesuai dengan MIGRATION_GUIDE tahap 8

**Reason:** Menjaga kebersihan dan konsistensi tree directory sesuai konvensi terbaru.

**Root Cause:**
-

**Solution:**
Pindahkan dan strukturisasi folder data, sql schema, dan lyrics plugin.

**Changed Files:**
- `data/export_to_sqlite.py`
- `cache/schema.sql`
- `plugins/lyrics.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-028

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Backend
**Priority:** High
**Title:** Memecah monolith websocket handler dan launcher GUI

**Reason:** File handler WS menjadi terlalu panjang dan sulit dibaca.

**Root Cause:**
-

**Solution:**
Pisahkan router utama dan event WS sesuai domain bisnisnya (`ws_*.py`), serta pecah `launcher/gui.py`.

**Changed Files:**
- `server/handlers/websocket.py`
- `server/connection_manager.py`
- `server/handlers/ws_*.py`
- `launcher/gui.py`
- `launcher/gui/app.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-027

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Core
**Priority:** Medium
**Title:** Memecah monolith controller

**Reason:** Menjaga modul `controller.py` agar tetap slim dengan prinsip Single Responsibility.

**Root Cause:**
-

**Solution:**
Ekstrak fungsi mutasi antrean ke `queue_ops.py` dan mode playback ke `mode_ops.py`.

**Changed Files:**
- `engine/playback/queue_ops.py`
- `engine/playback/mode_ops.py`
- `engine/playback/controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-026

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Core
**Priority:** Medium
**Title:** Memecah monolith engine/radio_engine

**Reason:** File radio_engine mencapai 440 baris dan tanggung jawabnya saling tumpang tindih.

**Root Cause:**
-

**Solution:**
Pisahkan logika radio menjadi sub-modul: `artist_selector`, `track_interleaver`, dan `prefetcher`.

**Changed Files:**
- `engine/radio_engine.py`
- `engine/radio/artist_selector.py`
- `engine/radio/track_interleaver.py`
- `engine/radio/prefetcher.py`
- `engine/radio/engine.py`
- `engine/radio/__init__.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-025

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Adapters
**Priority:** Medium
**Title:** Extract logika integrasi yt-dlp dari engine/ytdlp_client

**Reason:** Menghindari class god (yt-dlp) dan isolasi komponen adapter yang tepat.

**Root Cause:**
-

**Solution:**
Pisahkan logika `YtDlpClient` ke direktori `adapters/ytdlp/` yang berisi `searcher`, `resolver`, dan `downloader`.

**Changed Files:**
- `adapters/ytdlp/common.py`
- `adapters/ytdlp/searcher.py`
- `adapters/ytdlp/resolver.py`
- `adapters/ytdlp/downloader.py`
- `adapters/ytdlp/__init__.py`
- `engine/ytdlp_client.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-024

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Adapters
**Priority:** Medium
**Title:** Extract logika koneksi, IPC, dan observer MPV

**Reason:** Mengurai file `engine/mpv_controller.py` untuk pattern arsitektur Adapter yang bersih.

**Root Cause:**
-

**Solution:**
Pisahkan MPV Controller ke dalam package `adapters/mpv/` dengan `connection.py`, `ipc.py`, dan `observer.py`.

**Changed Files:**
- `adapters/mpv/connection.py`
- `adapters/mpv/ipc.py`
- `adapters/mpv/observer.py`
- `adapters/mpv/__init__.py`
- `engine/mpv_controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-023

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Persistence
**Priority:** Medium
**Title:** Extract god-class cache/db

**Reason:** Memecah cache/db yang menjadi terlalu besar.

**Root Cause:**
-

**Solution:**
Pisahkan `cache/db.py` (388 baris) ke dalam modul-modul repository di `persistence/` (`track_repo`, `artist_repo`, dll) dan buat Facade untuk `Database` di `persistence/__init__.py`.

**Changed Files:**
- `persistence/db.py`
- `persistence/track_repo.py`
- `persistence/session_repo.py`
- `persistence/artist_repo.py`
- `persistence/genre_repo.py`
- `persistence/library_repo.py`
- `persistence/__init__.py`
- `cache/db.py`
- `persistence/schema.sql`
- `scripts/architecture_lint.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-13-022

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Core
**Priority:** Low
**Title:** Setup struktur folder target migrasi

**Reason:** Persiapan arsitektur migrasi.

**Root Cause:**
-

**Solution:**
Persiapkan struktur folder untuk `adapters/`, `engine/radio/`, `persistence/`, `launcher/gui/`. Pisahkan constants `CMD_*` ke `core/commands.py` dan security ke `config_security.py`.

**Changed Files:**
- `adapters/__init__.py`
- `engine/radio/__init__.py`
- `persistence/__init__.py`
- `launcher/__init__.py`
- `core/command_bus.py`
- `core/commands.py`
- `config.py`
- `config_security.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-021

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Tooling
**Priority:** Low
**Title:** Gabung subprocess dep-check Python

**Reason:** Boot startup shell lambat.

**Root Cause:**
-

**Solution:**
Gabung 7 proses subprocess check ke 1 panggilan di `start.sh` dan `start.bat`. Hapus `sleep` artifisial.

**Changed Files:**
- `start.sh`
- `start.bat`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-020

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Cleanup
**Area:** Core
**Priority:** Low
**Title:** Hapus OTel span dari command_bus

**Reason:** OTel observability tidak digunakan.

**Root Cause:**
-

**Solution:**
Hapus overhead setup_tracing OTel dari `command_bus.py` dan `observability.py`.

**Changed Files:**
- `core/command_bus.py`
- `core/observability.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-019

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** Backend
**Priority:** Low
**Title:** Tambah include_lyrics flag di broadcast

**Reason:** Mengurangi payload broadcast periodik saat lirik tidak dibutuhkan.

**Root Cause:**
-

**Solution:**
Tambahkan `include_lyrics` di `state_to_dict` (default False). True saat initial state saja.

**Changed Files:**
- `server/serializers.py`
- `server/services/broadcast_service.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-018

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Backend
**Priority:** Medium
**Title:** Optimasi toggle_pause dan parallel broadcast

**Reason:** Responsivitas WS lambat saat pause.

**Root Cause:**
-

**Solution:**
Buat `toggle_pause` jadi fire-and-forget; parallel broadcast WS client; dan query Discover saat fetch parallel.

**Changed Files:**
- `server/handlers/websocket.py`
- `engine/playback/controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Medium

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-017

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** DB
**Priority:** Medium
**Title:** Tambah idx_songs_artist_id pada DB

**Reason:** JOIN query dari DB lambat saat Discover/Radio.

**Root Cause:**
-

**Solution:**
Buat index `idx_songs_artist_id` di schema sqlite.

**Changed Files:**
- `cache/schema.sql`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-016

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Backend
**Priority:** Low
**Title:** Optimasi handler event listeners

**Reason:** Redundansi throttler event track progress.

**Root Cause:**
-

**Solution:**
Hapus throttle `_on_track_progress` di WS layer karena sudah ditangani controller. Paralelkan query pasca-download.

**Changed Files:**
- `server/handlers/event_listeners.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-015

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Backend
**Priority:** Medium
**Title:** Jadikan increment play count fire-and-forget

**Reason:** Play count query IO memblokir transisi track baru.

**Root Cause:**
-

**Solution:**
Bungkus `increment_play_count` di track loader dalam `safe_create_task`.

**Changed Files:**
- `engine/playback/track_loader.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-014

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Backend
**Priority:** Low
**Title:** Throttle event lirik dan lazy import syncedlyrics

**Reason:** Modul mem-broadcast event secara membabi buta.

**Root Cause:**
-

**Solution:**
Pasang batas minimum 0.5s antara broadcast. Sembunyikan import modul `syncedlyrics` agar di-load hanya saat diperlukan.

**Changed Files:**
- `plugins/lyrics.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-013

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Core
**Priority:** Medium
**Title:** Throttle publish TrackProgressEvent

**Reason:** Event track progress terlalu sering menyebabkan UI render loop berat.

**Root Cause:**
-

**Solution:**
Throttle ke maksimal 1x per detik dan parallelkan `observe_property` saat start connect.

**Changed Files:**
- `engine/mpv_controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-012

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Core
**Priority:** Medium
**Title:** Parallelkan start db.init dan mpv.connect

**Reason:** Boot startup lambat karena DB dan MPV sinkron/berurutan.

**Root Cause:**
-

**Solution:**
Gunakan `asyncio.gather` untuk init paralel. Naikkan interval poller dan tambah cron `db_maintenance` tiap 6 jam.

**Changed Files:**
- `main.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-011

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Backend
**Priority:** High
**Title:** verify_password dipindah ke thread pool

**Reason:** Fungsi hashing (100k iter PBKDF2) memblokir event loop asyncio, membuat semua client hang saat ada yg login.

**Root Cause:**
-

**Solution:**
Pindahkan ke `run_in_executor`.

**Changed Files:**
- `server/handlers/auth.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-010

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Performance
**Area:** Core
**Priority:** Low
**Title:** Lazy import yt_dlp

**Reason:** Beban memori dan delay saat boot, plus mencegah thread zombie saat network timeout.

**Root Cause:**
-

**Solution:**
Lazy import yt-dlp pada `_extract_sync` dan `_download_sync`. Tambahkan `socket_timeout` pada opsi yt-dlp.

**Changed Files:**
- `engine/ytdlp_client.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-11-009

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Docs
**Priority:** Low
**Title:** Pecah verify_docs.py

**Reason:** File skrip validasi terlalu besar (850 baris).

**Root Cause:**
-

**Solution:**
Ekstrak package `shared/` dan modul `verify_docs/`. Tidak ada breaking change pada CLI.

**Changed Files:**
- `scripts/shared/`
- `scripts/verify_docs/`
- `scripts/verify_docs.py`
- `scripts/verify_security.py`
- `scripts/verify_structure.py`
- `scripts/architecture_lint.py`
- `scripts/generate_report.py`
- `scripts/generate_file_index.py`
- `docs/STRUCTURE.md`
- `docs/architecture/folder_structure.md`
- `AI_CONTEXT.md`
- `docs/AI_CONTEXT.md`
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-10-008

**Tanggal:** 2026-07-10
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** CI
**Area:** Tooling
**Priority:** Low
**Title:** Pindahkan .pre-commit-config.yaml ke root

**Reason:** Pre-commit butuh konfig ada di root repo.

**Root Cause:**
-

**Solution:**
Pindahkan lokasinya.

**Changed Files:**
- `.pre-commit-config.yaml`
- `docs/PATCHLOG.md`
- `docs/devops/tooling.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-10-007

**Tanggal:** 2026-07-10
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Docs
**Priority:** Low
**Title:** Sinkronisasi kontradiksi docs dan scripts

**Reason:** Ketidaksesuaian path dan nama skrip dengan file dokumentasi.

**Root Cause:**
-

**Solution:**
Sesuaikan tulisan docs dan konfigurasi hooks.

**Changed Files:**
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`
- `docs/STRUCTURE.md`
- `docs/INDEX.md`
- `.pre-commit-config.yaml`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-09-006

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Feature
**Area:** UI/JS
**Priority:** Medium
**Title:** Self-host Tabler Icons & hapus Google Fonts CDN

**Reason:** Memastikan UI tetap berfungsi penuh dan estetik secara offline (Local First).

**Root Cause:**
-

**Solution:**
Unduh dan host secara lokal file css/fonts vendor.

**Changed Files:**
- `web/static/index.html`
- `web/static/css/tokens.css`
- `web/static/css/vendor/tabler-icons.min.css`
- `web/static/css/vendor/fonts/*`
- `web/static/sw.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-09-005

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** Core
**Priority:** Medium
**Title:** Pindahkan logika unduhan ke mv daripada cp

**Reason:** Menduplikat file ke `cache/mp3` tidak efisien dan boros space.

**Root Cause:**
-

**Solution:**
Ubah operasi agar memindahkan file dari temp langsung ke folder `downloads/`.

**Changed Files:**
- `engine/download_manager.py`
- `server/handlers/websocket.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-09-004

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Fix
**Area:** UI/JS
**Priority:** Low
**Title:** Fix bug image cover di mode radio

**Reason:** Gambar sampul kadang broken di DOM karena reuse element (DOM recycle).

**Root Cause:**
-

**Solution:**
Hapus class terkait old img saat elemen tersebut di-recycle sebelum dimasukkan kembali.

**Changed Files:**
- `web/static/js/render/queue.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-09-003

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Docs
**Area:** Docs
**Priority:** Low
**Title:** Pembuatan awal dokumentasi knowledge base

**Reason:** Membutuhkan rekam dokumen arsitektur dan status untuk di-refer.

**Root Cause:**
-

**Solution:**
Buat struktur dan baseline docs.

**Changed Files:**
- `docs/INDEX.md`
- `docs/STRUCTURE.md`
- `docs/FILE_INDEX.md`
- `docs/PATCHLOG.md`
- `docs/REPORT.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-09-002

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Core
**Priority:** Medium
**Title:** Pecah monolith start.py ke launcher

**Reason:** Script bootstrap menjadi terlalu rumit.

**Root Cause:**
-

**Solution:**
Pecah proses menjadi `launcher/gui.py`, `launcher/process.py`, `launcher/network.py`, dll.

**Changed Files:**
- `start.py`
- `launcher/`
- `launcher/__init__.py`
- `launcher/gui.py`
- `launcher/process.py`
- `launcher/network.py`
- `launcher/updater.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

---

## PATCH-2026-07-09-001

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** All
**Priority:** Low
**Title:** Replace semua identitas legacy (YTGUI dll)

**Reason:** Re-branding project ke nama baru: LunaWave.

**Root Cause:**
-

**Solution:**
Ganti seluruh hardcode di config, main, js, dan manifest.

**Changed Files:**
- `config.py`
- `main.py`
- `core/observability.py`
- `web/static/js/utils.js`
- `web/static/manifest.json`
- `web/static/sw.js`
- `web/static/index.html`
- `scripts/generate_icons.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
-

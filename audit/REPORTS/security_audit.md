# Audit Keamanan — ytgui (bagas.fm)

Ruang lingkup: source code non-markdown (backend Python, frontend JS). `.backup_patchlog/` diabaikan. Setiap temuan dipetakan ke kategori yang diminta dan ke **OWASP Top 10 (2021)**.

---

## Ringkasan Eksekutif

Postur keamanan project ini **di atas rata-rata untuk solo/self-hosted project**: password hashing benar (PBKDF2+salt+timing-safe compare), rate limiting login & command, validasi SSRF/path-traversal pada stream proxy, SQL murni parameterized (nihil SQL Injection), dan escaping XSS konsisten di frontend (`textContent`/`escapeHtml`). Temuan yang ada didominasi **Medium/Low** — celah paling signifikan adalah **broken session revocation saat logout** dan **beberapa gap defense-in-depth** (Origin validation WS, iterasi PBKDF2 di bawah rekomendasi terbaru).

| Severity | Jumlah |
|---|---|
| 🔴 Critical | 0 |
| 🟠 High | 1 |
| 🟡 Medium | 4 |
| 🟢 Low | 4 |
| ⚪ Info / Not Applicable | 4 |

---

## SEC-01 — Broken Authentication: Logout tidak me-revoke session token di server

**Severity:** 🟠 High
**OWASP:** A07:2021 – Identification and Authentication Failures

**Lokasi:** `web/static/js/services/auth.js` (`logout()`) vs `server/handlers/websocket.py` / `cache/db.py`

**Deskripsi:**
`logout()` di frontend hanya menghapus token dari `localStorage` (`safeStorage.remove("ytgui_session_token")`) dan menutup koneksi WS. **Tidak ada WS action `logout`/`revoke_session` yang dikirim ke server**, dan memang tidak ada handler semacam itu terdaftar di `_ws_handlers` (`server/handlers/websocket.py`). Token yang sudah diterbitkan (`db.create_session(token, now+86400)`) tetap **valid di database selama 24 jam** meskipun user menekan "Logout".

**Dampak:** Jika token pernah bocor (device publik, XSS di masa depan, screen-share, dsb.), "logout" tidak menutup jendela serangan — token curian tetap bisa dipakai login otomatis (`{"type":"cmd","action":"auth","data":{"token":"<stolen>"}}`) hingga 24 jam berikutnya walau pemilik sah sudah logout.

**Cara reproduksi:**
1. Login sebagai admin, catat/curi `ytgui_session_token` dari localStorage.
2. Tekan tombol Logout di UI.
3. Dari sesi terpisah (mis. curl/websocket client lain), kirim `{"type":"cmd","action":"auth","data":{"token":"<token lama>"}}`.
4. Server tetap mengembalikan `auth_status: success` — akses admin penuh didapat walau user sudah "logout".

**Solusi:** Tambahkan WS action `logout` yang memanggil `db.delete_session(token)` di server, dan panggil ini dari `logout()` sebelum token dihapus di client.

**Kode perbaikan:**
```python
# server/handlers/websocket.py
@register_ws_handler("logout")
async def _handle_logout(data, ws, client_ip, state, ytdlp, manager, db):
    token = data.get("token")
    if token and db:
        await db.delete_session(token)
    manager.authenticated_connections.discard(ws)
    await ws.send_str(json.dumps({"type": "auth_status", "data": {"success": False, "message": "Logged out"}}))
```
```javascript
// web/static/js/services/auth.js — di dalam logout(), sebelum safeStorage.remove(...)
const token = window.safeStorage.get("ytgui_session_token");
if (token) {
    wsSend("logout", { token: token });
}
```

---

## SEC-02 — Security Misconfiguration: Tidak ada validasi `Origin` header pada WebSocket handshake

**Severity:** 🟡 Medium
**OWASP:** A05:2021 – Security Misconfiguration (terkait CSWSH — Cross-Site WebSocket Hijacking)

**Lokasi:** `server/handlers/websocket.py` — `ws_handler()`

**Deskripsi:** `ws_handler` menerima koneksi WebSocket dari origin manapun tanpa memeriksa header `Origin`. Eksploitasi penuh dimitigasi karena autentikasi memerlukan token eksplisit dalam payload JSON (bukan cookie ambient), sehingga halaman pihak ketiga tidak bisa otomatis membawa kredensial korban. Namun tanpa validasi `Origin`, aplikasi tidak punya lapisan pertahanan kedua — request read-only tak berautentikasi (`search`, `discover` bila tersedia untuk non-admin di masa depan) tetap bisa dipanggil dari origin manapun, dan ini menyimpang dari praktik *defense in depth* standar untuk WS endpoint.

**Cara reproduksi:**
1. Buat halaman HTML di domain lain berisi `new WebSocket("ws://target-ip:8765/ws")`.
2. Koneksi WS **berhasil terbuka** tanpa penolakan berbasis origin — server tidak pernah mengecek `request.headers.get("Origin")`.

**Solusi:** Tambahkan whitelist Origin (atau minimal reject origin asing jika app tidak dimaksudkan diakses cross-origin).

**Kode perbaikan:**
```python
async def ws_handler(request):
    origin = request.headers.get("Origin", "")
    host_header = request.headers.get("Host", "")
    if origin and host_header and origin not in (f"http://{host_header}", f"https://{host_header}"):
        return web.HTTPForbidden(text="Origin tidak diizinkan")
    ...
```

---

## SEC-03 — Password Storage: Iterasi PBKDF2 (100.000) di bawah rekomendasi terbaru

**Severity:** 🟡 Medium
**OWASP:** A02:2021 – Cryptographic Failures

**Lokasi:** `core/security.py` — `hash_password()`

**Deskripsi:**
```python
key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
```
Implementasi dasarnya **sudah benar** (salt acak per-password via `secrets.token_bytes`, `secrets.compare_digest` untuk perbandingan timing-safe, tidak ada fallback plaintext). Namun 100.000 iterasi berada di bawah rekomendasi OWASP terbaru untuk PBKDF2-HMAC-SHA256 (≥ 600.000 iterasi per OWASP Password Storage Cheat Sheet edisi terbaru), sehingga hash lebih rentan terhadap serangan brute-force offline jika database/`admin_password.txt` bocor.

**Cara reproduksi:** Tidak ada eksploitasi langsung — ini masalah *cryptographic margin*, teruji lewat perhitungan: 100k iterasi PBKDF2-SHA256 di GPU modern jauh lebih cepat di-brute-force dibanding 600k+.

**Solusi:** Naikkan iterasi count, atau migrasi ke algoritma memory-hard (`argon2id`/`scrypt`) yang jauh lebih resisten terhadap GPU cracking untuk aplikasi baru.

**Kode perbaikan:**
```python
import hashlib, secrets, base64

PBKDF2_ITERATIONS = 600_000  # naik dari 100_000

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(key).decode()}"
```
*(Fungsi `verify_password` sudah membaca iterasi dari hash string, jadi tetap backward-compatible dengan hash lama bila migrasi bertahap.)*

---

## SEC-04 — Rate Limiting Bypass: `X-Forwarded-For` dipercaya penuh tanpa validasi proxy chain saat `TRUSTED_PROXY=true`

**Severity:** 🟡 Medium
**OWASP:** A04:2021 – Insecure Design (terkait bypass rate-limiting/brute-force protection)

**Lokasi:** `server/handlers/websocket.py` (baris pengecekan `TRUSTED_PROXY`), `config.py`

**Deskripsi:**
```python
if TRUSTED_PROXY and "X-Forwarded-For" in request.headers:
    client_ip = request.headers.get("X-Forwarded-For").split(",")[0].strip()
```
Default `TRUSTED_PROXY=false` (aman). Namun jika operator mengaktifkannya (mis. saat deploy di belakang nginx/cloudflare tunnel) tanpa reverse proxy yang benar-benar *strip* header `X-Forwarded-For` dari client asli, **client dapat memalsukan IP mereka sendiri** dengan mengirim header `X-Forwarded-For: 1.2.3.4` langsung ke server (jika port server ter-expose, atau reverse proxy tidak overwrite header). Ini membuat rate-limit login (`MAX_LOGIN_ATTEMPTS`) dan rate-limit command menjadi mudah di-bypass — attacker brute-force password admin tinggal mengganti nilai `X-Forwarded-For` di tiap request untuk "reset" counter percobaan login.

**Cara reproduksi (asumsi `TRUSTED_PROXY=true` dan port aplikasi ter-expose langsung, bukan hanya lewat proxy):**
1. Kirim beberapa percobaan login gagal dengan header `X-Forwarded-For: 1.1.1.1`.
2. Setelah mendekati `MAX_LOGIN_ATTEMPTS`, ganti header menjadi `X-Forwarded-For: 1.1.1.2`, dst.
3. Rate limit tidak pernah tercapai karena `client_ip` berubah tiap request — brute force password admin bisa dilakukan tanpa batas.

**Solusi:** Dokumentasikan dengan tegas bahwa `TRUSTED_PROXY` hanya boleh diaktifkan jika server *tidak* dapat diakses langsung (hanya lewat reverse proxy tepercaya), dan idealnya validasi bahwa request datang dari IP proxy yang dikenal sebelum mempercayai header tersebut.

**Kode perbaikan:**
```python
# config.py
TRUSTED_PROXY_IPS = set(os.environ.get("TRUSTED_PROXY_IPS", "127.0.0.1").split(","))

# websocket.py
client_ip = request.remote
if TRUSTED_PROXY and client_ip in TRUSTED_PROXY_IPS and "X-Forwarded-For" in request.headers:
    client_ip = request.headers.get("X-Forwarded-For").split(",")[0].strip()
```

---

## SEC-05 — Missing Validation: `video_id` dari WebSocket tidak divalidasi format (celah minor untuk resource exhaustion)

**Severity:** 🟡 Medium
**OWASP:** A03:2021 – Injection (kategori terdekat: input validation gap; bukan SQLi/command injection nyata)

**Lokasi:** `server/serializers.py::dict_to_track()`

**Deskripsi:** HTTP endpoint `serve_stream` memvalidasi `video_id` ketat dengan `^[a-zA-Z0-9_-]{11}$`, tapi jalur WebSocket (`dict_to_track`, dipakai oleh `play_track`, `queue_add`, `download`) hanya mengecek non-kosong. `video_id` sembarangan diteruskan ke `yt-dlp` (thread pool 4 worker, timeout 25 detik per panggilan) — attacker terautentikasi dapat mengirim banyak `video_id` invalid secara cepat untuk menghabiskan slot thread pool (resource exhaustion / minor DoS terhadap fitur pemutaran, meski tidak untuk seluruh server karena aiohttp event loop tetap responsif).

*(Detail teknis identik dengan BUG-06 pada audit bug sebelumnya — dicantumkan ulang di sini karena relevan sebagai kategori security "Missing Validation".)*

**Solusi & kode perbaikan:** Lihat regex validasi yang sama seperti `serve_stream`, diterapkan di `dict_to_track()`.

```python
import re
_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

def dict_to_track(data: dict) -> Optional[TrackInfo]:
    video_id = data.get("video_id")
    if not video_id or not _VIDEO_ID_RE.match(video_id):
        return None
    return TrackInfo(video_id=video_id, ...)
```

---

## SEC-06 — Secret Exposure (Low, mitigated): Password admin auto-generate dicetak ke `stderr` saat startup

**Severity:** 🟢 Low
**OWASP:** A02:2021 – Cryptographic Failures / A09:2021 – Security Logging and Monitoring Failures

**Lokasi:** `config.py` (blok auto-generate password)

**Deskripsi:**
```python
print(f"PASSWORD ADMIN GENERATED: {raw_password}")
```
Password plaintext dicetak sekali ke konsol (`stderr`) saat pertama kali dijalankan tanpa `YTGUI_ADMIN_PASS`. Ini secara desain "hanya sekali" dan tidak ditulis ke file (`admin_password.txt` menyimpan versi ter-hash, bukan plaintext — sudah benar). Risiko rendah karena hanya operator lokal (akses terminal Termux) yang melihatnya, **namun** jika stdout/stderr proses ini pernah di-pipe ke file log persisten (mis. `nohup python main.py > run.log 2>&1 &` — pola umum di Termux/screen session), password plaintext akan tersimpan permanen di file log tersebut.

**Cara reproduksi:** Jalankan `python start.py > /tmp/run.log 2>&1` pada instalasi baru → buka `/tmp/run.log` → password plaintext admin ada di dalamnya.

**Solusi:** Tambahkan peringatan eksplisit di output agar operator tidak meredirect ke file log persisten, atau gunakan mekanisme terpisah (file sementara yang di-print path-nya saja, bukan isinya, lalu dihapus otomatis setelah dibaca sekali).

**Kode perbaikan:**
```python
print(f"\n==========================================")
print(f"PASSWORD ADMIN GENERATED: {raw_password}")
print(f"⚠️  JANGAN redirect output ini ke file log permanen (mis. `> run.log`).")
print(f"Harap simpan password ini! Tidak akan ditampilkan lagi.")
print(f"==========================================\n")
```

---

## SEC-07 — Broken Authentication (Low): Tidak ada mekanisme logout-all-sessions / rotasi token setelah ganti password

**Severity:** 🟢 Low
**OWASP:** A07:2021 – Identification and Authentication Failures

**Lokasi:** `cache/db.py`, `server/handlers/auth.py` (tidak ada handler "change password" ditemukan sama sekali di codebase — password hanya diset lewat env var/first-run)

**Deskripsi:** Karena tidak ada fitur ubah password dari UI, tidak ada juga mekanisme invalidasi semua token sesi aktif jika password admin dianggap bocor (selain menghapus manual baris di tabel `sessions` via akses langsung ke DB). Untuk aplikasi yang tokennya berumur 24 jam dan tidak di-revoke saat logout (lihat SEC-01), operator tidak punya jalan cepat "kill semua sesi" dari dalam aplikasi jika curiga token bocor.

**Solusi:** Tambahkan command/CLI flag sederhana untuk revoke semua sesi aktif (`DELETE FROM sessions`), dan idealnya expose lewat endpoint admin-only atau start-up flag.

**Kode perbaikan (tambahan method + start flag):**
```python
# cache/db.py
async def revoke_all_sessions(self):
    await self._conn.execute("DELETE FROM sessions")
    await self._conn.commit()
```
```python
# main.py — opsional, dijalankan manual: python main.py --revoke-sessions
if "--revoke-sessions" in sys.argv:
    await db.revoke_all_sessions()
    print("Semua sesi admin telah dicabut.")
    return
```

---

## SEC-08 — Encryption at Rest: Data tidak dienkripsi (informasional, sesuai skala aplikasi)

**Severity:** 🟢 Low (Informational)
**OWASP:** A02:2021 – Cryptographic Failures

**Lokasi:** `cache/db.py` (SQLite plaintext), `cache/mp3/` (file audio plaintext), `data/library.db`

**Deskripsi:** Database SQLite dan file cache MP3 disimpan tanpa enkripsi at-rest. Untuk aplikasi self-hosted single-user di device milik sendiri (Termux/Android), ini adalah trade-off yang **wajar** (encryption at rest untuk file lokal di device pribadi umumnya YAGNI) — tapi perlu dicatat eksplisit bahwa jika device dipakai bersama (shared device) atau backup device tidak terenkripsi, riwayat pemutaran/lagu tersimpan bisa dibaca siapa saja dengan akses filesystem.

**Solusi (opsional, hanya jika threat model berubah ke shared/multi-user device):** Gunakan SQLCipher untuk `library.db`, atau enkripsi filesystem-level (mis. Android's built-in device encryption, yang sudah default di kebanyakan device modern) — tidak perlu perubahan kode aplikasi untuk opsi kedua.

---

## SEC-09 — Rate Limiting: Password hash comparison tidak menerapkan account lockout permanen, hanya sliding window 5 menit

**Severity:** 🟢 Low
**OWASP:** A07:2021 – Identification and Authentication Failures

**Lokasi:** `server/handlers/auth.py`

**Deskripsi:** `MAX_LOGIN_ATTEMPTS` per 300 detik sudah diterapkan dengan baik (bagus, mencegah brute-force naif) — tapi karena window rate-limit hanya 5 menit dan tidak ada mekanisme lockout jangka panjang/notifikasi, attacker dengan waktu tak terbatas tetap bisa brute-force password secara perlahan (mis. beberapa percobaan tiap 5 menit selama berhari-hari) tanpa terdeteksi/terhenti permanen, terutama karena tidak ada alerting/logging terpusat untuk pola brute-force lambat semacam ini.

**Cara reproduksi:** Login gagal berulang dengan jeda >5 menit antar-batch percobaan — rate limit selalu "reset", tidak ada akumulasi jangka panjang.

**Solusi:** Tambahkan lapisan kedua: hitung total percobaan gagal per-IP dalam window lebih panjang (mis. 24 jam) dan log/alert jika melebihi threshold, walau tidak diblokir permanen (menghindari DoS lockout terhadap IP yang salah).

**Kode perbaikan (opsional, logging tambahan):**
```python
# di dalam handle_auth, jalur gagal login
attempts.append(now)
manager.login_attempts[client_ip] = attempts
if len(attempts) >= MAX_LOGIN_ATTEMPTS:
    logger.warning(f"Kemungkinan brute-force login dari {client_ip}: {len(attempts)} percobaan gagal")
```

---

## Kategori yang Diperiksa Tapi **Tidak Ditemukan Masalah** (Not Applicable / Aman)

| Kategori | Status | Catatan |
|---|---|---|
| **SQL Injection** | ✅ Aman | Seluruh query di `cache/db.py` memakai parameterized query (`?` placeholder via `aiosqlite`). Tidak ditemukan satu pun string interpolation (`f"SELECT..."`, `.format()`, `%`) untuk membangun SQL. |
| **XSS (Cross-Site Scripting)** | ✅ Aman (mayoritas) | Frontend konsisten memakai `textContent` atau `escapeHtml()` (helper berbasis `div.textContent` → `innerHTML`, pola aman) untuk merender data dinamis (judul lagu, artis, lirik) yang berasal dari YouTube/pengguna. Tidak ditemukan `innerHTML =` dengan data tak ter-escape di 30 titik penggunaan `innerHTML` yang diperiksa. |
| **CSRF** | ✅ Risiko rendah | Aplikasi tidak memakai cookie untuk autentikasi (token dikirim eksplisit dalam payload JSON WebSocket), sehingga tidak ada *ambient credential* yang bisa dieksploitasi CSRF klasik. Endpoint HTTP (`/api/stream`, `/health`, `/metrics`) semuanya read-only/idempotent, tidak ada state-changing HTTP endpoint berbasis cookie. |
| **SSRF** | ✅ Aman | `serve_stream` (HTTP) memvalidasi domain redirect/proxy hanya ke `*.googlevideo.com`/`*.youtube.com` dengan scheme HTTPS wajib — SSRF ke internal network/metadata endpoint (mis. `169.254.169.254`) diblokir. `LyricsFetcher` memakai base URL tetap (`lrclib.net`), bukan URL dinamis dari input user. |
| **Command Injection** | ✅ Aman | Seluruh pemanggilan proses eksternal (`mpv`, `yt-dlp` via library, `taskkill`/`pkill`/`fuser`) memakai `asyncio.create_subprocess_exec`/`subprocess.run` dengan **list argumen**, bukan `shell=True` atau string concatenation — tidak ada celah shell injection. |
| **File Upload Vulnerability** | ⚪ Not Applicable | Aplikasi tidak memiliki fitur upload file dari user sama sekali (hanya download dari YouTube ke server). |
| **Open Redirect** | ✅ Aman | Satu-satunya `HTTPFound`/redirect (`serve_stream`) divalidasi ketat ke domain googlevideo/youtube dengan scheme HTTPS sebelum redirect — tidak menerima URL redirect arbitrer dari parameter user. |
| **JWT Issue** | ⚪ Not Applicable | Aplikasi tidak memakai JWT — session token adalah random opaque hex (`secrets.token_hex(16)`) yang divalidasi lewat lookup DB, bukan token self-contained yang bisa dipalsukan/decode. Pendekatan ini menghindari seluruh kelas masalah umum JWT (`alg: none`, weak secret, dsb.) sepenuhnya. |
| **API Key Exposure** | ⚪ Not Applicable | Tidak ditemukan API key pihak ketiga yang perlu dirahasiakan (yt-dlp tidak butuh API key, lrclib.net API publik tanpa key). |
| **Hardcoded Secret** | ✅ Aman | Tidak ditemukan secret/password/token hardcoded di source code (di luar file test yang memang memakai dummy value). `ADMIN_PASSWORD` selalu berasal dari env var atau digenerate acak saat runtime. |
| **Broken Authorization / Privilege Escalation** | ✅ Risiko rendah | Model otorisasi sederhana (binary admin/non-admin), tidak ditemukan jalur bagi non-admin untuk eskalasi ke admin (`require_auth` konsisten diperiksa di `handle_ws_message` sebelum dispatch ke seluruh `_ws_handlers`, kecuali action `auth` itu sendiri — sesuai desain). |

---

## Pemetaan ke OWASP Top 10 (2021)

| OWASP Category | Temuan Terkait |
|---|---|
| A01 Broken Access Control | — (tidak ada temuan signifikan) |
| A02 Cryptographic Failures | SEC-03 (iterasi PBKDF2), SEC-06 (password tercetak ke stderr), SEC-08 (no encryption at rest, informational) |
| A03 Injection | SEC-05 (missing validation `video_id` WS) — bukan SQLi/command injection nyata |
| A04 Insecure Design | SEC-04 (X-Forwarded-For trust tanpa validasi proxy) |
| A05 Security Misconfiguration | SEC-02 (no Origin validation WS) |
| A06 Vulnerable Components | Tidak diaudit di sini — lihat `requirements.txt`; disarankan jalankan `pip-audit`/`safety` secara berkala (di luar cakupan static code review ini) |
| A07 Identification & Authentication Failures | **SEC-01 (High)**, SEC-07, SEC-09 |
| A08 Software & Data Integrity Failures | — (tidak ada temuan; tidak ada deserialization tak aman/auto-update mechanism) |
| A09 Security Logging & Monitoring Failures | SEC-06 (terkait), SEC-09 (terkait) |
| A10 SSRF | — (aman, lihat tabel di atas) |

---

## Prioritas Perbaikan

1. **SEC-01** — Implementasikan revoke session saat logout (High, dampak nyata terhadap keamanan akun admin).
2. **SEC-02** — Validasi Origin header WS (defense-in-depth murah untuk diterapkan).
3. **SEC-04** — Batasi kepercayaan terhadap `X-Forwarded-For` hanya dari IP proxy dikenal.
4. **SEC-05** — Samakan validasi `video_id` di jalur WS dengan jalur HTTP.
5. **SEC-03** — Naikkan iterasi PBKDF2 (atau migrasi ke argon2id) saat ada kesempatan refactor auth.
6. Sisanya (SEC-06 s/d SEC-09) bersifat hardening tambahan, bisa dikerjakan bertahap.

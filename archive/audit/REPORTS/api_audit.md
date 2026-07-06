# Audit API — ytgui

Catatan: Aplikasi ini pada dasarnya **bukan REST murni** — sebagian besar operasi (play, queue, download, favorite, search, dsb.) dikirim lewat satu koneksi **WebSocket (`/ws`)** dengan skema `{type, action, data}`, sedangkan hanya segelintir endpoint yang benar-benar HTTP (`/`, `/admin`, `/health`, `/metrics`, `/api/stream/{video_id}`). Audit di bawah mencakup keduanya karena keduanya adalah "API" aplikasi ini.

File yang diaudit utamanya: `server/app.py`, `server/handlers/http.py`, `server/handlers/websocket.py`, `server/handlers/auth.py`, `server/middleware.py`, `core/security.py`, `core/constants.py`, `config.py`, `server/serializers.py`, `web/static/js/ws.js`, `web/static/js/services/auth.js`.

---

## 1. REST Standard

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| Seluruh aksi domain (`play_track`, `queue_add`, `toggle_favorite`, `download`, dst.) via WS `action` | Bukan resource-oriented REST — semua operasi CRUD (queue, favorite, download) diekspos sebagai RPC command dalam satu channel WS, bukan endpoint HTTP dengan verb yang sesuai (POST/PUT/DELETE) | Medium | Jika tetap butuh REST untuk sebagian aksi non-realtime (favorite, download, queue CRUD), buat resource HTTP eksplisit (`POST /api/favorites/{id}`, `DELETE /api/queue/{index}`), pertahankan WS hanya untuk event realtime (state, progress) |
| `GET /`, `GET /admin` | Dua route berbeda me-render file yang sama (`index.html`) tanpa pembeda peran di server — pemisahan admin/portal murni dilakukan di client JS | Low | Jika `/admin` memang harus jadi entry point terpisah, pertimbangkan flag/context yang dikirim server, atau gabungkan jadi satu route dengan routing client-side saja tanpa endpoint kembar |

## 2. HTTP Status

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| `GET /health` | Selalu mengembalikan **HTTP 200** meski body berisi `"status": "degraded"` (DB terputus / mpv belum konek) | Medium | Kembalikan `503 Service Unavailable` saat `status != "ok"` agar load balancer / health probe (mis. Docker/K8s) bisa mendeteksi dengan benar |
| `GET /api/stream/{video_id}` | Campur `HTTPBadRequest`, `HTTPForbidden`, `HTTPServiceUnavailable`, `HTTPInternalServerError` — sudah cukup baik, tapi kegagalan SSRF-check dan kegagalan resolve stream sama-sama dikembalikan sebagai teks polos, bukan format konsisten | Low | Standardisasi semua response error (lihat kategori Error Response) |
| WS command gagal (`handle_ws_message` catch-all) | Tidak ada "status code" WS yang konsisten (WS tidak punya status HTTP), tapi juga tidak ada kode error terstruktur — hanya `{"type":"error","data": str(e)}` | Medium | Tambahkan `code` (mis. `AUTH_REQUIRED`, `RATE_LIMITED`, `VALIDATION_ERROR`, `INTERNAL`) selain pesan teks |

## 3. Naming

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| Route HTTP: `/api/stream/{id}` vs `/health`, `/metrics`, `/admin`, `/` | Tidak konsisten — sebagian pakai prefix `/api`, sebagian tidak | Low | Konsistenkan: semua endpoint data di bawah `/api/...`, sedangkan `/health` dan `/metrics` boleh tetap di root (konvensi umum operasional) |
| Action WS: `toggle_favorite`, `queue_select`, `queue_add`, `enqueue_genre_songs`, `enqueue_artist_songs`, `radio_randomize`, `lyrics_offset` | Penamaan action campur pola verb-first (`toggle_`, `set_`) dan noun-first (`queue_select`, `queue_add`, `queue_remove`, `queue_reorder`) serta ada yang sangat spesifik/panjang (`enqueue_genre_songs` vs `enqueue_artist_songs` — pola tak seragam dengan `queue_add`) | Low | Tetapkan satu konvensi, misal selalu `resource.verb` (`queue.add`, `queue.remove`, `favorite.toggle`, `genre.enqueue`) agar mudah diprediksi dan didaftarkan otomatis |

## 4. Authentication

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| `GET /api/stream/{video_id}` | **Tidak ada autentikasi sama sekali.** Endpoint ini bisa memicu resolve stream via `ytdlp.get_stream_url()` (operasi mahal, keluar ke YouTube) oleh siapa pun tanpa login, dan tidak dibatasi rate limit | **High** | Wajibkan token sesi (mis. query param signed token / header) sebelum memproses request, atau minimal batasi rate per-IP khusus endpoint ini |
| `GET /admin` | Menyajikan HTML app admin tanpa pengecekan sesi di server — proteksi hanya di client JS (bisa dilewati) | Medium | Ini "aman" selama semua *aksi* tervalidasi di WS (yang memang sudah begitu), tapi sebaiknya beri catatan eksplisit / header agar tidak disalahartikan sebagai boundary keamanan |
| Token sesi WS disimpan di `localStorage` (`ytgui_session_token`, lihat `web/static/js/ws.js`) | Token 16-byte hex disimpan di `localStorage`, rentan dicuri lewat XSS (tidak ada perlindungan `httpOnly`) karena berbasis WS bukan cookie | Medium | Sulit dihindari sepenuhnya untuk WS token-based auth, tapi kurangi masa berlaku token (saat ini 24 jam — `int(now)+86400`), dan pastikan tidak ada celah XSS di sisi client (audit input yang di-render tanpa escaping) |
| `GET /metrics` | Autentikasi berbasis `X-Metrics-Token` dibandingkan dengan `==` biasa, bukan `secrets.compare_digest` | Low | Gunakan `secrets.compare_digest` untuk mencegah timing attack, konsisten dengan pola yang sudah dipakai di `handle_auth` |
| Login admin (`handle_auth`) | Sudah baik: PBKDF2-SHA256 (100k iterasi), `compare_digest`, session token acak, limit 5 percobaan/5 menit | — (positif) | Pertahankan; pertimbangkan menambah backoff progresif atau captcha setelah beberapa kali gagal |

## 5. Authorization

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| Semua action WS setelah login | Hanya ada satu peran: *authenticated* vs *not*. Tidak ada granularitas (mis. siapa boleh `download`, siapa hanya boleh `play`) — sesuai konteks single-admin app ini mungkin cukup, tapi berisiko jika ke depan ditambah multi-user | Low | Jika direncanakan multi-user, tambahkan scope/role per token, bukan boolean tunggal |
| `GET /api/stream/{video_id}` | Tidak ada pengecekan otorisasi apa pun (lihat juga poin Authentication) — siapa pun yang tahu/menebak `video_id` (11 karakter, mudah didapat dari YouTube) dapat memicu proxy stream | High | Terapkan minimal cek origin/referrer atau token, terutama karena endpoint ini menjadi pintu proxy ke resource eksternal |

## 6. Pagination

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| WS `discover` (`get_recent(15)`, `get_favorites(15)`, `get_cached(15)`, `get_featured_artists(100)`, `get_featured_genres(100)`) | Limit di-hardcode di kode server, tidak ada parameter `limit`/`offset`/`cursor` dari client, tidak ada cara mengambil halaman berikutnya | Medium | Tambahkan parameter `limit`/`offset` (atau cursor) di payload `discover`, kembalikan juga `has_more`/`total` |
| WS `search` (`ytdlp.search(query, max_results=10)`) | Hasil pencarian dibatasi 10, tidak bisa "load more" | Low | Tambahkan parameter `max_results`/halaman berikutnya dari client (dengan batas atas wajar agar tidak disalahgunakan) |

## 7. Caching

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| `GET /api/stream/{video_id}` (cache-hit lokal) | `web.FileResponse(cache_file, headers={"Access-Control-Allow-Origin": "*"})` — tidak set `Cache-Control`, `ETag`, atau `Last-Modified`, berbeda dari jalur proxy live yang set `Cache-Control: private, max-age=3600` → perilaku cache browser tidak konsisten antara file lokal vs proxy | Medium | Samakan header caching untuk kedua jalur; tambahkan `ETag`/`Last-Modified` + dukungan `If-None-Match` agar bisa balas `304` |
| `GET /` (`serve_index`) | `Cache-Control: no-cache` untuk shell SPA — sudah tepat agar update selalu ter-fetch | — (positif) | Pertahankan |
| Static assets (`/static`) | `add_static` bawaan aiohttp tanpa konfigurasi cache header eksplisit (immutable/long-lived cache untuk asset ber-hash) | Low | Tambahkan `Cache-Control: public, max-age=...` khusus untuk `/static` jika asset di-versioning (hash filename) |
| `stream_url` cache di DB (`STREAM_URL_TTL_SEC = 21600`) | TTL 6 jam untuk URL stream YouTube — cukup baik, tapi tidak ada mekanisme invalidasi manual jika YouTube mencabut URL lebih awal (hanya ditangani reaktif saat dapat 403/410 dari upstream) | Low | Sudah ditangani lewat retry-refetch saat 403/410; cukup didokumentasikan sebagai desain yang disengaja |

## 8. Validation

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| `GET /api/stream/{video_id}` | Validasi `video_id` dengan regex `^[a-zA-Z0-9_-]{11}$` — baik dan mencegah path traversal (ada juga `is_relative_to` check) | — (positif) | Pertahankan |
| WS handlers (`volume_set`, `queue_reorder`, `seek`, `lyrics_offset`, dll.) | Validasi minim/tidak konsisten: `int(data.get("volume", 80))`, `int(data.get("index", 0))`, `float(data.get("position", 0))` dipanggil langsung tanpa cek batas (mis. `volume` bisa negatif atau > `MAX_VOLUME=150`, `index` bisa negatif/di luar panjang queue) | Medium | Validasi range eksplisit sebelum `command_bus.execute` (clamp volume 0–150, index 0..len(queue)-1, dst.), jangan andalkan lapisan command/engine untuk menahan semua input tak terduga |
| `dict_to_track` (`server/serializers.py`) | Tidak memvalidasi `video_id` sesuai format YouTube (beda dengan validasi ketat di `serve_stream`), `duration` di-cast `int()` tanpa cek non-negatif, `title`/`artist` tidak dibatasi panjang/karakter | Medium | Terapkan validasi seragam (regex `video_id`, panjang string, angka non-negatif) di satu tempat (mis. helper validasi bersama), agar tidak berbeda-beda per endpoint |
| Exception generik di `handle_ws_message` | Saat `int()`/`float()` gagal atau field lain error, pesan exception mentah (`str(e)`) dikirim balik ke client | Medium | Lihat kategori *Error Response* — jangan expose pesan internal mentah |

## 9. Versioning

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| Semua endpoint HTTP & protokol WS | Tidak ada versi sama sekali — tidak ada `/v1/` di URL, tidak ada field `version` di payload WS (`{type, action, data}`) | Medium | Tambahkan `/api/v1/...` untuk HTTP, dan field `protocol_version` di handshake WS agar client lama/baru bisa dideteksi dan kompatibilitas dijaga saat skema command berubah |

## 10. Rate Limit

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| `GET /api/stream/{video_id}` | **Tidak ada rate limit** — endpoint termahal (memicu resolve yt-dlp + proxy streaming) justru tanpa proteksi sama sekali, berbeda dari WS yang sudah dibatasi | **High** | Terapkan rate limit per-IP (mis. token bucket) khusus endpoint ini, karena ini titik DoS paling murah untuk diserang |
| `GET /health`, `GET /metrics` | Tidak ada rate limit (untuk `/metrics` setidaknya ada auth token/localhost check) | Low | Umumnya wajar untuk endpoint operasional, tapi tetap pertimbangkan limit ringan untuk mencegah scraping berlebihan |
| WS command (`check_rate_limit`, `MAX_RATE_LIMIT=30/60 detik`) & login attempt (`MAX_LOGIN_ATTEMPTS=5/300 detik`) | Disimpan **in-memory** (`manager.command_history`, `manager.login_attempts`) — reset saat server restart, dan tidak konsisten jika aplikasi dijalankan multi-proses/multi-instance (tiap instance punya limit sendiri) | Medium | Untuk single-instance/local app ini mungkin cukup, tapi jika akan discale, pindahkan ke store bersama (Redis dsb.) |

## 11. Timeout

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| `serve_stream` — proxy ke upstream googlevideo (`http_session.get(stream_url, headers=headers)`) | **Tidak ada timeout** pada request ke upstream (`aiohttp.ClientSession()` dibuat tanpa `timeout=` default di `main.py`, dan tidak di-override per-request) — jika upstream hang, koneksi client bisa menggantung tanpa batas | **High** | Tambahkan `timeout=aiohttp.ClientTimeout(total=..., sock_connect=..., sock_read=...)` pada `ClientSession` atau per-request `.get()` |
| `ytdlp.get_stream_url()` | Sudah punya timeout (`YTDLP_RESOLVE_TIMEOUT_SEC = 25`) | — (positif) | Pertahankan |
| WS handler secara umum | Tidak ada timeout eksplisit untuk operasi command (`command_bus.execute`) — jika salah satu command internal hang (mis. panggilan mpv/db lambat), tidak ada batas waktu yang memutus | Medium | Bungkus eksekusi command dengan `asyncio.wait_for(..., timeout=N)` agar tidak memblokir loop koneksi WS |

## 12. Retry

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| `serve_stream` | Ada retry (maks. 2 percobaan) saat stream URL YouTube kedaluwarsa (403/410) — pola bagus, tapi `except Exception` yang menangkap *semua* jenis error lalu retry generik tanpa membedakan error yang retry-able vs tidak (mis. error DNS vs error 4xx permanen lain) | Medium | Bedakan exception (network transient vs client error) sebelum memutuskan retry; tambahkan backoff kecil antar percobaan |
| WS commands (`play_track`, `download`, dll.) | Tidak ada mekanisme retry sisi server; jika client mengirim ulang (mis. akibat reconnect WS) tidak ada dedupe (lihat kategori Idempotency) | Medium | Kombinasikan dengan idempotency key agar retry dari client aman |

## 13. Idempotency

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| WS `download`, `queue_add`, `play_track` | Tidak ada idempotency key — jika client mengirim command dua kali (double klik, retry setelah WS reconnect/timeout), tidak ada mekanisme dedupe di server, berpotensi duplikasi entri queue atau proses download ganda | Medium | Tambahkan `request_id` unik dari client yang di-cache sebentar di server untuk menolak duplikat dalam window singkat, terutama untuk `download` dan `queue_add` |
| `POST`-like actions lain (`toggle_favorite`, `radio_randomize`) | `toggle_favorite` secara desain memang toggle (idempotensi tidak relevan dalam arti klasik, tapi retry ganda = state flip-flop yang tidak diinginkan) | Low | Untuk toggle, pertimbangkan kirim state target eksplisit (`set_favorite: true/false`) alih-alih toggle buta, agar retry aman |

## 14. Error Response

| API | Masalah | Severity | Solusi |
|---|---|---|---|
| HTTP (`serve_stream`, dll.) vs WS (`handle_ws_message`) | Format error **tidak konsisten**: HTTP mengembalikan teks polos (`web.HTTPBadRequest(text="...")`) sedangkan WS mengembalikan JSON (`{"type":"error","data":"..."}"`) — tidak ada skema error terpadu (tanpa `code`, `timestamp`, atau struktur baku) di seluruh aplikasi | Medium | Buat skema error standar, mis. `{"error": {"code": "...", "message": "...", "details": {...}}}`, dipakai konsisten baik di response HTTP (JSON body) maupun payload WS |
| `handle_ws_message` catch-all (`except Exception as e: ... "data": str(e)`) | Mengirim **pesan exception mentah** ke client — berpotensi membocorkan detail internal (path file, nama variabel, struktur query) yang berguna bagi penyerang | Medium | Log detail lengkap di server (sudah dilakukan via `logger.error(..., exc_info=True)`), tapi kirim ke client pesan generik yang aman, mis. "Terjadi kesalahan internal, coba lagi" |
| `serve_stream` error (`return web.HTTPInternalServerError(text=f"Gagal mencari stream: {e}")`) | Sama seperti di atas — pesan exception (`{e}`) ikut dikirim ke response HTTP | Medium | Sanitasi pesan sebelum dikirim; simpan detail hanya di log server |

---

### Ringkasan Prioritas

- **High**: (1) `/api/stream/{video_id}` tanpa autentikasi/otorisasi, (2) endpoint yang sama tanpa rate limit, (3) proxy stream tanpa timeout ke upstream.
- **Medium**: mayoritas temuan lain — konsistensi error/caching/naming, validasi input WS, pagination hardcoded, tidak ada versioning API, token sesi di `localStorage`, rate limit in-memory (tidak scalable), idempotensi command WS.
- **Low**: penamaan route/action yang kurang seragam, cache header static assets, perbandingan token metrics tanpa `compare_digest`.

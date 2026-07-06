# Executive Summary — ytgui (bagas.fm)

**Ruang lingkup analisis:** source code murni (Python backend, JS/CSS frontend, tests, CI). Semua file `.md` diabaikan sesuai instruksi. Analisis berbasis 167 file non-md (~11.000 LOC Python+JS), termasuk direktori `.backup_patchlog/` yang menunjukkan histori patch aktif.

---

## 1. Kualitas Keseluruhan

**Overall Score: 74 / 100 — "Solid Beta, Belum Production-Grade Penuh"**

Codebase ini jauh di atas rata-rata proyek solo/hobi. Ada pemisahan layer yang jelas (`core/`, `engine/`, `server/`, `cache/`, `plugins/`, `services/`), praktik keamanan yang matang untuk skala proyeknya (PBKDF2 100k iterasi, rate limiting, SSRF guard, path traversal guard, constant-time comparison), dan test suite nyata (131 test function, CI aktif via GitHub Actions). Komentar patch bertag `TASK-1.1`, `PATCH-YTDLP-RESOLVE-TIMEOUT-01`, `PATCHLOG_APPLIED` menunjukkan proses audit-fix yang disiplin dan terlacak.

Namun proyek belum "production-grade" karena: frontend masih 25 file JS vanilla tanpa module system (global namespace via `window.*`), tidak ada bundler/build step, tidak ada type checking (no mypy/TS), backend menyimpan password default di file plaintext-adjacent (`admin_password.txt` walau isinya hash), dan arsitektur real-time (WebSocket + mpv IPC socket) rentan terhadap race condition khas single-process audio player yang sudah pernah jadi sumber bug (autoplay race, MPV reconnection).

---

## 2. Skor per Dimensi

| Dimensi | Skor | Alasan Singkat |
|---|---|---|
| **Release Readiness** | 62/100 | CI ada tapi hanya `pytest`, tidak ada lint/type-check gate, tidak ada staging/versioning/release pipeline, no Dockerfile ditemukan |
| **Technical Debt** | 68/100 | Debt sedang: direktori `.backup_patchlog/` & `scratch/` masih ikut ter-commit (harus di-gitignore/dibersihkan), banyak inline patch-comment yang seharusnya sudah di-refactor permanen |
| **Architecture** | 78/100 | Layering backend rapi (core/engine/server/cache terpisah jelas dengan `ports.py` untuk abstraksi), tapi frontend flat/global-namespace tanpa module boundary |
| **Security** | 82/100 | Sangat baik untuk ukuran solo project: PBKDF2, rate-limit login & command, SSRF allowlist domain googlevideo/youtube, path traversal check di `serve_stream`, `secrets.compare_digest` untuk timing-safe compare |
| **Performance** | 70/100 | Streaming via chunked proxy (16KB chunks) dan stream URL caching (TTL 6 jam) baik; tapi single mpv process + socket IPC adalah bottleneck skalabilitas, tidak ada async batching/pooling terlihat di db layer |
| **Maintainability** | 70/100 | Struktur direktori & naming konsisten, tapi ~17 file JS saling coupling lewat `window.*` global membuat perubahan berisiko regresi tak terduga |
| **Testability** | 65/100 | 131 test ada dan terorganisir rapi (unit/integration terpisah, ada `conftest.py` & fixtures) — bagus — tapi coverage tidak diukur otomatis (tidak ada coverage report/badge di CI), dan tidak ada test untuk frontend JS sama sekali |
| **Scalability** | 58/100 | Arsitektur single-process, single mpv-instance, socket lokal (`mpv-yt-player.sock`) → didesain untuk single-user/self-hosted, bukan multi-tenant; rate limit state disimpan in-memory (`manager.login_attempts`) sehingga tidak scale ke multi-instance/horizontal deployment |

---

## 3. Risk Matrix

| Risiko | Probabilitas | Dampak | Level | Area |
|---|---|---|---|---|
| Frontend global-namespace coupling menyebabkan regresi silent saat refactor | Tinggi | Sedang | 🟠 **Tinggi** | `web/static/js/*` |
| In-memory rate-limit/session state hilang saat restart / tidak scale multi-instance | Sedang | Sedang | 🟡 **Sedang** | `server/middleware.py`, `handlers/auth.py` |
| Direktori `.backup_patchlog/` & `scratch/` ikut ter-deploy/ter-commit (info leakage, bloat) | Tinggi | Rendah | 🟡 **Sedang** | root repo |
| mpv socket/process crash tanpa auto-restart penuh (dependency eksternal) | Sedang | Tinggi | 🟠 **Tinggi** | `engine/mpv_controller.py` |
| Tidak ada coverage measurement → blind spot pada bagian kritis yang tidak tertest | Sedang | Sedang | 🟡 **Sedang** | CI / tests |
| SSRF/path-traversal sudah dimitigasi dengan baik | Rendah | Tinggi | 🟢 **Rendah** | `server/handlers/http.py` |
| Default admin password auto-generate tersimpan sebagai hash di file lokal | Rendah | Sedang | 🟢 **Rendah** | `config.py` |
| Tidak ada lint/type-check gate di CI → bug style/tipe lolos ke main | Tinggi | Rendah | 🟡 **Sedang** | `.github/workflows/ci.yml` |

---

## 4. Prioritas Perbaikan (Urutan Rekomendasi)

**P0 — Segera**
1. Bersihkan `.backup_patchlog/` dan `scratch/` dari repo (pindah ke `.gitignore`, atau arsipkan di luar repo).
2. Tambahkan `pytest --cov` + coverage threshold di CI agar blind spot testing terlihat.

**P1 — Jangka Pendek**
3. Migrasi frontend ke ES modules (`type="module"`) untuk menghilangkan ketergantungan `window.*` global — akan sangat menekan risiko regresi di masa depan seiring 25 file JS bertambah.
4. Tambahkan health-check/auto-restart yang lebih robust untuk proses `mpv` (saat ini reconnection logic ada tapi belum ada circuit breaker/backoff yang terlihat eksplisit).
5. Tambahkan lint (ruff/flake8) & type-check (mypy) sebagai gate CI, bukan hanya test.

**P2 — Jangka Menengah**
6. Pindahkan rate-limit & session state in-memory ke storage eksternal (SQLite yang sudah dipakai, atau Redis) agar siap untuk skenario multi-instance/restart-resilient.
7. Tambahkan Dockerfile + versioning/release pipeline sederhana untuk mendukung "Release Readiness".
8. Tambahkan test untuk lapisan frontend JS (minimal untuk `store.js` dan `ws.js` sebagai state-critical modules).

**P3 — Nice to Have**
9. Dokumentasikan arsitektur `ports.py`/dependency-injection pattern agar konsisten dipakai di seluruh `engine/`.
10. Evaluasi apakah `services/discover_service.py` (satu-satunya file di luar `server/services/`) sebaiknya dipindah agar struktur folder konsisten.

---

*Catatan: skor bersifat estimasi kualitatif berdasarkan audit source code (bukan hasil static-analysis tool otomatis), difokuskan pada indikator konkret yang ditemukan di kode: pola keamanan, struktur folder, keberadaan test/CI, dan pola coupling.*

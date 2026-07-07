# LunaWave - Project Roadmap

Dokumen ini berisi gambaran besar prioritas pengembangan LunaWave pasca-audit, yang bertujuan untuk membawa project ini dari kondisi saat ini menjadi **Production-Ready**.

AI Agent wajib memperbarui status pada dokumen ini apabila seluruh task dalam sebuah Sprint telah diselesaikan.

---

## 🎯 Visi & Tujuan Utama
Mengubah LunaWave menjadi aplikasi *personal music streaming server* yang aman, memiliki performa stabil di kondisi *multi-user*, dan secara keseluruhan siap untuk rilis ke produksi dengan *zero critical blockers*.

---

## 🏃 Sprints / Prioritas Perbaikan

### ⛔ Sprint 0: TIER 0 — Blockers (Darurat)
**Status:** 🔴 TODO
**Fokus:** Masalah kritis yang memblokir build dan membahayakan sistem dasar.
- Fix `run.py` / Dockerfile crash (C-01).
- Tambahkan zero HTTP security headers (C-02).
- Invalidasi server-side session saat logout (C-03).
- Pindahkan `import time` di `mpv_controller.py` untuk cegah error runtime (C-04).
- Sinkronisasi versi `aiosqlite` di config (C-05).
- Pruning memori `_stream_rate_limit` untuk hindari memory leak (C-06).

### 🔴 Sprint 1: TIER 1 — High Priority
**Status:** 🔴 TODO
**Fokus:** Celah keamanan berbahaya, performa inti, dan standarisasi test.
- Amankan wildcard CORS pada endpoint stream (H-01).
- Hapus binary Windows node_modules dari repo dan sesuaikan `.gitignore` (H-03).
- Limit `MAX_VOLUME` menjadi aman untuk hardware (H-04).
- Hapus operasi side-effects dari saat meng-import `config.py` (H-05).
- Implementasikan Token Rotation setelah proses login baru (H-08).
- Tingkatkan batas minimum Test Coverage menjadi 60% dan pastikan `http_session` diinjeksi dengan benar (H-06, H-07).
- Perlindungan eksploitasi *X-Forwarded-For* spoofing (H-02).

### 🟡 Sprint 2: TIER 2 — Medium Priority
**Status:** 🔴 TODO
**Fokus:** Optimasi performa client, skalabilitas ringan, dan *technical debt* arsitektur.
- Batasi ConnectionManager maksimum WebSocket aktif.
- Optimasi PWA & UI: Stop fake beat `requestAnimationFrame` saat tab *hidden*, sesuaikan `syncBrowserAudio()` agar tidak dipanggil di setiap tick, tambah ukuran ikon manifest.
- Kurangi beban network: Ubah *Full State Broadcast* menjadi *Delta/Diff Broadcast*.
- Standarisasi *bilingual naming* (Indonesia/Inggris) di dalam _database schema_ dan Python code.
- Aktifkan aturan Mypy yang lebih ketat (`check_untyped_defs`).
- Generate Source Map untuk `bundle.js` frontend.
- Refactor `Database.__getattr__` proxy untuk interface yang lebih stabil.

### 🟢 Sprint 3+: TIER 3 — Tech Debt & Low Priority
**Status:** 🔴 TODO
**Fokus:** Daya tahan jangka panjang, persintensi data, dan dokumentasi lengkap.
- Simpan / *persist* `AppState` (minimal track, volume, antrean) ke SQLite saat server dimatikan.
- Buat state *Rate Limiting* persisten (tidak hilang saat restart).
- Buat standar bahasa log yang seragam di seluruh aplikasi.
- Update `.env.example`, buat `CHANGELOG.md` di root, perbaiki versi di config.
- Persiapkan *load tests* dan lengkapi instruksi _deployment_ Reverse Proxy / Nginx.

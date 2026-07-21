# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Charging-gate loudness batch analysis (`_is_charging_or_unknown()`,
  ditambahkan di rilis Background/Battery Survival di bawah) sekarang
  dipanggil lewat `run_in_executor`, bukan langsung di event loop —
  mencegah panggilan `termux-battery-status` yang lambat/hang membekukan
  seluruh server (WS, HTTP, broadcast progress) sampai 5 detik.

### Fixed — Background/Battery Survival (perf_background_battery_survival)
- Notifikasi now-playing di Android sekarang persistent (`--ongoing`,
  tidak bisa ter-swipe-dismiss selama track aktif) — mencegah Android
  membekukan proses server setelah notifikasi hilang.
- Wake-lock (`termux-wake-lock` PARTIAL) diakuisisi otomatis saat startup
  sebagai lapisan sekunder fail-safe; langkah manual HyperOS/MIUI
  (Autostart, battery saver "No restrictions", lock di recent-apps) tetap
  wajib sebagai lapisan primer — didokumentasikan di `docs/CONSTRAINTS.md`.
- Tiga loop `requestAnimationFrame` (progress bar, audio visualizer glow,
  radio moon phase) sekarang berhenti total saat tab/layar disembunyikan
  dan resume akurat saat kembali terlihat, mengurangi CPU/baterai
  terbuang di background.
- Reconnect WebSocket sekarang pakai exponential backoff (2s→4s→8s→16s→
  30s, cap) alih-alih retry flat 2 detik terus-menerus, dan langsung
  mencoba ulang begitu tab kembali terlihat.
- Proses ffmpeg (analisis loudness) dan worker thread yt-dlp sekarang
  dijalankan di prioritas CPU/IO lebih rendah; analisis loudness batch
  juga ditunda (charging-gate) saat perangkat tidak sedang di-charge.
- SQLite `PRAGMA synchronous=NORMAL` ditambahkan (kombinasi dengan WAL
  yang sudah ada) untuk mengurangi fsync per-commit.
- **Deferred:** broadcast progress adaptif per-visibility klien (PERF-5)
  sengaja BELUM dikerjakan — menyentuh `server/handlers/websocket.py`
  yang governed, butuh sign-off eksplisit terpisah.

### Added — Radio Toggle Redesign / "Night Dial" (Fitur C, selesai)
- Implementasi desain "Night Dial" untuk toggle radio.
- Menggunakan CSS pure-CSS starfield (`radio-hero.css`) dan animasi rAF terisolasi (`radio-hero-moon.js`) untuk fase bulan.
- Fallback otomatis ke mode statis (tanpa rAF) jika user mengaktifkan `prefers-reduced-motion`.
- Penghapusan 233 baris kode animasi lama (cleanup fitur lama).

### Changed — Redesain Login (Fitur B, selesai)
- Login admin dipindah dari password auto-generate
  (`cache/admin_password.txt`) ke akun yang dibuat sendiri lewat layar
  **Initial Setup** saat server pertama kali dijalankan. Kredensial
  sekarang disimpan di tabel `admin_account` (SQLite), bukan lagi file
  cache plaintext-hash.
- Launcher desktop tidak lagi punya mekanisme auth sendiri: tombol
  "Reset Password" sekarang hanya membuka antarmuka web di browser,
  mengarah ke Initial-Setup-ulang/Login yang sama dengan client biasa.
- Env var override (`LUNAWAVE_ADMIN_PASS` / `YTGUI_ADMIN_PASS`) tetap
  tersedia sebagai jalur non-default untuk provisioning non-interaktif
  (CI, automated deploy); tidak pernah menimpa akun yang sudah ada.

### ⚠️ Dampak Upgrade
- Kredensial admin lama TIDAK dimigrasikan otomatis. Instalasi existing
  akan diarahkan ke Initial Setup lagi saat upgrade — efeknya seperti
  logout paksa, admin wajib membuat akun baru sekali. Ini perilaku yang
  disengaja, bukan bug. Rasional lengkap & alternatif yang dipertimbangkan:
  [ADR-0008](docs/adr/0008-admin-credentials-in-sqlite.md).

## [1.0.0] - 2026-07-14
### Added
- Initial stable baseline version.
- Rebranding from YTGUI to LunaWave with backward-compatible shim.
- Comprehensive test suite (393 tests passing).
- Clean hexagonal architecture (ports/adapters), CommandBus/EventBus, and plugin system.
- `CHANGELOG.md`, `CONTRIBUTING.md`, and `SECURITY.md`.

### Fixed
- All outstanding sprint items that were critical for stable baseline.

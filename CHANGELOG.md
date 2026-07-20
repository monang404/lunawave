# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
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

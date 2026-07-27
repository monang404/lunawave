# Security Policy

## Supported Versions

Currently, we only support the latest stable version of LunaWave.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within LunaWave, please send an e-mail to the maintainers or open an issue (if it is not sensitive).

We will strive to address all security vulnerabilities promptly.

## Proteksi Akses Observabilitas

LunaWave tidak mengekspos data operasional atau log aplikasi ke jaringan publik secara default. Endpoint observabilitas, yang mencakup `/metrics`, `/admin/logs`, `/api/logs/tail`, dan `/api/logs/stats`, dilindungi secara terpusat:
- Hanya dapat diakses langsung dari **localhost** (`127.0.0.1` atau `::1`).
- Akses dari luar localhost (jaringan) mewajibkan penyertaan header `X-Metrics-Token` yang valid (dicocokkan dengan `LUNAWAVE_METRICS_TOKEN` menggunakan `secrets.compare_digest`).

Hal ini memastikan tidak ada data jejak, aktivitas sesi, atau konfigurasi (kredensial sama sekali tidak dicatat di log) yang bocor melalui dashboard log.

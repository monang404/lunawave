# Disaster Recovery Plan

## Recovery Point Objective (RPO)
Sistem memiliki siklus backup otomatis setiap 24 jam dengan rotasi 7 hari. RPO maksimal adalah **24 Jam**.

## Langkah Pemulihan Database (Database Corruption)
1. Matikan container: `docker compose down`
2. Pindahkan database yang rusak: `mv data/lunawave.db data/lunawave.db.corrupted`
3. Salin file backup terbaru: `cp data/lunawave.db.<timestamp>.bak data/lunawave.db`
4. Nyalakan kembali container: `docker compose up -d`
5. Verifikasi log: `docker compose logs -f`

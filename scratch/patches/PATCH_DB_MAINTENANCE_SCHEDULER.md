# PATCH_DB_MAINTENANCE_SCHEDULER.md

**ID:** `PATCH-2026-07-11-011`
**Tanggal:** 2026-07-11
**Prioritas:** SEDANG-TINGGI (dampak kumulatif)
**File Terdampak:**
- `main.py`

## Ringkasan
`cache/db.py` sudah punya `evict_stale_tracks()` dan `cleanup_sessions()` yang
fungsional dan benar, tapi tidak ada satupun pemanggil di seluruh codebase
(dikonfirmasi via grep). Tabel `sessions` dan `tracks` di SQLite tidak pernah
dibersihkan otomatis — hanya `sessions` yang tidak sengaja terhapus kalau ada
yang login pakai token yang sudah expired persis (jarang).

## Root Cause
Tidak ada periodic background task untuk maintenance DB — pola ini sudah ada
di `main.py` untuk keperluan lain (`check_connectivity`, `mpv_reconnect_checker`)
tapi tidak dibuat untuk DB.

## Rencana Fix
Tambahkan satu periodic task baru di `main.py`, mengikuti pola task lain yang
sudah ada (`safe_create_task` + loop `while True: await asyncio.sleep(...)`),
dijalankan setiap 6 jam.

## Diff yang Direncanakan
```python
# main.py — tambahkan dekat definisi check_connectivity()

async def db_maintenance():
    while True:
        await asyncio.sleep(6 * 3600)  # setiap 6 jam
        try:
            evicted = await db.evict_stale_tracks()
            await db.cleanup_sessions()
            if evicted:
                structlog.get_logger(__name__).info(
                    f"DB maintenance: {evicted} track stale dihapus."
                )
        except Exception as e:
            structlog.get_logger(__name__).warning(f"DB maintenance gagal: {e}")

# di dekat connectivity_task:
tasks.append(safe_create_task(db_maintenance(), name="db_maintenance"))
```

## Dampak
- Mencegah pertumbuhan tak terbatas tabel `sessions` (setiap login sukses
  membuat 1 baris baru, TTL 24 jam, tidak pernah dihapus otomatis) dan `tracks`
  (metadata cache yang sudah tidak relevan >30 hari & tidak pernah diputar).
- Dampak per-run kecil, tapi kumulatif signifikan untuk instance yang jalan
  lama (bertahun-tahun, sesuai use-case app lokal/self-hosted ini).

## Risiko Regresi
- Sangat rendah — kedua fungsi sudah ada dan sudah punya query yang aman
  (WHERE play_count=0 AND bukan favorit AND bukan file lokal untuk eviction).
- Perlu pastikan `db.evict_stale_tracks()` tidak terpanggil sebelum `db.init()`
  selesai (aman karena task ini dibuat setelah `await db.init()` di alur `main()`).

**Status:** 📝 RENCANA — belum diterapkan ke source, menunggu instruksi apply.

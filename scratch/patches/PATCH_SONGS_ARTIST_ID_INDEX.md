# PATCH_SONGS_ARTIST_ID_INDEX.md

**ID:** `PATCH-2026-07-11-015`
**Tanggal:** 2026-07-11
**Prioritas:** MINOR — opsional (pencegahan)
**File Terdampak:**
- `cache/schema.sql`
- `cache/db.py` (`init()` — tambahkan migrasi `CREATE INDEX IF NOT EXISTS`
  seperti pola migrasi kolom yang sudah ada, karena DB production sudah ada
  dan `schema.sql` cuma jalan lewat `executescript` yang aman untuk `IF NOT EXISTS`)

## Ringkasan
Tabel `songs` tidak punya index untuk `artist_id`, yang dipakai di JOIN pada
`get_random_songs()`, `get_artist_songs_strict()`, `get_genre_songs()`.
`EXPLAIN QUERY PLAN` dikonfirmasi menunjukkan `SCAN s` (full table scan) untuk
JOIN ini.

## Catatan Kejujuran Soal Dampak
Dicek langsung ke `data/lunawave.db` aktual: tabel `songs` cuma 963 baris,
`artists` 100 baris. Full scan di ukuran ini masih di bawah 1 milidetik —
**tidak signifikan untuk kondisi data saat ini**. Query juga tetap butuh
`ORDER BY RANDOM()` yang secara inheren perlu full-scan-like behavior
(index tidak menghilangkan kebutuhan itu, cuma mempercepat bagian JOIN-nya).
Ditandai MINOR murni sebagai pencegahan kalau tabel `songs` bertambah
signifikan di masa depan (misalnya import artis baru dalam jumlah besar).

## Rencana Fix
```sql
-- cache/schema.sql, tambahkan setelah index songs yang sudah ada:
CREATE INDEX IF NOT EXISTS idx_songs_artist_id ON songs(artist_id);
```
```python
# cache/db.py, init() — tambahkan migrasi idempotent seperti pola yang sudah ada
# untuk is_favorite/click_count (karena DB lama sudah exist di disk sebelum
# schema.sql ini diupdate, executescript CREATE INDEX IF NOT EXISTS di
# schema.sql saja sudah cukup karena dijalankan tiap init() — TIDAK perlu
# migrasi terpisah seperti ALTER TABLE, cukup pastikan baris index baru
# di schema.sql).
```

## Dampak
Marjinal saat ini, jadi investasi murah untuk masa depan.

## Risiko Regresi
Sangat rendah — index tambahan murni additive, tidak mengubah query/behavior.

**Status:** 📝 RENCANA — belum diterapkan ke source, menunggu instruksi apply.

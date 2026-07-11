# PATCH_DISCOVER_PARALLEL_QUERIES.md

**ID:** `PATCH-2026-07-11-014`
**Tanggal:** 2026-07-11
**Prioritas:** MINOR — opsional
**File Terdampak:**
- `server/handlers/websocket.py` ⚠️ **FILE RESTRICTED** (lihat `AI_CONTEXT.md`) —
  butuh izin eksplisit, sudah diberikan user pada 2026-07-11 (pilihan "Semua 1-6"
  setelah saya tandai file ini restricted di laporan awal).
- `server/handlers/event_listeners.py`

## Ringkasan
3 lokasi melakukan beberapa query DB independen secara sequential (`await` satu
per satu) padahal query-nya tidak saling bergantung: action `discover` dan
`delete_download` di `websocket.py`, serta `_on_download_complete` di
`event_listeners.py`.

## Catatan Kejujuran Soal Dampak
`cache/db.py` memakai **satu koneksi aiosqlite** (satu worker thread). Jadi
walau di-`asyncio.gather()`, eksekusi query di level DB tetap serial di thread
itu — potensi penghematan cuma overhead scheduling event-loop antar-`await`
(sub-milidetik per query), BUKAN penghematan waktu eksekusi DB yang nyata.
Saya tetap sertakan patch ini karena low-risk dan tidak ada downside, tapi
secara jujur ini **tidak lolos kriteria "dampak terukur signifikan"** secara
ketat — ditandai MINOR sesuai kriteria di template.

## Rencana Fix
Bungkus query independen dengan `asyncio.gather()`.

## Diff yang Direncanakan

### `server/handlers/websocket.py` — action `discover`
```python
# SEBELUM:
        elif action == "discover":
            ds = DiscoverService(db)
            recent = await ds.get_recent(15)
            favorites = await ds.get_favorites(15)
            cached = await ds.get_cached(15)
            featured_artists = await ds.get_featured_artists(100)
            featured_genres = await ds.get_featured_genres(100)

# SESUDAH:
        elif action == "discover":
            ds = DiscoverService(db)
            recent, favorites, cached, featured_artists, featured_genres = await asyncio.gather(
                ds.get_recent(15),
                ds.get_favorites(15),
                ds.get_cached(15),
                ds.get_featured_artists(100),
                ds.get_featured_genres(100),
            )
```
(perlu tambah `import asyncio` di atas file jika belum ada — cek dulu.)

### `server/handlers/websocket.py` — action `delete_download` (bagian update discover)
```python
# SEBELUM:
                    ds = DiscoverService(db)
                    recent = await ds.get_recent(15)
                    cached = await ds.get_cached(15)
                    featured_artists = await ds.get_featured_artists(100)
                    featured_genres = await ds.get_featured_genres(100)

# SESUDAH:
                    ds = DiscoverService(db)
                    recent, cached, featured_artists, featured_genres = await asyncio.gather(
                        ds.get_recent(15),
                        ds.get_cached(15),
                        ds.get_featured_artists(100),
                        ds.get_featured_genres(100),
                    )
```

### `server/handlers/event_listeners.py` — `_on_download_complete`
```python
# SEBELUM:
            ds = DiscoverService(playback_controller.resolver.db)
            recent = await ds.get_recent(15)
            cached = await ds.get_cached(15)
            featured_artists = await ds.get_featured_artists(100)
            featured_genres = await ds.get_featured_genres(100)

# SESUDAH:
            ds = DiscoverService(playback_controller.resolver.db)
            recent, cached, featured_artists, featured_genres = await asyncio.gather(
                ds.get_recent(15),
                ds.get_cached(15),
                ds.get_featured_artists(100),
                ds.get_featured_genres(100),
            )
```
(`import asyncio` — cek, kemungkinan sudah ada karena `asyncio.iscoroutinefunction`
tidak dipakai di file ini, perlu ditambah kalau belum ada.)

## Dampak
Rendah/marjinal (lihat catatan kejujuran di atas) — sub-milidetik per aksi.

## Risiko Regresi
- Sangat rendah — query-query ini benar-benar independen (read-only, tabel
  berbeda/tidak saling bergantung), urutan hasil tidak berubah karena pakai
  unpacking tuple sesuai urutan `gather()`.

**Status:** 📝 RENCANA — belum diterapkan ke source, menunggu instruksi apply.

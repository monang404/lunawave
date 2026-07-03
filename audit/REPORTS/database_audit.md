# Audit Database — ytgui

**Sumber tunggal (single source of truth):** `cache/schema.sql`, dieksekusi oleh `cache/db.py` saat runtime.
**Diabaikan sesuai instruksi:** semua file `.backup*` dan `*.md`.

---

## 1. Schema

Ada 6 tabel dalam 2 domain terpisah yang tidak saling terhubung:

- **Cache domain**: `tracks`, `sessions` — data operasional (metadata lagu yang pernah diputar, cache stream URL, sesi login).
- **Catalog domain**: `artists`, `genres`, `artist_genres`, `songs` — data seed untuk Radio Mode.

`tracks.artist` hanya kolom TEXT bebas, **tidak** ber-foreign-key ke `artists.id`. Ini desain yang sah (cache tidak boleh bergantung ke katalog), tapi konsekuensinya tidak ada cara query "semua track yang pernah diputar dari artist X di katalog" tanpa string matching.

### Migration dilakukan lewat kode, bukan file schema bernomor
Empat kolom/index (`tracks.is_favorite`, `artists.click_count`, `genres.click_count`, `idx_songs_artist_id`) ditambahkan lewat blok `try/except: pass` di `Database.init()` (`cache/db.py`), bukan lewat migration file bernomor/tervensi. Setiap exception ditelan diam-diam — kalau `ALTER TABLE` gagal karena alasan lain (disk penuh, file corrupt, lock), kegagalan itu tidak akan pernah terlihat di log.

### Schema drift — 3 sumber definisi berbeda untuk tabel yang sama

| File | Status | Masalah |
|---|---|---|
| `cache/schema.sql` | Aktif (dipakai app) | Source of truth |
| `data/export_to_sqlite.py` | Aktif, tapi jalur terpisah | `DROP TABLE` lalu recreate tanpa kolom `click_count`, tanpa `PRAGMA journal_mode=WAL` / `foreign_keys` |
| `data/archive/import_artists.py` | Arsip, tapi masih direferensikan dari kode aktif | Skema `artist_genres` berbeda total (`genre TEXT` bukan `genre_id` FK ke tabel `genres`), ada tabel `artist_seeds` yang tidak eksis di `schema.sql` |

`engine/radio_engine.py` (baris ~92) masih mengarahkan user ke `python data/import_artists.py` saat tabel `artists` kosong — path itu sudah pindah ke `data/archive/`, dan skemanya sudah tidak sinkron dengan yang dipakai aplikasi saat ini.

---

## 2. Index

- `idx_local_path`, `idx_play_count` — partial index, sudah tepat sesuai pola query (`WHERE local_path IS NOT NULL`, `WHERE play_count > 0`).
- `idx_songs_youtube_id` **redundan**. Kolom `songs.youtube_id` sudah dideklarasikan `UNIQUE NOT NULL`, dan SQLite otomatis membuat unique index untuk itu. Index eksplisit ini adalah duplikat — menambah beban write dan storage tanpa manfaat query.
- Tidak ada index berdiri sendiri untuk `artist_genres.genre_id`. Yang ada hanya composite primary key `(artist_id, genre_id)`, yang leading column-nya `artist_id`. Query arah sebaliknya (dari genre → cari semua artist) tidak bisa memakai index itu secara efisien; index terpisah pada `genre_id` akan membantu.

---

## 3. Foreign Key

**Temuan kritis:** `cache/db.py` **tidak pernah** menjalankan `PRAGMA foreign_keys=ON`. Hanya script arsip (`data/archive/import_artists.py`) yang melakukannya, dan script itu tidak dipakai oleh aplikasi yang berjalan.

Di SQLite, FK enforcement **default OFF per koneksi**. Artinya seluruh `ON DELETE CASCADE` yang dideklarasikan di `artist_genres` dan `songs` **tidak pernah benar-benar aktif** pada koneksi produksi. Kalau suatu saat ditambahkan fitur hapus artist, baris terkait di `songs` dan `artist_genres` akan tertinggal sebagai data yatim (orphan), bukan ter-cascade otomatis seperti yang diasumsikan oleh skema.

Saat ini risiko belum termanifestasi karena tidak ada statement `DELETE FROM artists/songs/genres` di kode aktif — tapi ini adalah bom waktu begitu fitur manajemen katalog ditambahkan.

---

## 4. Constraint

- `artists.nama` **tidak UNIQUE**. Namun `Database.increment_artist_click()` melakukan:
  ```sql
  UPDATE artists SET click_count = COALESCE(click_count, 0) + 1 WHERE nama = ?
  ```
  Kalau ada dua artist dengan nama sama, klik akan menambah `click_count` ke **keduanya sekaligus** — bug integritas data yang laten selama nama tidak dijamin unik.
- `genres.nama_genre` sudah UNIQUE — pola query yang sama (`increment_genre_click`) aman untuk kasus ini.
- Tidak ada `CHECK` constraint pada `artists.kategori` di skema aktif — padahal versi arsip (`import_artists.py`) memilikinya (`CHECK(kategori IN ('individu','band'))`). Validasi ini hilang saat migrasi ke `schema.sql`, sehingga nilai `kategori` sekarang bisa diisi string apa saja.

---

## 5. Normalization / Denormalization

- Tabel `tracks` sengaja **didenormalisasi** — title/artist disimpan sebagai snapshot (bukan referensi ke tabel lain). Ini tepat untuk cache layer yang harus tetap valid meski data sumber di YouTube berubah/dihapus.
- `artist_genres` sebagai tabel pivot many-to-many sudah mengikuti 3NF dengan benar.
- Tidak ditemukan masalah normalisasi signifikan lain di skema aktif.

---

## 6. Query & Bottleneck

Pola paling berisiko performanya: **`ORDER BY RANDOM() LIMIT n`**, dipakai di:
- `get_random_songs`
- `get_genre_songs`
- `get_artist_songs_strict`
- `get_genre_artists`
- `get_featured_artists` / `get_featured_genres` (lewat subquery `WHERE id IN (SELECT id ... ORDER BY RANDOM() LIMIT n)`)

Ini adalah anti-pattern klasik SQLite: `ORDER BY RANDOM()` selalu memicu **full table scan + full sort**, tidak bisa memanfaatkan index apa pun, dengan biaya O(n log n) di setiap pemanggilan — bukan O(log n). Untuk ukuran katalog saat ini (ratusan–ribuan baris) masih terasa cepat, tapi setiap kali `RadioEngine` meminta batch lagu baru (yang terjadi berulang kali sepanjang sesi radio), query ini melakukan scan ulang seluruh tabel dari nol. Ini adalah **bottleneck skalabilitas utama** yang akan makin terasa begitu tabel `songs`/`artists` tumbuh besar.

Query berbasis CTE + window function (`ROW_NUMBER() OVER (PARTITION BY artist_id ORDER BY RANDOM())` di `get_random_songs` dan `get_genre_songs`) bahkan lebih berat: seluruh hasil JOIN dimaterialisasi dan diberi ranking dulu sebelum akhirnya di-`LIMIT`.

### Race condition di jalur write
Di `server/handlers/event_listeners.py` (`_on_download_complete`):
```python
safe_create_task(playback_controller.resolver.db.upsert_track(event.track, local_path=...), name="upsert_dl_track")
# langsung disusul tanpa menunggu task di atas selesai:
recent = await ds.get_recent(15)
favorites = await ds.get_favorites(15)
cached = await ds.get_cached(15)
```
`upsert_track()` dijalankan lewat `safe_create_task` — **fire-and-forget**, tidak di-`await`. Baris berikutnya langsung membaca ulang tabel `tracks` yang sama untuk membangun payload `discover_data` yang di-broadcast ke semua client. Karena urutan commit `upsert_track` tidak dijamin selesai lebih dulu, hasil broadcast **berpotensi tidak menyertakan track yang baru saja selesai di-download** — stale read akibat race antara write asinkron dan read sinkron setelahnya.

---

## 7. Cascade

Sudah dibahas di bagian Foreign Key: cascade dideklarasikan di skema (`ON DELETE CASCADE` pada `artist_genres.artist_id`, `artist_genres.genre_id`, `songs.artist_id`) tapi **tidak pernah aktif** secara efektif karena `PRAGMA foreign_keys=ON` tidak pernah dijalankan pada koneksi produksi.

---

## 8. Consistency

- Single persistent connection (`aiosqlite`) + WAL mode adalah pilihan yang tepat untuk SQLite di aplikasi single-proses — mengurangi overhead open/close per query (dicatat sendiri di komentar kode sebagai fix "CRITICAL-04").
- `scratch/check_db.py` membuka **koneksi kedua** (`sqlite3` sinkron, terpisah dari `aiosqlite`) ke file database yang sama saat koneksi utama masih terbuka. Ini hanya script debug di folder `scratch/`, tapi kalau pernah dijalankan bersamaan dengan aplikasi yang hidup, berpotensi menimbulkan lock contention pada WAL — sebaiknya tidak pernah dijalankan di environment produksi.
- `toggle_favorite()` melakukan SELECT-cek-lalu-UPDATE dalam **dua statement terpisah** (bukan satu operasi atomic). Komentar di kode sendiri sudah mengakui ini: *"Hanya operasi UPDATE yang atomic — tidak untuk keseluruhan blok SELECT+UPDATE ini."* Race antara dua request toggle yang bersamaan bisa menghasilkan state akhir yang tidak terduga, meski dampaknya kecil untuk fitur favorite.

---

## Ringkasan Prioritas

| Prioritas | Temuan | Lokasi |
|---|---|---|
| Tinggi | `PRAGMA foreign_keys=ON` tidak pernah di-set → seluruh CASCADE tidak aktif | `cache/db.py` |
| Tinggi | Race condition write-then-read (fire-and-forget upsert lalu langsung baca ulang) | `server/handlers/event_listeners.py` |
| Sedang | Schema drift antar 3 file berbeda (schema.sql vs export_to_sqlite.py vs archive/import_artists.py) | `cache/schema.sql`, `data/export_to_sqlite.py`, `data/archive/import_artists.py` |
| Sedang | `ORDER BY RANDOM()` full-scan berulang di jalur Radio Mode — bottleneck skalabilitas | `cache/db.py` (get_random_songs, get_genre_songs, dll) |
| Sedang | `artists.nama` tanpa UNIQUE tapi dipakai sebagai key update pada `increment_artist_click` | `cache/schema.sql`, `cache/db.py` |
| Sedang | `CHECK` constraint pada `kategori` hilang dibanding versi arsip | `cache/schema.sql` |
| Rendah | Index `idx_songs_youtube_id` redundan (kolom sudah UNIQUE) | `cache/schema.sql` |
| Rendah | Migration lewat try/except silent-swallow, bukan migration bernomor/tervensi | `cache/db.py` |
| Rendah | Script debug (`scratch/check_db.py`) membuka koneksi sqlite kedua ke file yang sama | `scratch/check_db.py` |

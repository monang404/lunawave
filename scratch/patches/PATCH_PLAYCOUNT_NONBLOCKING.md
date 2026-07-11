# PATCH_PLAYCOUNT_NONBLOCKING.md

**ID:** `PATCH-2026-07-11-012`
**Tanggal:** 2026-07-11
**Prioritas:** SEDANG
**File Terdampak:**
- `engine/playback/track_loader.py`

## Ringkasan
`load_track()` melakukan `await self.resolver.db.increment_play_count(...)`
(sebuah UPDATE + COMMIT SQLite) di jalur kritis SEBELUM mengembalikan URI ke
`play_track()`, padahal dua side-effect lain di baris sebelahnya (sponsorblock,
lyrics) sudah benar memakai `safe_create_task` (fire-and-forget).

## Root Cause
Inkonsistensi pola: satu DB write di-`await` langsung, dua lainnya tidak,
padahal ketiganya sama-sama tidak perlu selesai sebelum audio mulai diputar.

## Rencana Fix
Ganti `await` menjadi `safe_create_task`, konsisten dengan pola sponsorblock/lyrics
di baris tepat di bawahnya.

## Diff yang Direncanakan
```python
# engine/playback/track_loader.py, method load_track()

# SEBELUM:
        uri = await self.resolver.resolve(track)

        # C-02: Increment play count for favorites
        await self.resolver.db.increment_play_count(track.video_id)

        safe_create_task(self.sponsorblock.fetch_segments(track.video_id), ...)
        safe_create_task(self.lyrics_fetcher.fetch(track), ...)

# SESUDAH:
        uri = await self.resolver.resolve(track)

        # C-02: Increment play count for favorites — non-blocking,
        # konsisten dengan sponsorblock/lyrics di bawah ini.
        safe_create_task(
            self.resolver.db.increment_play_count(track.video_id),
            name=f"incr_play_count_{track.video_id}"
        )

        safe_create_task(self.sponsorblock.fetch_segments(track.video_id), ...)
        safe_create_task(self.lyrics_fetcher.fetch(track), ...)
```

## Dampak
- Menghilangkan 1 round-trip DB write (commit SQLite) dari jalur kritis start
  playback — jalur ini dipakai di SETIAP kali user menekan play/next/prev,
  jadi walau per-panggilan kecil, ini yang paling sering dieksekusi di seluruh app.

## Risiko Regresi
- Rendah. `increment_play_count` idempotent secara efek (nambah counter),
  tidak ada kode lain yang butuh nilai baliknya secara sinkron.
- `safe_create_task` sudah menangani exception secara terpusat (tidak silent-crash)
  sesuai `core/task_utils.py`.
- Satu skenario tepi: kalau app di-kill tepat setelah `mpv.play()` tapi sebelum
  task background ini sempat commit, play_count untuk track itu bisa tidak
  ter-increment untuk 1 kali putar. Ini dianggap dapat diterima (sama seperti
  risiko yang sudah diterima untuk sponsorblock/lyrics fetch yang juga
  fire-and-forget).

**Status:** 📝 RENCANA — belum diterapkan ke source, menunggu instruksi apply.

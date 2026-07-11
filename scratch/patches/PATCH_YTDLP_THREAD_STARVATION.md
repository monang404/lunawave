# PATCH_YTDLP_THREAD_STARVATION.md

**ID:** `PATCH-2026-07-11-010`
**Tanggal:** 2026-07-11
**Prioritas:** TINGGI
**File Terdampak:**
- `engine/ytdlp_client.py`

## Ringkasan
`get_stream_url()` membungkus `run_in_executor()` dengan `asyncio.wait_for(timeout=25)`,
tapi `wait_for` cuma membatalkan sisi *awaiter*-nya di event loop — thread yang
sudah terlanjur jalan di `ThreadPoolExecutor(max_workers=4)` TIDAK ikut berhenti,
karena Python tidak bisa interrupt thread biasa. yt-dlp sendiri tidak diberi
`socket_timeout`, jadi kalau network lambat/flaky (skenario umum di Termux/mobile),
thread itu bisa terus jalan (dengan retry internal yt-dlp) jauh lebih lama dari 25 detik.

Karena pool cuma 4 worker dan dipakai bersama oleh `search()`, `get_stream_url()`,
dan `download_mp3()`, beberapa timeout beruntun bisa menghabiskan semua worker
dengan thread "zombie" — request play/search/download baru akan antre tanpa
kepastian durasi, meski UI sudah menampilkan error "gagal ambil stream" di detik ke-25.

## Root Cause
1. Tidak ada `socket_timeout` / `retries` yang dibatasi di `_YDL_OPTS_INFO`, jadi
   yt-dlp bisa retry lama di level network-nya sendiri.
2. `asyncio.wait_for()` tidak benar-benar membatalkan pekerjaan sinkron yang
   sudah berjalan di thread executor — hanya melepas si pemanggil dari menunggu.

## Rencana Fix
1. Tambahkan `"socket_timeout": 10` dan `"extractor_retries": 1` ke `_YDL_OPTS_INFO`
   supaya yt-dlp sendiri menyerah cepat di level thread, bukan cuma di level
   `wait_for` Python.
2. (Opsional, kalau mau lebih aman) Naikkan `max_workers` executor dari 4 → 6,
   atau pisahkan executor khusus untuk `get_stream_url` (paling sering timeout)
   dari executor `search`/`download`, supaya satu jenis operasi yang macet tidak
   memblokir jenis operasi lain.

## Diff yang Direncanakan
```python
# engine/ytdlp_client.py
_YDL_OPTS_INFO = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "format_sort": ["abr", "asr"],
    "socket_timeout": 10,        # BARU: paksa yt-dlp menyerah di level network
    "extractor_retries": 1,      # BARU: batasi retry internal yt-dlp
}
```

## Dampak
- Thread di executor akan menyerah dalam ~10-20 detik alih-alih berpotensi
  menggantung sangat lama, sehingga pool 4 worker tidak habis terpakai oleh
  thread zombie saat network buruk.
- Mengurangi risiko app freeze total untuk fitur cari/putar lagu setelah periode
  jaringan buruk (paling relevan untuk platform utama: Termux/mobile).

## Risiko Regresi
- `socket_timeout: 10` lebih pendek dari default yt-dlp — di jaringan yang memang
  lambat tapi masih jalan (bukan mati total), permintaan yang tadinya berhasil
  (walau lambat) bisa jadi gagal lebih cepat. Trade-off ini disengaja: gagal cepat
  lebih baik daripada menghabiskan worker pool.
- Perlu tes di kondisi jaringan lambat riil (throttle network) untuk pastikan
  10 detik tidak terlalu agresif untuk kasus normal Termux.

**Status:** 📝 RENCANA — belum diterapkan ke source, menunggu instruksi apply.

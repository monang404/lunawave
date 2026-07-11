# PATCH_STATE_LYRICS_DEDUP.md

**ID:** `PATCH-2026-07-11-013`
**Tanggal:** 2026-07-11
**Prioritas:** SEDANG
**File Terdampak:**
- `server/serializers.py`

**Verifikasi frontend (SUDAH DICEK):** `web/static/js/ws.js` case `"state"`
memakai `Object.assign(store, msg.data)` — field yang tidak ada di `msg.data`
otomatis tidak disentuh. Field `lyrics_lines`/`lyrics_timestamps` hanya pernah
di-assign di case `"lyrics"` (baris 165-166). Jadi menghapus field ini dari
`state_to_dict()` **aman**, tidak ada frontend logic yang bergantung padanya
lewat message `state`.

## Ringkasan
`state_to_dict()` menyertakan `lyrics_lines`, `lyrics_timestamps`, `lyrics_index`,
`lyrics_offset` — padahal `BroadcastService.broadcast_lyrics()` sudah mengirim
data yang sama persis lewat message `type: "lyrics"` terpisah. Karena
`broadcast_state()` dipanggil jauh lebih sering (track start, queue update,
download complete, discover update) dibanding kebutuhan lirik berubah, array
lirik penuh ikut terkirim ulang berkali-kali ke semua klien yang terhubung.

## Root Cause
Duplikasi data antara dua message type (`state` dan `lyrics`) yang seharusnya
saling melengkapi, bukan tumpang tindih.

## Rencana Fix
Hapus 4 field lirik dari `state_to_dict()`. Field `lyrics_index` dan
`lyrics_offset` sebenarnya ringan (angka tunggal) — opsi aman: **hanya hapus
`lyrics_lines` dan `lyrics_timestamps`** (yang berukuran besar/array), biarkan
`lyrics_index`/`lyrics_offset` tetap ada di state kalau frontend memang perlu
akses cepat tanpa nunggu message lyrics terpisah.

## Diff yang Direncanakan
```python
# server/serializers.py, state_to_dict()

# SEBELUM:
        "lyrics_lines": list(state.lyrics_lines),
        "lyrics_timestamps": list(state.lyrics_timestamps),
        "lyrics_index": state.lyrics_index,
        "lyrics_offset": state.lyrics_offset,

# SESUDAH (hapus array besar, simpan index/offset yang ringan):
        "lyrics_index": state.lyrics_index,
        "lyrics_offset": state.lyrics_offset,
```

## Dampak
- Mengurangi ukuran payload `broadcast_state()` secara signifikan untuk lagu
  dengan lirik LRC panjang (bisa beberapa KB per broadcast), pada jalur yang
  sering terpanggil (setiap ganti track, queue update, dll) dan dikirim ke
  SEMUA klien terkoneksi — relevan untuk device Termux/mobile dengan bandwidth
  terbatas.

## Risiko Regresi
- Rendah — sudah diverifikasi ke frontend (lihat di atas). Satu-satunya
  skenario tepi: kalau di masa depan ada state snapshot awal (pertama connect)
  yang mengandalkan `state` message untuk lirik SEBELUM `lyrics` message
  pertama datang, akan ada jeda singkat lirik kosong sampai `lyrics` message
  menyusul. Cek alur `ws_handler()` di `websocket.py`: saat baru connect,
  hanya `state` yang dikirim (bukan `lyrics`) — jadi ada risiko lirik lagu yang
  sedang diputar tidak langsung muncul saat klien baru connect/refresh sampai
  event lirik berikutnya trigger. Mitigasi: kirim juga message `lyrics` terpisah
  tepat setelah `state` awal di `ws_handler()` (perubahan kecil tambahan,
  di luar scope minimal tapi disarankan bareng patch ini).

**Status:** 📝 RENCANA — belum diterapkan ke source, menunggu instruksi apply.

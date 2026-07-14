# PATCH_BATTERY_DRAIN.md

Baca `AI_CONTEXT.md` dulu. Task: kurangi CPU usage dan boros baterai saat musik putar.

---

## ROOT CAUSE SUMMARY

Satu hot path aktif terus-menerus selama musik berjalan:

```
mpv socket → TrackProgressEvent (2–4×/detik)
    → 4 subscriber dipanggil bersamaan via asyncio.gather
    → 4 asyncio.Task baru di-spawn setiap kali
    → Prometheus counter increment setiap kali
    → Beberapa subscriber trigger broadcast WS lagi
```

Total: **8–16 asyncio Task baru per detik** hanya untuk progress tracking. Di Termux (single-core-equivalent workload), ini dominasi event loop dan penyebab utama panas + drain baterai.

Fix dibagi jadi 4 file, urutan pengerjaan dari paling impactful.

---

## TASK 1 — `engine/mpv_controller.py`: Throttle publish di sumber

Ini fix paling impactful. Sekarang setiap `time-pos` event dari mpv langsung di-publish tanpa throttle. mpv default mengirim `time-pos` update ~2–4 Hz (bisa lebih). Semua 4 subscriber dijalankan untuk setiap update.

Lyrics sync dan sponsorblock check tidak butuh sub-second precision — 1 Hz (1× per detik) sudah cukup akurat untuk keduanya.

**Tambahkan instance variable `_last_progress_ts` di `__init__`:**

Cari:
```python
        self.socket_path = socket_path or MPV_SOCKET
        self.tcp_port = tcp_port or os.environ.get("YT_PLAYER_MPV_PORT", "12345")
```

Ganti dengan:
```python
        self.socket_path = socket_path or MPV_SOCKET
        self.tcp_port = tcp_port or os.environ.get("YT_PLAYER_MPV_PORT", "12345")
        self._last_progress_ts: float = 0.0  # throttle TrackProgressEvent publish
```

**Throttle publish di `_handle_event`:**

Cari:
```python
            if name == "time-pos" and isinstance(data, (int, float)):
                await self._bus.publish(TrackProgressEvent(position=float(data)))
```

Ganti dengan:
```python
            if name == "time-pos" and isinstance(data, (int, float)):
                import time as _time
                _now = _time.monotonic()
                # Throttle: publish maksimal 1× per detik untuk hemat CPU/baterai.
                # Lyrics sync dan sponsorblock tidak butuh resolusi lebih tinggi dari ini.
                if _now - self._last_progress_ts >= 1.0:
                    self._last_progress_ts = _now
                    await self._bus.publish(TrackProgressEvent(position=float(data)))
```

**Dampak:** Beban event loop turun dari ~12 Task/detik menjadi ~4 Task/detik (4 subscriber × 1 Hz). Pengurangan ~66%.

---

## TASK 2 — `server/handlers/event_listeners.py`: Hapus throttle redundant

Setelah Task 1, throttle di `_on_track_progress` di event_listeners sudah tidak diperlukan lagi (TrackProgressEvent sudah di-throttle di sumber). Hapus guard `0.33 detik` agar kode lebih bersih — kalau throttle sumber diubah nanti, consumer tidak perlu ikut diubah.

Cari:
```python
    async def _on_track_progress(event: TrackProgressEvent):
        nonlocal last_progress
        position = event.position
        now = time.monotonic()
        if now - last_progress < 0.33:
            return
        last_progress = now
        await broadcast_service.broadcast_progress(position, playback_controller.state.status.name)
```

Ganti dengan:
```python
    async def _on_track_progress(event: TrackProgressEvent):
        # Throttle sudah ditangani di sumber (mpv_controller, 1 Hz).
        await broadcast_service.broadcast_progress(
            event.position, playback_controller.state.status.name
        )
```

Sekaligus hapus variable `last_progress` dan import `time` jika tidak dipakai di tempat lain di fungsi ini.

Cari:
```python
    last_progress = 0.0
```

Hapus baris tersebut.

Cek apakah `import time` di file ini masih dipakai di tempat lain. Cari semua penggunaan `time.` — jika hanya untuk `last_progress`, hapus juga importnya.

---

## TASK 3 — `plugins/lyrics.py`: Throttle `LyricsUpdatedEvent`

Saat ini setiap ganti baris lirik = `bus.publish(LyricsUpdatedEvent())` = `broadcast_lyrics()` = JSON serialize seluruh array `lyrics_lines` (bisa 200+ baris) + WS send. Dengan lagu yang liriknya cepat berganti, ini bisa 1× per 2–3 detik.

Tambahkan throttle: hanya broadcast jika index benar-benar berubah DAN minimal 0.5 detik dari broadcast lirik terakhir.

**Tambahkan instance variable `_last_lyrics_broadcast_ts` di `__init__`:**

Cari:
```python
        self._current_generation = 0
```

Ganti dengan:
```python
        self._current_generation = 0
        self._last_lyrics_broadcast_ts: float = 0.0  # throttle LyricsUpdatedEvent
```

**Throttle di `_on_progress`:**

Cari:
```python
    async def _on_progress(self, event: TrackProgressEvent):
        """Find the active lyric index based on current playback position."""
        position = event.position
        if not self.lyrics_data or not isinstance(position, (int, float)):
            return

        timestamps = getattr(self.state, "lyrics_timestamps", [])
        if not timestamps:
            timestamps = [t for t, _ in self.lyrics_data]
            self.state.lyrics_timestamps = timestamps
        adjusted_position = position + self.state.lyrics_offset
        active_idx = bisect.bisect_right(timestamps, adjusted_position) - 1
        active_idx = max(0, active_idx)

        if self.state.lyrics_index != active_idx:
            self.state.lyrics_index = active_idx
            await self._bus.publish(LyricsUpdatedEvent())
```

Ganti dengan:
```python
    async def _on_progress(self, event: TrackProgressEvent):
        """Find the active lyric index based on current playback position."""
        position = event.position
        if not self.lyrics_data or not isinstance(position, (int, float)):
            return

        timestamps = self.state.lyrics_timestamps
        if not timestamps:
            timestamps = [t for t, _ in self.lyrics_data]
            self.state.lyrics_timestamps = timestamps

        adjusted_position = position + self.state.lyrics_offset
        active_idx = bisect.bisect_right(timestamps, adjusted_position) - 1
        active_idx = max(0, active_idx)

        if self.state.lyrics_index != active_idx:
            self.state.lyrics_index = active_idx
            import time as _time
            _now = _time.monotonic()
            # Throttle: jangan broadcast lirik lebih dari 1× per 0.5 detik
            # untuk menghindari serialize ratusan baris lirik terlalu sering.
            if _now - self._last_lyrics_broadcast_ts >= 0.5:
                self._last_lyrics_broadcast_ts = _now
                await self._bus.publish(LyricsUpdatedEvent())
```

---

## TASK 4 — `main.py`: Naikkan interval background pollers

Dua background task yang wake up terlalu sering tanpa alasan kuat:

**Fix A — `mpv_reconnect_checker`: dari 5 detik ke 30 detik**

`_observe_events` sudah handle reconnect sendiri saat disconnect. Checker ini hanya fallback redundant — tidak perlu setiap 5 detik.

Cari:
```python
    async def mpv_reconnect_checker():
        while True:
            await asyncio.sleep(5)
```

Ganti dengan:
```python
    async def mpv_reconnect_checker():
        while True:
            await asyncio.sleep(30)  # 5→30 det: reconnect check cukup sekali per 30 detik
```

**Fix B — `connectivity_check`: dari 60 detik ke 5 menit**

App music player tidak perlu tahu status internet setiap 60 detik. HTTP request ke Google setiap menit = DNS lookup + TCP + TLS handshake berulang = wake radio chip di Android = drain baterai nyata.

Cari:
```python
            await asyncio.sleep(60)
```

Di dalam fungsi `check_connectivity()`, ganti dengan:
```python
            await asyncio.sleep(300)  # 60→300 det: cek konektivitas cukup sekali per 5 menit
```

---

## VERIFIKASI

```bash
python -m pytest tests/ -x -q
# Semua harus pass
```

Manual test setelah patch:
- Play lagu → lirik tetap sync (maks delay 1 detik, tidak terasa)
- SponsorBlock tetap skip segment dengan akurat
- Progress bar di UI update ~1× per detik (sebelumnya ~3–4×, tidak ada perbedaan visual)
- HP terasa lebih dingin setelah 10–15 menit putar musik

---

## CATATAN

- **Task 1 throttle 1 Hz** adalah trade-off yang tepat: progress bar di UI sudah di-throttle di frontend juga (animasi CSS), dan lyrics tidak butuh presisi millisecond. Jika terasa terlalu kasar, bisa turunkan ke `0.5` (2 Hz) tapi `1.0` sudah cukup untuk semua use case.
- **Task 3** hanya throttle broadcast ke WS — internal `lyrics_index` tetap diupdate setiap kali ada perubahan, jadi tidak ada lyric yang "dilewati" secara internal.
- **Task 4 Fix B** tidak mempengaruhi fungsionalitas — `state.is_online` hanya dipakai untuk display info di UI, bukan gate untuk playback.

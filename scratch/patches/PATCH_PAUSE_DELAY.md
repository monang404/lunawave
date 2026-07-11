# PATCH_PAUSE_DELAY.md

Baca `AI_CONTEXT.md` dulu. Task: fix jeda 1–3 detik saat pause/play di LunaWave.

---

## ROOT CAUSE

Dua bug terpisah yang bersusun:

**Bug A — `toggle_pause()` di-await sebelum WS broadcast:**
Di `controller.py`, urutan eksekusinya:
1. Update `state.status`
2. `await bus.publish(TrackPauseChangedEvent)` → trigger `_on_pause_changed` di event_listeners → `await broadcast_service.broadcast_progress()` → `await ws.send_str()` untuk **setiap** klien **sequential**
3. `await mpv.toggle_pause()` → write ke IPC socket

Masalah: step 2 adalah await penuh. Kalau ada 2+ WS client, semua dikirim sequential sebelum mpv bahkan disentuh. Tapi ini bukan bottleneck utama.

**Bug B (bottleneck utama) — Round-trip IPC untuk konfirmasi pause:**
`mpv.toggle_pause()` menggunakan `_command(["cycle", "pause"])` yang hanya fire-and-forget (tidak await response). Tapi **konfirmasi** datang balik lewat observer loop: mpv → socket → `readline()` → `_handle_event` → `bus.publish(TrackPauseChangedEvent)` → `_on_pause_changed` di controller → update `state.status` lagi.

Jadi ada **dua path** yang bersaing update state yang sama:
- Path A (cepat): controller langsung set `state.status = PAUSED`
- Path B (lambat): mpv observer loop kirim `property-change pause=true` → trigger `_on_pause_changed` lagi

Path B tidak menyebabkan jeda UI (karena state sudah diset di Path A), tapi **dia bisa override state yang salah** kalau timing tidak tepat, dan inilah yang menyebabkan UI kadang "balik" ke status sebelumnya setelah beberapa detik.

**Bug C — `broadcast()` sequential:**
`ConnectionManager.broadcast()` mengirim ke semua WS client satu per satu dengan `await`. Dengan 2+ client, setiap client menunggu client sebelumnya selesai.

---

## PERUBAHAN

### FILE 1: `engine/playback/controller.py`

**Cari:**
```python
    async def _on_cmd_toggle_pause(self, _data=None):
        if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED):
            new_status = PlayerStatus.PAUSED if self.state.status == PlayerStatus.PLAYING else PlayerStatus.PLAYING
            self.state.status = new_status
            await self.bus.publish(TrackPauseChangedEvent(is_paused=(new_status == PlayerStatus.PAUSED)))
            await self.mpv.toggle_pause()
```

**Ganti dengan:**
```python
    async def _on_cmd_toggle_pause(self, _data=None):
        if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED):
            new_status = PlayerStatus.PAUSED if self.state.status == PlayerStatus.PLAYING else PlayerStatus.PLAYING
            self.state.status = new_status
            # Fire mpv dan broadcast secara bersamaan — tidak perlu tunggu satu sama lain.
            # mpv.toggle_pause() adalah write ke socket saja, tidak ada response yang perlu di-await.
            await asyncio.gather(
                self.bus.publish(TrackPauseChangedEvent(is_paused=(new_status == PlayerStatus.PAUSED))),
                self.mpv.toggle_pause(),
            )
```

Tambahkan `import asyncio` di bagian atas file jika belum ada. Cek dulu — kemungkinan sudah ada.

---

### FILE 2: `server/handlers/websocket.py`

**Cari method `broadcast` di class `ConnectionManager`:**
```python
    async def broadcast(self, message: dict):
        data = json.dumps(message, ensure_ascii=False)
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_str(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)
```

**Ganti dengan:**
```python
    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        data = json.dumps(message, ensure_ascii=False)
        results = await asyncio.gather(
            *[ws.send_str(data) for ws in list(self.active_connections)],
            return_exceptions=True,
        )
        dead = [
            ws for ws, result in zip(list(self.active_connections), results)
            if isinstance(result, Exception)
        ]
        for ws in dead:
            self.disconnect(ws)
```

Pastikan `import asyncio` ada di module level file ini (bukan hanya di dalam `__init__`).

---

## VERIFIKASI

```bash
python -m pytest tests/ -x -q
```

Semua test harus pass. Tidak ada perubahan interface atau API.

Manual test: play lagu → klik pause → UI harus update **instan** tanpa jeda.

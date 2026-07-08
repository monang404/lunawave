
text = '''
---
master_id: M-061
verification_status: SUDAH_BENAR
verified_location: engine/playback/radio_commands.py:20-22
code_evidence: 
```python
        async with self.playback_controller._lock:
            if self.state.playback_mode == PlaybackMode.RADIO:
                seed = cmd.seed_artist if cmd else None
```
verification_note: Berbeda dengan klaim, kode aktual sudah memiliki proteksi Null terhadap argumen `cmd` (berupa `if cmd else None`) sehingga pengecekan attribute `cmd.seed_artist` tidak akan memicu AttributeError.
---

---
master_id: M-062
verification_status: VALID
verified_location: core/state.py:58-65
code_evidence: 
```python
    @classmethod
    def from_dict(cls, data: dict) -> Optional['TrackInfo']:
        if not data:
            return None
        try:
            video_id = VideoId(data.get("video_id", ""))
        except ValueError:
            return None
```
verification_note: Sesuai klaim, Exception `ValueError` ditangkap dan hanya mengembalikan `None` diam-diam (silent fail).
---

---
master_id: M-063
verification_status: VALID
verified_location: engine/playback/controller.py:177-179
code_evidence: 
```python
        next_data = {}
        if self.state.current_track:
            next_data["video_id"] = self.state.current_track.video_id
```
verification_note: `next_data` dideklarasikan dan diisi, namun tidak pernah dipakai di kode mana pun setelahnya di dalam fungsi `_on_track_ended`.
---

---
master_id: M-064
verification_status: VALID
verified_location: server/services/discover_service.py:130-132
code_evidence: 
```python
        except Exception as e:
            print(f"Error in get_featured_genres: {e}")
        return genres
```
verification_note: `get_featured_genres` menangkap exception dan melakukan `print` biasa, bukan menggunakan `logger.error` seperti fungsi-fungsi lain di sekitarnya.
---

---
master_id: M-065
verification_status: VALID
verified_location: core/log_config.py:396-404
code_evidence: 
```python
        if msg is None:  # error card
            _print_error_card(name, str(event), event_dict)
            return ""

        tag = _module_tag(name)
        line = f"{_GY}{ts}{_R} {tag} {sym} {msg}"
        sys.stderr.write(line + "\\n")
        sys.stderr.flush()
        return ""  # prevent default handler from double-printing
```
verification_note: `_CompactRenderer.__call__` secara vulgar mengembalikan `return ""` mem-bypass chain return structlog.
---

---
master_id: M-066
verification_status: VALID
verified_location: core/log_config.py:119-122
code_evidence: 
```python
def _summary_worker():
    while True:
        time.sleep(600)  # every 10 minutes
        with STATS.lock:
```
verification_note: `_summary_worker` dijalankan dengan `while True` tanpa flag `_stop` atau exit condition saat graceful shutdown, menjadikannya infinite loop abadi.
---

---
master_id: M-067
verification_status: VALID
verified_location: web/static/js/utils.js:194-197
code_evidence: 
```javascript
    } catch (e) {
        console.warn("Color extraction failed:", e);
        if (callback) callback("var(--bg-elevated)");
    }
```
verification_note: Saat error, callback dipanggil dengan string literal `"var(--bg-elevated)"` yang tidak sesuai schema object `{r, g, b}` yang diharapkan pemanggilnya.
---

---
master_id: M-068
verification_status: VALID
verified_location: web/static/js/utils.js:91-93
code_evidence: 
```javascript
        const cleanTitle = window.cleanTrackTitle(track.title);
        const query = encodeURIComponent(track.artist + " " + cleanTitle);
        const response = await fetch(`${ITUNES_API_URL}?term=${query}&media=music&limit=1`);
```
verification_note: Pemanggilan URL `ITUNES_API_URL` tidak didefinisikan sebelumnya di dalam `utils.js` (atau dependensi lain), sehingga bisa memicu `ReferenceError`.
---

---
master_id: M-069
verification_status: VALID
verified_location: web/static/js/audio.js:141-143
code_evidence: 
```javascript
export async function _resumeAndPlay(audio) {
    if (audioCtx && audioCtx.state === 'suspended') {
        try { await audioCtx.resume(); } catch (e) { console.warn("[audio] ctx resume failed:", e); }
```
verification_note: File `audio.js` bukanlah modul dan dieksekusi di global namespace HTML, menggunakan keyword `export` murni akan melempar SyntaxError fatal.
---

---
master_id: M-070
verification_status: VALID
verified_location: server/services/discover_service.py:51-53
code_evidence: 
```python
            async with self.db.conn.execute(  # type: ignore
                "SELECT video_id, title, artist, duration, thumbnail, local_path, view_count, play_count, is_favorite FROM tracks WHERE is_favorite = 1 OR play_count > 0 ORDER BY is_favorite DESC, play_count DESC LIMIT ?", (n,)
            ) as cursor:
```
verification_note: `DiscoverService` tidak menggunakan layer `repository` (seperti `DiscoverRepository`) secara modular, melainkan menulis SQL raw secara repetitif langsung menembak database via koneksi `self.db.conn`.
---

---
master_id: M-071
verification_status: VALID
verified_location: server/handlers/websocket.py:60-61
code_evidence: 
```python
        targets = list(self.active_connections)
        results = await asyncio.gather(*(send(ws) for ws in targets))
```
verification_note: Broadcast state dan data mengirimkan payload ke semua iterasi `active_connections` (semua socket), tak peduli socket tersebut telah login/terautentikasi atau belum, mengekspos status player ke anonymous user.
---

---
master_id: M-072
verification_status: VALID
verified_location: engine/playback/queue_commands.py:23-25
code_evidence: 
```python
            if 0 <= cmd.index < len(self.state.queue):
                removed = self.state.queue[cmd.index]
                del self.state.queue[cmd.index]
```
verification_note: Penghapusan berdasar index di pertengahan elemen `deque` via `del` akan memicu iterasi / pergeseran komputasi internal, membuat efisiensi menjadi linear O(n).
---

---
master_id: M-073
verification_status: VALID
verified_location: core/state.py:43-55
code_evidence: 
```python
    is_favorite: Optional[int] = 0

    def to_dict(self) -> dict:
        return {
            ...
            "is_favorite": bool(getattr(self, "is_favorite", 0)),
        }
```
verification_note: Variabel dideklarasikan bertipe `Optional[int]` (integer), tetapi dipaksa dibaca atau dikonversi menjadi boolean ketika melakukan serialisasi `to_dict()`, berpotensi menghasilkan inkonsistensi.
---

---
master_id: M-074
verification_status: VALID
verified_location: core/event_bus.py:33-37
code_evidence: 
```python
        if inspect.ismethod(handler):
            ref = weakref.WeakMethod(handler)
        else:
            ref = handler  # type: ignore
        self._subscribers[event_type].append(ref)
```
verification_note: Jika callback function bukan bound method (`inspect.ismethod`), maka handler di-simpan secara hard-reference `ref = handler`, tidak ditangani sebagai weakref, sehingga tidak terserap oleh garbage collection dan rentan kebocoran memori.
---

---
master_id: M-075
verification_status: VALID
verified_location: server/handlers/ws/queue_handlers.py:57-59
code_evidence: 
```python
            await command_bus.execute(SetModeCommand(mode=PlaybackMode.QUEUE))
            await command_bus.execute(QueueReplaceCommand(tracks=songs))
            await command_bus.execute(QueueSelectCommand(index=0))
```
verification_note: Handler mengeksekusi 3 command bus berurutan dengan jeda `await`. Tiap await berpotensi melepaskan kendali event loop dan membiarkan handler concurrent lainnya memutasi queue di sela-sela instruksi (Race Condition).
---

Batch ini: 14 valid, 0 tidak ditemukan, 1 sudah benar, 0 perlu konfirmasi.
'''

with open('c:/Users/PUTRA JAYA LIMBANGAN/Documents/ytgui/ytgui-project/docs/verifikasi_ekstraksi.md', 'a', encoding='utf-8') as f:
    f.write(text)

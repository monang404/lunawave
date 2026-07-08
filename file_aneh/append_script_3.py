
text = '''
---
master_id: M-195
verification_status: SUDAH_BENAR
verified_location: web/static/js/events/lyrics-events.js:34, 59
code_evidence: 
```javascript
    if (dom.lyricOffsetMinus) {
        dom.lyricOffsetMinus.addEventListener("click", () => {
...
        if (btnSyncMinus) {
            btnSyncMinus.addEventListener("click", (e) => {
```
verification_note: Klaim salah. Pendeklarasian event listener di `lyrics-events.js` tidak ditumpuk pada satu elemen button yang sama, melainkan diikat ke dua ID tombol yang berbeda (yakni `btnSyncMinus` pada laman lirik dan `dom.lyricOffsetMinus` pada floating menu settings).
---

---
master_id: M-196
verification_status: SUDAH_BENAR
verified_location: web/static/js/render/lyrics.js:9-19
code_evidence: 
```javascript
    if (!dom.lyricsContent._scrollBound) {
        dom.lyricsContent._scrollBound = true;
...
        dom.lyricsContent.addEventListener("wheel", setScrolling, {passive: true});
        dom.lyricsContent.addEventListener("touchmove", setScrolling, {passive: true});
    }
```
verification_note: Klaim salah. Penulisan `dom.lyricsContent.innerHTML = html` saat update tidak menghancurkan tag parent `dom.lyricsContent` itu sendiri, sehingga variabel state `_scrollBound` tetap menempel. Karena validasi if terpasang, listener hanya ditambah tepat satu kali (Tidak ada kebocoran memory / duplicate binding).
---

---
master_id: M-197
verification_status: VALID
verified_location: web/static/index.html, web/static/js/events/settings-events.js
code_evidence: 
```html
        <div class="settings-sheet" id="settings-sheet" role="dialog" aria-modal="true" aria-label="Settings">
```
verification_note: Jendela interaksi seperti `.settings-sheet` dibiarkan terbuka menindih layar (overlay) tetapi sama sekali tidak memiliki script Focus Trap, menyebabkan input keyboard (seperti tombol TAB) akan menembus dan berinteraksi dengan player bar yang tertutup di bawahnya.
---

---
master_id: M-198
verification_status: VALID
verified_location: web/static/index.html:56-59
code_evidence: 
```html
                        <div class="login-input-group">
                            <input type="text" id="admin-username" placeholder="Username" autocomplete="off">
                        </div>
                        <div class="login-input-group">
                            <input type="password" id="admin-password" placeholder="Password">
                        </div>
```
verification_note: Tag isian otentikasi login sama sekali tidak dibekali tag khusus label form (`<label for="...">`) maupun atribut aria, hanya mengandalkan placeholder teks visual yang buta bagi screen reader.
---

---
master_id: M-199
verification_status: VALID
verified_location: web/static/index.html:180
code_evidence: 
```html
                            <input type="range" min="0" max="150" value="80" class="vol-slider" id="vol-slider">
```
verification_note: Parameter interaksi standar asesibilitas (`aria-label`, `aria-valuemin`, `aria-valuenow`, dsb) dihilangkan / aben pada elemen slider kontrol volume.
---

---
master_id: M-200
verification_status: VALID
verified_location: (Global JS Frontend)
code_evidence: 
(Tidak ada baris bukti spesifik karena file testing tidak ditemukan di repositori)
verification_note: Lingkungan antarmuka JavaScript `web/static/js/*` sepenuhnya telanjang tanpa kerangka penguji otomasi runner (seperti vitest, jest) untuk mendeteksi regresi kode front-end.
---

---
master_id: M-201
verification_status: VALID
verified_location: tests/integration/test_e2e.py:27
code_evidence: 
```python
    db.verify_session = AsyncMock(return_value=True)
```
verification_note: Mock logic di Test E2E memaksa otentikasi WS (token apa saja) menghasilkan nilai valid sah (return_value=True) tanpa pengujian verifikasi data palsu, mengeksploitasi celah pengujian pada test runner.
---

---
master_id: M-202
verification_status: VALID
verified_location: (Global Test Suites)
code_evidence: 
(Tidak ada file/suite concurrency tests)
verification_note: Tidak adanya pengujian beban race condition (seperti di Queue command yang notabene rentan) menyembunyikan kemungkinan server state rusak saat banyak admin concurrent memanipulasi player bersamaan.
---

---
master_id: M-203
verification_status: VALID
verified_location: plugins/notifications.py:83-96
code_evidence: 
```python
    def _blocking_read_loop(self):
        while not self._stop.is_set():
...
            except Exception as e:
                logger.warning(f"Now-playing FIFO reader error: {e}")
                time.sleep(1)
```
verification_note: Pemanggilan loop file deskriptor OS berjalan lepas di _blocking_read_loop tanpa satu pun script test python di layer `tests/` yang memverifikasi cleanup (`_stop.set()`) maupun kehandalannya terhadap exception IO.
---

---
master_id: M-204
verification_status: VALID
verified_location: (Global Test Suites)
code_evidence: 
(Tidak ada direktori load test)
verification_note: Absennya test profil beban atau stresstest (misal menggunakan tool locust atau wrk) meloloskan skenario kemungkinan bottleneck stream async I/O bila dihajar traffic listener.
---

---
master_id: M-205
verification_status: VALID
verified_location: tests/fixtures/sample_track.json:1-28
code_evidence: 
```json
{
    "id": "dQw4w9WgXcQ",
    "title": "Never Gonna Give You Up",
...
}
```
verification_note: Data simulasi tiruan track json yt-dlp `sample_track.json` dibiarkan steril dan mulus tak menantang (1 skenario normal) mengacuhkan verifikasi kelolosan pada payload kotor (missing formats list, null title).
---

---
master_id: M-206
verification_status: VALID
verified_location: Dockerfile:28
code_evidence: 
```dockerfile
# Command to run the application
CMD ["python", "run.py"]
```
verification_note: Instruksi default image container menunjuk ke skrip awalan `run.py` yang jelas-jelas tidak eksis / fiktif di dalam root folder project (seharusnya `start.py`), menjamin crash fatal saat run.
---

---
master_id: M-207
verification_status: VALID
verified_location: Dockerfile:1-29
code_evidence: 
(Seluruh file Dockerfile)
verification_note: Penulisan definisi lingkungan eksekusi (Dockerfile) menghilangkan praktik hardening (`USER appuser`), menuntun python interpreter dan instance server berjalan langsung di atas privilege super (root).
---

---
master_id: M-208
verification_status: VALID
verified_location: Dockerfile:1-29
code_evidence: 
(Seluruh file Dockerfile)
verification_note: Absen total parameter `HEALTHCHECK` pada file docker yang sangat penting guna memberitahu Docker Daemon status ketersediaan endpoint `/health`.
---

---
master_id: M-209
verification_status: VALID
verified_location: docker-compose.yml:10-11
code_evidence: 
```yaml
    volumes:
      # Mount cache and db for persistence
      - ./data:/app/data
```
verification_note: Direktori operasional persisten yang ditunjuk cuma tunggal `/app/data` (basis data SQlite), namun direktori utama `/app/cache` (menyimpan token admin di `admin_password.txt`, socket cache list) dilewatkan sirna jika container reboot.
---

Batch ini: 13 valid, 0 tidak ditemukan, 2 sudah benar, 0 perlu konfirmasi.

'''

with open('docs/verifikasi_ekstraksi.md', 'a', encoding='utf-8') as f:
    f.write(text)

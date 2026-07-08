
text = '''
---
master_id: M-210
verification_status: VALID
verified_location: docker-compose.yml:7-8
code_evidence: 
```yaml
    ports:
      - "8765:8765"
```
verification_note: Port binding `8765:8765` tanpa spesifikasi host localhost (`127.0.0.1:8765:8765`) di Docker mem-bypass firewall ufw secara default iptables dan terekspos mentah-mentah ke IP 0.0.0.0 publik.
---

---
master_id: M-211
verification_status: SUDAH_BENAR
verified_location: Dockerfile:15-19
code_evidence: 
```dockerfile
# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
```
verification_note: Klaim salah. Dockerfile di repository ini sama sekali tidak memiliki proses instalasi NPM atau build Javascript (`npm install`), melainkan murni python back-end. Caching dependensi python via `requirements.txt` juga sudah benar diletakkan sebelum `COPY . .`.
---

---
master_id: M-212
verification_status: VALID
verified_location: .github/workflows/ci.yml:9-67
code_evidence: 
(Hanya ada jobs: test-ubuntu dan test-windows)
verification_note: Pipeline CI di file `.github/workflows/ci.yml` terhenti murni di fase testing (Continuous Integration), dan sama sekali tidak memiliki fase pengantaran otomatis rilis (Continuous Deployment / CD).
---

---
master_id: M-213
verification_status: VALID
verified_location: .github/workflows/ci.yml:61-64
code_evidence: 
```yaml
    - name: Test start.bat syntax
      run: |
        # Just check if start.bat parses without syntax error
        cmd.exe /c "start.bat --help" || exit 0
```
verification_note: Test spesifik platform Windows secara by-design dipasangi instruksi bohong-bohongan yang hanya menguji ekstensi batch, melompati eksekusi suite `pytest` yang krusial seperti di Ubuntu.
---

---
master_id: M-214
verification_status: VALID
verified_location: .github/workflows/ci.yml:40-41
code_evidence: 
```yaml
    - name: Run tests with coverage
      run: pytest tests/ -v --cov=. --cov-report=term-missing --cov-fail-under=40
```
verification_note: Ambang batas (threshold) coverage CI dibiarkan tersendat di angka miskin `40`, memfasilitasi PR lolos meriah meski nyaris tidak tersentuh unit tests.
---

---
master_id: M-215
verification_status: VALID
verified_location: package.json:14, .github/workflows/ci.yml
code_evidence: 
```json
    "test": "echo \"Error: no test specified\" && exit 1"
```
verification_note: Repositori memiliki skrip javascript dan `package.json`, tetapi tidak ada hook di CI untuk menguji frontend, dan skrip uji npm default melempar gagal buatan.
---

---
master_id: M-216
verification_status: VALID
verified_location: .github/workflows/ci.yml:14, 17
code_evidence: 
```yaml
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
```
verification_note: Pemanggilan GitHub Actions bersandar pada ref tag mutabel `v4` dan `v5` ketimbang immutable full komit SHA (hash-pinning), membuka ruang kerentanan supply chain (contoh insiden serangan dependensi).
---

---
master_id: M-217
verification_status: VALID
verified_location: config.py:33-35, .env.example:2-3
code_evidence: 
```python
WEB_PORT = int(os.environ.get("LUNAWAVE_PORT", 8765))
ADMIN_USERNAME = os.environ.get("LUNAWAVE_ADMIN_USER", "admin")
...
# di .env.example:
YTGUI_PORT=8765
YTGUI_ADMIN_USER=admin
```
verification_note: Penamaan Env Var amat ceroboh dan terbelah (Schizophrenia): source code `config.py` menarget parameter awalan `LUNAWAVE_*`, sementara dokumen panduan `.env.example` dan `start.sh` mengajarkan awalan `YTGUI_*`.
---

---
master_id: M-218
verification_status: VALID
verified_location: config.py:47, 65-69
code_evidence: 
```python
    _password_file = BASE_DIR / "cache" / "admin_password.txt"
...
            raw_password = secrets.token_urlsafe(12)
            _admin_password = hash_password(raw_password)
...
            with open(_password_file, "w", encoding="utf-8") as f:
                f.write(_admin_password)
```
verification_note: Walau di-hash, string rahasia final admin di-dump sebagai plaintext file tepat di folder `/cache` yang membaur dengan data unduhan audio/thumbnail tak penting, mempermudah eksposur bila ada directory traversal.
---

---
master_id: M-219
verification_status: VALID
verified_location: requirements.txt:2, pyproject.toml:13
code_evidence: 
```text
# requirements.txt
aiosqlite==0.20.0
...
# pyproject.toml
    "aiosqlite==0.22.1",
```
verification_note: Sinkronisasi dependensi putus. `requirements.txt` (yang dipakai oleh docker) mematok versi lama library seperti `aiosqlite==0.20.0`, bertabrakan asimetris dengan `pyproject.toml` yang menuntut versi `aiosqlite==0.22.1`.
---

Batch ini: 9 valid, 0 tidak ditemukan, 1 sudah benar, 0 perlu konfirmasi.

'''

with open('docs/verifikasi_ekstraksi.md', 'a', encoding='utf-8') as f:
    f.write(text)

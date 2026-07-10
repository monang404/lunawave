# Security

> Kebijakan keamanan LunaWave — cara melaporkan vulnerability, audit secrets, dan checklist sebelum go public.
> Untuk threat model lengkap, lihat → [threat_model.md](threat_model.md)

---

## Melaporkan Vulnerability

LunaWave adalah proyek open source self-hosted. Jika menemukan vulnerability:

1. **Jangan buat public GitHub Issue** untuk security vulnerability.
2. Kirim laporan ke maintainer via email atau GitHub Security Advisory (Private).
3. Sertakan: deskripsi, langkah reproduksi, dampak yang mungkin, dan versi yang terpengaruh.
4. Respons awal dalam **72 jam**. Fix dan disclosure dalam **14 hari** untuk vulnerability kritis.

### Scope

| In Scope | Out of Scope |
|---|---|
| Autentikasi WebSocket | Keamanan jaringan di luar aplikasi |
| Injeksi command ke MPV/yt-dlp | Keamanan OS host |
| Akses file di luar `cache/mp3/` | Vulnerability di MPV atau yt-dlp itu sendiri |
| Hardcoded credentials | Serangan yang butuh akses fisik ke server |
| Path traversal via URL/filename | |

---

## Audit Secrets & Credentials

### Checklist Sebelum Push

Pastikan hal berikut tidak ada di kode:

- [ ] Password atau API key hardcoded
- [ ] Token autentikasi dalam source code
- [ ] Credential dalam komentar atau string debug
- [ ] File `.env` yang tidak di-gitignore

### File yang Wajib Di-gitignore

```gitignore
# Runtime — tidak boleh di-commit
data/lunawave.db
cache/mp3/
*.db
*.db-shm
*.db-wal

# Secrets
.env
.env.local
config.local.py

# OS & tooling noise
__pycache__/
*.pyc
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
```

> **Aksi:** Cek `data/lunawave.db` dan `cache/mp3/` sudah ada di `.gitignore`. Jalankan `git status` — pastikan keduanya tidak muncul sebagai untracked file.

### Scan Otomatis

```bash
# Bandit — static analysis untuk security issue Python
bandit -r lunawave/ -c pyproject.toml

# pip-audit — cek vulnerability di dependencies
pip-audit -r requirements.txt
```

Kedua tool sudah terintegrasi di CI — lihat → [../devops/ci_cd.md](../devops/ci_cd.md)

---

## Autentikasi WebSocket

LunaWave menggunakan token-based auth untuk WebSocket. Hal yang harus dijaga:

- Token di-generate dengan entropi cukup (`secrets.token_urlsafe(32)`)
- Token tidak di-log dalam bentuk plaintext
- Session expired menggunakan **waktu absolut** (bukan monotonic clock) — lihat ADR-0004
- `ADMIN_ONLY_ACTIONS` harus mencakup semua command yang bersifat destruktif

```python
# Contoh yang benar
import secrets
token = secrets.token_urlsafe(32)

# Yang harus dihindari
import time
expiry = time.monotonic() + 3600  # ← BUG: monotonic tidak valid sebagai timestamp absolut
```

---

## `SECURITY.md` (Root Repo)

File `SECURITY.md` di root repo adalah standar GitHub untuk disclosure policy. Harus dibuat sebelum repo dipublikasi.

**Isi minimal:**

```markdown
# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| latest | ✅ |

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Send a report to [email/GitHub Security Advisory link].

We will respond within 72 hours and aim to release a fix within 14 days
for critical vulnerabilities.
```

> **Status:** ❌ Belum ada. Buat sebelum repo dipublikasi.

---

## Referensi Terkait

- Threat model detail → [threat_model.md](threat_model.md)
- Bandit config → [../devops/tooling.md](../devops/tooling.md)
- CI security audit → [../devops/ci_cd.md](../devops/ci_cd.md)
- Open source readiness checklist → [../opensource/readiness.md](../opensource/readiness.md)
- ADR autentikasi → [../adr/0004-command-bus-single-writer.md](../adr/0004-command-bus-single-writer.md)

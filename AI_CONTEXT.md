---
last_verified: 2026-07-10
sprint: 3.2
---

# AI_CONTEXT.md — Baca ini sebelum menyentuh kode apapun

## Ringkasan Project
LunaWave adalah music player berbasis YouTube yang jalan sebagai server lokal
(aiohttp + asyncio), diakses via browser. Audio diputar oleh MPV via IPC socket.
Platform utama: Termux (Android) + Windows.
Arsitektur: Hexagonal (Ports & Adapters). Frontend: Vanilla JS, no framework.

## Sprint Aktif: 3.2 (selesai) → 3.3 (berikutnya)
- Sprint 3.2 selesai: refactor `start.py` → `launcher/` ✅
- Sprint 3.3 target: lihat `docs/STATUS.md` untuk daftar lengkap

## File yang TIDAK BOLEH disentuh tanpa izin eksplisit
- `engine/playback/controller.py` — risiko tinggi, closure kompleks
- `server/handlers/websocket.py` — jangan pecah dulu, ikuti MIGRATION_GUIDE Tahap 3
- `cache/admin_password.txt` — JANGAN commit
- `web/static/index.html` — tidak dipecah, ini keputusan final

## Batasan teknis yang tidak boleh dilanggar
- Tidak boleh ganti aiohttp ke framework lain
- Tidak boleh tambah JS framework (React, Vue, dll)
- Tidak boleh ganti SQLite ke DB lain
- Tidak boleh refactor 2 tahap sekaligus dalam 1 commit
- Setiap file yang dipindah WAJIB ada backward-compat alias

## Alur kerja AI yang benar

### Sebelum mulai
1. Baca file ini
2. Baca `docs/STATUS.md` — cek kondisi file yang akan disentuh
3. Baca `docs/PATCHLOG.md` — 2-3 entri terakhir
4. Gunakan `scripts/find_owner.py` untuk orientasi cepat (lihat §Developer Scripts)
5. Baru kerjakan task

### Setelah selesai (wajib, jangan skip)
1. Jalankan `python scripts/doctor.py` — satu perintah untuk semua health check (docs + arsitektur + struktur + keamanan)
   - Atau per-checker jika hanya ingin cek satu aspek (lihat §Developer Scripts)
2. Jalankan `python scripts/generate_file_index.py` — jika ada file/class/fungsi baru atau berubah
3. Jalankan `python scripts/generate_report.py` — jika ada penambahan/penghapusan file
4. Append entry baru ke `docs/PATCHLOG.md` dengan format ID `PATCH-YYYY-MM-DD-NNN`
5. Update `docs/STATUS.md` jika kondisi file berubah

## Output Generated — Kemana Hasilnya Disimpan

Scripts generator **tidak membuat file baru**. Mereka meng-inject hasil ke dalam
dokumen yang sudah ada, hanya di antara marker:

```
<!-- BEGIN:GENERATED -->
...blok ini ditimpa otomatis setiap kali script dijalankan...
<!-- END:GENERATED -->
```

**Jangan pernah edit teks di antara marker ini secara manual** — akan ditimpa.
**Jangan hapus marker-nya** — script tidak akan tau harus inject ke mana.

| Script | Meng-update bagian mana |
|--------|------------------------|
| `generate_file_index.py` | Blok `BEGIN:GENERATED` di `docs/FILE_INDEX.md` |
| `generate_report.py` | Blok `BEGIN:GENERATED` di `docs/REPORT.md` §Statistik Project |
| `architecture_lint.py` | Tidak menulis file — stdout + exit code |
| `verify_docs.py` | Tidak menulis file — stdout + exit code |
| `verify_structure.py` | Tidak menulis file — stdout + exit code |
| `verify_security.py` | Tidak menulis file — stdout + exit code |
| `doctor.py` | Tidak menulis file — aggregasi output semua checker di atas ke satu dashboard |
| `find_owner.py` | Tidak menulis file — hanya print ke stdout |

Bagian dokumen **di luar marker** (narasi, rekomendasi, keputusan) adalah
wilayah manual — AI boleh edit, tapi harus append ke `PATCHLOG.md` setelahnya.

## Developer Scripts

Project ini punya tooling di `scripts/` untuk membantu orientasi dan menjaga docs tetap sinkron.
**Selalu gunakan ini sebelum membaca puluhan file secara manual.**

### Orientasi cepat — gunakan ini dulu sebelum baca kode

```bash
# Siapa yang bertanggung jawab atas sebuah modul, class, atau fungsi?
# Jawab: layer arsitektur, callers, dependencies, status di STATUS.md, ADR terkait
python scripts/find_owner.py DownloadManager
python scripts/find_owner.py cache/db.py
python scripts/find_owner.py publish          # cari berdasarkan nama fungsi
```

```bash
# Cek kesehatan project secara menyeluruh sebelum mulai kerja
python scripts/doctor.py
```

### Setelah edit kode

```bash
# Cara paling mudah — jalankan semua checker sekaligus
python scripts/doctor.py

# Atau per-aspek jika ingin cek satu hal saja:
python scripts/architecture_lint.py   # import boundary
python scripts/verify_docs.py         # frontmatter, PATCHLOG, coverage docstring
python scripts/verify_structure.py    # file besar, pending items
python scripts/verify_security.py     # credential & DB files di .gitignore

# Regenerate docs setelah ada perubahan file/fungsi
python scripts/generate_file_index.py
python scripts/generate_report.py

# Atau regenerate + semua check sekaligus
python scripts/run_all.py
```

### Kapan pakai doctor.py vs checker individual

| Situasi | Pakai |
|---------|-------|
| Orientasi awal / cek kondisi repo | `doctor.py` |
| Setelah edit kode — validasi menyeluruh | `doctor.py` |
| Debug satu aspek saja (mis. docs) | `verify_docs.py --verbose` |
| CI / pre-commit (strict mode) | `doctor.py --strict` atau `architecture_lint.py` |
| Tambah checker baru ke dashboard | Tambah entri ke `CHECKERS` di `doctor.py` |

### JSON contract antar checker dan doctor.py

Semua checker (`verify_docs`, `architecture_lint`, `verify_structure`, `verify_security`) mengimplementasikan kontrak ini:
- Flag `--json` → cetak satu objek JSON ke stdout
- Schema wajib:
```json
{
  "checker": "nama_checker",
  "repository_status": "PASS|WARN|FAIL",
  "score": 0,
  "pass": 0, "warn": 0, "fail": 0,
  "checks": [
    {
      "name": "Nama Cek", "status": "PASS|WARN|FAIL",
      "message": "...", "count": 0, "items": [],
      "current": null, "total": null, "percentage": null, "weight": null
    }
  ]
}
```
- Exit code: `0` = tidak ada FAIL, `1` = ada FAIL

`doctor.py` hanya membaca JSON ini — tidak punya logika validasi sendiri. Untuk tambah checker baru, cukup implementasikan kontrak di atas lalu daftarkan di `CHECKERS` list di `doctor.py`.

### Struktur internal scripts/ (untuk AI yang perlu memodifikasi tooling)

`scripts/` kini punya dua sub-package internal:
- **`shared/`** — utilitas bersama: `check_result.py` (dataclass `CheckResult` + fungsi `_score`/`_overall_status`), `skip_dirs.py` (`SKIP_DIRS` + `walk_py_files`), `generated_block.py` (`replace_marker_block`)
- **`verify_docs/`** — pecahan dari `verify_docs.py` monolitik: `helpers.py`, `checks_docs.py`, `checks_coverage.py`, `checks_files.py`, `render.py`

Semua checker mengimport `CheckResult` dari `shared.check_result`. CLI dan exit code identik dengan sebelum refactor.

## Pointer ke detail
| Butuh info tentang | Cara tercepat |
|--------------------|---------------|
| File mana yang relevan untuk task ini | `python scripts/find_owner.py <nama_class_atau_file>` |
| Semua file & fungsinya | `docs/FILE_INDEX.md` ← sebagian sudah auto-generated, lebih akurat |
| Kondisi per-file & sprint target | `docs/STATUS.md` |
| Struktur folder | `docs/STRUCTURE.md` |
| Roadmap refactoring | `docs/MIGRATION_GUIDE.md` |
| Arsitektur ideal | `docs/kompas/Blueprint.md` |
| Keputusan arsitektur | `docs/kompas/adr/` |
| Temuan & status bug | `docs/REPORT.md` |
| Kesehatan project | `python scripts/doctor.py` |
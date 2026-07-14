---
title: Rencana Migrasi `scripts/` → `automation/` — LunaWave
dasar: scripts-intelligence-review.md (2026-07-13) + audit langsung codebase
tanggal: 2026-07-13
status: menunggu 3 konfirmasi keputusan
---

# Rencana Migrasi `scripts/` → `automation/`

Setiap unit kerja di bawah ini punya format sama: **Masalah** (kenapa perlu dikerjakan),
**Solusi** (apa yang dilakukan), **Definition of Done** (kapan dianggap selesai). Urutan
Fase 0–4 mengikuti dependency asli — kolom **Prasyarat** di Peta Task menunjukkan apa
yang harus selesai duluan, bukan urutan bebas pilih.

---

## Keputusan yang Perlu Dikonfirmasi Dulu

| # | Keputusan | Rekomendasi |
|---|---|---|
| 1 | Nama folder final: `automation/` vs `tools/` | **`automation/`** — `tools/` generik, berisiko jadi tempat sampah lagi seperti yang terjadi ke `scripts/` |
| 2 | `run_all.py`: perjelas jadi "regenerate docs + doctor" (Opsi A), atau hapus dan pindahkan ke flag `doctor.py --regenerate-docs` (Opsi B)? | **Opsi A** — perubahan minimal |
| 3 | Backward-compat alias untuk `scripts/` lama? | **Skip** — hanya 1 pemakai internal (`tests/unit/scripts/test_export_to_sqlite.py`), tidak ada dependency runtime |

---

## Peta Task

| Fase | Task | Ringkasan | Prasyarat |
|---|---|---|---|
| 0 | 0.1 | Pindahkan 6 file salah kategori keluar dari `scripts/` | — |
| 0 | 0.2 | Perjelas/hapus `run_all.py`, hilangkan `CHECKS` mati | — |
| 0 | 0.3 | Satukan `LARGE_FILE_THRESHOLD` jadi 1 konstanta | — |
| 0 | 0.4 | `find_owner.py`: tambah `--json`, perbaiki `SKIP_DIRS` | — |
| 0 | 0.5 | Perbaiki `check_patchlog()` agar dukung urutan descending | — |
| 0 | 0.6 | `git mv scripts automation` (+ folder test) | 0.1 |
| 0 | 0.7 | Update 2 referensi wajib (pre-commit, import test) | 0.6 |
| 0 | 0.8 | Update `AI_CONTEXT.md` (path + kontrak AI agent) | 0.6 |
| 0 | 0.9 | Regenerate `FILE_INDEX.md` & `REPORT.md` | 0.6 |
| 0 | 0.10 | Update referensi teks di ±15 file dokumentasi lain | 0.6 |
| 0 | 0.11 | Jalankan `doctor.py`, pastikan tidak ada regresi | 0.6–0.10 |
| 0 | 0.12 | Append entry migrasi ke `PATCHLOG.md` | 0.11 |
| 0 | 0.13 | Update `STATUS.md` jika perlu | 0.1 |
| 1 | 1.1 | Bangun `shared/repo_index.py` (fondasi index + cache) | Fase 0 stabil* |
| 2 | 2.1 | Bangun `event_graph.py` | 1.1 |
| 2 | 2.2 | Bangun `call_graph.py` (prioritas rendah) | 1.1 |
| 3 | 3.1 | Bangun `test_locator.py` | 1.1 |
| 3 | 3.2 | Bangun `patchlog.py` + migrasi urutan `PATCHLOG.md` | 0.5 |
| 3 | 3.3 | Bangun `impact.py` | 1.1, 2.1, 3.1 |
| 3 | 3.4 | Bangun `hotspot.py` | 3.2, 1.1 |
| 4 | 4.1 | Bangun `context_pack.py` (endpoint AI agent) | semua di atas + 0.4 |

\* *"Fase 0 stabil"* = task 0.1–0.13 selesai dan `doctor.py` jalan hijau minimal
beberapa hari tanpa masalah baru.

---

## Fase 0 — Migrasi & Housekeeping

### 0.1 Housekeeping: Pindahkan File Salah Kategori

**Masalah:** 6 dari 17 file di `scripts/` bukan tooling permanen — skrip sekali-pakai
atau salah folder — dan mencairkan sinyal "daftar alat resmi" bagi AI/dev yang baca
folder ini.

**Solusi:**

| File | Tindakan | Alasan |
|---|---|---|
| `generate_tests.py` | → `scratch/` atau hapus | Sekali-pakai, tidak idempoten |
| `fix_failing_tests.py` | → `scratch/` atau hapus | idem |
| `fix_imports.py` | → `scratch/` atau hapus | idem |
| `cleanup_tests.py` | → `scratch/` atau hapus | `shutil.move` tanpa cek existing → crash jika dijalankan ulang |
| `fix_docs.py` | → `scratch/`, kecuali dikeraskan (`--dry-run` + backup) | Manipulasi AST-index, rawan corrupt tanpa dry-run |
| `export_to_sqlite.py` | → `data/export_to_sqlite.py` | Docstring modul sendiri sudah menyebut `data.export_to_sqlite` |
| `package.sh` | → `scratch/` | Komentar header sendiri masih `# scratch/zip_project.sh` |

Pakai `scratch/` yang sudah ada di root — jangan bikin `automation/scratch/` baru.

**Definition of Done:**
- 6 file tidak lagi ada di `scripts/`
- `tests/unit/scripts/test_export_to_sqlite.py` pindah ke `tests/unit/data/`, import
  `from scripts.export_to_sqlite` → `from data.export_to_sqlite`
- Test suite hijau
- 1 commit terpisah (belum digabung rename folder)

### 0.2 Putuskan Nasib `run_all.py`

**Masalah:** `run_all.py` punya list `CHECKS` mati (didefinisikan, tidak dipakai) dan
tanggung jawabnya tumpang tindih dengan `doctor.py` — dua "pintu masuk" yang
membingungkan.

**Solusi:** Opsi A (sesuai keputusan #2) — perjelas `run_all.py` HANYA sebagai
"regenerate docs (`generate_file_index` + `generate_report`) lalu jalankan
`doctor.py`"; hapus `CHECKS` mati.

**Definition of Done:**
- Docstring `run_all.py` mencerminkan tanggung jawab tunggal ini
- Variabel `CHECKS` dead code dihapus
- 1 commit terpisah

### 0.3 Satukan `LARGE_FILE_THRESHOLD`

**Masalah:** 4 angka berbeda untuk konsep yang sama — 200/350 (`verify_structure.py`),
360 (`verify_docs/helpers.py`), 200/350 (`generate_file_index.py`), 300
(`generate_report.py`). File 320-baris bisa PASS di satu checker, FAIL di checker lain.

**Solusi:** Satu konstanta `LARGE_FILE_THRESHOLD` di `shared/`, semua checker import
dari sana.

**Definition of Done:** `grep` angka threshold hardcoded di ke-4 file = 0 hasil; semua
checker menunjuk konstanta `shared/` yang sama.

### 0.4 `find_owner.py`: Tambah `--json`, Perbaiki `SKIP_DIRS`

**Masalah:** `find_owner.py` adalah tool paling "intelligence-shaped" di folder ini,
tapi satu-satunya yang console-only (tidak bisa dikonsumsi program/AI tanpa parsing
teks bebas). Ia juga punya `SKIP_DIRS` lokal terduplikasi alih-alih pakai
`shared.SKIP_DIRS`, rawan drift.

**Solusi:** Tambah flag `--json` dengan skema selaras checker lain. Ganti `SKIP_DIRS`
lokal jadi named-variant eksplisit di `shared/skip_dirs.py` (mis.
`SKIP_DIRS_FOR_OWNERSHIP`) — tool ini memang perlu tahu isi `tests/`, jadi solusinya
konstanta bernama, bukan hardcode lokal.

**Definition of Done:** `find_owner.py <target> --json` menghasilkan JSON valid; tidak
ada `SKIP_DIRS` hardcoded lokal tersisa di file ini; logic inti diekstrak jadi fungsi
`get_owner_info(query, root) -> dict` yang dipakai baik oleh mode `--json` maupun
console — supaya `context_pack.py` (4.1) nanti bisa `import` langsung tanpa subprocess.

### 0.5 Perbaiki `check_patchlog()` untuk Urutan Descending

**Masalah:** `docs/PATCHLOG.md` saat ini append-only (oldest-first). Rencana
`patchlog.py` (task 3.2) akan membalik ke newest-first, tapi `check_patchlog()` di
`verify_docs/checks_docs.py` belum bisa validasi urutan descending.

**Solusi:** Update `check_patchlog()` agar bisa memvalidasi baik entri lama (ascending)
maupun entri baru (descending) selama masa transisi.

**Definition of Done:** `verify_docs.py` tidak FAIL pada `PATCHLOG.md` yang sebagian
entrinya sudah dibalik; ada test unit baru untuk kasus ini.

### 0.6 Rename Folder

**Masalah:** Nama `scripts/` tidak mencerminkan arah platform (lihat keputusan #1).
Harus pakai `git mv` supaya history file tidak putus.

**Solusi:**
```
git mv scripts automation
git mv tests/unit/scripts tests/unit/automation
```

**Definition of Done:** `git log --follow automation/doctor.py` masih menunjukkan
history sebelum rename; tidak ada file Python tersisa di `scripts/`.

### 0.7 Update Referensi Wajib

**Masalah:** `automation/` langsung patah tanpa 2 update ini.

**Solusi:**

| File | Update |
|---|---|
| `.pre-commit-config.yaml` | 2 entry (`architecture_lint.py`, `verify_docs.py`) → path `automation/...` |
| `tests/unit/data/test_export_to_sqlite.py` | Import `from scripts.export_to_sqlite` → `from data.export_to_sqlite` (file sudah dipindah di 0.1) |

**Definition of Done:** `pre-commit run --all-files` lulus; test import di atas lulus.
Boleh 1 commit yang sama dengan 0.6 — rename tanpa fix ini langsung broken.

### 0.8 Update `AI_CONTEXT.md`

**Masalah:** Ini dokumen paling sering dibaca AI agent di awal task. Kalau masih rujuk
`scripts/`, agent salah arah; juga belum ada kontrak eksplisit kapan pakai `--json`.

**Solusi** (checklist, teks siap-tempel di Lampiran):
- Ganti semua path literal `scripts/...` → `automation/...`
- Judul `## Developer Scripts` → `## Automation Tools` (Lampiran L1)
- Tambah kata **WAJIB** di step `find_owner.py` pada "Alur kerja AI" (Lampiran L2)
- Tambah section baru "Kontrak Output untuk AI Agent" (Lampiran L3)
- Update tabel "Output Generated" & "Pointer ke detail" ke path baru
- Judul "Struktur internal `scripts/`" → "Struktur internal `automation/`"
- Tambah catatan migrasi sementara, hapus setelah Sprint 3.3 (Lampiran L4)
- Update frontmatter `last_verified` → tanggal eksekusi

**Definition of Done:** `grep "scripts/"` pada `AI_CONTEXT.md` = 0 hasil (kecuali di
dalam catatan migrasi L4 yang sengaja menyebutnya sebagai referensi historis); section
"Kontrak Output untuk AI Agent" ada. Commit terpisah dengan pesan jelas.

### 0.9 Regenerate Docs Auto-Generated

**Masalah:** `docs/FILE_INDEX.md` dan `docs/REPORT.md` masih render path lama di blok
`GENERATED`.

**Solusi:** Jalankan `python automation/generate_file_index.py` dan
`python automation/generate_report.py` dari lokasi baru.

**Definition of Done:** Blok `BEGIN/END:GENERATED` di kedua file reflect `automation/`,
tidak ada sisa `scripts/`.

### 0.10 Update Dokumentasi Naratif Lain

**Masalah:** ±15 file docs lain menyebut `scripts/...`; kalau dibiarkan jadi
menyesatkan (bukan "patah", tapi salah).

**Solusi:** Cek satu-satu, bedakan instruksi ("jalankan `scripts/doctor.py`") vs
catatan historis ADR — jangan sed mass-replace buta.

| File | Tindakan |
|---|---|
| `docs/INDEX.md`, `docs/STATUS.md`, `docs/PATCHLOG.md` | Ganti path manual |
| `docs/adr/0002-sqlite-over-json-cache.md` | Biarkan — referensi historis, ADR tidak diedit ulang |
| `docs/architecture/folder_structure.md` | **Wajib** update — peta folder resmi |
| `docs/architecture/backend.md`, `docs/architecture/layer_diagram.md`, `docs/backend/persistence.md`, `docs/development/project_structure.md`, `docs/frontend/pwa.md`, `docs/testing/testing_strategy.md`, `docs/testing/unit_testing.md` | Cek konteks tiap referensi |
| `scratch/patches/*.md` | Biarkan — dokumen historis/sesi lama |

**Definition of Done:** Semua baris di atas ditandai selesai atau skip-dengan-alasan;
`docs/architecture/folder_structure.md` sudah update.

### 0.11 Verifikasi `doctor.py`

**Masalah:** Perlu memastikan tidak ada broken path internal setelah semua rename.

**Solusi:** Jalankan `python automation/doctor.py` dari root.

**Definition of Done:** `overall_status` sama atau lebih baik dibanding sebelum
migrasi — tidak ada checker baru yang FAIL akibat migrasi.

### 0.12 Entry `PATCHLOG.md`

**Masalah:** Konvensi project (`AI_CONTEXT.md`) mewajibkan tiap task selesai
di-append ke `PATCHLOG.md`.

**Solusi:** Tambah entry format `PATCH-YYYY-MM-DD-NNN` mendeskripsikan migrasi ini.

**Definition of Done:** Entry ada, ID berurut benar.

### 0.13 Update `STATUS.md` (Kondisional)

**Masalah:** Kalau file yang dipindah di 0.1 tercatat statusnya di `STATUS.md` dengan
path lama, jadi stale.

**Solusi:** Cek `STATUS.md`, update path yang berubah.

**Definition of Done:** Tidak ada path lama (`scripts/generate_tests.py`, dst.)
tersisa di `STATUS.md` — atau dikonfirmasi memang tidak pernah tercatat di sana.

---

## Fase 1 — Fondasi Index

### 1.1 `shared/repo_index.py`

**Masalah:** 3 implementasi AST-walk terduplikasi (`find_owner`, `generate_file_index`,
`generate_report`) tanpa cache — mahal waktu & token untuk AI yang query berkali-kali
dalam satu sesi.

**Solusi:** Satu module (bukan CLI, dipanggil sebagai library) yang AST-walk seluruh
repo **sekali**, hasilnya di-cache ke `.cache/repo_index.json` dengan invalidasi
berbasis mtime — dipanggil lagi, hanya file yang mtime-nya berubah yang di-parse
ulang; `reverse_deps` dihitung ulang dengan invert dict imports (murah, bukan re-parse
AST). Publish/subscribe event dideteksi dari `ast.Call` ke
`bus.publish(...)`/`bus.subscribe(...)` — **bukan** dari field docstring
`Publishes:`/`Subscribes to:`, karena survei ke seluruh repo menunjukkan field
`Publishes:` hampir selalu `None` walau modulnya benar-benar publish (docstring
auto-generated tidak ikut ter-update saat kode berubah — lihat mis. `download_manager.py`
yang jelas-jelas publish `DownloadCompleteEvent` tapi docstring-nya bilang `None`).

```python
"""
Module: automation.shared.repo_index

Purpose:
    Index AST satu kali untuk seluruh repo (classes, functions, imports, layer,
    event publish/subscribe, reverse-deps), dengan cache ber-invalidasi mtime.

Depends on:
    - automation.shared.skip_dirs (walk_py_files)
"""

from __future__ import annotations
import ast, json, time
from pathlib import Path
from automation.shared.skip_dirs import walk_py_files

CACHE_PATH = Path(".cache/repo_index.json")
_BUS_METHODS = {"publish", "subscribe"}


def _event_name(node: ast.Call) -> str | None:
    """publish: bus.publish(DownloadCompleteEvent(...)) -> arg adalah Call.
    subscribe: bus.subscribe(DownloadCompleteEvent, handler) -> arg adalah Name."""
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Call) and isinstance(first.func, ast.Name):
        return first.func.id
    if isinstance(first, ast.Name):
        return first.id
    return None


def _parse_file(path: Path, root: Path) -> dict:
    rel = str(path.relative_to(root)).replace("\\", "/")
    source = path.read_text(encoding="utf-8", errors="replace")
    entry = {
        "layer": rel.split("/")[0] if "/" in rel else "root",
        "classes": [], "functions": [], "imports": [],
        "publishes": [], "subscribes": [],
        "loc": source.count("\n") + 1, "docstring_purpose": "",
    }
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return entry

    doc = ast.get_docstring(tree) or ""
    if "Purpose:" in doc:
        after = doc.split("Purpose:", 1)[1].lstrip("\n")
        entry["docstring_purpose"] = after.split("\n\n")[0].strip().replace("\n", " ")

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            entry["classes"].append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                entry["functions"].append(node.name)
        elif isinstance(node, ast.Import):
            entry["imports"] += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            entry["imports"].append(node.module)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in _BUS_METHODS:
                ev = _event_name(node)
                if ev:
                    key = "publishes" if node.func.attr == "publish" else "subscribes"
                    entry[key].append(ev)
    return entry


def _rebuild_reverse_deps(files_index: dict) -> None:
    for entry in files_index.values():
        entry["reverse_deps"] = []
    for rel, entry in files_index.items():
        for imp in entry["imports"]:
            imp_path = imp.replace(".", "/") + ".py"
            if imp_path in files_index:
                files_index[imp_path]["reverse_deps"].append(rel)


def _load_or_build(root: Path, force: bool) -> dict:
    current = {str(p.relative_to(root)).replace("\\", "/"): p.stat().st_mtime
               for p in walk_py_files(root)}

    if not force and CACHE_PATH.exists():
        cached = json.loads(CACHE_PATH.read_text())
        old = cached["_meta"]["source_mtimes"]
        changed = {f for f, m in current.items() if old.get(f) != m}
        deleted = set(old) - set(current)
        if not changed and not deleted:
            return cached  # tidak ada yang berubah — pakai cache apa adanya

        files_index = cached["files"]
        for f in deleted:
            files_index.pop(f, None)
        for f in changed:                       # <- hanya file berubah di-reparse
            files_index[f] = _parse_file(root / f, root)
    else:
        files_index = {f: _parse_file(root / f, root) for f in current}

    _rebuild_reverse_deps(files_index)           # murah: invert dict, bukan AST
    data = {"_meta": {"generated_at": time.time(), "source_mtimes": current},
            "files": files_index}
    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(data, indent=2))
    return data


def build_index(root: Path) -> dict:
    """Full rebuild — abaikan cache lama."""
    return _load_or_build(root, force=True)


def load_index(root: Path) -> dict:
    """Load dari cache; reparse hanya file yang mtime-nya berubah."""
    return _load_or_build(root, force=False)
```

**Definition of Done:**
- `find_owner.py`, `generate_file_index.py`, `generate_report.py` migrasi baca dari
  index ini (tidak re-scan sendiri)
- `.cache/repo_index.json` muncul setelah run pertama
- Ubah 1 file source lalu jalankan lagi → hanya file itu yang di-reindex

---

## Fase 2 — Event & Call Intelligence

### 2.1 `event_graph.py`

**Masalah:** Event flow (EventBus/CommandBus, ADR-0004/0005) tidak terlihat padahal
tiap docstring modul sudah punya field `Subscribes to:`/`Publishes:`.

**Solusi:** Baca `publishes`/`subscribes` per file yang sudah dideteksi `repo_index`,
lalu invert jadi peta `event_name → {publishers, subscribers}` — tool ini sendiri
tidak perlu AST-walk lagi, tinggal konsumsi index.

```python
"""
Module: automation.event_graph

Purpose:
    Peta event_name -> {publishers, subscribers} dari EventBus, dibangun dari
    hasil AST-detect repo_index (bukan docstring).

CLI:
    python automation/event_graph.py [--event <nama>] [--json]
"""

import argparse, json
from pathlib import Path
from automation.shared.repo_index import load_index


def build_event_graph(root: Path) -> dict:
    index = load_index(root)["files"]
    graph: dict[str, dict[str, list[str]]] = {}
    for rel, entry in index.items():
        for ev in entry.get("publishes", []):
            graph.setdefault(ev, {"publishers": [], "subscribers": []})["publishers"].append(rel)
        for ev in entry.get("subscribes", []):
            graph.setdefault(ev, {"publishers": [], "subscribers": []})["subscribers"].append(rel)
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", help="Filter satu nama event, mis. DownloadCompleteEvent")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent

    graph = build_event_graph(root)
    if args.event:
        graph = {args.event: graph.get(args.event, {"publishers": [], "subscribers": []})}

    if args.json_output:
        print(json.dumps(graph, indent=2))
        return
    for event, info in sorted(graph.items()):
        print(f"\n{event}")
        print(f"  publishers  : {', '.join(info['publishers']) or '(tidak ditemukan)'}")
        print(f"  subscribers : {', '.join(info['subscribers']) or '(tidak ada)'}")


if __name__ == "__main__":
    main()
```

**Definition of Done:** Tanpa argumen → peta lengkap semua event di repo; `--event
<nama>` memfilter satu event; `--json` menghasilkan JSON valid selaras skema checker
lain.

### 2.2 `call_graph.py` (Prioritas Rendah)

**Masalah:** Tidak ada peta pemanggilan tingkat fungsi — `find_owner.py` hanya
tingkat modul/import.

**Solusi:** Scan on-demand per nama fungsi (bukan simpan full call-graph
semua×semua fungsi di `repo_index` — terlalu besar untuk index yang dibaca semua
tool lain). Keterbatasan yang disengaja: matching berdasar nama saja, bisa
false-positive kalau 2 fungsi di file berbeda kebetulan sama nama — cukup untuk
tool prioritas rendah ini, jangan investasi resolusi scope lebih jauh sebelum ada
kebutuhan nyata.

```python
"""
Module: automation.call_graph

Purpose:
    Cari caller & callee dari 1 nama fungsi, scan AST on-demand (bukan
    disimpan di repo_index — call-graph lengkap semua-fungsi terlalu besar).

CLI:
    python automation/call_graph.py <function_name> [--json]
"""

import argparse, ast, json
from pathlib import Path
from automation.shared.skip_dirs import walk_py_files


def find_callers(root: Path, target: str) -> list[str]:
    callers = []
    for path in walk_py_files(root):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            name = None
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
            if name == target:
                callers.append(str(path.relative_to(root)).replace("\\", "/"))
                break
    return sorted(set(callers))


def find_callees(root: Path, target: str) -> list[str]:
    for path in walk_py_files(root):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == target:
                callees = {n.func.id for n in ast.walk(node)
                           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
                return sorted(callees)
    return []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("function_name")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent

    result = {
        "function": args.function_name,
        "callers": find_callers(root, args.function_name),
        "callees": find_callees(root, args.function_name),
    }
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{result['function']}")
        print(f"  dipanggil oleh : {', '.join(result['callers']) or '(tidak ditemukan)'}")
        print(f"  memanggil      : {', '.join(result['callees']) or '(tidak ada)'}")


if __name__ == "__main__":
    main()
```

**Definition of Done:** Query 1 nama fungsi menghasilkan list caller & callee;
`--json` valid.

---

## Fase 3 — Impact & Testing Intelligence

### 3.1 `test_locator.py`

**Masalah:** Tidak ada pemetaan source ↔ test dua arah (pernah manual sekali di
`cleanup_tests.py`, hardcoded, tidak reusable).

**Solusi:** Konvensi penamaan di repo ini sudah konsisten:
`tests/unit/<subpath>/test_<nama>.py` selalu mirror `<subpath>/<nama>.py` — terlihat
langsung dari struktur folder `tests/unit/` yang persis mengikuti struktur source
per-layer. Manfaatkan itu langsung, tidak perlu heuristic yang lebih rumit.

```python
"""
Module: automation.test_locator

Purpose:
    Petakan source <-> test dua arah via konvensi path-mirroring
    tests/unit/<subpath>/test_<nama>.py <-> <subpath>/<nama>.py.

CLI:
    python automation/test_locator.py --for <file>
    python automation/test_locator.py --orphan
"""

import argparse, json
from pathlib import Path
from automation.shared.skip_dirs import walk_py_files

TEST_ROOT = Path("tests/unit")
SKIP_PREFIXES = ("tests/", "automation/", "scratch/", "data/")


def find_test_for(root: Path, rel_source: str) -> Path | None:
    parts = Path(rel_source).parts
    candidate = root / TEST_ROOT.joinpath(*parts[:-1], f"test_{parts[-1]}")
    return candidate if candidate.exists() else None


def find_orphans(root: Path) -> list[str]:
    orphans = []
    for path in walk_py_files(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        if rel.startswith(SKIP_PREFIXES) or "__init__" in rel:
            continue
        if find_test_for(root, rel) is None:
            orphans.append(rel)
    return sorted(orphans)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--for", dest="target")
    group.add_argument("--orphan", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent

    if args.orphan:
        result = find_orphans(root)
    else:
        test = find_test_for(root, args.target)
        result = {"source": args.target, "test": str(test.relative_to(root)) if test else None}

    print(json.dumps(result, indent=2) if args.json_output else result)


if __name__ == "__main__":
    main()
```

**Definition of Done:** `--for` pada file yang sudah diketahui test-nya mengembalikan
path yang benar; `--orphan` tidak menghasilkan false-positive pada sample manual check.

### 3.2 `patchlog.py`

**Masalah:** `docs/PATCHLOG.md` ditulis manual, rawan salah ID/urutan/frontmatter;
baca histori 1 file harus scroll ratusan baris.

**Solusi:** `NNN` di ID **bukan** reset per hari — dikonfirmasi dari frontmatter
`PATCHLOG.md` saat ini (`latest_patch_id: PATCH-2026-07-13-037` sejalan dengan
`total_entries: 37`), jadi tinggal `len(entries) + 1`. Entry baru disisip di atas
(newest-first); entry lama dibiarkan apa adanya sampai dimigrasi manual. Perhatikan:
baris `**File Terdampak:**` di entry lama kadang punya teks tambahan sebelum daftar
bertitik (mis. "33 file total. File signifikan:") — regex parsing harus non-greedy
skip teks itu, bukan asumsi baris kosong langsung diikuti bullet.

```python
"""
Module: automation.patchlog

Purpose:
    Baca/tulis docs/PATCHLOG.md terstruktur. ID PATCH-YYYY-MM-DD-NNN, NNN = total
    entries berjalan (bukan reset per hari).

CLI:
    python automation/patchlog.py add "<deskripsi>" --files a.py,b.py
    python automation/patchlog.py latest --n 5 [--json]
    python automation/patchlog.py history --file <path> [--json]
"""

import argparse, json, re
from datetime import date
from pathlib import Path

PATCHLOG = Path("docs/PATCHLOG.md")

ENTRY_RE = re.compile(
    r"\*\*ID:\*\* `(?P<id>PATCH-[\d-]+)`.*?"
    r"\*\*Tanggal:\*\* (?P<tanggal>[\d-]+).*?"
    r"\*\*Ringkasan:\*\* (?P<ringkasan>.+?)\n.*?"
    r"\*\*File Terdampak:\*\*.*?\n\n(?P<files>(?:- .+\n?)+)",
    re.DOTALL,
)


def parse_entries(text: str) -> list[dict]:
    entries = []
    for m in ENTRY_RE.finditer(text):
        files = re.findall(r"- `([^`]+)`", m.group("files"))
        entries.append({"id": m.group("id"), "tanggal": m.group("tanggal"),
                         "ringkasan": m.group("ringkasan").strip(), "files": files})
    return entries


def add_entry(desc: str, files: list[str]) -> str:
    text = PATCHLOG.read_text(encoding="utf-8")
    entries = parse_entries(text)
    new_id = f"PATCH-{date.today().isoformat()}-{len(entries) + 1:03d}"
    files_block = "\n".join(f"- `{f}`" for f in files)
    block = (
        f"\n## [{date.today().isoformat()}] {desc}\n\n"
        f"**ID:** `{new_id}`\n\n**Tanggal:** {date.today().isoformat()}\n\n"
        f"**Ringkasan:** {desc}\n\n**File Terdampak:**\n\n{files_block}\n\n---\n"
    )
    marker = "---\n\n"                       # tepat setelah blockquote format-notice
    idx = text.index(marker) + len(marker)
    new_text = text[:idx] + block + text[idx:]
    new_text = re.sub(r"latest_patch_id:.*", f"latest_patch_id: {new_id}", new_text, count=1)
    new_text = re.sub(r"total_entries:.*", f"total_entries: {len(entries) + 1}", new_text, count=1)
    PATCHLOG.write_text(new_text, encoding="utf-8")
    return new_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("description")
    p_add.add_argument("--files", required=True, help="Comma-separated")

    p_latest = sub.add_parser("latest")
    p_latest.add_argument("--n", type=int, default=5)
    p_latest.add_argument("--json", action="store_true", dest="json_output")

    p_hist = sub.add_parser("history")
    p_hist.add_argument("--file", required=True)
    p_hist.add_argument("--json", action="store_true", dest="json_output")

    args = parser.parse_args()

    if args.cmd == "add":
        print(f"Ditambahkan: {add_entry(args.description, args.files.split(','))}")
        return

    entries = parse_entries(PATCHLOG.read_text(encoding="utf-8"))
    result = entries[:args.n] if args.cmd == "latest" else \
             [e for e in entries if args.file in e["files"]]
    print(json.dumps(result, indent=2) if args.json_output else result)


if __name__ == "__main__":
    main()
```

**Definition of Done:** `add` menghasilkan entry dengan ID unik berurut benar;
`latest`/`history` cocok dengan isi `PATCHLOG.md`; `verify_docs.py` tetap PASS.

### 3.3 `impact.py`

**Masalah:** Tidak ada cara cepat menaksir blast radius sebelum refactor/hapus file;
`find_owner.py` hanya 1-hop statis.

**Solusi:** Sisi event WAJIB ikut dihitung, bukan sekadar nice-to-have: docstring
`core/event_bus.py` sendiri bilang tujuan EventBus adalah supaya modul **tidak**
saling import langsung — justru untuk menghindari circular import. Artinya
reverse-dep berbasis-import saja **pasti** melewatkan subscriber yang paling rawan
ke-broke kalau kontrak event berubah. Resolusi `<file_or_symbol>` yang berupa nama
class/fungsi (bukan path) memakai ulang `resolve_target()` dari `find_owner.py`,
tidak perlu ditulis ulang.

```python
"""
Module: automation.impact

Purpose:
    Blast radius sebelum refactor/hapus: reverse-dep transitif (import graph)
    DIGABUNG reverse-dep via event bus (subscriber dari event yang dipublish
    file target) — sisi event wajib, bukan opsional (lihat rationale di atas).

CLI:
    python automation/impact.py <file_or_symbol> [--json]
"""

import argparse, json
from pathlib import Path
from automation.shared.repo_index import load_index
from automation.event_graph import build_event_graph
from automation.test_locator import find_test_for


def transitive_reverse_deps(index: dict, target: str) -> set[str]:
    seen, queue = set(), [target]
    while queue:
        current = queue.pop()
        for dep in index["files"].get(current, {}).get("reverse_deps", []):
            if dep not in seen:
                seen.add(dep)
                queue.append(dep)
    return seen


def event_impacted(index: dict, graph: dict, target: str) -> set[str]:
    published = index["files"].get(target, {}).get("publishes", [])
    impacted = set()
    for ev in published:
        impacted.update(graph.get(ev, {}).get("subscribers", []))
    return impacted


def compute_impact(root: Path, target: str) -> dict:
    index = load_index(root)
    graph = build_event_graph(root)

    via_import = transitive_reverse_deps(index, target)
    via_event = event_impacted(index, graph, target)

    tests = set()
    for f in via_import | via_event | {target}:
        t = find_test_for(root, f)
        if t:
            tests.add(str(t.relative_to(root)))

    return {
        "target": target,
        "impacted_via_import": sorted(via_import),
        "impacted_via_event": sorted(via_event),
        "related_tests": sorted(tests),
        "risk_score": len(via_import) + 2 * len(via_event),  # event dibobot 2x
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file_or_symbol")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    result = compute_impact(root, args.file_or_symbol)
    print(json.dumps(result, indent=2) if args.json_output else result)


if __name__ == "__main__":
    main()
```

**Definition of Done:** Uji pada 1 file berdependensi banyak → reverse-dep lebih dari
1-hop; skor risiko konsisten (reverse-dep lebih banyak = skor lebih tinggi).

### 3.4 `hotspot.py`

**Masalah:** Tidak ada cara memprioritaskan file paling berisiko/sering berubah.

**Solusi:** Sengaja pakai reverse-dep **1-hop** dari `repo_index` (bukan transitif ala
`impact.py`) — hotspot menghitung skor untuk SEMUA file sekaligus, jadi transitif per
file akan terlalu mahal dijalankan berulang-ulang untuk seluruh repo. Reuse
`parse_entries()` dari `patchlog.py` langsung, jangan tulis parser PATCHLOG kedua.

```python
"""
Module: automation.hotspot

Purpose:
    Ranking file paling berisiko: skor = churn (jumlah kemunculan di
    PATCHLOG.md) x sentralitas (reverse-dep 1-hop dari repo_index).

CLI:
    python automation/hotspot.py [--top N] [--json]
"""

import argparse, json
from collections import Counter
from pathlib import Path
from automation.shared.repo_index import load_index
from automation.patchlog import parse_entries, PATCHLOG


def compute_hotspots(root: Path) -> list[dict]:
    index = load_index(root)["files"]
    entries = parse_entries(PATCHLOG.read_text(encoding="utf-8"))

    churn = Counter()
    for entry in entries:
        for f in entry["files"]:
            churn[f] += 1

    scored = []
    for rel, info in index.items():
        centrality = len(info.get("reverse_deps", []))
        c = churn.get(rel, 0)
        if c == 0 and centrality == 0:
            continue
        scored.append({"file": rel, "churn": c, "centrality": centrality,
                        "score": c * centrality})
    return sorted(scored, key=lambda x: x["score"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    result = compute_hotspots(root)[:args.top]
    print(json.dumps(result, indent=2) if args.json_output else result)


if __name__ == "__main__":
    main()
```

**Definition of Done:** `--top 5` menghasilkan 5 file terurut skor descending; skor
bisa direproduksi ulang dari data yang sama.

---

## Fase 4 — AI Ergonomics & Endpoint

### 4.1 `context_pack.py`

**Masalah:** AI agent harus memanggil 4–5 tool terpisah lalu menggabungkan manual —
boros token, rawan lupa satu aspek.

**Solusi:** Murni orkestrasi — import langsung fungsi dari tiap tool (bukan
subprocess ke masing-masing CLI, lebih cepat dan tidak fragile ke perubahan format
print). Ini sebabnya `get_owner_info()` di 0.4 harus jadi fungsi yang bisa di-import,
bukan cuma logic yang nempel di dalam `print()`.

```python
"""
Module: automation.context_pack

Purpose:
    Satu panggilan yang menggabungkan semua tool automation/ jadi 1 JSON —
    endpoint utama untuk AI agent supaya tidak perlu 5 panggilan terpisah.

CLI:
    python automation/context_pack.py <file_or_feature> --json
"""

import argparse, json
from pathlib import Path
from automation.find_owner import get_owner_info          # hasil refactor 0.4
from automation.shared.repo_index import load_index
from automation.event_graph import build_event_graph
from automation.test_locator import find_test_for
from automation.patchlog import parse_entries, PATCHLOG


def _status_lines_for(root: Path, target: str) -> list[str]:
    status = (root / "docs" / "STATUS.md").read_text(encoding="utf-8", errors="replace")
    return [line.strip() for line in status.splitlines() if target in line]


def build_context_pack(root: Path, target: str) -> dict:
    index = load_index(root)
    entry = index["files"].get(target, {})
    test = find_test_for(root, target)
    history = [e for e in parse_entries(PATCHLOG.read_text(encoding="utf-8"))
               if target in e["files"]]

    return {
        "target": target,
        "ownership": get_owner_info(target, root),
        "deps": entry.get("imports", []),
        "reverse_deps": entry.get("reverse_deps", []),
        "event_flow": {
            "publishes": entry.get("publishes", []),
            "subscribes": entry.get("subscribes", []),
        },
        "related_test": str(test.relative_to(root)) if test else None,
        "patchlog_history": history[:3],
        "status_notes": _status_lines_for(root, target),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file_or_feature")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    print(json.dumps(build_context_pack(root, args.file_or_feature), indent=2))


if __name__ == "__main__":
    main()
```

**Definition of Done:** 1 panggilan pada file contoh menghasilkan JSON berisi semua 5
komponen tanpa AI perlu panggil tool lain; didokumentasikan sebagai endpoint utama di
`AI_CONTEXT.md` (update section "Kontrak Output untuk AI Agent" — baris "belum ada"
diganti merujuk `context_pack.py`).

---

## Lampiran — Teks Siap Tempel untuk `AI_CONTEXT.md` (rujukan task 0.8)

**L1 — Judul section:**
```markdown
## Automation Tools

Project ini punya automation tooling di `automation/` untuk orientasi, validasi,
dan menjaga docs tetap sinkron — dipakai baik oleh developer manusia maupun AI
agent yang mengerjakan task di repo ini.
**Selalu gunakan ini sebelum membaca puluhan file secara manual.**
```

**L2 — Step "Alur kerja AI" (ganti step 4 di "Sebelum mulai"):**
```markdown
4. WAJIB jalankan `python automation/find_owner.py <target>` untuk orientasi cepat
   sebelum grep/baca manual — ini lebih murah token dan lebih akurat
```

**L3 — Section baru "Kontrak Output untuk AI Agent":**
```markdown
## Kontrak Output untuk AI Agent

Semua tool di `automation/` yang mendukung `--json` WAJIB dipanggil dengan flag
itu ketika dipanggil oleh AI agent (bukan manusia interaktif).

| Tugas | Tool | Mode AI (--json) |
|---|---|---|
| Cek kesehatan repo sebelum mulai | `automation/doctor.py` | belum ada agregasi JSON — panggil tiap checker satu-satu |
| Cari owner/dependency file/class/fungsi | `automation/find_owner.py` | tersedia sejak task 0.4 |
| Cek satu aspek spesifik | `verify_docs.py --json`, dst. | sudah ada |

Catatan: `doctor.py` saat ini hanya merender dashboard teks untuk manusia. Jika
kamu (AI agent) butuh hasil gabungan dalam JSON, panggil tiap checker satu-satu
dengan `--json`, bukan `doctor.py` — sampai `context_pack.py` (Fase 4) siap.
```

**L4 — Catatan migrasi sementara:**
```markdown
> **Catatan migrasi (hapus setelah Sprint 3.3):** folder `scripts/` telah
> di-rename menjadi `automation/` pada [tanggal]. Jika menemukan referensi
> `scripts/...` di file lain yang belum ter-update, laporkan sebagai
> dokumentasi stale — jangan asumsikan folder lama masih ada.
```

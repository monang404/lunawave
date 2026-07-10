#!/usr/bin/env python3
"""
verify_docs.py — Documentation Health Checker untuk LunaWave.

Purpose:
    Memeriksa kualitas dokumentasi project, bukan memvalidasi semua path
    yang tertulis di file Markdown. Fokus pada kondisi repository saat ini,
    bukan histori, roadmap, atau proposal refactor.

    Cek yang dijalankan: Documentation Structure, PATCHLOG, Frontmatter
    (termasuk owner opsional), Generated Sections, FILE_INDEX, REPORT,
    Documentation Coverage (file .py belum tercatat di FILE_INDEX/REPORT),
    Module Docstring Coverage, Large Files (>300 LOC), Empty Packages.

Subscribes to:
    docs/ filesystem, project .py files

Publishes:
    stdout (ringkasan, detail verbose, atau JSON)

Cara pakai:
    python scripts/verify_docs.py                # ringkasan
    python scripts/verify_docs.py --verbose      # detail lengkap
    python scripts/verify_docs.py --show-docstring   # file tanpa module docstring
    python scripts/verify_docs.py --show-large-files # file >300 LOC
    python scripts/verify_docs.py --json         # output JSON

Exit code: 0 = PASS / WARN,  1 = ada FAIL
"""

import argparse
import ast
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Konstanta & path default
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_DOCS_DIR = DEFAULT_PROJECT_ROOT / "docs"

PATCH_ID_RE = re.compile(r"\*\*ID:\*\*\s*`(PATCH-\d{4}-\d{2}-\d{2}-\d{3})`")
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
GENERATED_BEGIN_RE = re.compile(r"<!--\s*BEGIN:GENERATED\s*-->")
GENERATED_END_RE = re.compile(r"<!--\s*END:GENERATED\s*-->")

# Pattern untuk mengambil referensi path .py dari teks markdown
PY_REF_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_/\\.-]*\.py)")

NOISE_DIRS: frozenset[str] = frozenset({
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".tox", "dist", "build",
})

REQUIRED_DOCS = [
    "INDEX.md", "STATUS.md", "REPORT.md", "PATCHLOG.md",
    "FILE_INDEX.md", "STRUCTURE.md", "AI_CONTEXT.md",
]

# Docstring module wajib mengandung field-field ini
DOCSTRING_REQUIRED_FIELDS = ("Purpose:", "Subscribes to:", "Publishes:")

LARGE_FILE_THRESHOLD = 300   # LOC
STALE_DAYS_DEFAULT = 30
PREVIEW_COUNT = 3             # item ditampilkan sebelum "(+N more)"

# Dokumen yang di-skip dari cek frontmatter (dicek terpisah atau memang historis)
SKIP_FRONTMATTER = frozenset({"PATCHLOG.md"})

# __init__.py hanya dianggap "signifikan" (ikut divalidasi) kalau isinya lebih
# dari sekadar re-export/import kosong. Mengurangi false positive pada paket
# yang __init__.py-nya memang sengaja tipis.
INIT_FILENAME = "__init__.py"

# Bobot tiap cek terhadap skor akhir (total = 100). Cek yang berpengaruh
# langsung terhadap kebenaran/kelengkapan dokumentasi (Documentation
# Structure, PATCHLOG, FILE_INDEX, Documentation Coverage) diberi bobot jauh
# lebih besar dibanding cek kosmetik (Large Files, Empty Packages).
CHECK_WEIGHTS: dict[str, int] = {
    "Documentation Structure": 20,
    "PATCHLOG": 15,
    "FILE_INDEX": 15,
    "Documentation Coverage": 15,
    "Module Docstring": 12,
    "REPORT": 8,
    "Frontmatter": 8,
    "Generated Sections": 4,
    "Large Files": 2,
    "Empty Packages": 1,
}

# Untuk cek yang punya mode CLI khusus, warning selalu menyertakan hint
# perintah yang bisa langsung dijalankan developer.
CHECK_HINTS: dict[str, str] = {
    "Module Docstring": "python scripts/verify_docs.py --show-docstring",
    "Large Files": "python scripts/verify_docs.py --show-large-files",
}


# ---------------------------------------------------------------------------
# Model data
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name: str
    status: str          # "PASS" | "WARN" | "FAIL"
    message: str = ""    # satu baris keterangan
    items: list[str] = field(default_factory=list)
    current: int | None = None   # untuk cek bertipe "coverage": jumlah yang OK
    total: int | None = None     # untuk cek bertipe "coverage": jumlah total

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def percentage(self) -> int | None:
        if not self.total:
            return None
        return round(100 * (self.current or 0) / self.total)


# ---------------------------------------------------------------------------
# Utilitas
# ---------------------------------------------------------------------------

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> dict | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip()
    return fm


def collect_py_files(project_root: Path) -> list[Path]:
    """Kumpulkan semua .py file (relatif ke project_root), exclude noise dirs."""
    result: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in NOISE_DIRS]
        dp = Path(dirpath)
        for fn in filenames:
            if fn.endswith(".py"):
                result.append((dp / fn).relative_to(project_root))
    return sorted(result)


def count_lines(abs_path: Path) -> int:
    try:
        return len(read_text(abs_path).splitlines())
    except Exception:
        return 0


def get_module_docstring(abs_path: Path) -> str | None:
    """Ambil module-level docstring via AST. Return None jika tidak ada / syntax error."""
    try:
        tree = ast.parse(abs_path.read_text(encoding="utf-8", errors="replace"))
        return ast.get_docstring(tree)
    except SyntaxError:
        return None


def fmt_items(items: list[str], verbose: bool, indent: str = "  ") -> list[str]:
    """Format daftar item (dengan bullet) dan truncation opsional."""
    if not items:
        return []
    if verbose or len(items) <= PREVIEW_COUNT:
        return [f"{indent}• {it}" for it in items]
    shown = items[:PREVIEW_COUNT]
    rest = len(items) - PREVIEW_COUNT
    return [f"{indent}• {it}" for it in shown] + [f"{indent}(+{rest} more)"]


def is_significant_init(abs_path: Path) -> bool:
    """True jika __init__.py berisi implementasi nyata (bukan cuma re-export
    kosong/`__all__`/import), sehingga layak ikut divalidasi seperti modul
    biasa. Ini mengurangi false positive dari paket yang sengaja punya
    __init__.py tipis."""
    try:
        source = abs_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return True  # gagal dibaca/parse -> aman diperlakukan sebagai signifikan

    body = tree.body
    if body and isinstance(body[0], ast.Expr) and isinstance(
        getattr(body[0], "value", None), ast.Constant
    ):
        body = body[1:]  # lewati module docstring

    for node in body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "__all__":
                continue
        return True  # ada statement lain (fungsi, class, logic, dst.)
    return False


def filter_ignorable_inits(
    py_files: list[Path], project_root: Path
) -> list[Path]:
    """Buang __init__.py yang tidak signifikan dari daftar file yang dicek.
    Dipakai oleh Module Docstring, Documentation Coverage, dan FILE_INDEX
    supaya __init__.py kosong/re-export tidak jadi false positive."""
    return [
        p for p in py_files
        if not (p.name == INIT_FILENAME and not is_significant_init(project_root / p))
    ]


# ---------------------------------------------------------------------------
# Cek 1 — Struktur docs/
# ---------------------------------------------------------------------------

def check_docs_structure(docs_dir: Path) -> CheckResult:
    missing = [f"docs/{doc}" for doc in REQUIRED_DOCS if not (docs_dir / doc).exists()]
    if missing:
        return CheckResult(
            "Documentation Structure", "FAIL",
            f"{len(missing)} file wajib tidak ditemukan", missing,
        )
    return CheckResult(
        "Documentation Structure", "PASS",
        f"{len(REQUIRED_DOCS)} file wajib hadir",
    )


# ---------------------------------------------------------------------------
# Cek 2 — PATCHLOG (ID unik, urutan, sinkron frontmatter)
# ---------------------------------------------------------------------------

def check_patchlog(docs_dir: Path) -> CheckResult:
    patchlog = docs_dir / "PATCHLOG.md"
    if not patchlog.exists():
        return CheckResult("PATCHLOG", "FAIL", "docs/PATCHLOG.md tidak ditemukan")

    text = read_text(patchlog)
    ids = PATCH_ID_RE.findall(text)

    if not ids:
        return CheckResult(
            "PATCHLOG", "WARN",
            "Tidak ada entry dengan format PATCH-YYYY-MM-DD-NNN",
        )

    issues: list[str] = []

    # ID unik
    seen: set[str] = set()
    dupes: list[str] = []
    for pid in ids:
        if pid in seen:
            dupes.append(pid)
        seen.add(pid)
    if dupes:
        issues.append(f"ID duplikat: {', '.join(sorted(set(dupes)))}")

    # Urutan kronologis (ID berbasis tanggal → lexicographic sort sudah cukup)
    if ids != sorted(ids):
        issues.append("ID tidak berurutan kronologis")

    # Sinkron dengan frontmatter latest_patch_id
    fm = parse_frontmatter(text)
    if fm is None:
        issues.append("Frontmatter tidak ditemukan — latest_patch_id tidak bisa diverifikasi")
    else:
        latest_fm = fm.get("latest_patch_id", "")
        last_id = ids[-1]
        if not latest_fm:
            issues.append("Frontmatter tidak punya field 'latest_patch_id'")
        elif latest_fm != last_id:
            issues.append(
                f"latest_patch_id='{latest_fm}' tidak cocok dengan entry terakhir ('{last_id}')"
            )

    if issues:
        status = "FAIL" if dupes else "WARN"
        return CheckResult("PATCHLOG", status, "", issues)
    return CheckResult("PATCHLOG", "PASS", f"{len(ids)} entries, IDs unik & sinkron")


# ---------------------------------------------------------------------------
# Cek 3 — Frontmatter semua docs/*.md
# ---------------------------------------------------------------------------

def check_frontmatter(docs_dir: Path, stale_days: int) -> CheckResult:
    today = date.today()
    issues: list[str] = []
    checked = 0

    for f in sorted(docs_dir.glob("*.md")):
        if f.name in SKIP_FRONTMATTER:
            continue
        checked += 1
        text = read_text(f)
        rel = f"docs/{f.name}"
        fm = parse_frontmatter(text)

        if fm is None:
            issues.append(f"{rel}: tidak punya frontmatter")
            continue

        # Field wajib
        for req in ("title", "last_verified"):
            if req not in fm:
                issues.append(f"{rel}: field '{req}' tidak ditemukan")

        # Owner — opsional, tapi kalau ada tidak boleh kosong
        if "owner" in fm and not fm["owner"]:
            issues.append(f"{rel}: field 'owner' ada tapi kosong")

        # Validasi & freshness last_verified
        lv = fm.get("last_verified", "")
        if lv:
            try:
                lv_date = datetime.strptime(lv, "%Y-%m-%d").date()
                age = (today - lv_date).days
                if age < 0:
                    issues.append(f"{rel}: last_verified={lv} adalah tanggal masa depan")
                elif age > stale_days:
                    issues.append(
                        f"{rel}: last_verified={lv} sudah {age} hari lalu (ambang: {stale_days})"
                    )
            except ValueError:
                issues.append(f"{rel}: format last_verified='{lv}' tidak valid (harus YYYY-MM-DD)")

        # Validasi generated (kalau ada)
        gen = fm.get("generated", "")
        if gen and gen.lower() not in ("true", "false", "yes", "no", "manual"):
            issues.append(f"{rel}: nilai 'generated' tidak dikenali ('{gen}')")

    if not checked:
        return CheckResult("Frontmatter", "WARN", "Tidak ada file .md di docs/")
    if issues:
        return CheckResult("Frontmatter", "WARN", f"{len(issues)} issue(s)", issues)
    return CheckResult("Frontmatter", "PASS", f"{checked} file OK")


# ---------------------------------------------------------------------------
# Cek 4 — Generated Markers (BEGIN:GENERATED / END:GENERATED) di semua docs
# ---------------------------------------------------------------------------

def check_generated_blocks(docs_dir: Path) -> CheckResult:
    issues: list[str] = []

    for f in sorted(docs_dir.glob("*.md")):
        text = read_text(f)
        has_begin = bool(GENERATED_BEGIN_RE.search(text))
        has_end = bool(GENERATED_END_RE.search(text))
        rel = f"docs/{f.name}"

        if has_begin and not has_end:
            issues.append(f"{rel}: BEGIN:GENERATED ada, END:GENERATED hilang")
        elif has_end and not has_begin:
            issues.append(f"{rel}: END:GENERATED ada, BEGIN:GENERATED hilang")
        elif has_begin and has_end:
            begin_pos = GENERATED_BEGIN_RE.search(text).start()  # type: ignore[union-attr]
            end_pos = GENERATED_END_RE.search(text).start()      # type: ignore[union-attr]
            if begin_pos > end_pos:
                issues.append(f"{rel}: END:GENERATED muncul sebelum BEGIN:GENERATED")

    if issues:
        return CheckResult("Generated Sections", "WARN", f"{len(issues)} broken marker(s)", issues)
    return CheckResult("Generated Sections", "PASS", "Semua marker BEGIN/END lengkap")


# ---------------------------------------------------------------------------
# Cek 5 — FILE_INDEX (sinkron dengan .py di disk)
# ---------------------------------------------------------------------------

def check_file_index(docs_dir: Path, project_root: Path) -> CheckResult:
    fi_path = docs_dir / "FILE_INDEX.md"
    if not fi_path.exists():
        return CheckResult("FILE_INDEX", "FAIL", "docs/FILE_INDEX.md tidak ditemukan")

    fi_text = read_text(fi_path)
    actual_py = collect_py_files(project_root)
    checked_py = filter_ignorable_inits(actual_py, project_root)
    issues: list[str] = []

    # Semua .py aktual (di luar __init__.py yang tidak signifikan) harus
    # muncul di FILE_INDEX (nama file cukup, tidak harus path penuh)
    missing_from_index: list[str] = []
    for py_path in checked_py:
        py_str = str(py_path).replace("\\", "/")
        py_name = py_path.name
        if py_str not in fi_text and py_name not in fi_text:
            missing_from_index.append(py_str)

    for m in missing_from_index:
        issues.append(f"Belum ada di FILE_INDEX: {m}")

    # Entry di FILE_INDEX yang tidak ada di disk
    indexed_refs = {
        m.group(1).replace("\\", "/")
        for m in PY_REF_RE.finditer(fi_text)
    }
    actual_names = {p.name for p in actual_py}

    for ref in sorted(indexed_refs):
        ref_path = project_root / ref
        if not ref_path.exists() and Path(ref).name not in actual_names:
            issues.append(f"Entry di FILE_INDEX tidak ada di disk: {ref}")

    total = len(checked_py)
    current = total - len(missing_from_index)

    if issues:
        has_stale = any("tidak ada di disk" in i for i in issues)
        status = "FAIL" if has_stale else "WARN"
        result = CheckResult("FILE_INDEX", status, f"{len(issues)} issue(s)", issues)
    else:
        result = CheckResult("FILE_INDEX", "PASS", f"{total} file Python terdaftar")

    result.current = current
    result.total = total
    return result


# ---------------------------------------------------------------------------
# Cek 6 — REPORT (generated section valid)
# ---------------------------------------------------------------------------

def check_report(docs_dir: Path) -> CheckResult:
    path = docs_dir / "REPORT.md"
    if not path.exists():
        return CheckResult("REPORT", "FAIL", "docs/REPORT.md tidak ditemukan")

    text = read_text(path)
    has_begin = bool(GENERATED_BEGIN_RE.search(text))
    has_end = bool(GENERATED_END_RE.search(text))

    if has_begin and not has_end:
        return CheckResult("REPORT", "WARN", "BEGIN:GENERATED ada, END:GENERATED hilang")
    if has_end and not has_begin:
        return CheckResult("REPORT", "WARN", "END:GENERATED ada, BEGIN:GENERATED hilang")

    if has_begin and has_end:
        m_begin = GENERATED_BEGIN_RE.search(text)
        m_end = GENERATED_END_RE.search(text)
        if m_begin and m_end:
            inner = text[m_begin.end():m_end.start()].strip()
            if not inner:
                return CheckResult("REPORT", "WARN", "Generated section kosong (tidak ada konten)")

    return CheckResult("REPORT", "PASS", "Generated section valid")


# ---------------------------------------------------------------------------
# Cek 7 — Module Docstring Coverage
# ---------------------------------------------------------------------------

def check_module_docstrings(project_root: Path) -> CheckResult:
    py_files = filter_ignorable_inits(collect_py_files(project_root), project_root)
    missing: list[str] = []

    for py_rel in py_files:
        docstring = get_module_docstring(project_root / py_rel)
        rel_str = str(py_rel).replace("\\", "/")

        if not docstring:
            missing.append(f"{rel_str} (no module docstring)")
            continue

        # Cek field wajib — laporkan field mana saja yang hilang, bukan
        # sekadar "docstring tidak lengkap".
        missing_fields = [f for f in DOCSTRING_REQUIRED_FIELDS if f not in docstring]
        if missing_fields:
            missing.append(f"{rel_str} (missing: {', '.join(missing_fields)})")

    total = len(py_files)
    current = total - len(missing)
    result = CheckResult(
        "Module Docstring",
        "WARN" if missing else "PASS",
        f"{current}/{total} file OK" if missing else f"{total} file OK",
        missing,
    )
    result.current = current
    result.total = total
    return result


# ---------------------------------------------------------------------------
# Cek 8 — Documentation Coverage (file .py belum tercatat di FILE_INDEX atau REPORT)
# ---------------------------------------------------------------------------

def check_documentation_coverage(docs_dir: Path, project_root: Path) -> CheckResult:
    """File Python baru wajib disebut minimal di salah satu dari FILE_INDEX.md
    atau REPORT.md (cukup nama file, tidak harus path lengkap). Kalau tidak
    disebut di keduanya, berarti file itu belum terdokumentasi sama sekali."""
    fi_path = docs_dir / "FILE_INDEX.md"
    report_path = docs_dir / "REPORT.md"

    fi_text = read_text(fi_path) if fi_path.exists() else ""
    report_text = read_text(report_path) if report_path.exists() else ""

    py_files = filter_ignorable_inits(collect_py_files(project_root), project_root)
    missing: list[str] = []

    for py_rel in py_files:
        py_str = str(py_rel).replace("\\", "/")
        py_name = py_rel.name
        in_index = py_str in fi_text or py_name in fi_text
        in_report = py_str in report_text or py_name in report_text
        if not in_index and not in_report:
            missing.append(py_str)

    total = len(py_files)
    current = total - len(missing)
    result = CheckResult(
        "Documentation Coverage",
        "WARN" if missing else "PASS",
        f"{len(missing)} file belum disebut di FILE_INDEX maupun REPORT"
        if missing else f"{total} file terdokumentasi",
        missing,
    )
    result.current = current
    result.total = total
    return result


# ---------------------------------------------------------------------------
# Cek 9 — Large Files (>300 LOC)
# ---------------------------------------------------------------------------

def check_large_files(project_root: Path) -> CheckResult:
    py_files = collect_py_files(project_root)
    large: list[tuple[str, int]] = []

    for py_rel in py_files:
        n = count_lines(project_root / py_rel)
        if n > LARGE_FILE_THRESHOLD:
            large.append((str(py_rel).replace("\\", "/"), n))

    if large:
        large.sort(key=lambda x: -x[1])
        items = [f"{path} ({loc} LOC)" for path, loc in large]
        return CheckResult(
            "Large Files", "WARN",
            f"{len(large)} file >{LARGE_FILE_THRESHOLD} LOC", items,
        )
    return CheckResult("Large Files", "PASS", f"Semua file ≤{LARGE_FILE_THRESHOLD} LOC")


# ---------------------------------------------------------------------------
# Cek 10 — Empty Packages (hanya __init__.py kosong, tidak ada modul lain)
# ---------------------------------------------------------------------------

def check_empty_packages(project_root: Path) -> CheckResult:
    py_files = collect_py_files(project_root)
    py_set = set(py_files)

    # Kelompokkan per parent directory
    by_dir: dict[Path, list[Path]] = defaultdict(list)
    for p in py_files:
        by_dir[p.parent].append(p)

    empty_pkgs: list[str] = []

    for dir_path, files_in_dir in sorted(by_dir.items()):
        init_rel = dir_path / "__init__.py"
        if init_rel not in py_set:
            continue  # bukan package

        # Ada modul lain (selain __init__.py) di direktori ini?
        non_init = [f for f in files_in_dir if f.name != "__init__.py"]
        if non_init:
            continue

        # Ada file .py di subdirektori manapun?
        dir_parts = dir_path.parts
        has_sub_py = any(
            p
            for p in py_files
            if len(p.parts) > len(dir_parts) + 1
            and p.parts[: len(dir_parts)] == dir_parts
            and p.name != "__init__.py"
        )
        if has_sub_py:
            continue

        # __init__.py kontennya kosong/trivial?
        init_abs = project_root / init_rel
        try:
            content = init_abs.read_text(encoding="utf-8", errors="replace").strip()
            meaningful = [
                ln for ln in content.splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            ]
            if meaningful:
                continue
        except Exception:
            continue

        label = str(dir_path).replace("\\", "/") if dir_path != Path(".") else "."
        empty_pkgs.append(label)

    if empty_pkgs:
        return CheckResult(
            "Empty Packages", "WARN",
            f"{len(empty_pkgs)} package kosong ditemukan", empty_pkgs,
        )
    return CheckResult("Empty Packages", "PASS", "Tidak ada empty package")


# ---------------------------------------------------------------------------
# Render output
# ---------------------------------------------------------------------------

def _score(results: list[CheckResult]) -> int:
    """Skor berbobot: cek kritikal (Documentation Structure, PATCHLOG,
    FILE_INDEX, Documentation Coverage, ...) menentukan skor jauh lebih besar
    dibanding cek kosmetik (Large Files, Empty Packages). Untuk cek bertipe
    coverage (punya current/total), WARN diberi kredit parsial proporsional
    terhadap persentase yang sudah OK, bukan hukuman flat."""
    total_weight = sum(CHECK_WEIGHTS.get(r.name, 0) for r in results) or 1
    earned = 0.0

    for r in results:
        weight = CHECK_WEIGHTS.get(r.name, 0)
        if r.status == "PASS":
            earned += weight
        elif r.status == "FAIL":
            earned += 0.0
        else:  # WARN
            if r.total:
                ratio = (r.current or 0) / r.total
            else:
                ratio = 0.5
            earned += weight * ratio

    return round(100 * earned / total_weight)


def _overall_status(results: list[CheckResult]) -> str:
    if any(r.status == "FAIL" for r in results):
        return "FAIL"
    if any(r.status == "WARN" for r in results):
        return "WARN"
    return "PASS"


def render_summary(results: list[CheckResult], verbose: bool) -> None:
    pass_results = [r for r in results if r.status == "PASS"]
    non_pass = [r for r in results if r.status != "PASS"]
    coverage_results = [r for r in results if r.total]
    status = _overall_status(results)
    score = _score(results)

    bar = "=" * 50

    print(bar)
    print("Documentation Health")
    print(bar)
    print()
    print("Repository")
    print(status)

    print()
    print("Score")
    print(f"{score} / 100")

    if coverage_results:
        print()
        print("Coverage")
        for r in coverage_results:
            print()
            print(r.name)
            print(f"{r.current} / {r.total} ({r.percentage}%)")

    if non_pass:
        print()
        print("Warnings")
        for r in non_pass:
            print()
            print(f"{r.name} ({r.count})" if r.count else f"{r.name}")
            if r.items:
                for line in fmt_items(r.items, verbose):
                    print(line)
            elif r.message:
                print(f"  • {r.message}")
            hint = CHECK_HINTS.get(r.name)
            if hint and r.count:
                print("Hint:")
                print(f"  {hint}")

    if pass_results:
        print()
        print("Passed")
        print()
        for r in pass_results:
            print(f"\u2714 {r.name}")

    print()
    print(bar)
    print(f"Status: {status}")
    print(bar)


def render_json(results: list[CheckResult]) -> None:
    warn_count = sum(1 for r in results if r.status == "WARN")
    fail_count = sum(1 for r in results if r.status == "FAIL")
    pass_count = sum(1 for r in results if r.status == "PASS")
    data = {
        "repository_status": _overall_status(results),
        "score": _score(results),
        "pass": pass_count,
        "warn": warn_count,
        "fail": fail_count,
        "checks": [
            {
                "name": r.name,
                "status": r.status,
                "message": r.message,
                "count": r.count,
                "items": r.items,
                "current": r.current,
                "total": r.total,
                "percentage": r.percentage,
                "weight": CHECK_WEIGHTS.get(r.name),
            }
            for r in results
        ],
    }
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _run_all_checks(docs_dir: Path, project_root: Path, stale_days: int) -> list[CheckResult]:
    return [
        check_docs_structure(docs_dir),
        check_patchlog(docs_dir),
        check_frontmatter(docs_dir, stale_days),
        check_generated_blocks(docs_dir),
        check_file_index(docs_dir, project_root),
        check_report(docs_dir),
        check_documentation_coverage(docs_dir, project_root),
        check_module_docstrings(project_root),
        check_large_files(project_root),
        check_empty_packages(project_root),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Documentation Health Checker untuk LunaWave.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--docs-dir", default=str(DEFAULT_DOCS_DIR),
        help="Folder docs (default: dihitung dari lokasi script ini, bukan cwd)",
    )
    parser.add_argument(
        "--project-root", default=str(DEFAULT_PROJECT_ROOT),
        help="Root project (default: parent dari folder scripts/)",
    )
    parser.add_argument(
        "--stale-days", type=int, default=STALE_DAYS_DEFAULT,
        help=f"Ambang hari sebelum last_verified dianggap basi (default: {STALE_DAYS_DEFAULT})",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Tampilkan seluruh detail item tanpa truncation",
    )
    parser.add_argument(
        "--show-docstring", action="store_true",
        help="Hanya tampilkan daftar file yang belum punya module docstring standar",
    )
    parser.add_argument(
        "--show-large-files", action="store_true",
        help=f"Hanya tampilkan file Python >{LARGE_FILE_THRESHOLD} LOC",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output JSON (cocok untuk CI atau integrasi tool lain)",
    )
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir).resolve()
    project_root = Path(args.project_root).resolve()

    if not docs_dir.exists():
        print(f"FAIL  Folder docs tidak ditemukan: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    # --- Mode khusus (single-check, tidak tampilkan keseluruhan) ---

    if args.show_docstring:
        result = check_module_docstrings(project_root)
        if result.status == "PASS":
            print("Semua file Python sudah punya module docstring lengkap.")
        else:
            print(f"File tanpa module docstring standar ({result.count}):")
            for item in result.items:
                print(f"  {item}")
        sys.exit(0)

    if args.show_large_files:
        result = check_large_files(project_root)
        if result.status == "PASS":
            print(f"Semua file Python ≤{LARGE_FILE_THRESHOLD} LOC.")
        else:
            print(f"File >{LARGE_FILE_THRESHOLD} LOC ({result.count}):")
            for item in result.items:
                print(f"  {item}")
        sys.exit(0)

    # --- Mode normal: jalankan semua cek ---

    results = _run_all_checks(docs_dir, project_root, args.stale_days)

    if args.json_output:
        render_json(results)
    else:
        render_summary(results, verbose=args.verbose)

    has_fail = any(r.status == "FAIL" for r in results)
    sys.exit(1 if has_fail else 0)


if __name__ == "__main__":
    main()

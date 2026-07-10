#!/usr/bin/env python3
"""
architecture_lint.py — Validasi batas arsitektur berdasarkan aturan di
docs/kompas/architecture/dependency_rules.md.

Cara pakai:
    python scripts/architecture_lint.py              # cek seluruh project
    python scripts/architecture_lint.py --file config.py   # cek 1 file saja
    python scripts/architecture_lint.py --strict     # exit 1 jika ada violation (default untuk pre-commit)

Exit code:
    0  — tidak ada violation
    1  — ada violation

Cocok dipasang sebagai pre-commit hook (lihat .pre-commit-config.yaml).
"""

import argparse
import ast
import os
import sys

# Fix Unicode output di Windows (cp1252 tidak support emoji/karakter UTF-8)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".mypy_cache"}

# ---------------------------------------------------------------------------
# Aturan dependency — direpresentasikan dari dependency_rules.md
# Kunci: layer yang mengimport. Nilai: set layer yang BOLEH diimport.
# ---------------------------------------------------------------------------
ALLOWED: dict[str, set[str]] = {
    "core":        set(),                                               # tidak boleh import siapapun
    "adapters":    {"core"},
    "persistence": {"core"},
    "plugins":     {"core"},
    "engine":      {"core", "adapters", "persistence"},
    "services":    {"core", "persistence"},
    "server":      {"core", "engine", "services", "persistence"},
    "launcher":    {"core", "server"},
    # Folder ini tidak dalam aturan hexagonal — diberi kebebasan penuh
    "data":        None,
    "scripts":     None,
    "cache":       {"core"},  # cache/ ekuivalen persistence/ sebelum pindah
}

# Mapping path -> layer
def path_to_layer(rel_path: str) -> str | None:
    """Ambil layer dari path relatif project (misal 'core/state.py' -> 'core')."""
    parts = rel_path.replace("\\", "/").split("/")
    if not parts:
        return None
    top = parts[0]
    return top if top in ALLOWED else None


def module_to_layer(module: str) -> str | None:
    """Ambil layer dari nama module (misal 'core.state' -> 'core')."""
    top = module.split(".")[0]
    return top if top in ALLOWED else None


# ---------------------------------------------------------------------------
# Violation dataclass
# ---------------------------------------------------------------------------

@dataclass
class Violation:
    file: str
    line: int
    importer_layer: str
    imported_module: str
    imported_layer: str

    def __str__(self) -> str:
        return (
            f"  {self.file}:{self.line}\n"
            f"    ↳ `{self.importer_layer}/` tidak boleh import dari `{self.imported_layer}/`\n"
            f"      import: {self.imported_module}"
        )


# ---------------------------------------------------------------------------
# Per-file check
# ---------------------------------------------------------------------------

def check_file(path: Path, project_root: Path) -> list[Violation]:
    rel = str(path.relative_to(project_root)).replace("\\", "/")
    importer_layer = path_to_layer(rel)

    if importer_layer is None:
        return []  # File di root atau layer tidak dikenal — skip

    allowed_for_layer = ALLOWED.get(importer_layer)
    if allowed_for_layer is None:
        return []  # Layer tanpa aturan (data/, scripts/) — bebas

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_layer = module_to_layer(alias.name)
                if imported_layer and imported_layer != importer_layer:
                    if imported_layer not in allowed_for_layer:
                        violations.append(Violation(
                            file=rel,
                            line=node.lineno,
                            importer_layer=importer_layer,
                            imported_module=alias.name,
                            imported_layer=imported_layer,
                        ))

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_layer = module_to_layer(node.module)
                if imported_layer and imported_layer != importer_layer:
                    if imported_layer not in allowed_for_layer:
                        violations.append(Violation(
                            file=rel,
                            line=node.lineno,
                            importer_layer=importer_layer,
                            imported_module=node.module,
                            imported_layer=imported_layer,
                        ))

    return violations


# ---------------------------------------------------------------------------
# Scan seluruh project
# ---------------------------------------------------------------------------

def scan_project(project_root: Path, target_file: str | None = None) -> list[Violation]:
    all_violations = []

    if target_file:
        path = (project_root / target_file).resolve()
        if not path.exists():
            print(f"❌ File tidak ditemukan: {path}", file=sys.stderr)
            sys.exit(1)
        return check_file(path, project_root)

    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                path = Path(dirpath) / fn
                all_violations.extend(check_file(path, project_root))

    return all_violations


# ---------------------------------------------------------------------------
# Report known violations (dari REPORT.md) — untuk suppress di pre-commit
# jika user memilih --warn-only
# ---------------------------------------------------------------------------

KNOWN_VIOLATIONS = {
    # F-06 dari REPORT.md — sudah terdokumentasi, belum di-fix (target Sprint 4)
    ("config.py", "core"),
    # cache/ belum dipindah ke persistence/ — engine & services boleh import cache/
    # selama migrasi belum selesai (target Sprint 4-5, lihat STATUS.md & MIGRATION_GUIDE.md)
    ("engine/playback/track_loader.py", "cache"),
    ("engine/playback/controller.py",   "cache"),
    ("services/discover_service.py",    "cache"),
}

def is_known(v: Violation) -> bool:
    return (v.file, v.imported_layer) in KNOWN_VIOLATIONS


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validasi batas arsitektur LunaWave.")
    parser.add_argument("--file", help="Cek hanya 1 file (path relatif dari project root)")
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print violations tapi exit 0 (untuk mode informational, bukan blocking)",
    )
    parser.add_argument(
        "--show-known",
        action="store_true",
        help="Tampilkan juga known/documented violations (default: suppress)",
    )
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    violations = scan_project(root, args.file)

    new_violations = [v for v in violations if not is_known(v)]
    known_violations = [v for v in violations if is_known(v)]

    if not violations:
        print("✅ architecture_lint: tidak ada violation.")
        sys.exit(0)

    has_new = len(new_violations) > 0

    if new_violations:
        print(f"\n❌ architecture_lint: {len(new_violations)} VIOLATION BARU ditemukan!\n")
        for v in new_violations:
            print(str(v))
        print()

    if known_violations and args.show_known:
        print(f"\n⚠️  {len(known_violations)} known violation (sudah terdokumentasi di REPORT.md, belum di-fix):\n")
        for v in known_violations:
            print(str(v))
        print()
    elif known_violations and not args.show_known:
        print(
            f"ℹ️  {len(known_violations)} known violation diabaikan "
            f"(tambah --show-known untuk lihat). Lihat REPORT.md §F-06."
        )

    if args.warn_only:
        sys.exit(0)
    elif has_new:
        print(
            "💡 Tips: Jika violation ini disengaja (temporary), tambahkan ke KNOWN_VIOLATIONS\n"
            "   di scripts/architecture_lint.py dan dokumentasikan di REPORT.md.\n"
            "   Untuk skip pre-commit sementara: git commit --no-verify"
        )
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
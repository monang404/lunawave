#!/usr/bin/env python3
"""
doctor.py — Laporan kesehatan project LunaWave secara menyeluruh.

Cara pakai:
    python scripts/doctor.py
    python scripts/doctor.py --strict    # exit 1 jika ada masalah ❌

Cek yang dijalankan:
    1. verify_docs.py    — PATCHLOG, frontmatter, referensi path
    2. architecture_lint — import boundary violations
    3. Big file check    — file Python >200 baris
    4. Empty/pending     — rfc/ kosong, CONSTRAINTS.md belum ada
    5. Security          — admin_password.txt ada di .gitignore?
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

OK    = "✅"
WARN  = "⚠️ "
ERROR = "❌"
INFO  = "ℹ️ "

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv"}

results: list[tuple[str, str]] = []  # (level, message)


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def run_script(script: str, extra_args: list[str] = []) -> tuple[int, str]:
    """Jalankan script lain dan kembalikan (returncode, combined output)."""
    cmd = [sys.executable, str(SCRIPT_DIR / script)] + extra_args
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        output = (proc.stdout + proc.stderr).strip()
        return proc.returncode, output
    except Exception as e:
        return 1, str(e)


# ---------------------------------------------------------------------------
# Check 1: verify_docs.py
# ---------------------------------------------------------------------------

def check_docs() -> None:
    section("1. Dokumentasi (PATCHLOG, frontmatter, referensi path)")
    rc, output = run_script("verify_docs.py")
    print(output)
    if rc != 0:
        results.append((ERROR, "verify_docs: ada error fatal di dokumentasi"))
    elif "⚠️" in output:
        results.append((WARN, "verify_docs: ada peringatan dokumentasi"))
    else:
        results.append((OK, "verify_docs: semua bersih"))


# ---------------------------------------------------------------------------
# Check 2: architecture_lint.py
# ---------------------------------------------------------------------------

def check_architecture() -> None:
    section("2. Arsitektur (import boundary)")
    rc, output = run_script("architecture_lint.py", ["--show-known"])
    print(output)
    if rc != 0:
        results.append((ERROR, "architecture_lint: ada violation baru"))
    elif "known violation" in output:
        results.append((WARN, "architecture_lint: ada known violation belum di-fix (lihat REPORT.md)"))
    else:
        results.append((OK, "architecture_lint: boundaries bersih"))


# ---------------------------------------------------------------------------
# Check 3: file besar
# ---------------------------------------------------------------------------

def check_big_files() -> None:
    section("3. File Python Besar (>200 baris)")
    import os

    big = []
    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                path = Path(dirpath) / fn
                try:
                    n = sum(1 for _ in path.open(encoding="utf-8", errors="replace"))
                    if n > 200:
                        rel = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
                        big.append((rel, n))
                except Exception:
                    pass

    big.sort(key=lambda x: -x[1])

    if not big:
        print("  Semua file Python di bawah 200 baris.")
        results.append((OK, "big-files: semua file di bawah 200 baris"))
    else:
        critical = [(r, n) for r, n in big if n > 350]
        for rel, n in big:
            flag = "❌" if n > 350 else "⚠️ "
            print(f"  {flag}  {rel} ({n} baris)")
        if critical:
            results.append((ERROR, f"big-files: {len(critical)} file kritis (>350 baris) perlu dipecah"))
        else:
            results.append((WARN, f"big-files: {len(big)} file antara 200–350 baris — perhatikan"))


# ---------------------------------------------------------------------------
# Check 4: pending docs
# ---------------------------------------------------------------------------

def check_pending_docs() -> None:
    section("4. Dokumen Pending")

    issues = []

    # CONSTRAINTS.md disebut di STATUS.md tapi belum ada
    constraints = PROJECT_ROOT / "docs" / "CONSTRAINTS.md"
    if not constraints.exists():
        print(f"  {WARN}  docs/CONSTRAINTS.md belum dibuat (disebut di STATUS.md §Sprint 3.3)")
        issues.append("CONSTRAINTS.md belum ada")
    else:
        print(f"  {OK}  docs/CONSTRAINTS.md ada")

    # rfc/ — folder kosong
    rfc_dir = PROJECT_ROOT / "docs" / "kompas" / "rfc"
    if rfc_dir.exists():
        rfc_files = list(rfc_dir.glob("*.md"))
        if not rfc_files:
            print(f"  {WARN}  docs/kompas/rfc/ kosong — isi atau hapus (disebut di STATUS.md)")
            issues.append("rfc/ kosong")
        else:
            print(f"  {OK}  docs/kompas/rfc/ ada {len(rfc_files)} dokumen")
    else:
        print(f"  {INFO}  docs/kompas/rfc/ tidak ditemukan")

    # launcher/updater.py masih stub?
    updater = PROJECT_ROOT / "launcher" / "updater.py"
    if updater.exists():
        content = updater.read_text(encoding="utf-8", errors="replace")
        if "pass" in content and len(content) < 500:
            print(f"  {WARN}  launcher/updater.py masih stub — belum diimplementasi")
            issues.append("updater.py masih stub")
        else:
            print(f"  {OK}  launcher/updater.py ada implementasi")

    if issues:
        results.append((WARN, f"pending-docs: {len(issues)} item pending — " + ", ".join(issues)))
    else:
        results.append((OK, "pending-docs: semua item terpenuhi"))


# ---------------------------------------------------------------------------
# Check 5: security
# ---------------------------------------------------------------------------

def check_security() -> None:
    section("5. Keamanan")

    gitignore = PROJECT_ROOT / ".gitignore"
    admin_pw = "cache/admin_password.txt"

    if not gitignore.exists():
        print(f"  {ERROR}  .gitignore tidak ditemukan!")
        results.append((ERROR, "security: .gitignore tidak ada"))
        return

    content = gitignore.read_text(encoding="utf-8", errors="replace")
    if admin_pw in content or "admin_password.txt" in content:
        print(f"  {OK}  cache/admin_password.txt ada di .gitignore")
        results.append((OK, "security: admin_password.txt terlindungi di .gitignore"))
    else:
        print(f"  {ERROR}  cache/admin_password.txt TIDAK ada di .gitignore — risiko commit credential!")
        results.append((ERROR, "security: admin_password.txt tidak ada di .gitignore"))

    # Cek apakah ada *.db di .gitignore (bukan library.db yang perlu di-ignore)
    if "*.db" in content or "cache/library.db" in content:
        print(f"  {OK}  File .db di-ignore")
    else:
        print(f"  {WARN}  File .db mungkin tidak di-ignore — cek .gitignore")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary() -> int:
    section("RINGKASAN")
    errors = [m for lvl, m in results if lvl == ERROR]
    warns  = [m for lvl, m in results if lvl == WARN]
    oks    = [m for lvl, m in results if lvl == OK]

    for lvl, m in results:
        print(f"  {lvl}  {m}")

    print(f"\n  {OK} {len(oks)}   {WARN} {len(warns)}   {ERROR} {len(errors)}")

    if errors:
        print(f"\n  Ada {len(errors)} masalah kritis yang perlu dibereskan.")
        return 1
    elif warns:
        print(f"\n  Tidak ada error fatal. {len(warns)} peringatan perlu ditinjau.")
        return 0
    else:
        print("\n  Project sehat.")
        return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Project health check LunaWave.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 jika ada masalah apapun (termasuk ⚠️)")
    args = parser.parse_args()

    print("🩺 LunaWave Doctor — Project Health Check")
    print(f"   Project root: {PROJECT_ROOT}")

    check_docs()
    check_architecture()
    check_big_files()
    check_pending_docs()
    check_security()

    rc = print_summary()

    if args.strict and any(lvl in (WARN, ERROR) for lvl, _ in results):
        sys.exit(1)
    sys.exit(rc)


if __name__ == "__main__":
    main()

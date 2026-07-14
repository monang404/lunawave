#!/usr/bin/env python3
"""
Module: scripts.run_all

Purpose:
    Run all documentation generators and the project health check in a
    single command.

Inputs:
    None (delegates to child scripts).

Outputs:
    Updated docs/ files from generators; health check report on stdout.

Side Effects:
    Invokes generate_file_index.py, generate_report.py, and doctor.py
    as subprocesses.

CLI:
    python scripts/run_all.py [--check] [--strict]


Subscribes to:
    None

Publishes:
    None
"""

import argparse
import io
import subprocess
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

GENERATORS = [
    ("generate_file_index.py", "FILE_INDEX.md"),
    ("generate_report.py", "REPORT.md (statistik)"),
]


def run(script: str, label: str, extra_args: list[str] = None) -> int:  # type: ignore
    if extra_args is None:
        extra_args = []
    print(f"\n▶  {label}")
    print(f"   {script}", flush=True)
    cmd = [sys.executable, str(SCRIPT_DIR / script)] + extra_args
    result = subprocess.run(cmd, cwd=str(SCRIPT_DIR.parent))
    if result.returncode != 0:
        print(f"   ❌ Gagal (exit {result.returncode})")
    else:
        print("   ✅ Selesai")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Jalankan semua generator + health check LunaWave."
    )
    parser.add_argument(
        "--check", action="store_true", help="Hanya jalankan checks, tidak generate"
    )
    parser.add_argument("--strict", action="store_true", help="Exit 1 jika ada masalah")
    args = parser.parse_args()

    print("🚀 LunaWave — Run All")
    failed = []

    if not args.check:
        print("\n== GENERATORS ==")
        for script, label in GENERATORS:
            rc = run(script, label)
            if rc != 0:
                failed.append(label)

    print("\n== HEALTH CHECKS ==")
    rc = run("doctor.py", "Project health check")
    if rc != 0:
        failed.append("doctor")

    print(f"\n{'=' * 40}")
    if failed:
        print(f"❌ {len(failed)} proses gagal: {', '.join(failed)}")
        if args.strict:
            sys.exit(1)
    else:
        print("✅ Semua selesai tanpa error.")

    sys.exit(0)


if __name__ == "__main__":
    main()

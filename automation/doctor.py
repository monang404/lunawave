#!/usr/bin/env python3
"""
Module: scripts.doctor

Purpose:
    Orchestrate all registered health checkers and display a consolidated
    project health dashboard with aggregate scores.

Inputs:
    JSON output from each checker script listed in CHECKERS.

Outputs:
    Terminal dashboard with per-checker status and a final summary.

Side Effects:
    Spawns a subprocess for each checker script.

CLI:
    python scripts/doctor.py [--strict]


Subscribes to:
    None

Publishes:
    None
"""

import io
import json
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

OK = "✅"
WARN = "⚠️ "
ERROR = "❌"

# ---------------------------------------------------------------------------
# Daftar checker — SATU-SATUNYA tempat yang perlu diubah untuk menambah,
# menghapus, atau mengubah urutan checker. Tidak ada logika lain di file ini
# yang perlu disentuh saat menambah checker baru (Open/Closed Principle).
# ---------------------------------------------------------------------------
CHECKERS: list[dict] = [
    {
        "script": "verify_docs.py",
        "title": "Dokumentasi (PATCHLOG, frontmatter, referensi path, coverage)",
        "args": [],
    },
    {
        "script": "architecture_lint.py",
        "title": "Arsitektur (import boundary)",
        "args": ["--show-known"],
    },
    {
        "script": "verify_structure.py",
        "title": "Struktur Project (file besar, item pending)",
        "args": [],
    },
    {
        "script": "verify_security.py",
        "title": "Keamanan (.gitignore, credential exposure)",
        "args": [],
    },
    {
        "script": "event_graph.py",
        "title": "Event Pub/Sub (Dead & Ghost Events)",
        "args": [],
    },
]


# ---------------------------------------------------------------------------
# Eksekusi checker
# ---------------------------------------------------------------------------


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def run_checker_json(script: str, extra_args: list[str]) -> tuple[int, dict | None, str]:
    """Jalankan satu checker dengan --json dan parse output-nya.

    Mengembalikan (returncode, parsed_dict_or_None, raw_stdout_for_fallback).
    """
    cmd = [sys.executable, str(SCRIPT_DIR / script), "--json"] + extra_args
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    except Exception as e:
        return 1, None, str(e)

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = None

    return proc.returncode, data, (proc.stdout + proc.stderr).strip()


def run_all_checkers() -> list[dict]:
    """Jalankan semua checker terdaftar. Mengembalikan list of dict, satu
    per checker, berisi metadata eksekusi + data JSON (atau None jika gagal
    parse)."""
    outcomes = []
    for entry in CHECKERS:
        rc, data, raw = run_checker_json(entry["script"], entry["args"])
        outcomes.append(
            {
                "script": entry["script"],
                "title": entry["title"],
                "returncode": rc,
                "data": data,
                "raw": raw,
            }
        )
    return outcomes


# ---------------------------------------------------------------------------
# Dashboard rendering — murni presentasi, tidak ada keputusan validasi
# ---------------------------------------------------------------------------


def render_checker(outcome: dict, index: int) -> tuple[str, str]:
    """Cetak satu bagian dashboard untuk satu checker.

    Mengembalikan (level, ringkasan_satu_baris) untuk dipakai di summary akhir.
    level adalah salah satu dari OK, WARN, ERROR.
    """
    section(f"{index}. {outcome['title']}")
    data = outcome["data"]
    script = outcome["script"]

    if data is None:
        # Checker gagal menghasilkan JSON valid — tampilkan output mentah
        # apa adanya. doctor.py tidak menebak alasan kegagalan (itu urusan
        # checker), hanya melaporkan bahwa integrasi gagal.
        if outcome["raw"]:
            print(outcome["raw"])
        return ERROR, f"{script}: gagal parse JSON output"

    status = data.get("repository_status", "FAIL")
    score = data.get("score", "?")
    checks = data.get("checks", [])

    fail_checks = [c for c in checks if c.get("status") == "FAIL"]
    warn_checks = [c for c in checks if c.get("status") == "WARN"]

    print(f"  Status  : {status}")
    print(f"  Score   : {score} / 100")

    for c in fail_checks:
        print(f"  {ERROR}  {c['name']}: {c['message']}")
        for item in (c.get("items") or [])[:3]:
            print(f"       • {item}")

    for c in warn_checks:
        print(f"  {WARN}  {c['name']}: {c['message']}")

    checker_name = data.get("checker", script)

    if outcome["returncode"] != 0 or status == "FAIL":
        return ERROR, f"{checker_name}: {len(fail_checks)} FAIL check(s) — score {score}/100"
    elif warn_checks:
        return WARN, f"{checker_name}: {len(warn_checks)} peringatan — score {score}/100"
    else:
        return OK, f"{checker_name}: semua bersih (score {score}/100)"


def print_summary(results: list[tuple[str, str]]) -> int:
    section("RINGKASAN")
    errors = [m for lvl, m in results if lvl == ERROR]
    warns = [m for lvl, m in results if lvl == WARN]
    oks = [m for lvl, m in results if lvl == OK]

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
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 jika ada masalah apapun (termasuk ⚠️)"
    )
    args = parser.parse_args()

    print("🩺 LunaWave Doctor — Project Health Check")
    print(f"   Project root: {PROJECT_ROOT}")

    outcomes = run_all_checkers()

    results: list[tuple[str, str]] = []
    for i, outcome in enumerate(outcomes, start=1):
        results.append(render_checker(outcome, i))

    rc = print_summary(results)

    if args.strict and any(lvl in (WARN, ERROR) for lvl, _ in results):
        sys.exit(1)
    sys.exit(rc)


if __name__ == "__main__":
    main()

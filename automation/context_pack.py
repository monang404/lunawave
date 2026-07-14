#!/usr/bin/env python3
"""
Module: automation.context_pack

Purpose:
    Satu panggilan yang menggabungkan semua tool automation/ jadi 1 JSON —
    endpoint utama untuk AI agent supaya tidak perlu 5 panggilan terpisah.

Subscribes to:
    None

Publishes:
    None

CLI:
    python automation/context_pack.py <file_or_feature> [--json]
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from find_owner import get_owner_info
from patchlog import PATCHLOG, parse_entries
from shared.repo_index import load_index
from test_locator import find_test_for


def _status_lines_for(root: Path, target: str) -> list[str]:
    status = (root / "docs" / "STATUS.md").read_text(encoding="utf-8", errors="replace")
    return [line.strip() for line in status.splitlines() if target in line]


def build_context_pack(root: Path, target: str) -> dict:
    index = load_index(root)
    entry = index["files"].get(target, {})
    test = find_test_for(root, target)
    history = [
        e for e in parse_entries(PATCHLOG.read_text(encoding="utf-8")) if target in e["files"]
    ]

    return {
        "target": target,
        "ownership": get_owner_info(target, root),
        "deps": entry.get("imports", []),
        "reverse_deps": entry.get("reverse_deps", []),
        "event_flow": {
            "publishes": entry.get("publishes", []),
            "subscribes": entry.get("subscribes", []),
        },
        "related_test": str(test.relative_to(root)).replace("\\", "/") if test else None,
        "patchlog_history": history[:3],
        "status_notes": _status_lines_for(root, target),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file_or_feature")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    result = build_context_pack(PROJECT_ROOT, args.file_or_feature)

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

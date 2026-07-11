"""
verify_docs/render.py — Render output verify_docs ke teks atau JSON.

Purpose:
    Menyediakan _score, _overall_status, render_summary, dan render_json
    untuk verify_docs. Scoring menggunakan fungsi generik dari shared dengan
    CHECK_WEIGHTS lokal verify_docs.

Subscribes to:
    shared.check_result

Publishes:
    _score, _overall_status, render_summary, render_json
"""

from __future__ import annotations

import json

from shared.check_result import CheckResult
from shared.check_result import _score as _score_generic
from shared.check_result import _overall_status
from .helpers import CHECK_HINTS, CHECK_WEIGHTS, fmt_items

# Re-export _overall_status agar caller bisa import dari sini
__all__ = ["_score", "_overall_status", "render_summary", "render_json"]


def _score(results: list[CheckResult]) -> int:
    """Skor berbobot verify_docs menggunakan CHECK_WEIGHTS lokal."""
    return _score_generic(results, CHECK_WEIGHTS)


def render_summary(results: list[CheckResult], verbose: bool) -> None:
    pass_results     = [r for r in results if r.status == "PASS"]
    non_pass         = [r for r in results if r.status != "PASS"]
    coverage_results = [r for r in results if r.total]
    status = _overall_status(results)
    score  = _score(results)

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
        "checker": "verify_docs",
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

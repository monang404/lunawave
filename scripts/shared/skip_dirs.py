"""
shared/skip_dirs.py — Set direktori yang diabaikan saat scan file system.

Purpose:
    Menyatukan semua versi SKIP_DIRS dari berbagai script menjadi satu set
    paling lengkap, plus menyediakan generator walk_py_files() yang sudah
    handle skip secara konsisten.

Subscribes to:
    —

Publishes:
    SKIP_DIRS, walk_py_files
"""

from __future__ import annotations

import os
from pathlib import Path

# Gabungan paling lengkap dari semua SKIP_DIRS / NOISE_DIRS di seluruh scripts/
SKIP_DIRS: frozenset[str] = frozenset({
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    "dist",
    "build",
})


def walk_py_files(root: Path):
    """Generator yang yield Path absolut untuk setiap file .py di bawah root.

    Direktori yang ada di SKIP_DIRS dilewati secara rekursif sehingga
    __pycache__, .git, dsb. tidak pernah di-scan.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                yield Path(dirpath) / fn

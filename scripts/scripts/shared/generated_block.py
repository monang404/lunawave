"""
shared/generated_block.py — Utilitas penggantian blok <!-- BEGIN/END:GENERATED -->.

Purpose:
    Menyediakan fungsi replace_marker_block() yang mengganti isi di antara
    pasangan marker BEGIN:GENERATED / END:GENERATED menggunakan regex.
    Hanya berisi logika substitusi — fallback "kalau marker belum ada" bersifat
    spesifik tiap file dan tetap ada di masing-masing script secara lokal.

Subscribes to:
    —

Publishes:
    replace_marker_block
"""

from __future__ import annotations

import re

_DEFAULT_BEGIN = "<!-- BEGIN:GENERATED -->"
_DEFAULT_END   = "<!-- END:GENERATED -->"


def replace_marker_block(
    original: str,
    block: str,
    begin: str = _DEFAULT_BEGIN,
    end: str = _DEFAULT_END,
) -> str:
    """Ganti isi di antara marker BEGIN/END:GENERATED dengan *block* baru.

    Mengasumsikan marker sudah ada di *original*. Jika belum ada, kembalikan
    *original* tidak berubah — logika fallback untuk kasus tersebut diserahkan
    ke caller masing-masing.

    Args:
        original: string isi file lengkap.
        block: konten baru yang akan disisipkan di antara marker.
        begin: string marker pembuka (default: <!-- BEGIN:GENERATED -->).
        end: string marker penutup (default: <!-- END:GENERATED -->).

    Returns:
        String dengan blok di antara marker sudah diganti.
    """
    if begin not in original:
        return original

    pattern = re.compile(
        re.escape(begin) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    new_block = f"{begin}\n{block}\n{end}"
    return pattern.sub(new_block, original)

"""
Module: core.mem_stats

Purpose:
    Baca penggunaan RAM (RSS) proses saat ini secara cross-platform tanpa
    dependency pip baru (tidak pakai psutil — lihat ADR-0010).

Responsibilities:
    - Linux/Termux: parse VmRSS dari /proc/self/status.
    - Windows: baca lewat ctypes + psapi.GetProcessMemoryInfo (API OS bawaan).
    - Platform lain / kegagalan apa pun: kembalikan None, tidak pernah raise.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Thread-safe (read-only, tidak ada shared state).
"""

import sys


def get_rss_mb() -> float | None:
    """
    Mengembalikan RSS (Resident Set Size) proses saat ini dalam MB.

    Selalu fail-safe: kalau platform tidak didukung atau pembacaan gagal
    dengan alasan apa pun, kembalikan None (bukan exception).
    """
    try:
        if sys.platform == "win32":
            return _get_rss_mb_windows()
        return _get_rss_mb_proc()
    except Exception:
        return None


def _get_rss_mb_proc() -> float | None:
    """Baca VmRSS dari /proc/self/status (Linux, termasuk Termux/Android)."""
    try:
        with open("/proc/self/status", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    # Format: "VmRSS:	   12345 kB"
                    if len(parts) >= 2:
                        kb = float(parts[1])
                        return round(kb / 1024, 2)
        return None
    except Exception:
        return None


def _get_rss_mb_windows() -> float | None:
    """Baca RSS via ctypes + psapi.GetProcessMemoryInfo (Windows, no install)."""
    try:
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        psapi = ctypes.WinDLL("psapi.dll")
        kernel32 = ctypes.WinDLL("kernel32.dll")

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        handle = kernel32.GetCurrentProcess()

        ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        if not ok:
            return None
        return round(counters.WorkingSetSize / (1024 * 1024), 2)
    except Exception:
        return None

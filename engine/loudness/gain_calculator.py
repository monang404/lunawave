"""
Module: engine.loudness.gain_calculator

Purpose:
    Hitung gain (dB) yang perlu diterapkan ke sebuah track supaya loudness-nya
    mendekati target, berdasarkan hasil pengukuran integrated loudness (LUFS).

Responsibilities:
    - compute_gain_db(): hitung gain dari LUFS terukur, di-clamp ke batas aman.
    - build_af_filter(): bentuk string filter MPV/ffmpeg (af=lavfi=[volume=XdB]).

Depends on:
    None (stateless, semua nilai masuk sebagai argumen)

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless — aman dipanggil dari mana saja.
"""

TARGET_LUFS = -14.0  # Sama seperti Spotify/YouTube Music
MAX_BOOST_DB = 8.0  # Clamp atas — tanpa true-peak limiting, boost besar berisiko clipping
MAX_CUT_DB = 12.0  # Clamp bawah — lagu yang sudah kenceng dipotong maksimal segini


def compute_gain_db(
    measured_lufs: float | None,
    target_lufs: float = TARGET_LUFS,
    max_boost_db: float = MAX_BOOST_DB,
    max_cut_db: float = MAX_CUT_DB,
) -> float:
    """Hitung gain (dB). None (belum dianalisis) -> 0.0 (passthrough, tidak
    ada normalisasi -- ini keputusan sengaja, bukan default sembarangan)."""
    if measured_lufs is None:
        return 0.0
    gain = target_lufs - measured_lufs
    return max(-max_cut_db, min(max_boost_db, gain))


def build_af_filter(gain_db: float) -> str:
    """Bentuk string untuk property `af` MPV. gain_db=0.0 tetap menghasilkan
    filter eksplisit (bukan string kosong) supaya SELALU meng-override filter
    dari track sebelumnya -- MPV adalah proses persisten yang di-reuse antar
    track (loadfile replace), `af` TIDAK otomatis reset sendiri."""
    return f"lavfi=[volume={gain_db:.2f}dB]"

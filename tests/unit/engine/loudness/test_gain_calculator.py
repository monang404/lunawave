import pytest

from engine.loudness.gain_calculator import build_af_filter, compute_gain_db


def test_compute_gain_db_within_limits():
    gain = compute_gain_db(
        measured_lufs=-20.0, target_lufs=-14.0, max_boost_db=10.0, max_cut_db=15.0
    )
    assert gain == 6.0


def test_compute_gain_db_exceeds_max():
    gain = compute_gain_db(measured_lufs=-25.0, target_lufs=-14.0, max_boost_db=5.0)
    assert gain == 5.0


def test_compute_gain_db_exceeds_min():
    gain = compute_gain_db(measured_lufs=-8.0, target_lufs=-14.0, max_boost_db=10.0, max_cut_db=2.0)
    assert gain == -2.0


def test_compute_gain_db_zero_when_none():
    gain = compute_gain_db(None, target_lufs=-14.0)
    assert gain == 0.0


def test_build_af_filter():
    assert build_af_filter(6.0) == "lavfi=[volume=6.00dB]"
    assert build_af_filter(-2.5) == "lavfi=[volume=-2.50dB]"
    assert build_af_filter(0.0) == "lavfi=[volume=0.00dB]"

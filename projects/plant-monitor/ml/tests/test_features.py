"""Tests for src/features.py: integer device feature pipeline, golden vectors, boundaries.

ALL DATA IS SYNTHETIC (generated in tests or frozen in tests/golden/features_golden.json). Nothing here is a
model result or an accuracy. Traces to: FR-E01 (Model A inputs), FR-E04 (int8, on-device), NFR-01 (15-min
cadence), NFR-02 (relative moisture).
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import features as F
import prep

GOLDEN = json.loads((Path(__file__).parent / "golden" / "features_golden.json").read_text())


def _hist(m=50, t=40, lt=128):
    return [m] * F.HIST, [t] * F.HIST, [lt] * F.HIST


# ---------- golden vectors (contract with the C port)
@pytest.mark.parametrize("case", GOLDEN["features"], ids=lambda c: c["name"])
def test_golden_feature_vectors(case):
    got = F.feature_vector(case["m_hist"], case["temp_hist"], case["light_hist"], case["minute_of_day"], case["T"],
                           case["ticks_since_event"], case["soil"])
    assert got == case["expected"]
    assert all(-128 <= v <= 127 for v in got) and len(got) == 14      # FR-E04: int8 inputs


def test_golden_feature_names_match():
    assert GOLDEN["feature_names"] == list(F.FEATURE_NAMES)


@pytest.mark.parametrize("case", GOLDEN["tracker"], ids=lambda c: c["name"])
def test_golden_event_tracker(case):
    assert F.ticks_since_event_series(case["m"], case["valid"]).tolist() == case["expected_since"]


def test_golden_hand_computed_ramps_are_exact():
    # Hand-computed, independent of the implementation: a ramp of -1 pp per 15 min = -4 pp/h.
    # slope_1h in 1/2 pp/h = -8, slope_6h in 1/8 pp/h = -32, slope_24h in 1/16 pp/h = -64.
    c = {x["name"]: x for x in GOLDEN["features"]}["ramp_down_1pp_per_tick"]
    assert c["expected"][1:4] == [-8, -32, -64]
    c = {x["name"]: x for x in GOLDEN["features"]}["ramp_up_1pp_per_tick"]
    assert c["expected"][1:4] == [8, 32, 64]


# ---------- slope vs float reference
def test_slope_matches_numpy_polyfit_within_one_lsb():
    rng = np.random.default_rng(1)
    for _ in range(50):
        n = int(rng.choice([4, 24, 96]))
        y = rng.integers(0, 101, n)
        ref = np.polyfit(np.arange(n), y, 1)[0] * 4 * 64        # pp/h * 64
        assert abs(F.slope_x64(y) - ref) <= 0.5 + 1e-9


def test_slope_constant_is_zero_and_needs_two_samples():
    assert F.slope_x64([7, 7, 7, 7]) == 0
    with pytest.raises(ValueError):
        F.slope_x64([5])


# ---------- integer helpers: rounding boundaries
def test_rshift_round_half_up_boundary():
    assert F.rshift_round(15, 5) == 0 and F.rshift_round(16, 5) == 1        # 0.47 -> 0, 0.5 -> 1
    assert F.rshift_round(-15, 5) == 0 and F.rshift_round(-16, 5) == 0 and F.rshift_round(-17, 5) == -1


def test_div_round_half_away_from_zero_boundary():
    assert F.div_round(4, 10) == 0 and F.div_round(5, 10) == 1
    assert F.div_round(-4, 10) == 0 and F.div_round(-5, 10) == -1
    assert F.div_round(0, 3) == 0


def test_quantise_m_rounds_half_up_and_saturates():
    assert F.quantise_m(24.49) == 24 and F.quantise_m(24.5) == 25            # just below / at the rounding edge
    assert F.quantise_m(-0.4) == 0 and F.quantise_m(100.49) == 100 and F.quantise_m(250) == 100


def test_quantise_temp_offset_and_saturation():
    assert F.quantise_temp(20.0) == 40 and F.quantise_temp(-20.0) == 0 and F.quantise_temp(-25) == 0
    assert F.quantise_temp(235.0) == 255 and F.quantise_temp(240.0) == 255


def test_clip_boundaries():
    assert F.clip(127, -128, 127) == 127 and F.clip(128, -128, 127) == 127
    assert F.clip(-128, -128, 127) == -128 and F.clip(-129, -128, 127) == -128


# ---------- sin/cos table
def test_sin_table_matches_math_and_cos_is_shifted_sin():
    for h in range(24):
        assert abs(F.SIN_HOUR[h] - 127 * math.sin(2 * math.pi * h / 24)) <= 0.5 + 1e-9      # exact .5 cases are 63.5 at h=2,10
        assert F.SIN_HOUR[(h + 12) % 24] == -F.SIN_HOUR[h]                                    # antisymmetric
    m, t, lt = _hist()
    for hour in range(24):
        v = dict(zip(F.FEATURE_NAMES, F.feature_vector(m, t, lt, hour * 60, 25, 0, 0)))
        assert abs(v["cos_hour"] - 127 * math.cos(2 * math.pi * hour / 24)) <= 0.5 + 1e-9


def test_hour_boundary_59_vs_60_minutes():
    m, t, lt = _hist()
    a = dict(zip(F.FEATURE_NAMES, F.feature_vector(m, t, lt, 2 * 60 + 59, 25, 0, 0)))
    b = dict(zip(F.FEATURE_NAMES, F.feature_vector(m, t, lt, 3 * 60, 25, 0, 0)))
    assert a["sin_hour"] == F.SIN_HOUR[2] and b["sin_hour"] == F.SIN_HOUR[3]


# ---------- feature definitions
def test_feature_vector_rejects_wrong_history_length():
    m, t, lt = _hist()
    with pytest.raises(ValueError):
        F.feature_vector(m[:-1], t, lt, 0, 25, 0, 0)


def test_windows_use_only_the_most_recent_samples():
    # 96 samples: old part constant 80, last 4 ramp down 4 pp per tick -> slope_1h sees only the ramp
    m = [80] * 92 + [80, 76, 72, 68]
    v = dict(zip(F.FEATURE_NAMES, F.feature_vector(m, [40] * 96, [128] * 96, 0, 25, 0, 0)))
    # 4 pp / tick = 16 pp/h -> x2 = 32 for 1/2 pp/h units, sign negative; 1-h window is exactly the last 4 samples
    assert v["slope_1h"] == -32
    assert v["m_min_24h"] == 68 - 50 and v["m_max_24h"] == 80 - 50 and v["m_now"] == 68 - 50


def test_light_mean_uses_last_24_samples_only():
    lt = [0] * 72 + [200] * 24
    v = dict(zip(F.FEATURE_NAMES, F.feature_vector([50] * 96, [40] * 96, lt, 0, 25, 0, 0)))
    assert v["light_mean_6h"] == 200 - 128
    lt2 = [0] * 71 + [200] * 25            # 25 samples at 200: window of 24 still 200
    assert dict(zip(F.FEATURE_NAMES, F.feature_vector([50] * 96, [40] * 96, lt2, 0, 25, 0, 0)))["light_mean_6h"] == 72


def test_hours_since_event_cap_boundary_72h():
    m, t, lt = _hist()
    f = lambda k: dict(zip(F.FEATURE_NAMES, F.feature_vector(m, t, lt, 0, 25, k, 0)))["hours_since_event"]
    assert f(287) == 71 and f(288) == 72 and f(289) == 72 and f(10_000) == 72      # capped at 72 h (FR-E01)
    assert f(3) == 0 and f(4) == 1                                                  # 4 ticks = 1 h


def test_T_is_input_with_zero_point_50():
    m, t, lt = _hist()
    assert dict(zip(F.FEATURE_NAMES, F.feature_vector(m, t, lt, 0, 25, 0, 0)))["T"] == -25
    assert dict(zip(F.FEATURE_NAMES, F.feature_vector(m, t, lt, 0, 100, 0, 0)))["T"] == 50


# ---------- event tracker thresholds (mirrors prep.label_events)
def _tracker_onsets(m):
    tr = F.EventTracker()
    return [i for i, v in enumerate(m) if tr.step(v)]


def test_rise_threshold_boundary_9_vs_10_points():
    below = [40, 40, 49, 49, 49]            # +9 over 2 ticks
    at = [40, 40, 50, 50, 50]               # +10 over 2 ticks
    assert _tracker_onsets(below) == [] and _tracker_onsets(at) == [2]


def test_rise_window_boundary_2_vs_3_ticks():
    assert _tracker_onsets([40, 45, 50, 50]) == [2]          # +10 in exactly 2 ticks
    assert _tracker_onsets([40, 44, 47, 50, 50]) == []       # +10 needs 3 ticks: not a rise within the 2-tick window


def test_refractory_boundary_8_vs_9_ticks():
    # build explicitly instead of searching: onsets at 2 and 2+gap
    def two(gap):
        n = 2 + gap + 4
        s = [30] * n
        s[2:4] = [45, 45]              # rise at tick 2 (m[2]-m[0] = 15), back to 30 at tick 4 (fall)
        s[2 + gap:2 + gap + 2] = [45, 45]
        return s
    assert _tracker_onsets(two(8)) == [2]            # exactly 8 ticks later: suppressed
    assert _tracker_onsets(two(9)) == [2, 11]        # 9 ticks later: kept


def test_tracker_agrees_with_prep_label_events_on_integer_series():
    rng = np.random.default_rng(3)
    m = np.clip(np.cumsum(rng.integers(-9, 10, 400)) + 50, 0, 100)
    d = pd.DataFrame({"m": m.astype(float)})
    ev = prep.label_events(d)["event"] != prep.EVENT_NONE
    assert _tracker_onsets(m.tolist()) == list(np.flatnonzero(ev))
    assert ev.sum() > 3


def test_invalid_samples_never_rise_and_counter_saturates():
    tr = F.EventTracker()
    for v, ok in [(40, True), (40, True), (60, False)]:
        assert tr.step(v, ok) is False
    assert tr.since == F.HORIZON_TICKS
    tr2 = F.EventTracker()
    for _ in range(400):
        tr2.step(50)
    assert tr2.since == 288

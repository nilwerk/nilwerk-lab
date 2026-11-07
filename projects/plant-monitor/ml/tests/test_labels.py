"""Tests for src/labels.py: Model A label (hours to threshold, censoring, masks), baseline, weak Model B labels.

ALL DATA IS SYNTHETIC, built in the tests. No accuracy is claimed anywhere. Traces to: FR-E01 (72 h horizon,
dry threshold, baseline), FR-E02 (events), FR-E03 (fault classes), NFR-02 (relative moisture).
"""
import numpy as np
import pandas as pd
import pytest

import labels as L
import prep


def seg(m, events=(), faults=None, T0="2025-03-03 00:00"):
    n = len(m)
    d = pd.DataFrame({"time": pd.date_range(T0, periods=n, freq="15min"), "m": np.asarray(m, float)})
    d["m_clean"] = d["m"]
    d["event"] = prep.EVENT_NONE
    for e in events:
        d.loc[e, "event"] = prep.EVENT_WETTING
    d["fault"] = prep.FAULT_NONE
    for i, f in (faults or {}).items():
        d.loc[i, "fault"] = f
    return d


def flat_then(n_flat, n_total, hi=60.0, lo=10.0):
    """hi for n_flat ticks then lo (crossing at tick n_flat)."""
    return [hi] * n_flat + [lo] * (n_total - n_flat)


# ---------- Model A: crossing and hours
def test_crossing_hours_and_already_dry_zero():
    r = L.label_hours_to_threshold(seg(flat_then(8, 20)))
    assert r.loc[0, "y_hours"] == 2.0 and not r.loc[0, "y_censored"]       # 8 ticks = 2 h
    assert r.loc[7, "y_hours"] == 0.25
    assert r.loc[8, "y_hours"] == 0.0 and r.loc[8, "y_mask"]               # already below T: 0


def test_threshold_boundary_below_vs_at_vs_above():
    # T = 25: 24.99 is below (crossing), 25.0 is NOT below (strict), 25.01 not below
    for val, crosses in [(24.99, True), (25.0, False), (25.01, False)]:
        r = L.label_hours_to_threshold(seg([60, 60, val, val, 60, 60, 60, 60], events=()), horizon=3)
        assert (r.loc[0, "y_hours"] == 0.5) == crosses, val


def test_threshold_is_a_parameter_not_a_constant():
    m = [60, 40, 30, 20, 20, 20, 20, 20]
    assert L.label_hours_to_threshold(seg(m), threshold=25.0, horizon=4).loc[0, "y_hours"] == 0.75
    assert L.label_hours_to_threshold(seg(m), threshold=35.0, horizon=4).loc[0, "y_hours"] == 0.5


# ---------- horizon: 72 h = 288 ticks
def test_horizon_boundary_crossing_at_288_vs_289_ticks():
    n = 600
    r = L.label_hours_to_threshold(seg(flat_then(288, n)))
    assert r.loc[0, "y_hours"] == 72.0 and not r.loc[0, "y_capped"] and not r.loc[0, "y_censored"]   # crossing at exactly 72 h
    r2 = L.label_hours_to_threshold(seg(flat_then(289, n)))
    assert r2.loc[0, "y_hours"] == 72.0 and r2.loc[0, "y_capped"] and r2.loc[0, "y_mask"]            # beyond: capped, observed


def test_data_end_censors_when_horizon_not_fully_observed():
    n = 300                                              # 299 ticks after tick 0 are observed
    r = L.label_hours_to_threshold(seg([60.0] * n))
    assert r.loc[11, "y_hours"] == 72.0 and r.loc[11, "y_capped"]       # i+288 = 299 = n-1: observed
    assert r.loc[12, "y_censored"] and r.loc[12, "y_censor_reason"] == L.CENSOR_DATA_END and not r.loc[12, "y_mask"]
    assert np.isnan(r.loc[12, "y_hours"])


# ---------- censoring by wetting events
def test_event_before_crossing_censors_event_at_or_after_crossing_semantics():
    m = flat_then(10, 40)                                # crossing at tick 10
    r_before = L.label_hours_to_threshold(seg(m, events=[9]), horizon=20)
    assert r_before.loc[0, "y_censored"] and r_before.loc[0, "y_censor_reason"] == L.CENSOR_EVENT and not r_before.loc[0, "y_mask"]
    r_at = L.label_hours_to_threshold(seg(m, events=[10]), horizon=20)         # event AT the crossing tick censors
    assert r_at.loc[0, "y_censor_reason"] == L.CENSOR_EVENT
    r_after = L.label_hours_to_threshold(seg(m, events=[11]), horizon=20)      # event after the crossing: label stands
    assert r_after.loc[0, "y_hours"] == 2.5 and not r_after.loc[0, "y_censored"]


def test_event_exactly_at_t_does_not_censor_but_at_t_plus_1_does():
    m = flat_then(10, 40)
    r = L.label_hours_to_threshold(seg(m, events=[3]), horizon=20)             # window is (t, t']: event at t itself is outside
    assert r.loc[3, "y_hours"] == 1.75 and not r.loc[3, "y_censored"]
    assert r.loc[2, "y_censored"]                                              # event at t+1


def test_event_beyond_horizon_does_not_censor():
    m = [60.0] * 600
    r = L.label_hours_to_threshold(seg(m, events=[289]))
    assert not r.loc[0, "y_censored"] and r.loc[0, "y_capped"]                 # event at 289 > 288
    r2 = L.label_hours_to_threshold(seg(m, events=[288]))
    assert r2.loc[0, "y_censored"] and r2.loc[0, "y_censor_reason"] == L.CENSOR_EVENT


# ---------- masks, gaps, faults
def test_nan_gap_before_crossing_censors_and_invalid_now_is_masked():
    m = flat_then(10, 40)
    m[5] = np.nan
    r = L.label_hours_to_threshold(seg(m), horizon=20)
    assert r.loc[0, "y_censor_reason"] == L.CENSOR_GAP and not r.loc[0, "y_mask"]
    assert r.loc[5, "y_censor_reason"] == L.CENSOR_GAP and not r.loc[5, "y_mask"]       # m[t] itself invalid
    assert r.loc[6, "y_hours"] == 1.0 and r.loc[6, "y_mask"]


def test_synthetic_fault_ticks_are_masked_out_of_model_a_but_labelled_on_clean_series():
    d = seg(flat_then(10, 40), faults={2: prep.FAULT_SPIKE})
    d.loc[2, "m"] = 99.0                                  # faulty reading, clean series unchanged
    r = L.label_hours_to_threshold(d, horizon=20)
    assert r.loc[2, "y_hours"] == 2.0 and not r.loc[2, "y_mask"]
    assert r.loc[1, "y_mask"]


def test_next_index():
    assert L.next_index(np.array([0, 1, 0, 1], bool)).tolist() == [1, 3, 3, 4]


# ---------- baseline
def test_baseline_clips_between_0_and_72h_and_is_nan_before_first_event():
    d = seg([50.0] * 400, events=[10])
    b = L.baseline_hours(d, mean_interval_h=30.0)
    assert np.isnan(b[9]) and b[10] == 30.0
    assert b[10 + 4 * 10] == 20.0 and b[10 + 4 * 30] == 0.0 and b[10 + 4 * 31] == 0.0       # max(0, ...)
    assert L.baseline_hours(d, mean_interval_h=100.0)[10] == 72.0                            # min(.., 72)
    assert L.baseline_hours(d, mean_interval_h=72.0)[10] == 72.0 and L.baseline_hours(d, mean_interval_h=72.25)[10] == 72.0


# ---------- weak labels: waterlogged
def test_waterlogged_value_boundary_95_vs_95_01():
    for val, expect in [(95.0, False), (95.01, True)]:
        w = L.label_waterlogged(seg([val] * 30))
        assert bool(w.iloc[29]) == expect, val


def test_waterlogged_duration_boundary_23_vs_24_ticks_and_causal():
    w = L.label_waterlogged(seg([99.0] * 23 + [10.0] * 5))
    assert not w.any()                                                       # 23 ticks = 5.75 h: not enough
    w = L.label_waterlogged(seg([99.0] * 24 + [10.0] * 5))
    assert w.iloc[23] and not w.iloc[22] and not w.iloc[24]                  # True from tick 24th, only while above
    w = L.label_waterlogged(seg([99.0] * 12 + [np.nan] + [99.0] * 12))
    assert not w.any()                                                       # NaN breaks the run


# ---------- weak labels: fast drying
def _feat(slope, temp, light=0, light_known=False, valid=True):
    return pd.DataFrame({"slope_6h": [slope], "temp_now": [temp], "light_mean_6h": [light],
                         "light_known": [light_known], "feat_valid": [valid]})


def test_fast_drying_slope_boundary_at_p5_vs_one_below():
    thr = {"slope_6h_p5": -10, "temp_p75": 24, "light_p75": None}
    assert not L.label_fast_drying(_feat(-10, 30), thr).iloc[0]       # equal to p5: not below
    assert L.label_fast_drying(_feat(-11, 30), thr).iloc[0]


def test_fast_drying_temperature_boundary_at_p75_vs_one_above():
    thr = {"slope_6h_p5": -10, "temp_p75": 24, "light_p75": None}
    assert not L.label_fast_drying(_feat(-20, 24), thr).iloc[0]
    assert L.label_fast_drying(_feat(-20, 25), thr).iloc[0]


def test_fast_drying_light_or_temperature_and_light_boundary():
    thr = {"slope_6h_p5": -10, "temp_p75": 24, "light_p75": 50}
    assert not L.label_fast_drying(_feat(-20, 20, 50, True), thr).iloc[0]
    assert L.label_fast_drying(_feat(-20, 20, 51, True), thr).iloc[0]
    assert not L.label_fast_drying(_feat(-20, 20, 99, False), thr).iloc[0]    # placeholder light must be ignored


def test_fast_drying_invalid_features_are_false():
    thr = {"slope_6h_p5": -10, "temp_p75": 24, "light_p75": None}
    assert not L.label_fast_drying(_feat(-50, 40, valid=False), thr).iloc[0]


def test_fit_thresholds_use_training_valid_rows_only_and_integer_percentiles():
    f = pd.DataFrame({"slope_6h": list(range(-100, 0)) + [999] * 5, "temp_now": list(range(100, 200)) + [0] * 5,
                      "light_mean_6h": 0, "light_known": False, "feat_valid": [True] * 100 + [False] * 5})
    thr = L.fit_fast_drying_thresholds(f)
    assert thr["slope_6h_p5"] == -96 and thr["temp_p75"] == 174 and thr["light_p75"] is None   # invalid rows excluded
    with pytest.raises(ValueError):
        L.fit_fast_drying_thresholds(f.assign(feat_valid=False))

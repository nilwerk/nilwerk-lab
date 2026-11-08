"""Tests for task 4.AI2 (training pipeline). ALL DATA IS SYNTHETIC, built here; no accuracy is claimed.

Traces to FR-E01 (Model A baseline eval), FR-E02 (wetting metrics, FP budget), FR-E03 (fast path: single tick),
FR-E04 (int8 / size), A-019 (precision AND recall per class), A-032 (ignore mask, sector 5).
"""
import numpy as np
import pandas as pd
import pytest

import features as F
import labels as L
import prep
import train as T


def seg_frame(m_values, plant="mendeley_s1", events=None, segment="s0", start="2025-03-03"):
    """A segment frame with exactly the columns build_wetting_windows needs; labels come from the real A-032 rules."""
    n = len(m_values)
    d = pd.DataFrame({"time": pd.date_range(start, periods=n, freq="15min"), "m": [float(v) if v == v else np.nan for v in m_values]})
    d["m_u8"] = [F.quantise_m(v) if v == v else 0 for v in d["m"].fillna(0.0)]
    d["plant"], d["segment"], d["event"] = plant, segment, prep.EVENT_NONE
    for i, e in (events or {}).items():
        d.loc[i, "event"] = e
    return L.label_wetting_classes(d)


def test_windows_never_cross_a_segment_boundary():                       # playbook: segment-aware windows
    a = seg_frame([20.0] * (T.CONTEXT - 1), segment="a")                  # one tick short: no window
    b = seg_frame([20.0] * (T.CONTEXT - 1), segment="b", start="2025-03-10")
    w = T.build_wetting_windows(pd.concat([a, b], ignore_index=True))
    assert len(w["y"]) == 0                                               # a + b joined would have 22 ticks: must not window
    c = seg_frame([20.0] * T.CONTEXT, segment="c")
    assert len(T.build_wetting_windows(c)["y"]) == 1


def test_windows_skip_ticks_with_missing_samples_in_the_context():
    m = [20.0] * 30
    m[15] = np.nan
    w = T.build_wetting_windows(seg_frame(m))
    t = pd.to_datetime(w["time"])
    base = pd.Timestamp("2025-03-03")
    ticks = ((t - base) / pd.Timedelta(minutes=15)).astype(int)
    assert all(not (15 <= k < 15 + T.CONTEXT) for k in ticks)            # every window that would see tick 15 is dropped
    assert len(ticks) > 0


def test_window_values_d1_d4_m_now_and_integer_range():
    m = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 30, 31]
    w = T.build_wetting_windows(seg_frame(m))
    x = w["X"][-1]                                                        # window ends at tick 13 (m = 31)
    d1, d4 = x[:T.WINDOW], x[T.WINDOW:2 * T.WINDOW]
    assert d1[-1] == 1 and d1[-2] == 20                                   # 31-30, 30-10
    assert d4[-1] == 21                                                   # 31 - m[9] = 21
    assert x[2 * T.WINDOW] == 31
    assert x.min() >= -128 and x.max() <= 127 and len(x) == T.N_INPUTS


def test_valve_and_rain_columns_are_not_features():                      # concept 3.1: valve telemetry never a feature
    base = seg_frame([20.0] * 20 + [60.0])
    a = T.build_wetting_windows(base)["X"]
    b = T.build_wetting_windows(base.assign(irrigation=999.0, rain=999.0, temperature=99.0))["X"]
    assert np.array_equal(a, b)


def test_a032_ignore_ticks_labelled_minus_one_and_dropped_from_counts():
    ev = {20: prep.EVENT_WETTING}                                         # generic wetting: ignore +-pad, never a positive
    w = T.build_wetting_windows(seg_frame([20.0] * 20 + [40.0] * 15, events=ev))
    assert (w["y"] == T.LABEL_IGNORE).sum() >= 1 and (w["y"] == T.LABEL_POS).sum() == 0
    u = T.usable(w)
    assert (w["y"][u] != T.LABEL_IGNORE).all()
    assert u.sum() == len(w["y"]) - (w["y"] == T.LABEL_IGNORE).sum()


def test_a032_valve_event_is_positive_and_sector5_never_positive():
    m = [20.0] * 20 + [40.0] * 15
    ev = {20: prep.EVENT_WATERING}
    ok = T.build_wetting_windows(seg_frame(m, events=ev))
    s5 = T.build_wetting_windows(seg_frame(m, plant="mendeley_s5", events=ev))
    assert (ok["y"] == T.LABEL_POS).sum() == 1
    assert (s5["y"] == T.LABEL_POS).sum() == 0 and (s5["y"] == T.LABEL_NEG).sum() == 0   # sector 5: all ignored


def test_ignore_pad_is_the_a032_default_of_four():
    assert L.IGNORE_PAD_TICKS == 4 and L.FROZEN_WEAK_LABEL_RULE["slope_pct"] == 5     # no re-tuning (A-032)


def test_rule_baseline_threshold_is_eight_points_per_hour():             # concept 2.3 baseline row
    x = np.zeros((3, T.N_INPUTS), dtype=np.int64)
    x[:, 2 * T.WINDOW - 1] = [7, 8, 20]
    assert list(T.rule_predict(x)) == [False, True, True]


def test_per_class_metrics_reports_both_classes_with_counts():           # A-019
    yt = np.array([1, 1, 1, 0, 0, 0, 0, 0])
    yp = np.array([1, 1, 0, 1, 0, 0, 0, 0])
    m = T.per_class_metrics(yt, yp)
    w, n = m["wetting"], m["normal"]
    assert (w["tp"], w["fp"], w["fn"], w["support"]) == (2, 1, 1, 3)
    assert w["precision"] == pytest.approx(2 / 3) and w["recall"] == pytest.approx(2 / 3)
    assert (n["tp"], n["fp"], n["fn"], n["support"]) == (4, 1, 1, 5)
    assert n["precision"] == pytest.approx(4 / 5) and n["recall"] == pytest.approx(4 / 5)
    lo, hi = w["recall_ci95"]
    assert 0 < lo < 2 / 3 < hi < 1 and hi - lo > 0.4                      # three positives: a very wide interval


def test_per_class_metrics_undefined_is_none_not_zero():
    m = T.per_class_metrics(np.array([0, 0, 0]), np.array([0, 0, 0]))
    assert m["wetting"]["recall"] is None and m["wetting"]["precision"] is None


def test_false_alerts_per_unit_week_uses_672_ticks_per_week():           # FR-E02 <= 1 / unit-week
    yt = np.zeros(1344, dtype=int)                                        # exactly 2 weeks of negatives
    yp = np.zeros(1344, dtype=int)
    yp[:3] = 1
    assert T.per_class_metrics(yt, yp)["false_alerts_per_unit_week"] == pytest.approx(1.5)


def test_choose_p_fast_starts_at_0_9_and_meets_the_budget_on_val():      # concept 2.3
    rng = np.random.default_rng(0)
    p = np.concatenate([rng.uniform(0, 0.5, 2000), [0.95, 0.97]])
    y = np.zeros(len(p), dtype=int)
    thr, met = T.choose_p_fast(p, y)
    assert met and thr >= T.P_FAST_START and (p >= thr).mean() <= T.FP_BUDGET_PER_TICK
    thr2, _ = T.choose_p_fast(np.array([0.1, 0.2]), np.array([0, 0]))
    assert thr2 == T.P_FAST_START


def test_model_a_baseline_eval_excludes_censored_and_unmasked_ticks():   # FR-E01 metric ticks
    d = pd.DataFrame({"plant": "p", "y_mask": [True, True, False, True], "y_censored": [False, False, True, False],
                      "baseline_hours": [5.0, 7.0, 1.0, np.nan], "y_hours": [4.0, 10.0, np.nan, 3.0]})
    r = T.model_a_baseline_eval(d, mean_interval_h=12.0)
    assert r["ticks_metric"] == 2 and r["baseline_mae_h"] == pytest.approx(2.0) and r["ticks_censored"] == 1
    assert r["buckets"]["0-12h"]["n"] == 2 and r["buckets"]["48-72h"]["n"] == 0


def test_unexplained_report_is_separate_from_metrics():                  # A-032
    w = {"event": np.array([prep.EVENT_WETTING, prep.EVENT_WETTING, prep.EVENT_NONE], dtype=object),
         "plant": np.array(["mendeley_s5", "mendeley_s1", "mendeley_s1"], dtype=object)}
    r = T.unexplained_report(w, np.array([True, False, True]))
    assert r["sector5"] == {"onset_ticks": 1, "fired": 1} and r["other_sectors"] == {"onset_ticks": 1, "fired": 0}


# ---- TensorFlow part: skipped where TF is not installed (CI installs only requirements.txt)
def _toy_windows(n=600, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.integers(-3, 4, size=(n, T.N_INPUTS))
    y = np.zeros(n, dtype=int)
    pos = rng.choice(n, n // 10, replace=False)
    X[pos, 2 * T.WINDOW - 1] = rng.integers(12, 40, len(pos))             # a clear rise on positives
    y[pos] = 1
    return X.astype(np.int64), y


def test_training_is_deterministic_per_seed_and_int8_matches_budget():  # FR-E04
    pytest.importorskip("tensorflow")
    X, y = _toy_windows()
    p1 = T.predict_p1(T.train_model(X, y, seed=0, epochs=3), X)
    p2 = T.predict_p1(T.train_model(X, y, seed=0, epochs=3), X)
    assert np.allclose(p1, p2)
    tfl = T.to_int8_tflite(T.train_model(X, y, seed=0, epochs=3), X)
    rep = T.size_report(tfl)
    assert rep["flatbuffer_bytes"] < 30 * 1024 and rep["flash_ok"]       # flash budget
    assert rep["ram_estimate_bytes"] < 20 * 1024                          # RAM budget (estimate, see size_report doc)
    assert rep["input_quant"] == [pytest.approx(1 / 128), 0]             # device feeds its integer features unchanged
    pi = T.tflite_predict_p1(tfl, X[:50])
    assert pi.shape == (50,) and ((pi >= 0) & (pi <= 1)).all()

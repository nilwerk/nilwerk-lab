"""Tests for src/evaluate.py: A-032 enforcing mask (usable = pos | neg), precision/recall counting, Model A baseline table.
SYNTHETIC frames built here. Traces to FR-E01, FR-E02, A-032. No accuracy claimed.
"""
import numpy as np
import pandas as pd
import pytest

import evaluate as EV
import labels as L
import prep


def frame(events, plant="mendeley_s1", n=40, m=None):
    d = pd.DataFrame({"time": pd.date_range("2025-03-03", periods=n, freq="15min"),
                      "m": np.full(n, 50.0) if m is None else np.asarray(m, float)})
    d["plant"], d["event"] = plant, prep.EVENT_NONE
    for i, e in events.items():
        d.loc[i, "event"] = e
    return L.label_wetting_classes(d)


def test_usable_is_pos_or_neg_and_excludes_ignore_ticks():
    f = frame({10: prep.EVENT_WATERING, 25: prep.EVENT_WETTING})
    u = EV.wetting_usable(f)
    assert (u == (f["lbl_wetting_pos"] | f["lbl_wetting_neg"])).all()
    assert not u[f["lbl_wetting_ignore"]].any() and f["lbl_wetting_ignore"].sum() == 2 * L.IGNORE_PAD_TICKS + 1
    assert u[10]                                                                  # the positive is usable


def test_usable_is_empty_for_sector5_and_never_positive():
    f = frame({5: prep.EVENT_WATERING, 15: prep.EVENT_RAIN}, plant="mendeley_s5")
    assert not EV.wetting_usable(f).any()


def test_usable_rejects_sector5_positive_and_broken_partition():
    f = frame({5: prep.EVENT_WATERING}, plant="mendeley_s5")
    bad = f.assign(lbl_wetting_pos=True, lbl_wetting_ignore=False, lbl_wetting_neg=False)
    with pytest.raises(ValueError, match="excluded plant"):
        EV.wetting_usable(bad)
    broken = frame({}).assign(lbl_wetting_neg=False)
    with pytest.raises(ValueError, match="partition"):
        EV.wetting_usable(broken)


def test_precision_recall_ignores_predictions_on_ignore_ticks():
    f = frame({10: prep.EVENT_WATERING, 30: prep.EVENT_WETTING})
    pred = np.zeros(len(f), bool)
    pred[10] = True            # TP
    pred[30] = True            # on an ignore tick: neither TP nor FP
    pred[20] = True            # usable negative: FP
    r = EV.wetting_precision_recall(pd.Series(pred), f)
    assert (r["tp"], r["fp"], r["positives"], r["found"]) == (1, 1, 1, 1)


def test_precision_recall_counts_missed_positive_and_tolerance():
    f = frame({10: prep.EVENT_RAIN, 25: prep.EVENT_WATERING})
    pred = np.zeros(len(f), bool)
    pred[11] = True            # within +-1 of the rain positive
    r = EV.wetting_precision_recall(pd.Series(pred), f, tol=1)
    assert (r["tp"], r["fp"], r["positives"], r["found"]) == (1, 0, 2, 1)


def test_thirst_baseline_table_mae_and_coverage():
    n = 6
    g = pd.DataFrame({"y_mask": [True] * n, "y_hours": [0.0, 2, 4, 6, 8, 10], "y_capped": False,
                      "baseline_hours": [np.nan, 3.0, 4.0, 5.0, np.nan, 12.0], "segment": "a"})
    t = EV.thirst_baseline_table({"train": g, "val": g, "test": g}, const_hours=5.0)
    a = t[(t.split == "train") & (t.subset == "all y_mask")].iloc[0]
    assert a.n_ticks == 6 and a.coverage == pytest.approx(4 / 6)
    assert a.mae_baseline_h == pytest.approx((1 + 0 + 1 + 2) / 4)                 # only ticks where baseline exists
    assert a.mae_constant_h == pytest.approx((5 + 3 + 1 + 1 + 3 + 5) / 6)
    nd = t[(t.split == "train") & (t.subset.str.startswith("m above T"))].iloc[0]
    assert nd.n_ticks == 5 and nd.share_y_zero == 0

"""A-032 default ignore window (Lead decision on Theo C1): IGNORE_PAD_TICKS = 4, used when no pad is passed.
SYNTHETIC frames only. Traces to FR-E02 (wetting class) and FR-E01.
"""
import pandas as pd

import labels as L
import prep


def _seg(onset, n=40):
    d = pd.DataFrame({"time": pd.date_range("2025-03-03", periods=n, freq="15min"), "m": [50.0] * n})
    d["plant"] = "mendeley_s1"
    d["event"] = prep.EVENT_NONE
    d.loc[onset, "event"] = prep.EVENT_WETTING
    return d


def test_default_pad_constant_is_4():
    assert L.IGNORE_PAD_TICKS == 4


def test_default_pad_window_is_onset_plus_minus_4_without_pad_argument():
    r = L.label_wetting_classes(_seg(20))                       # NO pad argument: the default window applies
    ign = list(r.index[r["lbl_wetting_ignore"]])
    assert ign == list(range(16, 25))                           # 20-4 .. 20+4 inclusive = 9 ticks
    assert r.loc[15, "lbl_wetting_neg"] and r.loc[25, "lbl_wetting_neg"]    # first ticks outside are negatives

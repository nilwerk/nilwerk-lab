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


def test_training_windows_inherit_default_pad_4():
    # FR-E02 (A-032): the TRAINING path (train.build_wetting_windows -> labels.label_wetting_classes) must also use the
    # default pad 4, so the ignore ticks of a generic onset at tick 20 are 16..24 in the training labels too.
    import numpy as np
    import pandas as pd
    import train as T
    n = 40
    d = pd.DataFrame({"time": pd.date_range("2025-03-03", periods=n, freq="15min"), "m": [50.0] * n})
    d["m_u8"], d["plant"], d["segment"], d["event"] = 50, "mendeley_s1", "s0", prep.EVENT_NONE
    d.loc[20, "event"] = prep.EVENT_WETTING
    d = L.label_wetting_classes(d)                                        # NO pad argument: default applies
    w = T.build_wetting_windows(d)
    window_ticks = np.arange(T.CONTEXT - 1, n)                            # one window per tick with CONTEXT valid samples
    assert list(window_ticks[w["y"] == T.LABEL_IGNORE]) == list(range(16, 25))

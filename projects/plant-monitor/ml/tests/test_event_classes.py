"""Tests for decision A-032: Model B event classes (positives, ignore mask, sector-5 exclusion, no re-tuning).

ALL DATA IS SYNTHETIC, built here. No accuracy is claimed. Traces to FR-E02 (event detection: wetting + sensor
fault claims only) and FR-E01.
"""
import numpy as np
import pandas as pd
import pytest

import export as E
import labels as L
import prep


def evseg(events: dict, plant="mendeley_s1", n=30):
    d = pd.DataFrame({"time": pd.date_range("2025-03-03", periods=n, freq="15min"), "m": [50.0] * n})
    d["plant"] = plant
    d["event"] = prep.EVENT_NONE
    for i, e in events.items():
        d.loc[i, "event"] = e
    return d


def raw_frame(plants, weeks=12):
    rows = []
    for p, sc in plants:
        t = pd.date_range("2025-03-03", periods=weeks * 7 * 144, freq="10min")
        k = np.arange(len(t))
        saw = (k % 600) / 600.0
        rows.append(pd.DataFrame({"plant": p, "source": "mendeley", "time": t, "moisture_raw": 100 + 300 * sc * (1 - saw),
                                  "irrigation": (k % 600 == 0).astype(float),
                                  "temperature": 20 + 5 * np.sin(k / 144 * 2 * np.pi)}))
    return pd.concat(rows, ignore_index=True)


def test_a032_positives_are_only_valve_and_rain_events():
    r = L.label_wetting_classes(evseg({5: prep.EVENT_WATERING, 15: prep.EVENT_RAIN, 25: prep.EVENT_WETTING}))
    assert list(np.flatnonzero(r["lbl_wetting_pos"])) == [5, 15]
    assert not r.loc[25, "lbl_wetting_pos"]


def test_a032_generic_wetting_is_ignore_not_positive_not_negative():
    r = L.label_wetting_classes(evseg({10: prep.EVENT_WETTING}), pad=2)
    assert list(np.flatnonzero(r["lbl_wetting_ignore"])) == [8, 9, 10, 11, 12]       # onset +-2 ticks
    assert not r.loc[8:12, "lbl_wetting_pos"].any() and not r.loc[8:12, "lbl_wetting_neg"].any()
    assert r.loc[7, "lbl_wetting_neg"] and r.loc[13, "lbl_wetting_neg"]              # just outside: usable negative


def test_a032_classes_partition_every_tick_exactly_once():
    r = L.label_wetting_classes(evseg({3: prep.EVENT_WATERING, 4: prep.EVENT_WETTING, 20: prep.EVENT_RAIN}))
    assert (r[["lbl_wetting_pos", "lbl_wetting_ignore", "lbl_wetting_neg"]].sum(axis=1) == 1).all()


def test_a032_explained_event_next_to_unexplained_stays_positive():
    r = L.label_wetting_classes(evseg({10: prep.EVENT_WATERING, 11: prep.EVENT_WETTING}), pad=2)
    assert r.loc[10, "lbl_wetting_pos"] and not r.loc[10, "lbl_wetting_ignore"]


def test_a032_sector5_has_no_positives_and_is_fully_ignored():
    r = L.label_wetting_classes(evseg({5: prep.EVENT_WATERING, 15: prep.EVENT_RAIN}, plant="mendeley_s5"))
    assert not r["lbl_wetting_pos"].any() and not r["lbl_wetting_neg"].any() and r["lbl_wetting_ignore"].all()
    other = L.label_wetting_classes(evseg({5: prep.EVENT_WATERING}, plant="mendeley_s4"))
    assert other["lbl_wetting_pos"].sum() == 1                                       # only s5 is excluded


def test_a032_fr_e02_claims_cover_wetting_and_sensor_fault_only():
    assert L.FR_E02_CLAIM_CLASSES == ("wetting", "sensor_fault")
    assert "fast_drying" not in L.FR_E02_CLAIM_CLASSES and "waterlogged" not in L.FR_E02_CLAIM_CLASSES


def test_no_retuning_rule_constants_are_frozen():
    # A-032: zero train positives for fast_drying must NOT trigger a threshold change.
    assert L.FROZEN_WEAK_LABEL_RULE == {"slope_pct": 5, "hot_pct": 75, "waterlogged_pct": 95.0, "waterlogged_ticks": 24}
    assert (L.FAST_DRYING_SLOPE_PCT, L.HOT_PCT, L.WATERLOGGED_PCT, L.WATERLOGGED_TICKS) == (5, 75, 95.0, 24)


def test_no_retuning_thresholds_come_from_train_only_even_with_zero_positives():
    # Train: constant slope (p5 = that slope) so nothing is strictly below it -> zero positives. Val data that WOULD
    # produce positives must not change the fitted thresholds, and the zero must stay zero (no fallback fitting).
    n = 40
    tr = pd.DataFrame({"slope_6h": [-3] * n, "temp_now": [20] * n, "feat_valid": True})
    thr = L.fit_fast_drying_thresholds(tr)
    assert thr["slope_6h_p5"] == -3 and thr["temp_p75"] == 20
    assert not L.label_fast_drying(tr, thr).any()
    val = pd.DataFrame({"slope_6h": [-30] * n, "temp_now": [35] * n, "feat_valid": True})
    assert L.label_fast_drying(val, thr).all()                                        # thr unchanged by val data
    assert L.fit_fast_drying_thresholds(tr) == thr


@pytest.fixture(scope="module")
def ds_two_sectors():
    sp = prep.preprocess(raw_frame((("mendeley_s4", 1.0), ("mendeley_s5", 1.0))), seed=3)
    return E.build_dataset(sp)


def test_a032_dataset_partition_and_positive_classes(ds_two_sectors):
    for s in ("train", "val", "test"):
        g = ds_two_sectors[s]
        assert (g[["lbl_wetting_pos", "lbl_wetting_ignore", "lbl_wetting_neg"]].sum(axis=1) == 1).all()
        assert g.loc[g["lbl_wetting_pos"], "event"].isin(["watering", "rain"]).all()


def test_a032_event_class_table_matches_dataset_and_sector5_has_zero_positives(ds_two_sectors):
    d = ds_two_sectors
    t = E.event_class_table(d)
    allr = pd.concat([d[s] for s in ("train", "val", "test")])
    assert t["ticks"].sum() == len(allr)
    assert t["ignore_ticks"].sum() == int(allr["lbl_wetting_ignore"].sum())
    s5 = t[t["plant"] == "mendeley_s5"]
    assert s5["pos_watering"].sum() == 0 and s5["pos_rain"].sum() == 0 and s5["negative_ticks"].sum() == 0
    assert t[t["plant"] == "mendeley_s4"]["pos_watering"].sum() > 0                   # s4 keeps its explained events
    assert {"weak_fast_drying", "weak_waterlogged"} <= set(t.columns)                  # reported separately

"""Unit tests for src/prep.py.

ALL DATA HERE IS SYNTHETIC, generated in the test from simple formulas. It is not from any real
dataset and proves only that each preprocessing step does what the spec says. No model accuracy.
Traces to: FR-E01, FR-E02, FR-E03, NFR-02 (edge-ai-concept.md sections 3.4, 4, 5).
"""
import numpy as np
import pandas as pd
import pytest

import prep


def ts(start, n, freq):
    return pd.date_range(start, periods=n, freq=freq)


# ---------- 1. resample
def test_resample_is_causal_and_on_15min_grid():
    # SYNTHETIC: 10-min observations, value = minutes since start
    t = ts("2025-03-01 00:00", 7, "10min")
    df = pd.DataFrame({"plant": "p", "time": t, "moisture_raw": [0, 10, 20, 30, 40, 50, 60.0]})
    r = prep.resample_15min(df)
    assert list(r["time"].dt.minute) == [0, 15, 30, 45, 0]
    # value at tick = last obs at or before tick: 15 -> 10, 30 -> 30, 45 -> 40, 60 -> 60
    assert list(r["moisture_raw"]) == [0, 10, 30, 40, 60]
    assert not r["masked"].any()


def test_resample_masks_gaps_longer_than_1h_without_interpolating():
    # SYNTHETIC: observations at 0:00 and then a 3 h hole, then 3:00..3:30
    t = pd.to_datetime(["2025-03-01 00:00", "2025-03-01 03:00", "2025-03-01 03:15", "2025-03-01 03:30"])
    df = pd.DataFrame({"plant": "p", "time": t, "moisture_raw": [50.0, 20.0, 21.0, 22.0]})
    r = prep.resample_15min(df).set_index("time")
    assert r.loc["2025-03-01 01:00", "masked"] == False          # age exactly 1 h is still allowed
    assert r.loc["2025-03-01 01:00", "moisture_raw"] == 50.0
    assert r.loc["2025-03-01 01:15", "masked"] == True
    assert np.isnan(r.loc["2025-03-01 02:45", "moisture_raw"])
    assert r.loc["2025-03-01 03:00", "moisture_raw"] == 20.0     # no interpolation towards 50


def test_resample_event_columns_use_interval_max_not_future():
    # SYNTHETIC: valve open in the single 10-min obs at 00:20 -> belongs to tick 00:30 (interval (00:15,00:30])
    t = ts("2025-03-01 00:00", 7, "10min")
    irr = [0, 0, 1, 0, 0, 0, 0.0]
    df = pd.DataFrame({"plant": "p", "time": t, "moisture_raw": 1.0, "irrigation": irr})
    r = prep.resample_15min(df).set_index("time")
    assert r.loc["2025-03-01 00:30", "irrigation"] == 1
    assert r.loc["2025-03-01 00:15", "irrigation"] == 0


# ---------- 3. normalise
def test_normalise_maps_percentiles_to_0_100_and_clips():
    raw = pd.Series(np.linspace(300, 700, 101))                  # SYNTHETIC linear ramp
    dry, wet = prep.fit_dry_wet(raw)
    assert dry == pytest.approx(308.0) and wet == pytest.approx(692.0)
    m = prep.normalise(pd.Series([200, dry, 500, wet, 900.0]), dry, wet)
    assert list(m.round(6)) == [0.0, 0.0, 50.0, 100.0, 100.0] or list(m.round(1)) == [0.0, 0.0, 50.0, 100.0, 100.0]
    assert m.between(0, 100).all()


def test_normalise_handles_inverted_sensor_and_offset_augmentation():
    # SYNTHETIC capacitive-style probe: wetter = LOWER raw value
    m = prep.normalise(pd.Series([800.0, 500.0, 200.0]), dry=800.0, wet=200.0)
    assert list(m) == [0.0, 50.0, 100.0]
    d2, w2 = prep.offset_calibration(800.0, 200.0, shift_dry_pts=10, shift_wet_pts=-10)
    assert (d2, w2) == (740.0, 260.0)                            # span -600: +10 pts of span moves dry by -60


def test_fit_rejects_flat_signal():
    with pytest.raises(ValueError):
        prep.fit_dry_wet(pd.Series([5.0] * 10))


# ---------- dry threshold is data, not model output
def test_dry_threshold_is_a_parameter_default_25():
    m = pd.Series([10.0, 24.9, 25.0, 60.0])
    assert prep.DEFAULT_DRY_THRESHOLD == 25.0
    assert list(prep.below_threshold(m)) == [True, True, False, False]
    assert list(prep.below_threshold(m, threshold=40.0)) == [True, True, True, False]   # per-plant DB value


# ---------- 4. event labelling
def _series_with_jump(kind_cols=None):
    # SYNTHETIC: flat 30, jump to 60 at tick 20, slow decay afterwards; second jump at tick 60
    m = np.full(100, 30.0)
    m[20:] = 60.0 - 0.1 * np.arange(80)
    m[60:] = m[59] + 30.0 - 0.1 * np.arange(40)
    d = pd.DataFrame({"time": ts("2025-03-01", 100, "15min"), "m": m})
    d["irrigation"] = 0.0
    d["rain"] = 0.0
    return d


def test_event_onsets_found_once_and_classified():
    d = _series_with_jump()
    d.loc[19:21, "irrigation"] = 1.0       # valve open at first jump -> watering
    d.loc[59:61, "rain"] = 2.0             # rain at second jump -> rain
    e = prep.label_events(d)
    ev = e[e["event"] != prep.EVENT_NONE]
    assert list(ev.index) == [20, 60] and list(ev["event"]) == [prep.EVENT_WATERING, prep.EVENT_RAIN]


def test_event_without_ground_truth_is_generic_wetting_and_no_false_events_on_decay():
    d = _series_with_jump().drop(columns=["irrigation", "rain"])
    e = prep.label_events(d)
    assert list(e.loc[e["event"] != "none", "event"]) == [prep.EVENT_WETTING] * 2
    assert (e.loc[:19, "event"] == "none").all()


def test_baseline_interval_uses_given_rows_only():
    e = prep.label_events(_series_with_jump())
    assert prep.mean_watering_interval_h(e) == pytest.approx(10.0)    # 40 ticks * 15 min
    assert np.isnan(prep.mean_watering_interval_h(e.iloc[:30]))       # one event -> undefined, not invented


# ---------- 3.4 fault injection
def _clean(n=300):
    return pd.DataFrame({"time": ts("2025-03-01", n, "15min"), "m": np.full(n, 60.0)})   # SYNTHETIC flat 60


def test_inject_fault_classes_are_labelled_and_shaped():
    c = _clean()
    c["temperature"] = 20.0
    out = prep.inject_faults(c, np.random.default_rng(1), length_ticks=24)
    assert set(out["fault"]) == {"none", *prep.FAULT_CLASSES} and "offset" not in set(out["fault"])
    f = {k: out[out["fault"] == k] for k in prep.FAULT_CLASSES}
    assert len(f["out_of_soil"]) == 24 and len(f["flatline"]) == 24 and len(f["dropout"]) == 24 and len(f["spike"]) == 1
    assert f["out_of_soil"]["m"].iloc[-1] < 5.0 and f["out_of_soil"]["m"].iloc[0] > f["out_of_soil"]["m"].iloc[-1]
    assert abs(out.loc[f["out_of_soil"].index[-1], "temperature"] - 20.0) >= 2.5           # temperature drifts
    assert (f["flatline"]["m"] == 60.0).all()                                              # identical readings
    assert abs(f["spike"]["m"].iloc[0] - 60.0) >= 40.0                                     # single-tick jump >= 40
    assert f["dropout"]["m"].isna().sum() == 12 and (f["dropout"]["m"].dropna() == 60.0).all()   # missing, then held
    assert out.loc[out["fault"] == "none", "m"].eq(60.0).all()                             # rest untouched
    assert out["synthetic"].sum() == 24 * 3 + 1 and (out["m_clean"] == 60.0).all()
    assert out["m"].dropna().between(0, 100).all()


def test_fault_injection_is_reproducible_with_seed():
    a = prep.inject_faults(_clean(), np.random.default_rng(7))
    b = prep.inject_faults(_clean(), np.random.default_rng(7))
    pd.testing.assert_frame_equal(a, b)


# ---------- 5. leakage-free split
def _plants(n_weeks=12, plants=("a", "b", "c")):
    # SYNTHETIC: one observation every 6 h per plant
    rows = []
    for p in plants:
        t = ts("2025-03-03", n_weeks * 7 * 4, "6h")
        rows.append(pd.DataFrame({"plant": p, "time": t, "moisture_raw": np.linspace(0, 1, len(t))}))
    return pd.concat(rows, ignore_index=True)


def test_split_has_no_plant_day_in_two_sets_and_gap_before_each_boundary():
    df = _plants()
    df["split"] = prep.assign_split(df)
    df["day"] = df["time"].dt.normalize()
    assert set(df["split"]) == {"train", "val", "test", "drop"}
    assert (df.groupby(["plant", "day"])["split"].nunique() == 1).all()          # a plant-day is in exactly one set
    kept = df[df["split"] != "drop"]
    lookup = df.groupby(["plant", "day"])["split"].first()
    for (p, d), s in kept.groupby(["plant", "day"])["split"].first().items():
        later = lookup.get((p, d + pd.Timedelta(days=3)))
        # a later day that was itself dropped only happens at a boundary one gap further on, so it is same-set by construction
        assert later in (None, "drop", s), f"{p} {d}: 72 h window reaches into {later}"
        for k in (1, 2, 3):                                    # no other set anywhere inside the 3-day look-ahead
            assert lookup.get((p, d + pd.Timedelta(days=k))) in (None, "drop", s)


def test_split_week_pattern_and_heldout_plant():
    df = _plants(plants=("a", "z"))
    df["split"] = prep.assign_split(df, heldout_plants=("z",))
    assert (df.loc[df["plant"] == "z", "split"] == "test").all()
    a = df[df["plant"] == "a"]
    wk = (a["time"].dt.normalize() - a["time"].dt.normalize().min()).dt.days // 7
    assert (a.loc[wk == 4, "split"].isin(["test", "drop"])).all() and (a.loc[wk == 4, "split"] == "test").any()
    assert (a.loc[wk == 5, "split"].isin(["val", "drop"])).all() and (a.loc[wk == 5, "split"] == "val").any()


def test_preprocess_end_to_end_no_leak_of_calibration_or_synthetic_into_test():
    # SYNTHETIC: sawtooth moisture raw 100..400, 10-min cadence, 12 weeks, two plants + one held-out
    rows = []
    for p, scale in (("a", 1.0), ("b", 1.5), ("z", 2.0)):
        t = ts("2025-03-03", 12 * 7 * 144, "10min")
        saw = (np.arange(len(t)) % 600) / 600.0
        rows.append(pd.DataFrame({"plant": p, "time": t, "moisture_raw": 100 + 300 * scale * (1 - saw)}))
    out = prep.preprocess(pd.concat(rows, ignore_index=True), heldout_plants=("z",), seed=3)
    tr, va, te, cal = out["train"], out["val"], out["test"], out["_calibration"]
    assert len(tr) and len(va) and len(te)
    assert (te["fault"] == "none").all() and not te["synthetic"].any()           # test stays free of synthetic data
    assert tr["synthetic"].any()
    assert "z" not in set(tr["plant"]) | set(va["plant"])                         # held-out plant never trained on
    assert tr["m"].dropna().between(0, 100).all() and te["m"].dropna().between(0, 100).all()
    # calibration comes from train rows only: re-fit and compare for plant a
    dry, wet = prep.fit_dry_wet(tr[tr["plant"] == "a"]["moisture_raw"])
    c = cal.set_index("plant").loc["a"]
    assert (c["dry"], c["wet"]) == (dry, wet)
    counts = prep.split_counts(out)
    assert list(counts["split"]) == ["train", "val", "test"] and counts.loc[0, "ticks"] == len(tr)


# ---------- refractory suppression (kills the refractory_ticks mutation)
def _two_rises(second_at):
    m = np.full(60, 30.0)
    m[10:13] = 45.0                     # first rise visible at tick 10
    m[second_at:second_at + 3] = 45.0   # second rise after a return to 30
    return pd.DataFrame({"time": ts("2025-03-01", 60, "15min"), "m": m})


def test_refractory_suppresses_second_onset_within_8_ticks_but_not_after():
    assert list(prep.label_events(_two_rises(16)).query("event != 'none'").index) == [10]    # gap 6 -> one onset
    assert list(prep.label_events(_two_rises(18)).query("event != 'none'").index) == [10]    # gap 8 -> still suppressed
    assert list(prep.label_events(_two_rises(19)).query("event != 'none'").index) == [10, 19]  # gap 9 -> both
    assert list(prep.label_events(_two_rises(16), refractory_ticks=0).query("event != 'none'").index) == [10, 16]


# ---------- segments: nothing spans a join between non-contiguous data
def _seg_frame():
    # SYNTHETIC: two segments separated by a gap; segment 1 ends low (20), segment 2 starts high (60)
    a = pd.DataFrame({"time": ts("2025-03-01", 40, "15min"), "m": np.full(40, 20.0)})
    b = pd.DataFrame({"time": ts("2025-03-10", 40, "15min"), "m": np.full(40, 60.0)})
    d = pd.concat([a, b], ignore_index=True)
    d["segment"] = prep.add_segments(d)
    return d


def test_add_segments_breaks_at_gaps():
    d = _seg_frame()
    assert list(d["segment"].unique()) == [0, 1] and (d["segment"].iloc[:40] == 0).all()


def test_no_event_invented_across_join_and_baseline_ignores_gap():
    d = _seg_frame()
    flat = pd.concat([prep.label_events(g.reset_index(drop=True)) for _, g in d.groupby("segment")], ignore_index=True)
    assert (flat["event"] == "none").all()                          # a 20 -> 60 jump across the gap is not a rise
    # shift over the concatenated frame WOULD invent one: shows why per-segment matters
    assert (prep.label_events(d.drop(columns="segment"))["event"] != "none").any()
    # baseline: events 10 h apart inside each segment; the 9-day join must not enter the mean
    e = d.assign(event="none")
    e.loc[[0, 40 - 1, 40, 79], "event"] = "wetting"
    assert prep.mean_watering_interval_h(e) == pytest.approx(((39 * 0.25) + (39 * 0.25)) / 2)
    assert prep.mean_watering_interval_h(e.drop(columns="segment")) > 24 * 3     # without segments the gap leaks in


def test_preprocess_never_places_faults_or_events_across_segments():
    out = prep.preprocess(_long_sawtooth(), seed=5)
    for name in ("train", "val"):
        for seg, g in out[name].groupby("segment"):
            assert (g["time"].diff().dropna() <= pd.Timedelta("15min")).all()      # each segment is contiguous
            f = g[g["fault"] != "none"]
            assert f.groupby("fault")["time"].apply(lambda t: (t.diff().dropna() <= pd.Timedelta("15min")).all()).all()
    assert out["train"]["segment"].nunique() > 1


def _long_sawtooth(plants=(("a", 1.0, "mendeley"), ("b", 1.5, "mendeley")), weeks=12, start="2025-03-03", freq="10min"):
    rows = []
    for p, scale, src in plants:
        t = ts(start, weeks * 7 * (144 if freq == "10min" else 24), freq)
        saw = (np.arange(len(t)) % 600) / 600.0
        rows.append(pd.DataFrame({"plant": p, "source": src, "time": t, "moisture_raw": 100 + 300 * scale * (1 - saw)}))
    return pd.concat(rows, ignore_index=True)


# ---------- global calendar-week split
def test_split_uses_global_weeks_not_per_plant_counts():
    # SYNTHETIC: plant b starts 3 days after plant a; with per-plant weeks their test weeks would be offset
    a = pd.DataFrame({"plant": "a", "time": ts("2025-03-03", 12 * 28, "6h"), "moisture_raw": 1.0})
    b = pd.DataFrame({"plant": "b", "time": ts("2025-03-06", 12 * 28, "6h"), "moisture_raw": 1.0})
    df = pd.concat([a, b], ignore_index=True)
    df["split"] = prep.assign_split(df)
    df["wk"] = (df["time"].dt.normalize() - pd.Timestamp("2025-03-03")).dt.days // 7
    kept = df[df["split"] != "drop"]
    expect = lambda wk: "test" if wk % 5 == 4 else ("val" if wk % 5 == 0 and wk > 0 else "train")
    assert all(sp == expect(wk) for wk, sp in zip(kept["wk"], kept["split"]))        # same rule, same week index for a and b
    for sp in ("test", "val"):
        assert {p: set(kept[(kept["plant"] == p) & (kept["split"] == sp)]["wk"]) for p in "ab"}["b"] <= {4, 9} | {5, 10}
    # no calendar day is test for one plant and train/val for the other
    assert (kept.groupby(kept["time"].dt.normalize())["split"].nunique() == 1).all()


# ---------- source column and hourly flag
def test_source_column_flows_to_outputs_and_mendeley_only_variant():
    raw = pd.concat([_long_sawtooth(), _long_sawtooth(plants=(("i1", 1.2, "ismn"),))], ignore_index=True)
    both = prep.preprocess(raw, seed=1)
    only = prep.preprocess(raw, seed=1, sources=("mendeley",))
    assert set(both["train"]["source"]) == {"mendeley", "ismn"}
    assert set(only["train"]["source"]) == {"mendeley"} and "i1" not in set(only["_calibration"]["plant"])
    assert set(only["_calibration"]["source"]) == {"mendeley"}
    only2 = prep.preprocess(raw, seed=1, sources=("mendeley",))
    pd.testing.assert_frame_equal(only["train"], only2["train"])                  # reproducible
    assert "ISMN" in prep.model_label(both["train"]) and "ISMN" not in prep.model_label(only["train"])
    assert "source_ismn" in prep.split_counts(both).columns


def test_missing_source_defaults_to_unspecified_and_mixed_source_per_plant_rejected():
    out = prep.preprocess(_long_sawtooth().drop(columns="source"), seed=1)
    assert set(out["train"]["source"]) == {"unspecified"}
    bad = pd.DataFrame({"plant": "p", "source": ["a", "b"], "time": ts("2025-03-01", 2, "1h"), "moisture_raw": [1.0, 2.0]})
    with pytest.raises(ValueError):
        prep.resample_15min(bad)


def test_hourly_source_is_flagged_upsampled_and_fresh_marks_real_observations():
    t = ts("2025-03-01", 5, "1h")
    hourly = pd.DataFrame({"plant": "h", "source": "ismn", "time": t, "moisture_raw": [1, 2, 3, 4, 5.0]})
    r = prep.resample_15min(hourly)
    assert r["upsampled"].all() and len(r) == 17
    assert r["fresh"].sum() == 5 and list(r["fresh"].iloc[:5]) == [True, False, False, False, True]
    fine = pd.DataFrame({"plant": "f", "source": "mendeley", "time": ts("2025-03-01", 20, "10min"), "moisture_raw": 1.0})
    assert not prep.resample_15min(fine)["upsampled"].any()


def test_empty_split_warns():
    with pytest.warns(UserWarning, match="empty"):
        prep.preprocess(_long_sawtooth(weeks=3), seed=1, inject=False)

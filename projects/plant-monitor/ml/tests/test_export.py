"""Tests for src/export.py: feature frame, dataset assembly, parquet-or-CSV export, plus an end-to-end
leakage check of the label thresholds. ALL DATA IS SYNTHETIC; no accuracy claimed.
Traces to: FR-E01, FR-E02, FR-E03, FR-E04, NFR-02.
"""
import json

import numpy as np
import pandas as pd
import pytest

import export as E
import features as F
import labels as L
import prep


def raw_frame(weeks=12, plants=(("a", 1.0), ("b", 1.5), ("c", 1.2))):
    rows = []
    for p, sc in plants:
        t = pd.date_range("2025-03-03", periods=weeks * 7 * 144, freq="10min")
        k = np.arange(len(t))
        saw = (k % 600) / 600.0
        rows.append(pd.DataFrame({"plant": p, "source": "mendeley", "time": t, "moisture_raw": 100 + 300 * sc * (1 - saw),
                                  "irrigation": (k % 600 == 0).astype(float),
                                  "temperature": 20 + 5 * np.sin(k / 144 * 2 * np.pi)}))
    return pd.concat(rows, ignore_index=True)


@pytest.fixture(scope="module")
def ds():
    sp = prep.preprocess(raw_frame(), heldout_plants=("c",), seed=1)
    return E.build_dataset(sp)


# ---------- build_features
def _seg(n=200, m=None, with_temp=True):
    d = pd.DataFrame({"time": pd.date_range("2025-03-03", periods=n, freq="15min"),
                      "m": np.linspace(80, 20, n) if m is None else np.asarray(m, float)})
    if with_temp:
        d["temperature"] = 21.0
    return d


def test_feature_valid_boundary_95_vs_96_samples():
    f = E.build_features(_seg())
    assert not f["feat_valid"].iloc[94] and f["feat_valid"].iloc[95]            # first valid tick has exactly 96 samples
    assert not f["feat_valid"].iloc[:95].any()


def test_nan_in_window_invalidates_exactly_the_windows_containing_it():
    m = np.linspace(80, 20, 300)
    m[150] = np.nan
    f = E.build_features(_seg(300, m))
    assert not f["feat_valid"].iloc[150:246].any()          # windows ending at 150..245 contain tick 150
    assert f["feat_valid"].iloc[246] and f["feat_valid"].iloc[149]


def test_feature_columns_are_int8_and_match_scalar_function():
    f = E.build_features(_seg(), T=25, soil="pot")
    assert all(f[c].dtype == np.int8 for c in E.FEAT_COLS)
    i = 150
    m_u8 = [F.quantise_m(v) for v in f["m"].iloc[i - 95:i + 1]]
    since = F.ticks_since_event_series([F.quantise_m(v) for v in f["m"]])[i]
    t = f["time"].iloc[i]
    exp = F.feature_vector(m_u8, [F.quantise_temp(21.0)] * 96, [128] * 96, t.hour * 60 + t.minute, 25, int(since), F.SOIL_CODES["pot"])
    assert [int(f[c].iloc[i]) for c in E.FEAT_COLS] == exp


def test_placeholders_flagged_when_temperature_or_light_missing():
    f = E.build_features(_seg(with_temp=False))
    assert not f["temp_known"].iloc[0] and not f["light_known"].iloc[0]
    assert f["f_temp_now"].iloc[150] == 20                      # 20 degC placeholder
    g = E.build_features(_seg().assign(light=200))
    assert g["light_known"].iloc[0] and g["f_light_mean_6h"].iloc[150] == 72


def test_threshold_T_dry_default_25_and_rounding_in_T_u8():
    for T, exp in [(24.49, 24 - 50), (24.5, 25 - 50), (25.0, -25)]:
        assert E.build_features(_seg(), T=T)["f_T"].iloc[150] == exp


# ---------- build_dataset
def test_dataset_columns_and_masks_are_explicit(ds):
    for s in ("train", "val", "test"):
        for c in ("y_hours", "y_censored", "y_censor_reason", "y_mask", "y_capped", "feat_valid", "baseline_hours",
                  "lbl_fast_drying", "lbl_waterlogged", *E.FEAT_COLS, "source", "segment"):
            assert c in ds[s].columns, (s, c)
    tr = ds["train"]
    assert tr["y_mask"].sum() > 0 and (tr.loc[tr["y_censored"], "y_mask"] == False).all()    # censored never in the metric
    assert tr.loc[tr["fault"] != "none", "y_mask"].eq(False).all()


def test_dataset_meta_is_synthetic_flagged_and_baseline_from_train_only(ds):
    assert ds["_meta"]["synthetic_only"] is True
    assert ds["_meta"]["baseline_mean_interval_h"] == pytest.approx(100.0)       # sawtooth of 600 ticks of 10 min
    assert ds["test"]["synthetic"].sum() == 0                                    # no synthetic data in test


def test_labels_never_cross_segments(ds):
    for _, g in ds["train"].groupby("segment"):
        assert (g["time"].diff().dropna() <= pd.Timedelta("15min")).all()


def test_counts_table(ds):
    c = E.dataset_counts(ds)
    assert list(c["split"]) == ["train", "val", "test"] and (c["ticks"] > 0).all()
    assert (c["y_mask"] <= c["ticks"]).all() and (c["feat_valid"] <= c["ticks"]).all()


# ---------- export
def test_export_writes_parquet_when_engine_available_and_csv_otherwise(ds, tmp_path):
    man = E.export_dataset(ds, tmp_path / "pq")
    assert man["format"] == ("parquet" if E.parquet_available() else "csv")
    man_csv = E.export_dataset(ds, tmp_path / "csv", prefer_parquet=False)
    assert man_csv["format"] == "csv" and (tmp_path / "csv" / "train.csv").exists()


def test_csv_roundtrip_keeps_features_and_labels(ds, tmp_path):
    E.export_dataset(ds, tmp_path, prefer_parquet=False)
    back = E.read_table(tmp_path / "val.csv")
    assert len(back) == len(ds["val"])
    assert (back[E.FEAT_COLS].to_numpy() == ds["val"][E.FEAT_COLS].to_numpy()).all()
    assert np.allclose(back["y_hours"], ds["val"]["y_hours"], equal_nan=True)
    assert (back["y_mask"] == ds["val"]["y_mask"]).all()


def test_parquet_roundtrip_if_engine(ds, tmp_path):
    if not E.parquet_available():
        pytest.skip("no parquet engine installed: CSV export used (documented fallback)")
    E.export_dataset(ds, tmp_path)
    back = E.read_table(tmp_path / "train.parquet")
    assert back.shape == ds["train"].shape and back["f_m_now"].dtype == np.int8


def test_manifest_states_synthetic_and_counts(ds, tmp_path):
    E.export_dataset(ds, tmp_path)
    man = json.loads((tmp_path / "manifest.json").read_text())
    assert man["meta"]["synthetic_only"] is True and len(man["counts"]) == 3
    assert set(man["files"]) == {"train", "val", "test"}


def test_write_table_falls_back_to_csv_when_no_engine(monkeypatch, tmp_path):
    monkeypatch.setattr(E, "parquet_available", lambda: False)
    p = E.write_table(pd.DataFrame({"a": [1, 2]}), tmp_path / "x")
    assert p.suffix == ".csv" and p.exists()


def test_baseline_interval_comes_from_train_rows_only_not_test():
    # SYNTHETIC: watering every 100 h in weeks 0-4 (train), every 50 h later (test is week 4 of each block of 5)
    rows = []
    for p in ("a", "b"):
        t = pd.date_range("2025-03-03", periods=12 * 7 * 144, freq="10min")
        k = np.arange(len(t))
        period = np.where(k < 4 * 7 * 144, 600, 300)
        phase = (k % period) / period
        rows.append(pd.DataFrame({"plant": p, "source": "mendeley", "time": t, "moisture_raw": 100 + 300 * (1 - phase),
                                  "irrigation": (k % period == 0).astype(float)}))
    sp = prep.preprocess(pd.concat(rows, ignore_index=True), seed=2)
    ds2 = E.build_dataset(sp)
    m_train = prep.mean_watering_interval_h(sp["train"])
    m_test = prep.mean_watering_interval_h(sp["test"])
    assert abs(m_train - m_test) > 5                                 # the scenario really separates train from test
    assert ds2["_meta"]["baseline_mean_interval_h"] == pytest.approx(m_train)

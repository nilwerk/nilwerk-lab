"""Tests for src/loaders.py (Mendeley loader). Traces to FR-E01..FR-E03, NFR-02.

Unit tests use SYNTHETIC mini CSVs written in the test with the real column names of
02_processed_data/merged/dataset_zone_N.csv. The integration test runs on the real files if they were
downloaded (scripts/fetch_mendeley.sh) and is skipped otherwise; its numbers are DATA COUNTS, not model results.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import loaders
import prep

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
COLS = ["ts", "weather_temp", "weather_rain", "soil_moisture", "irrigation_duration_minutes"]


def write_zone(root: Path, sector: int, rows: list) -> None:
    d = root / "x" / "02_processed_data" / "merged"
    d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=COLS).to_csv(d / f"dataset_zone_{sector}.csv", index=False)


def test_local_time_becomes_utc_summer_and_winter():
    # SYNTHETIC: Europe/Rome is UTC+2 in July, UTC+1 in February
    t = pd.Series(pd.to_datetime(["2025-07-01 12:00", "2025-02-01 12:00"]))
    assert list(loaders.local_to_utc(t)) == list(pd.to_datetime(["2025-07-01 10:00", "2025-02-01 11:00"]))


def test_out_of_scale_moisture_is_dropped_not_clipped(tmp_path):
    # SYNTHETIC: -47 and 717 are error codes seen in the real files
    ts = pd.date_range("2025-07-01", periods=5, freq="10min")
    write_zone(tmp_path, 1, [[ts[0], 20, 0, 40.0, 0], [ts[1], 20, 0, -47.0, 0], [ts[2], 20, 0, 717.0, 0],
                             [ts[3], 20, 0, np.nan, 0], [ts[4], 20, 0, 55.0, 3.0]])
    f, st = loaders.load_sector(tmp_path / "x" / "02_processed_data" / "merged" / "dataset_zone_1.csv", 1)
    assert list(f["moisture_raw"]) == [40.0, 55.0]
    assert st["probe_rows"] == 4 and st["valid_rows"] == 2 and st["dropped_out_of_range"] == 2
    assert list(f["irrigation"]) == [0.0, 3.0] and (f["source"] == "mendeley").all()


def test_dead_probe_sector_is_excluded_with_reason(tmp_path):
    # SYNTHETIC: sector 1 healthy, sector 3 mostly exactly 0 (as the real sector 3: 84.5 % zeros)
    ts = pd.date_range("2025-07-01", periods=10, freq="10min")
    write_zone(tmp_path, 1, [[t, 20, 0, 30.0 + i, 0] for i, t in enumerate(ts)])
    write_zone(tmp_path, 3, [[t, 20, 0, 0.0 if i < 9 else 50.0, 0] for i, t in enumerate(ts)])
    raw, st = loaders.load_mendeley(tmp_path, sectors=(1, 3))
    assert list(raw["plant"].unique()) == ["mendeley_s1"]
    assert st.set_index("sector").loc[3, "excluded"].startswith("zero share") and st.set_index("sector").loc[1, "excluded"] == ""


def test_loader_output_feeds_preprocess_without_errors(tmp_path):
    # SYNTHETIC: 6 weeks of a saw-tooth probe, enough for the global-week split
    ts = pd.date_range("2025-03-03", periods=6 * 7 * 144, freq="10min")
    m = 60 - (np.arange(len(ts)) % 288) * 0.1
    write_zone(tmp_path, 2, [[t, 15, 0, v, 0] for t, v in zip(ts, m)])
    raw, _ = loaders.load_mendeley(tmp_path, sectors=(2,))
    sp = prep.preprocess(raw, inject=False)
    assert set(sp["train"]["source"]) == {"mendeley"} and len(sp["train"]) > 0


REAL = (RAW / "ex").exists()


@pytest.mark.skipif(not REAL, reason="Mendeley files not downloaded (scripts/fetch_mendeley.sh)")
def test_real_mendeley_counts_match_data_card():
    raw, st = loaders.load_mendeley(RAW)
    assert sorted(raw["plant"].unique()) == ["mendeley_s1", "mendeley_s2", "mendeley_s4", "mendeley_s5"]
    assert st.set_index("sector").loc[3, "excluded"] != ""            # dead probe gate fires on the real file
    assert len(raw) == 41258
    assert str(raw["time"].min()) == "2025-02-10 12:50:00" and str(raw["time"].max()) == "2025-09-24 14:10:00"
    sp = prep.preprocess(raw, inject=False, seed=0)
    ev = pd.concat([sp[s] for s in ("train", "val", "test")])["event"].value_counts()
    assert (ev["watering"], ev["rain"], ev["wetting"]) == (219, 125, 556)
    assert {s: len(sp[s]) for s in ("train", "val", "test")} == {"train": 46715, "val": 8832, "test": 9311}

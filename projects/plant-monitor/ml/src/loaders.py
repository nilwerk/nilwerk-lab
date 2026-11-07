"""Loaders that turn a concrete dataset into the canonical frame of prep.py (task 4.AI1).

Mendeley "Soil Moisture, Irrigation Actuator and Weather Dataset from a Multi-Sector Precision-Irrigation"
(doi 10.17632/c837v6p8ph.2, CC BY 4.0 per the dataset page, read 2026-11-06). Traces to FR-E01..FR-E03, NFR-02.

Layer used: 02_processed_data/merged/dataset_zone_{1..5}.csv (10-min grid, soil moisture = probe output on a
0-100 scale, raw/unfiltered, gaps kept as empty cells). NOT the "preprocessed" layer: its 24 h targets, cleaning
and interpolation are the authors' choices and its horizon is counted in rows, not hours (README section 7).

Mapping (all choices documented in data-cards/mendeley-precision-irrigation.md):
  plant        "mendeley_s<sector>"          (one probe per sector; 5 sectors)
  time         ts, Europe/Rome local naive -> UTC naive (DATA_DICTIONARY: "all timestamps are local time")
  moisture_raw soil_moisture; values outside [0, 100] are error codes/out of scale -> dropped (not clipped)
  irrigation   irrigation_duration_minutes (>0 while the valve was open in the bin). Ground truth for labelling
               only; valve telemetry is NEVER a model feature (concept 3.1).
  rain         weather_rain (ERA5 reanalysis, farm-wide, mm). A weak proxy: it is not an in-pot rain gauge.
  temperature  weather_temp (ERA5 air temperature, deg C), only used to make out-of-soil faults drift.
  source       "mendeley"

Quality gate: a sector whose valid readings are more than QUALITY_MAX_ZERO_SHARE exactly 0 is a dead or
saturated probe (sector 3: 84.5 % zeros) and is excluded, with the reason returned to the caller.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SOURCE = "mendeley"
SECTORS = (1, 2, 3, 4, 5)
LOCAL_TZ = "Europe/Rome"
QUALITY_MAX_ZERO_SHARE = 0.5
MOISTURE_VALID = (0.0, 100.0)


def find_root(raw_dir: Path) -> Path:
    """The directory that contains 02_processed_data (zip extracts into one extra level)."""
    raw_dir = Path(raw_dir)
    hits = [p.parent for p in raw_dir.rglob("02_processed_data") if p.is_dir()]
    if not hits:
        raise FileNotFoundError(f"no 02_processed_data under {raw_dir}")
    return sorted(hits)[0]


def local_to_utc(ts: pd.Series) -> pd.Series:
    """Europe/Rome naive local -> UTC naive. Nonexistent (spring-forward) times are shifted, ambiguous -> NaT."""
    return (ts.dt.tz_localize(LOCAL_TZ, ambiguous="NaT", nonexistent="shift_forward")
              .dt.tz_convert("UTC").dt.tz_localize(None))


def load_sector(path: Path, sector: int) -> tuple[pd.DataFrame, dict]:
    """One merged-layer CSV -> canonical rows (only ticks with a valid moisture reading) and a stats dict."""
    d = pd.read_csv(path, parse_dates=["ts"])
    n_grid = len(d)
    sm = d["soil_moisture"]
    n_probe = int(sm.notna().sum())
    ok = sm.between(*MOISTURE_VALID)
    zero_share = float((sm[ok] == 0).mean()) if ok.any() else float("nan")
    d = d[ok].copy()
    d["time"] = local_to_utc(d["ts"])
    d = d[d["time"].notna()]
    out = pd.DataFrame({
        "plant": f"mendeley_s{sector}",
        "time": d["time"].to_numpy(),
        "moisture_raw": d["soil_moisture"].to_numpy(dtype=float),
        "irrigation": d["irrigation_duration_minutes"].fillna(0.0).to_numpy(dtype=float),
        "rain": d["weather_rain"].fillna(0.0).to_numpy(dtype=float),
        "temperature": d["weather_temp"].to_numpy(dtype=float),
        "source": SOURCE,
    }).sort_values("time").reset_index(drop=True)
    stats = {"sector": sector, "grid_rows": n_grid, "probe_rows": n_probe, "valid_rows": len(out),
             "dropped_out_of_range": n_probe - int(ok.sum()), "zero_share": zero_share,
             "first_utc": out["time"].min(), "last_utc": out["time"].max(),
             "irrigation_bins": int((out["irrigation"] > 0).sum()), "rain_bins": int((out["rain"] > 0).sum())}
    return out, stats


def load_mendeley(raw_dir: Path, sectors: tuple[int, ...] = SECTORS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Canonical frame of all usable sectors + a per-sector stats table (with `excluded` reason, '' if kept)."""
    root = find_root(raw_dir) / "02_processed_data" / "merged"
    frames, stats = [], []
    for s in sectors:
        f, st = load_sector(root / f"dataset_zone_{s}.csv", s)
        reason = ""
        if not st["zero_share"] <= QUALITY_MAX_ZERO_SHARE:
            reason = f"zero share {st['zero_share']:.3f} > {QUALITY_MAX_ZERO_SHARE} (dead/saturated probe)"
        st["excluded"] = reason
        stats.append(st)
        if not reason:
            frames.append(f)
    if not frames:
        raise ValueError("no usable sector")
    return pd.concat(frames, ignore_index=True), pd.DataFrame(stats)

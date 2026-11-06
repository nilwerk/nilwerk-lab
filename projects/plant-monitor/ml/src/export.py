"""Feature frame builder, dataset assembly and table export (parquet if an engine exists, else CSV).

Implements docs/edge-ai-concept.md section 4 steps 5, 6 and 8. Traces to FR-E01, FR-E02, FR-E03, NFR-02.
SYNTHETIC-ONLY STATUS: no real dataset was loaded (hosts blocked, A-007); nothing here is a result.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

import features as F
import labels as L
import prep

FEAT_COLS = ["f_" + n for n in F.FEATURE_NAMES]


def parquet_available() -> bool:
    """True when pandas can write parquet (pyarrow or fastparquet importable). Else we export CSV."""
    return any(importlib.util.find_spec(x) is not None for x in ("pyarrow", "fastparquet"))


def build_features(seg: pd.DataFrame, T: float = prep.DEFAULT_DRY_THRESHOLD, soil: str = "pot",
                   default_temp_c: float = 20.0) -> pd.DataFrame:
    """Feature columns for every tick of ONE contiguous segment (device pipeline of concept 2.1, features.py).

    Adds: m_u8, f_<name> (14 int8-range ints), feat_valid (False during the first 95 ticks of the segment or
    when any of the last 96 m samples is missing), light_known (False: the public datasets have no light; the
    light sample is then a constant 128 placeholder and the feature must not be used for fast-drying labels),
    temp_known (False when no temperature column: constant default_temp_c placeholder).
    The wetting-event counter runs over the whole segment (EventTracker), exactly like the device would.
    Window features need 96 valid samples, so at segment starts the counter is unknown and saturated (72 h).
    FR-E01, FR-E04.
    """
    d = seg.reset_index(drop=True)
    n = len(d)
    m_valid = d["m"].notna().to_numpy()
    m_u8 = np.array([F.quantise_m(v) if ok else 0 for v, ok in zip(d["m"].fillna(0.0), m_valid)], dtype=np.int64)
    temp_known = "temperature" in d.columns and d["temperature"].notna().all()
    temp_u8 = (np.array([F.quantise_temp(v) for v in d["temperature"]], dtype=np.int64) if temp_known
               else np.full(n, F.quantise_temp(default_temp_c), dtype=np.int64))
    light_known = "light" in d.columns and d["light"].notna().all()
    light_u8 = d["light"].to_numpy(dtype=np.int64) if light_known else np.full(n, 128, dtype=np.int64)
    since = F.ticks_since_event_series(m_u8, m_valid)
    minute = (d["time"].dt.hour * 60 + d["time"].dt.minute).to_numpy()
    soil_code = F.soil_code(soil)  # db soil_type or device code name (C4)
    T_u8 = F.clip(int(np.floor(T + 0.5)), 0, 100)
    rows = np.zeros((n, len(F.FEATURE_NAMES)), dtype=np.int64)
    ok = np.zeros(n, dtype=bool)
    for i in range(F.HIST - 1, n):
        sl = slice(i - F.HIST + 1, i + 1)
        if not m_valid[sl].all():
            continue
        rows[i] = F.feature_vector(m_u8[sl], temp_u8[sl], light_u8[sl], int(minute[i]), T_u8, int(since[i]), soil_code)
        ok[i] = True
    out = d.copy()
    out["m_u8"] = m_u8
    for k, c in enumerate(FEAT_COLS):
        out[c] = rows[:, k].astype(np.int8)
    out["feat_valid"] = ok
    out["temp_known"] = bool(temp_known)
    out["light_known"] = bool(light_known)
    return out


def event_agreement(seg: pd.DataFrame) -> dict:
    """C6: agreement of label events (float prep.label_events) and device events (EventTracker on rounded m_u8) on ONE
    segment. Returns counts and rate = matched / max(1, union), matching onsets within +-1 tick. FR-E01."""
    f = build_features(seg)
    d = f.reset_index(drop=True)
    lab = np.flatnonzero((prep.label_events(d)["event"] != prep.EVENT_NONE).to_numpy())
    tr = F.EventTracker()
    dev = np.array([i for i, (m, ok) in enumerate(zip(d["m_u8"], d["m"].notna())) if tr.step(int(m), bool(ok))], dtype=int)
    matched = sum(1 for i in lab if len(dev) and np.abs(dev - i).min() <= 1)
    union = len(lab) + len(dev) - matched
    return {"label_events": int(len(lab)), "device_events": int(len(dev)), "matched": int(matched),
            "agreement_rate": matched / max(1, union)}


def build_dataset(splits: dict[str, pd.DataFrame], T: float = prep.DEFAULT_DRY_THRESHOLD, soil: str = "pot") -> dict:
    """Per split: features + Model A labels (+ baseline) + Model B weak labels, computed per contiguous segment.

    Fast-drying thresholds are fitted on the TRAIN split only. The baseline mean interval comes from TRAIN events
    only. Returns {'train','val','test', '_meta'}. FR-E01, FR-E02, FR-E03.
    """
    feats = {}
    for s in ("train", "val", "test"):
        parts = [build_features(g, T=T, soil=soil) for _, g in splits[s].groupby("segment", sort=False)]
        feats[s] = pd.concat(parts, ignore_index=True) if parts else splits[s].iloc[0:0].copy()
    train_feat = feats["train"]
    thr = L.fit_fast_drying_thresholds(train_feat.rename(columns=lambda c: c[2:] if c.startswith("f_") else c))
    mean_int = prep.mean_watering_interval_h(splits["train"])
    out = {}
    for s in ("train", "val", "test"):
        parts = []
        for _, g in feats[s].groupby("segment", sort=False):
            g = L.label_hours_to_threshold(g, threshold=T)
            g["baseline_hours"] = L.baseline_hours(g, mean_int)
            plain = g.rename(columns=lambda c: c[2:] if c.startswith("f_") else c)
            g["lbl_fast_drying"] = L.label_fast_drying(plain, thr).to_numpy()
            g["lbl_waterlogged"] = L.label_waterlogged(g).to_numpy()
            parts.append(g)
        out[s] = pd.concat(parts, ignore_index=True) if parts else feats[s]
    out["_meta"] = {"dry_threshold": T, "soil": soil, "baseline_mean_interval_h": mean_int, "fast_drying_thresholds": thr,
                    "synthetic_only": True, "feature_names": list(F.FEATURE_NAMES), "feature_spec": F.FEATURE_SPEC}
    return out


def dataset_counts(ds: dict) -> pd.DataFrame:
    """Tick, mask, censoring and weak-label counts per split, for the data card (concept 4, step 8)."""
    rows = []
    for s in ("train", "val", "test"):
        g = ds[s]
        rows.append({"split": s, "ticks": len(g), "feat_valid": int(g["feat_valid"].sum()), "y_mask": int(g["y_mask"].sum()),
                     "y_censored_event": int((g["y_censor_reason"] == L.CENSOR_EVENT).sum()),
                     "y_censored_gap": int((g["y_censor_reason"] == L.CENSOR_GAP).sum()),
                     "y_censored_data_end": int((g["y_censor_reason"] == L.CENSOR_DATA_END).sum()),
                     "y_capped_72h": int(g["y_capped"].sum()),
                     "fast_drying": int(g["lbl_fast_drying"].sum()), "waterlogged": int(g["lbl_waterlogged"].sum())})
    return pd.DataFrame(rows)


def write_table(df: pd.DataFrame, stem: Path, prefer_parquet: bool = True) -> Path:
    """Write df to <stem>.parquet when an engine exists (and prefer_parquet), else <stem>.csv. Returns the path."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    if prefer_parquet and parquet_available():
        p = stem.with_suffix(".parquet")
        df.to_parquet(p, index=False)
    else:
        p = stem.with_suffix(".csv")
        df.to_csv(p, index=False)
    return p


def read_table(path: Path) -> pd.DataFrame:
    path = Path(path)
    return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, parse_dates=["time"])


def export_dataset(ds: dict, out_dir: Path, prefer_parquet: bool = True) -> dict:
    """Write one table per split plus manifest.json (counts, thresholds, format, synthetic flag). Raw data never
    goes in git: out_dir is gitignored (ml/.gitignore: out/). Returns the manifest."""
    out_dir = Path(out_dir)
    files = {s: write_table(ds[s], out_dir / s, prefer_parquet).name for s in ("train", "val", "test")}
    manifest = {"files": files, "format": Path(next(iter(files.values()))).suffix.lstrip("."),
                "counts": dataset_counts(ds).to_dict(orient="records"), "meta": ds["_meta"]}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    return manifest

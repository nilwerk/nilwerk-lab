"""Dataset preprocessing for the Edge AI models (task 4.AI1).

Implements docs/edge-ai-concept.md sections 3.4, 4 and 5. Traces to FR-E01..FR-E03, NFR-02.

Canonical input frame (one row per raw observation, any cadence):
    plant            str   plant / sector / station id
    time             datetime64 (UTC, naive)
    moisture_raw     float raw sensor value in the dataset's own unit
    irrigation       float optional, >0 while a valve is open (ground truth for "watering")
    rain             float optional, >0 when rain was recorded (ground truth for "rain")
    temperature      float optional, deg C (used to make out-of-soil faults drift temperature)
    source           str   optional dataset id ("mendeley", "ismn", "projectplant"); default "unspecified".
                           Carried into every output frame so a Mendeley-only variant is reproducible
                           (select_sources) and a model can be labelled "trained with ISMN data" (model_label).

Loaders that turn a concrete dataset into this frame are NOT here: the Mendeley file layout
has not been inspected (host unreachable from the sandbox, A-007). No numbers in this module
are results; they are parameters.

Rules from the owner (Arsany):
  * The dry threshold T is a per-plant / per-threshold DB field (default 25 relative points).
    It is an input to labelling, never a model output.
  * ISMN data is research/demo only and is never committed; this module reads files from a
    gitignored data/ directory only.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

TICK = "15min"
MAX_GAP = pd.Timedelta("1h")        # no carry-over across longer gaps (concept 4, step 2)
DEFAULT_DRY_THRESHOLD = 25.0        # relative points; plant/threshold DB field, not a model output
DRY_PCT, WET_PCT = 2.0, 98.0        # percentiles mapped to 0 / 100 (concept 4, step 3)
HORIZON_DAYS = 3                    # 72 h forecast horizon (FR-E01) -> leakage gap

EVENT_NONE, EVENT_WATERING, EVENT_RAIN, EVENT_WETTING = "none", "watering", "rain", "wetting"
# Fault classes per concept 2.3 / 3.4: out of soil (class 4) and sensor fault (class 5: flatline, spike, dropout).
# A calibration offset is NOT a fault class; it is an augmentation (offset_calibration, concept 3.4).
FAULT_NONE, FAULT_OUT_OF_SOIL = "none", "out_of_soil"
FAULT_FLATLINE, FAULT_SPIKE, FAULT_DROPOUT = "flatline", "spike", "dropout"
FAULT_CLASSES = (FAULT_OUT_OF_SOIL, FAULT_FLATLINE, FAULT_SPIKE, FAULT_DROPOUT)
DEFAULT_SOURCE = "unspecified"
HOURLY_MIN_SPACING = pd.Timedelta("45min")   # median spacing at/above this = hourly-class source (ISMN)


# --------------------------------------------------------------------------- 1. resample
def resample_15min(df: pd.DataFrame, plant: str | None = None) -> pd.DataFrame:
    """Causal resampling of ONE plant's observations to a 15-min grid.

    Value at a tick = last observation at or before the tick (no interpolation, no look-ahead).
    If that observation is older than MAX_GAP the tick is masked: moisture is NaN, masked=True.
    Event columns (irrigation, rain) use the max over the interval (tick-15min, tick].
    Provenance: `source` is carried through (one value per plant). `fresh` is True where a NEW observation
    arrived in (tick-15min, tick]. `upsampled` is True for every row of a plant whose median observation
    spacing is >= 45 min (hourly source such as ISMN): those 15-min rows are held values, not measurements
    (concept 4: "kept hourly and flagged"), never silently unflagged.
    """
    d = df.sort_values("time").reset_index(drop=True)
    if d.empty:
        raise ValueError("no observations")
    grid = pd.DataFrame({"time": pd.date_range(d["time"].min().ceil(TICK), d["time"].max().floor(TICK), freq=TICK)})
    extra = ["temperature"] if "temperature" in d.columns else []
    obs = d[["time", "moisture_raw", *extra]].assign(obs_time=d["time"])
    out = pd.merge_asof(grid, obs, on="time", direction="backward")
    out["masked"] = (out["time"] - out["obs_time"] > MAX_GAP) | out["obs_time"].isna()
    out.loc[out["masked"], ["moisture_raw", *extra]] = np.nan
    out["fresh"] = (out["time"] - out["obs_time"] < pd.Timedelta(TICK)) & ~out["masked"]
    out = out.drop(columns="obs_time")
    spacing = d["time"].diff().dropna()
    out["upsampled"] = bool(len(spacing) and spacing.median() >= HOURLY_MIN_SPACING)
    srcs = d["source"].dropna().unique() if "source" in d.columns else []
    if len(srcs) > 1:
        raise ValueError(f"plant {plant!r} mixes several sources {list(srcs)}; use distinct plant ids per source")
    out["source"] = srcs[0] if len(srcs) else DEFAULT_SOURCE
    for col in ("irrigation", "rain"):
        if col in d.columns:
            ev = d.set_index("time")[col].resample(TICK, closed="right", label="right").max()
            out[col] = out["time"].map(ev).fillna(0.0).to_numpy()
    out.insert(0, "plant", plant if plant is not None else d["plant"].iloc[0])
    return out


# --------------------------------------------------------------------------- 3. normalise
def fit_dry_wet(train_raw: pd.Series) -> tuple[float, float]:
    """Dry/wet points = 2nd / 98th percentile of TRAINING values only."""
    v = train_raw.dropna()
    if len(v) < 2:
        raise ValueError("not enough training values to fit dry/wet")
    dry, wet = np.percentile(v, [DRY_PCT, WET_PCT])
    if wet == dry:
        raise ValueError("flat training signal, cannot calibrate")
    return float(dry), float(wet)


def normalise(raw: pd.Series, dry: float, wet: float) -> pd.Series:
    """Relative moisture 0-100 %: 100*(raw-dry)/(wet-dry), clipped. Works for inverted sensors (dry>wet)."""
    return (100.0 * (raw - dry) / (wet - dry)).clip(0.0, 100.0)


def offset_calibration(dry: float, wet: float, shift_dry_pts: float, shift_wet_pts: float) -> tuple[float, float]:
    """Move the dry/wet points by +/- relative points (NFR-02 robustness augmentation, concept 3.4)."""
    span = wet - dry
    return dry + span * shift_dry_pts / 100.0, wet + span * shift_wet_pts / 100.0


# --------------------------------------------------------------------------- dry threshold
def below_threshold(m: pd.Series, threshold: float = DEFAULT_DRY_THRESHOLD) -> pd.Series:
    """True where moisture is below the plant's dry threshold. `threshold` comes from the plant DB field."""
    return m < threshold


# --------------------------------------------------------------------------- 4. events
def label_events(d: pd.DataFrame, m_col: str = "m", rise_pts: float = 10.0, window_ticks: int = 2,
                 refractory_ticks: int = 8) -> pd.DataFrame:
    """Label wetting events on the tick where a rise starts being visible.

    A rise = m[t] - m[t-window_ticks] >= rise_pts (NaN never rises). Onset = first tick of a rise run,
    suppressed for refractory_ticks after the previous onset. Class: watering if an irrigation signal
    is >0 within the window, else rain if rain >0, else generic 'wetting'.
    """
    m = d[m_col]
    rise = (m - m.shift(window_ticks)) >= rise_pts
    onset = rise & ~rise.shift(1, fill_value=False)
    keep, last = [], -10**9
    for i, o in enumerate(onset.to_numpy()):
        ok = bool(o) and i - last > refractory_ticks
        keep.append(ok)
        if ok:
            last = i
    onset = pd.Series(keep, index=d.index)
    recent = lambda c: d[c].rolling(window_ticks + 1, min_periods=1).max() > 0 if c in d else pd.Series(False, index=d.index)
    event = pd.Series(EVENT_NONE, index=d.index, dtype=object)
    event[onset] = EVENT_WETTING
    event[onset & recent("rain")] = EVENT_RAIN
    event[onset & recent("irrigation")] = EVENT_WATERING
    return d.assign(event=event)


def mean_watering_interval_h(d: pd.DataFrame) -> float:
    """Baseline: mean hours between watering/wetting events in the given (TRAINING) rows.

    If a `segment` column is present, intervals are taken inside each contiguous segment only.
    """
    ev = d.loc[d["event"] != EVENT_NONE]
    key = ev["segment"] if "segment" in ev.columns else pd.Series(0, index=ev.index)
    gaps = ev.groupby(key)["time"].diff().dropna()      # never across a segment join (non-contiguous data)
    if gaps.empty:
        return float("nan")
    return float(gaps.dt.total_seconds().mean() / 3600.0)


# --------------------------------------------------------------------------- 3.4 faults
def inject_faults(d: pd.DataFrame, rng: np.random.Generator, m_col: str = "m", n_out_of_soil: int = 1,
                  n_flatline: int = 1, n_spike: int = 1, n_dropout: int = 1, length_ticks: int = 24,
                  temp_col: str = "temperature") -> pd.DataFrame:
    """Synthetic fault injection on ONE contiguous segment of a normalised series (train/val only).

    out_of_soil: m decays quickly to ~0 (air) with small noise for length_ticks; if a temperature column
        exists it drifts by 3-8 deg C towards ambient over the same window.
    flatline: m held at its value at the start for length_ticks (identical readings).
    spike: one tick jumps by >= 40 points (towards the side with room) and reverts.
    dropout: m missing (NaN) for the first half of length_ticks, then the last value held.
    Adds: fault (label), synthetic (bool), m_clean (original). Segments do not overlap.
    A calibration offset is not a fault; see offset_calibration.
    """
    out = d.copy()
    out["m_clean"] = out[m_col]
    out["fault"] = FAULT_NONE
    out["synthetic"] = False
    n = len(out)
    free = np.ones(n, dtype=bool)
    plan = ([(FAULT_OUT_OF_SOIL, length_ticks)] * n_out_of_soil + [(FAULT_FLATLINE, length_ticks)] * n_flatline
            + [(FAULT_SPIKE, 1)] * n_spike + [(FAULT_DROPOUT, length_ticks)] * n_dropout)
    base = out[m_col].to_numpy(dtype=float).copy()
    for kind, ln in plan:
        starts = [s for s in range(0, n - ln) if free[s:s + ln].all() and not np.isnan(base[s])]
        if not starts:
            continue
        s = int(rng.choice(starts))
        sl = slice(s, s + ln)
        free[max(0, s - 1):s + ln + 1] = False
        mcol = out.columns.get_loc(m_col)
        if kind == FAULT_OUT_OF_SOIL:
            tau = rng.uniform(1.0, 3.0)                       # ticks
            k = np.arange(ln)
            vals = base[s] * np.exp(-k / tau) + np.abs(rng.normal(0, 0.5, ln))
            if temp_col in out.columns:
                t0 = out[temp_col].iloc[s]
                if not np.isnan(t0):
                    drift = rng.choice([-1, 1]) * rng.uniform(3, 8) * (1 - np.exp(-k / tau))
                    out.iloc[sl, out.columns.get_loc(temp_col)] = t0 + drift
        elif kind == FAULT_FLATLINE:
            vals = np.full(ln, base[s])
        elif kind == FAULT_SPIKE:
            sign = 1.0 if base[s] <= 50 else -1.0
            vals = np.array([base[s] + sign * rng.uniform(40, 50)])
        else:
            vals = np.full(ln, base[s])
            vals[: max(1, ln // 2)] = np.nan
        out.iloc[sl, mcol] = np.clip(vals, 0, 100)
        out.iloc[sl, out.columns.get_loc("fault")] = kind
        out.iloc[sl, out.columns.get_loc("synthetic")] = True
    return out


def add_segments(g: pd.DataFrame) -> pd.Series:
    """Segment id (0,1,...) of time-sorted rows of ONE plant+split: a new segment starts wherever the time
    step is larger than one tick (weeks/days dropped or belonging to another split)."""
    return (g["time"].diff() > pd.Timedelta(TICK)).cumsum()


def select_sources(raw: pd.DataFrame, sources: tuple[str, ...]) -> pd.DataFrame:
    """Keep only rows of the given dataset ids, e.g. ('mendeley',) for the Mendeley-only variant."""
    if "source" not in raw.columns:
        raise ValueError("raw frame has no 'source' column")
    return raw[raw["source"].isin(sources)].copy()


def model_label(train: pd.DataFrame) -> str:
    """Provenance label for a model trained on this train split (ISMN constraint, concept 3.2)."""
    src = sorted(set(train["source"]))
    base = "trained with " + ", ".join(x.upper() if x == "ismn" else x.capitalize() for x in src) + " data"
    return base + (" (ISMN: research/demo use only)" if "ismn" in src else "")


# --------------------------------------------------------------------------- 5. split
def assign_split(df: pd.DataFrame, heldout_plants: tuple[str, ...] = (), test_every: int = 5,
                 gap_days: int = HORIZON_DAYS) -> pd.Series:
    """Split label per row ('train'|'val'|'test'|'drop'); unit = (plant, calendar day).

    GLOBAL calendar weeks (Monday-anchored, counted from the earliest day over ALL plants, so every plant uses the
    same week index and sectors sharing weather/irrigation cannot straddle a boundary): week k with
    k % test_every == test_every-1 is test, the week after it is val, the rest train. A day whose set differs from the set `gap_days` later is dropped,
    so no forecast window (72 h look-ahead) reaches into another set. heldout_plants go to test entirely.
    """
    day = df["time"].dt.normalize()
    label = pd.Series("train", index=df.index, dtype=object)
    g0 = day.min()
    g0 = g0 - pd.Timedelta(days=int(g0.weekday()))
    for plant, g in df.groupby("plant"):
        if plant in heldout_plants:
            label[g.index] = "test"
            continue
        wk = ((day[g.index] - g0).dt.days // 7)
        lab = np.where(wk % test_every == test_every - 1, "test", np.where((wk % test_every == 0) & (wk > 0), "val", "train"))
        per_day = pd.Series(lab, index=g.index).groupby(day[g.index]).first()
        later = per_day.copy()
        later.index = later.index - pd.Timedelta(days=gap_days)      # label of day D+gap, aligned on D
        nxt = later.reindex(per_day.index)
        per_day = per_day.where(nxt.isna() | (nxt == per_day), "drop")
        label[g.index] = day[g.index].map(per_day).to_numpy()
    return label


# --------------------------------------------------------------------------- pipeline
def preprocess(raw: pd.DataFrame, heldout_plants: tuple[str, ...] = (), seed: int = 0, inject: bool = True,
               sources: tuple[str, ...] | None = None) -> dict[str, pd.DataFrame]:
    """raw canonical frame -> {'train','val','test'} frames with m (0-100), event, fault, synthetic, masked,
    source, upsampled, fresh, segment.

    Order matters for leakage: resample -> split (global weeks) -> calibration fitted on train rows only ->
    normalise -> per contiguous segment: events -> faults (train/val only; the test set stays free of synthetic
    data). Events, baseline and fault injection never span a join between non-contiguous days/weeks.
    `sources` restricts the input to those dataset ids (e.g. ('mendeley',)) for a reproducible variant.
    Plant ids must be unique across datasets.
    """
    if "source" not in raw.columns:
        raw = raw.assign(source=DEFAULT_SOURCE)
    if sources is not None:
        raw = select_sources(raw, sources)
    rng = np.random.default_rng(seed)
    ticks = pd.concat([resample_15min(g, plant=p) for p, g in raw.groupby("plant")], ignore_index=True)
    ticks["split"] = assign_split(ticks, heldout_plants=heldout_plants)
    ticks = ticks[ticks["split"] != "drop"].copy()
    train_all = ticks[ticks["split"] == "train"]
    pooled = fit_dry_wet(train_all["moisture_raw"])
    calib = {}
    for p in ticks["plant"].unique():
        tr = train_all[train_all["plant"] == p]["moisture_raw"]
        calib[p] = fit_dry_wet(tr) if tr.notna().sum() > 1 else pooled      # held-out plants: pooled train fallback
    ticks["m"] = np.nan
    for p, (dry, wet) in calib.items():
        sel = ticks["plant"] == p
        ticks.loc[sel, "m"] = normalise(ticks.loc[sel, "moisture_raw"], dry, wet)
    parts = []
    for (p, s), g in ticks.groupby(["plant", "split"]):
        g = g.sort_values("time").reset_index(drop=True)
        seg = add_segments(g)
        for k, gs in g.groupby(seg):
            gs = label_events(gs.reset_index(drop=True))
            if inject and s in ("train", "val") and gs["m"].notna().sum() > 48:
                gs = inject_faults(gs, rng)
            else:
                gs = gs.assign(m_clean=gs["m"], fault=FAULT_NONE, synthetic=False)
            parts.append(gs.assign(segment=f"{p}|{s}|{k}"))
    allp = pd.concat(parts, ignore_index=True)
    out = {s: allp[allp["split"] == s].reset_index(drop=True) for s in ("train", "val", "test")}
    for s_, f in out.items():
        if f.empty:
            warnings.warn(f"split '{s_}' is empty: recording too short for the week-based split", stacklevel=2)
    src = ticks.groupby("plant")["source"].first()
    out["_calibration"] = pd.DataFrame([{"plant": p, "source": src[p], "dry": a, "wet": b} for p, (a, b) in calib.items()])
    return out


def split_counts(splits: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Tick and class counts per split, for the data card (concept 4, step 8)."""
    rows = []
    for s in ("train", "val", "test"):
        g = splits[s]
        rows.append({"split": s, "ticks": len(g), "masked": int(g["masked"].sum()),
                     **{f"event_{k}": int((g["event"] == k).sum()) for k in (EVENT_WATERING, EVENT_RAIN, EVENT_WETTING)},
                     **{f"fault_{k}": int((g["fault"] == k).sum()) for k in FAULT_CLASSES},
                     "upsampled": int(g["upsampled"].sum()),
                     **{f"source_{k}": int((g["source"] == k).sum()) for k in sorted(set(g["source"]))}})
    return pd.DataFrame(rows)

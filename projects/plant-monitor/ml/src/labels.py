"""Labels for Model A (hours to dry threshold, with censoring) and Model B weak event labels.

Implements docs/edge-ai-concept.md section 2.2 (Model A label), 2.3 (fast-drying / waterlogged labels) and
section 4 step 6 (labels with censoring and masks as explicit columns).
Traces to FR-E01 (thirst forecast, 72 h horizon), FR-E02 (event detection), FR-E03 (fault detection input
classes), NFR-02 (relative moisture).

SYNTHETIC-ONLY STATUS: never run on real data (dataset hosts blocked, A-007). Fast-drying and waterlogged are
WEAK, derived labels (concept 2.3); nothing here is ground truth and no accuracy is claimed.

All functions work on ONE contiguous segment (rows 15 min apart, see prep.add_segments); callers must group.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import features as F
import prep

HORIZON_TICKS = F.HORIZON_TICKS            # 288 = 72 h (FR-E01)
CENSOR_NONE, CENSOR_EVENT, CENSOR_GAP, CENSOR_DATA_END = "", "event", "gap", "data_end"
WATERLOGGED_PCT = 95.0                     # m above 95 ... (concept 2.3, strict)
WATERLOGGED_TICKS = 24                     # ... for at least 6 h = 24 ticks
FAST_DRYING_SLOPE_PCT = 5                  # slope 6h below the 5th percentile of the training distribution
HOT_PCT = 75                               # temperature or light above their 75th percentile


# --------------------------------------------------------------------------- Model A label
def next_index(flag: np.ndarray) -> np.ndarray:
    """For each i: smallest j > i with flag[j], else len(flag) (= none). O(n) backward scan."""
    n = len(flag)
    out = np.full(n, n, dtype=np.int64)
    nxt = n
    for i in range(n - 1, -1, -1):
        out[i] = nxt
        if flag[i]:
            nxt = i
    return out


def label_hours_to_threshold(seg: pd.DataFrame, threshold: float = prep.DEFAULT_DRY_THRESHOLD,
                             m_col: str = "m_clean", horizon: int = HORIZON_TICKS) -> pd.DataFrame:
    """Model A label per 15-min tick t (concept 2.2): hours until m first falls below T, with censoring.

    Columns added:
      y_hours         hours to threshold, 0..72 (0 if m[t] already below T; 72 if no crossing within the horizon)
      y_capped        True when y_hours = 72 because no crossing happened within the horizon (fully observed)
      y_censored      True when a wetting event (or a gap) comes before the crossing, or the data ends before
                      the horizon is known. These ticks are excluded from the FR-E01 metric (reported separately).
      y_censor_reason '' | 'event' | 'gap' | 'data_end'
      y_mask          True = tick usable for the metric: m[t] valid, not censored, no synthetic fault.
    Definition: crossing at j > t needs m[j] < T (strictly below, prep.below_threshold), j - t <= horizon, no
    wetting event in (t, j] (an event AT the crossing tick censors) and no invalid m in (t, j].
    Uses the CLEAN series (m_clean): faults are Model B's business and must not move the Model A target.
    """
    d = seg.reset_index(drop=True)
    m = d[m_col].to_numpy(dtype=float)
    n = len(d)
    valid = ~np.isnan(m)
    below = np.zeros(n, dtype=bool)
    below[valid] = prep.below_threshold(pd.Series(m[valid]), threshold).to_numpy()
    event = (d["event"] != prep.EVENT_NONE).to_numpy() if "event" in d else np.zeros(n, dtype=bool)
    nj, ne, ng = next_index(below), next_index(event), next_index(~valid)
    y = np.zeros(n)
    capped = np.zeros(n, dtype=bool)
    cens = np.zeros(n, dtype=bool)
    reason = [CENSOR_NONE] * n
    for i in range(n):
        if not valid[i]:
            cens[i], reason[i], y[i] = True, CENSOR_GAP, np.nan
            continue
        if below[i]:
            continue                                  # already dry: label 0
        j, e, g = nj[i], ne[i], ng[i]
        end = i + horizon
        if j <= end and j < n and j < e and j < g:
            y[i] = (j - i) / 4.0
            continue
        c = min(e, g)
        if c <= end and c < n:                        # a blocker comes at or before the horizon, before any crossing
            cens[i] = True
            reason[i] = CENSOR_EVENT if e <= g else CENSOR_GAP
            y[i] = np.nan
        elif end <= n - 1:                            # whole horizon observed, no crossing
            y[i], capped[i] = horizon / 4.0, True
        else:
            cens[i], reason[i], y[i] = True, CENSOR_DATA_END, np.nan
    fault_free = (d["fault"] == prep.FAULT_NONE).to_numpy() if "fault" in d else np.ones(n, dtype=bool)
    d["y_hours"], d["y_capped"], d["y_censored"], d["y_censor_reason"] = y, capped, cens, reason
    d["y_mask"] = valid & ~cens & fault_free
    return d


def baseline_hours(seg: pd.DataFrame, mean_interval_h: float) -> pd.Series:
    """Baseline prediction (concept 2.2): max(0, mean interval - time since last event), clipped to 72 h.

    `mean_interval_h` must come from TRAINING rows only (prep.mean_watering_interval_h). NaN until the first event
    of the segment (no time-since-event known) or when the mean interval is NaN. FR-E01 (beat the baseline).
    """
    ev = (seg["event"] != prep.EVENT_NONE).to_numpy()
    last = -1
    since = np.full(len(seg), np.nan)
    for i, e in enumerate(ev):
        if e:
            last = i
        if last >= 0:
            since[i] = (i - last) / 4.0
    return pd.Series(np.clip(mean_interval_h - since, 0.0, horizon_h()), index=seg.index)


def horizon_h() -> float:
    return HORIZON_TICKS / 4.0


# --------------------------------------------------------------------------- Model B weak labels
def fit_fast_drying_thresholds(train_feat: pd.DataFrame) -> dict:
    """5th percentile of slope_6h and 75th percentile of temperature / light from TRAINING feature rows only.

    Integer features (features.py units); np.percentile 'lower' keeps them integers. Light is optional
    (the public datasets may have none): then only temperature is used. Concept 2.3 (fast drying = weak label).
    """
    tr = train_feat[train_feat["feat_valid"]]
    if tr.empty:
        raise ValueError("no valid training feature rows")
    out = {"slope_6h_p5": int(np.percentile(tr["slope_6h"], FAST_DRYING_SLOPE_PCT, method="lower")),
           "temp_p75": int(np.percentile(tr["temp_now"], HOT_PCT, method="lower")), "light_p75": None}
    if "light_known" in tr.columns and tr["light_known"].any():
        out["light_p75"] = int(np.percentile(tr.loc[tr["light_known"], "light_mean_6h"], HOT_PCT, method="lower"))
    return out


def label_fast_drying(feat: pd.DataFrame, thr: dict) -> pd.Series:
    """Weak label (concept 2.3): slope_6h strictly below the training 5th percentile AND (temperature strictly
    above its 75th percentile OR light strictly above its 75th percentile). False where features are invalid."""
    slow = feat["slope_6h"] < thr["slope_6h_p5"]
    hot = feat["temp_now"] > thr["temp_p75"]
    if thr.get("light_p75") is not None:
        hot = hot | ((feat["light_mean_6h"] > thr["light_p75"]) & feat.get("light_known", True))
    return slow & hot & feat["feat_valid"]


def label_waterlogged(seg: pd.DataFrame, m_col: str = "m", pct: float = WATERLOGGED_PCT,
                      ticks: int = WATERLOGGED_TICKS) -> pd.Series:
    """Weak label (concept 2.3): m strictly above 95 for at least 24 consecutive ticks (6 h).

    Causal: True from the tick where the run reaches `ticks` onward while the run lasts (a device can only know
    after 6 h). A NaN or a value <= 95 ends the run.
    """
    above = (seg[m_col] > pct).to_numpy()
    out = np.zeros(len(above), dtype=bool)
    run = 0
    for i, a in enumerate(above):
        run = run + 1 if a else 0
        out[i] = run >= ticks
    return pd.Series(out, index=seg.index)


# --------------------------------------------------------------------------- Model B event labels (A-032)
# Decision A-032 (Arsany, approved 2026-11-06). Real-data finding: 556 of 900 Mendeley wetting events have no valve
# and no rain signal ("generic wetting"), 243 of them in sector 5 (probe jumps 30-40 points/h, cause unverified).
#   * wetting POSITIVES = valve-coincident watering (219) + rain-coincident (125) events only (FR-E02 evidence).
#   * generic / unexplained wetting is an IGNORE mask: never a positive, never a negative in training. It is used
#     only to report (evaluation) how the model reacts on events we cannot explain.
#   * sector 5 is excluded from wetting positives and from FR-E02 evidence: all its ticks are ignored for Model B.
#   * FR-E02 claims cover WETTING and SENSOR FAULT only. fast_drying / waterlogged stay weak labels, reported
#     separately in the data card, never as an FR-E02 claim.
#   * NO threshold re-tuning after seeing zero train positives (fast_drying train = 0): the percentile constants
#     above are frozen (FROZEN_WEAK_LABEL_RULE); see tests/test_labels.py::test_no_retuning_*.
EXCLUDED_WETTING_PLANTS = ("mendeley_s5",)          # A-032: sector 5 (unexplained probe jumps)
IGNORE_PAD_TICKS = 4   # ticks (+-1 h) around an unexplained onset; Lead decision (Theo C1): 4 gives 1.50 % vs 2.52 % contaminated negatives at 2
FR_E02_CLAIM_CLASSES = ("wetting", "sensor_fault")  # A-032: nothing else may be claimed under FR-E02
EXPLAINED_WETTING_EVENTS = (prep.EVENT_WATERING, prep.EVENT_RAIN)
FROZEN_WEAK_LABEL_RULE = {"slope_pct": FAST_DRYING_SLOPE_PCT, "hot_pct": HOT_PCT,
                          "waterlogged_pct": WATERLOGGED_PCT, "waterlogged_ticks": WATERLOGGED_TICKS}  # A-032: frozen


def label_wetting_classes(seg: pd.DataFrame, excluded_plants: tuple = EXCLUDED_WETTING_PLANTS,
                          pad: int = IGNORE_PAD_TICKS) -> pd.DataFrame:
    """Model B wetting labels for ONE contiguous segment of ONE plant (A-032, FR-E02 wetting class).

    Adds three boolean columns:
      lbl_wetting_pos     event is valve-coincident watering or rain-coincident, plant not excluded.
      lbl_wetting_ignore  generic 'wetting' onset +-`pad` ticks (unless that tick is a positive), or EVERY tick
                          of an excluded plant (sector 5). These ticks are neither positive nor negative: they must be
                          dropped from the training loss AND from the positive/negative counts of every evaluation
                          metric; they may only appear in a separate "unexplained wetting" report.
      lbl_wetting_neg     everything else: usable negative (no event, nothing unexplained nearby).
    This function only SETS the three columns (exactly one is True per tick); it does not drop rows. Consumers
    (4.AI2 training and evaluation) must select `lbl_wetting_pos | lbl_wetting_neg` themselves.
    """
    d = seg.copy()
    plant = d["plant"].iloc[0] if ("plant" in d and len(d)) else None
    excluded = plant in excluded_plants
    ev = d["event"]
    explained = ev.isin(EXPLAINED_WETTING_EVENTS).to_numpy()
    generic = (ev == prep.EVENT_WETTING).to_numpy()
    n = len(d)
    near = np.zeros(n, dtype=bool)
    for i in np.flatnonzero(generic):
        near[max(0, i - pad): i + pad + 1] = True
    pos = explained & (not excluded)
    ign = np.ones(n, dtype=bool) if excluded else (near & ~pos)
    d["lbl_wetting_pos"], d["lbl_wetting_ignore"] = pos, ign
    d["lbl_wetting_neg"] = ~pos & ~ign
    return d

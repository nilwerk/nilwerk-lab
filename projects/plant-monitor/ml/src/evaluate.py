"""Evaluation helpers for 4.AI2 slice 1: the enforcing wetting mask (A-032) and honest baselines.

Traces to FR-E01 (thirst forecast, 72 h horizon, beat the average-interval baseline), FR-E02 (event detection:
wetting + sensor fault claims only), A-032 (ignore mask; sector 5 never positive). No model is trained here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import features as F
import labels as L


# --------------------------------------------------------------------------- A-032 enforcing mask
def wetting_usable(df: pd.DataFrame) -> pd.Series:
    """A-032: `usable = pos | neg` for wetting training AND every precision/recall count. Ignore-mask ticks (generic
    wetting +-pad, all of sector 5) are never usable. Fails loudly if the three label columns do not partition the ticks
    or if an excluded plant carries a positive (FR-E02 evidence rule)."""
    pos, ign, neg = (df[c].astype(bool) for c in ("lbl_wetting_pos", "lbl_wetting_ignore", "lbl_wetting_neg"))
    if not ((pos.astype(int) + ign.astype(int) + neg.astype(int)) == 1).all():
        raise ValueError("lbl_wetting_pos/ignore/neg must partition every tick (A-032)")
    if "plant" in df and (pos & df["plant"].isin(L.EXCLUDED_WETTING_PLANTS)).any():
        raise ValueError("excluded plant (sector 5) has wetting positives (A-032)")
    return pos | neg


def wetting_precision_recall(pred_onset: pd.Series, df: pd.DataFrame, tol: int = 1) -> dict:
    """Event-level precision / recall of predicted onsets on ONE contiguous segment (A-032, FR-E02 wetting class).

    A prediction at a usable tick is TP if a positive lies within +-tol ticks, else FP (a usable negative).
    Predictions on ignore-mask ticks are dropped (neither TP nor FP). A positive is found if any prediction lies within
    +-tol ticks (the prediction may sit on an ignore tick). Only usable ticks are counted.
    """
    usable = wetting_usable(df).to_numpy()
    pos = df["lbl_wetting_pos"].to_numpy(bool)
    pred = np.asarray(pred_onset, bool)
    pi, qi = np.flatnonzero(pos), np.flatnonzero(pred)
    tp = fp = 0
    for i in qi:
        if not usable[i]:
            continue
        if len(pi) and np.abs(pi - i).min() <= tol:
            tp += 1
        else:
            fp += 1
    found = sum(1 for j in pi if len(qi) and np.abs(qi - j).min() <= tol)
    return {"tp": tp, "fp": fp, "positives": int(len(pi)), "found": int(found)}


def rule_detector_onsets(seg: pd.DataFrame) -> np.ndarray:
    """The on-device rule detector (features.EventTracker on int m) over ONE segment: bool onset per tick."""
    tr = F.EventTracker()
    return np.array([tr.step(int(m), bool(ok)) for m, ok in zip(seg["m_u8"], seg["m"].notna())], dtype=bool)


def event_detection_table(ds: dict) -> pd.DataFrame:
    rows = []
    for s in ("train", "val", "test"):
        tp = fp = pos = found = 0
        for _, g in ds[s].groupby("segment", sort=False):
            g = g.reset_index(drop=True)
            r = wetting_precision_recall(pd.Series(rule_detector_onsets(g)), g)
            tp, fp, pos, found = tp + r["tp"], fp + r["fp"], pos + r["positives"], found + r["found"]
        rows.append({"split": s, "positives": pos, "found": found, "tp": tp, "fp": fp,
                     "recall": found / pos if pos else float("nan"),
                     "precision": tp / (tp + fp) if tp + fp else float("nan")})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- Model A baseline (FR-E01)
def thirst_baseline_table(ds: dict, const_hours: float) -> pd.DataFrame:
    """Per split: MAE (hours) of the average-interval baseline against y_hours on ticks with y_mask (observed, not
    censored, valid m). Coverage = share of y_mask ticks where the baseline exists (it is NaN before the first event of
    a segment). A constant predictor (`const_hours` = TRAIN median of y_hours) is the sanity floor. No model yet."""
    rows = []
    for s in ("train", "val", "test"):
        g = ds[s]
        for subset, u in (("all y_mask", g[g["y_mask"]]), ("m above T (not yet dry)", g[g["y_mask"] & (g["y_hours"] > 0)])):
            has = u["baseline_hours"].notna()
            err = (u.loc[has, "baseline_hours"] - u.loc[has, "y_hours"]).abs()
            cerr = (const_hours - u["y_hours"]).abs()
            rows.append({"split": s, "subset": subset, "n_ticks": len(u), "n_segments": int(u["segment"].nunique()),
                         "coverage": float(has.mean()) if len(u) else float("nan"),
                         "mae_baseline_h": float(err.mean()) if len(err) else float("nan"),
                         "mae_constant_h": float(cerr.mean()) if len(cerr) else float("nan"),
                         "share_y_zero": float((u["y_hours"] == 0).mean()) if len(u) else float("nan"),
                         "share_capped_72h": float(u["y_capped"].mean()) if len(u) else float("nan")})
    return pd.DataFrame(rows)

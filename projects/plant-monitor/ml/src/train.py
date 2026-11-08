"""Task 4.AI2: training and evaluation of Model B (wetting) and the Model A baseline. Real-data slice, no synthetic rows.

Traces to FR-E01 (thirst forecast: only the average-interval BASELINE is evaluated here, no Model A network yet),
FR-E02 (wetting detection recall/precision, <= 1 false alert per unit-week), FR-E03 (fast path: one tick decides,
no debounce), FR-E04 / NFR-01 (size, RAM, int8 budgets), NFR-02 (relative moisture 0-100), A-019 (precision AND recall
per class), A-032 (labels: positives = valve/rain-explained onsets, sector 5 and generic wetting = ignore mask,
IGNORE_PAD_TICKS = 4 from labels.py, no threshold re-tuning).

Model B in this slice is a 2-class wetting classifier (0 normal, 1 wetting). Sensor fault / out-of-soil have no real
positives (synthetic only) and are NOT trained or claimed here (A-032: FR-E02 claim = wetting + sensor fault, the
second half is open). Fast-drying / waterlogged are weak labels outside every FR-E02 claim and are not trained.

Honesty notes the code enforces:
  * ignore-mask ticks (label -1) are dropped from the training loss AND from every metric count;
  * the decision threshold p_fast is chosen on VAL only; TEST is read once per seed after that;
  * the valve / rain columns are never features (concept 3.1); inputs come from the moisture history only;
  * the onset label comes from a rise rule (prep.label_events: >= 10 points within 2 ticks), so recall measures
    agreement with that label definition, not an independent detection of watering. See the report.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

import features as F
import labels as L
import prep

# ---- contract constants (each one documented, none is a result)
WINDOW = 8                     # ticks of history the network sees (2 h). DEVIATION from concept 2.3 (24 ticks): the real
                               # data has many probe gaps, a 28-tick context keeps only 12 of 40 test positives, 12 ticks keeps 20
CONTEXT = WINDOW + 4           # d4 needs 4 more ticks: CONTEXT consecutive valid m samples per window
RULE_RISE_PTS = 8              # rule baseline (concept 2.3): wetting if m rises >= 8 points within 1 h (4 ticks)
RULE_WINDOW = 4
FP_BUDGET_PER_TICK = 0.0015    # FR-E02 <= 1 false alert / unit-week at 672 ticks per week (concept 2.3: ~0.15 %)
TICKS_PER_WEEK = 672
P_FAST_START = 0.9             # concept 2.3 starting value, raised on validation until the FP budget holds
N_INPUTS = 2 * WINDOW + 2      # d1 and d4 per tick, plus m_now and slope_win
INPUT_SCALE = 1.0 / 128.0      # float model sees int / 128, so the int8 input quantisation is scale 1/128, zp 0
LABEL_POS, LABEL_NEG, LABEL_IGNORE = 1, 0, -1
SEEDS = (0, 1, 2, 3, 4)        # reported seed = SEEDS[0], fixed BEFORE training (no best-of selection)
HORIZON_BUCKETS = ((0, 12), (12, 24), (24, 48), (48, 72))   # concept 2.2, hours


# --------------------------------------------------------------------------- windows (Model B inputs)
def build_wetting_windows(split_df: pd.DataFrame) -> dict:
    """Integer input windows for every tick that has CONTEXT consecutive valid moisture samples inside one segment.

    Per window: d1[k] = m[t-k] - m[t-k-1] and d4[k] = m[t-k] - m[t-k-4] for k = WINDOW-1..0 (uint8 moisture points,
    clipped to int8), then m_now and slope over the window (features.slope_x64 over the last WINDOW samples, 1/8 pp/h units).
    Windows never cross a segment (gap, reset, day join); sample validity comes from the m column (NaN = invalid).
    Labels: LABEL_POS / LABEL_NEG / LABEL_IGNORE from labels.label_wetting_classes (A-032).
    FR-E02. Requires columns segment, m_u8, m, lbl_wetting_pos, lbl_wetting_neg, lbl_wetting_ignore, event, plant, time.
    """
    xs, meta = [], []
    for _, g in split_df.groupby("segment", sort=False):
        g = g.reset_index(drop=True)
        m = g["m_u8"].to_numpy(dtype=np.int64)
        ok = g["m"].notna().to_numpy()
        n = len(g)
        if n < CONTEXT:
            continue
        bad = np.concatenate([[0], np.cumsum(~ok)])                     # bad[i+1]-bad[j] = invalid samples in [j, i]
        for t in range(CONTEXT - 1, n):
            if bad[t + 1] - bad[t + 1 - CONTEXT] != 0:
                continue
            idx = np.arange(t - WINDOW + 1, t + 1)
            d1 = np.clip(m[idx] - m[idx - 1], -128, 127)
            d4 = np.clip(m[idx] - m[idx - 4], -128, 127)
            slope = F.clip(F.rshift_round(F.slope_x64(m[t - WINDOW + 1: t + 1]), 3), -128, 127)
            xs.append(np.concatenate([d1, d4, [int(m[t]), slope]]))
            pos, neg = bool(g.at[t, "lbl_wetting_pos"]), bool(g.at[t, "lbl_wetting_neg"])
            lab = LABEL_POS if pos else (LABEL_NEG if neg else LABEL_IGNORE)
            meta.append((lab, g.at[t, "event"], g.at[t, "plant"], g.at[t, "time"], bool(g.at[t, "lbl_wetting_ignore"])))
    X = np.array(xs, dtype=np.int64).reshape(-1, N_INPUTS)
    lab, ev, plant, tm, ign = (list(c) for c in zip(*meta)) if meta else ([], [], [], [], [])
    return {"X": X, "y": np.array(lab, dtype=np.int64), "event": np.array(ev, dtype=object),
            "plant": np.array(plant, dtype=object), "time": np.array(tm), "ignore": np.array(ign, dtype=bool)}


def to_float(X: np.ndarray) -> np.ndarray:
    """Model input as float32: integer features / 128 (int8 range -> [-1, 1)). The device feeds the same integers."""
    return (X.astype(np.float32) * INPUT_SCALE)


def rule_score(X: np.ndarray) -> np.ndarray:
    """Rule score = rise of m over the last hour in points (last d4). FR-E02 baseline input."""
    return X[:, 2 * WINDOW - 1]


def rule_predict(X: np.ndarray, rise_pts: float = RULE_RISE_PTS) -> np.ndarray:
    """Rule baseline (concept 2.3): wetting if m rose >= rise_pts (default 8) within 1 h. FR-E02 baseline."""
    return rule_score(X) >= rise_pts


def usable(win: dict) -> np.ndarray:
    """Mask of windows that count: positives and negatives only (A-032: ignore ticks are dropped everywhere)."""
    return win["y"] != LABEL_IGNORE


# --------------------------------------------------------------------------- metrics (A-019: per class)
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95 % interval for a proportion k/n; (nan, nan) when n = 0. Used because counts are tiny."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def per_class_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Precision and recall for class 0 (normal) and class 1 (wetting) with counts and Wilson intervals.

    y_true in {0,1} (ignore ticks must already be removed), y_pred boolean/int. No averaging over classes (A-019).
    Undefined values (no predicted or no true members) are None, never 0.
    """
    yt, yp = np.asarray(y_true).astype(int), np.asarray(y_pred).astype(int)
    out = {}
    for c, name in ((1, "wetting"), (0, "normal")):
        tp = int(((yt == c) & (yp == c)).sum())
        fp = int(((yt != c) & (yp == c)).sum())
        fn = int(((yt == c) & (yp != c)).sum())
        n_true, n_pred = tp + fn, tp + fp
        out[name] = {"support": n_true, "predicted": n_pred, "tp": tp, "fp": fp, "fn": fn,
                     "precision": tp / n_pred if n_pred else None, "recall": tp / n_true if n_true else None,
                     "precision_ci95": wilson(tp, n_pred) if n_pred else None,
                     "recall_ci95": wilson(tp, n_true) if n_true else None}
    neg = int((yt == 0).sum())
    fp1 = out["wetting"]["fp"]
    out["false_positive_rate_per_tick"] = fp1 / neg if neg else None
    out["false_alerts_per_unit_week"] = fp1 / (neg / TICKS_PER_WEEK) if neg else None
    return out


def choose_p_fast(p_val: np.ndarray, y_val: np.ndarray, budget: float = FP_BUDGET_PER_TICK,
                  start: float = P_FAST_START) -> tuple[float, bool]:
    """p_fast from VALIDATION only (concept 2.3): start at 0.9, raise until the per-tick false-positive rate <= budget.

    Returns (threshold, budget_met). Candidates are the distinct validation scores above `start` (then 1.0 + eps:
    nothing fires). If even firing on nothing... budget_met is False only when val has no negatives.
    """
    neg = p_val[y_val == 0]
    if len(neg) == 0:
        return start, False
    cands = sorted({start, *[float(x) for x in neg if x > start]})
    for thr in cands:
        if (neg >= thr).mean() <= budget:
            return thr, True
    return float(np.nextafter(neg.max(), 2.0)), True          # just above the highest negative score


# --------------------------------------------------------------------------- Model B network
def build_model():
    """MLP N_INPUTS -> 16 -> 8 -> 2 (softmax). Proposal in concept 2.3 is a small conv net; an MLP needs only
    fully_connected + softmax (fewer TFLM ops, smaller flatbuffer). FR-E04. TensorFlow is imported lazily."""
    import tensorflow as tf
    return tf.keras.Sequential([
        tf.keras.layers.Input(shape=(N_INPUTS,)),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(8, activation="relu"),
        tf.keras.layers.Dense(2, activation="softmax")])


def train_model(Xtr: np.ndarray, ytr: np.ndarray, seed: int, epochs: int = 40):
    """Train on usable train windows only, class-weighted (positives are rare). Deterministic per seed."""
    import tensorflow as tf
    tf.keras.utils.set_random_seed(seed)
    tf.config.experimental.enable_op_determinism()
    m = build_model()
    m.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="sparse_categorical_crossentropy")
    n1 = max(1, int((ytr == 1).sum()))
    n0 = max(1, int((ytr == 0).sum()))
    cw = {0: 1.0, 1: min(50.0, n0 / n1)}
    m.fit(to_float(Xtr), ytr, epochs=epochs, batch_size=128, class_weight=cw, shuffle=True, verbose=0)
    return m


def predict_p1(model, X: np.ndarray) -> np.ndarray:
    return model.predict(to_float(X), verbose=0, batch_size=1024)[:, 1]


# --------------------------------------------------------------------------- int8 TFLite and size estimate
def to_int8_tflite(model, Xrep: np.ndarray) -> bytes:
    """Full-integer post-training quantisation with a representative dataset (train windows). Input and output int8.

    The two extreme rows -128/128 and 127/128 are appended so the input quantisation is exactly scale 1/128, zp 0
    (the device then feeds its integer features unchanged). FR-E04.
    """
    import tensorflow as tf
    rep = np.vstack([to_float(Xrep[:500]), np.full((1, N_INPUTS), -1.0, np.float32), np.full((1, N_INPUTS), 127 / 128, np.float32)])
    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    conv.optimizations = [tf.lite.Optimize.DEFAULT]
    conv.representative_dataset = lambda: ([r[None, :]] for r in rep)
    conv.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conv.inference_input_type = tf.int8
    conv.inference_output_type = tf.int8
    return conv.convert()


def tflite_predict_p1(tflite: bytes, X: np.ndarray) -> np.ndarray:
    """Run the int8 model on integer feature rows (host interpreter); returns p(wetting) as float."""
    import tensorflow as tf
    it = tf.lite.Interpreter(model_content=tflite)
    it.allocate_tensors()
    i, o = it.get_input_details()[0], it.get_output_details()[0]
    s_in, z_in = i["quantization"]
    s_out, z_out = o["quantization"]
    out = np.empty(len(X))
    for k, row in enumerate(X):
        q = np.clip(np.round(row * INPUT_SCALE / s_in + z_in), -128, 127).astype(np.int8)
        it.set_tensor(i["index"], q[None, :])
        it.invoke()
        out[k] = (int(it.get_tensor(o["index"])[0][1]) - z_out) * s_out
    return out


def size_report(tflite: bytes) -> dict:
    """FR-E04 size estimate from the host flatbuffer. What is MEASURED: flatbuffer bytes (= flash counted per
    concept 2.4), input/output quantisation, tensor shapes, MAC count. What is an ESTIMATE: RAM = sum of ALL non-constant
    tensor bytes (an upper bound of the arena: every activation live at once) + the feature ring (96 + 192 B).
    NOT measured: MicroInterpreter instance, TFLM allocator overhead and Invoke() latency (need an esp-tflite-micro
    build on the board, task 4.AI3)."""
    import tensorflow as tf
    it = tf.lite.Interpreter(model_content=tflite)
    it.allocate_tensors()
    ops = it._get_ops_details()                         # private but stable API: per op input/output tensor ids
    produced = {int(x) for op in ops for x in op["outputs"]} | {int(d["index"]) for d in it.get_input_details()}
    details = it.get_tensor_details()
    act = [d for d in details if int(d["index"]) in produced]
    act_bytes = sum(int(np.prod(d["shape"])) * np.dtype(d["dtype"]).itemsize for d in act)
    wts = [d for d in details if int(d["index"]) not in produced and len(d["shape"]) == 2 and d["dtype"] == np.int8]
    macs = sum(int(np.prod(d["shape"])) for d in wts)   # one MAC per int8 weight of a fully connected layer
    i, o = it.get_input_details()[0], it.get_output_details()[0]
    return {"flatbuffer_bytes": len(tflite), "flash_budget_bytes": 30 * 1024, "flash_ok": len(tflite) < 30 * 1024,
            "activation_bytes_upper_bound": act_bytes, "feature_ring_bytes": 96 + 192,
            "ram_estimate_bytes": act_bytes + 96 + 192, "ram_budget_bytes": 20 * 1024,
            "ram_ok_estimate": act_bytes + 96 + 192 < 20 * 1024, "macs": macs,
            "input_quant": [float(i["quantization"][0]), int(i["quantization"][1])], "input_shape": [int(x) for x in i["shape"]],
            "output_quant": [float(o["quantization"][0]), int(o["quantization"][1])],
            "not_measured": ["MicroInterpreter instance + TFLM allocator overhead", "Invoke() latency on ESP32-C3 (< 50 ms budget)",
                             "firmware image size with/without AI component"]}


# --------------------------------------------------------------------------- Model A baseline evaluation
def model_a_baseline_eval(ds_split: pd.DataFrame, mean_interval_h: float) -> dict:
    """MAE (hours) of the average-interval baseline on ticks with y_mask and a defined baseline (FR-E01 metric ticks).

    Reported overall, per horizon bucket of the TRUE label (concept 2.2), per plant, and against a trivial reference
    that always predicts the training-set median label (so 'beats nothing' is visible). Censored ticks are excluded
    (reported as a count). No Model A network exists in this slice: nothing here is a model result.
    """
    d = ds_split
    ok = d["y_mask"] & d["baseline_hours"].notna() & d["y_hours"].notna()
    e = (d.loc[ok, "baseline_hours"] - d.loc[ok, "y_hours"]).abs()
    y = d.loc[ok, "y_hours"]
    out = {"ticks_total": int(len(d)), "ticks_metric": int(ok.sum()), "ticks_censored": int(d["y_censored"].sum()),
           "mean_interval_h_train": mean_interval_h, "baseline_mae_h": float(e.mean()) if ok.any() else None,
           "label_mean_h": float(y.mean()) if ok.any() else None, "fr_e01_target_mae_h": 12.0, "buckets": {}, "by_plant": {}}
    for lo, hi in HORIZON_BUCKETS:
        sel = (y >= lo) & ((y < hi) | ((hi == 72) & (y <= 72)))
        out["buckets"][f"{lo}-{hi}h"] = {"n": int(sel.sum()), "baseline_mae_h": float(e[sel].mean()) if sel.any() else None}
    for p, g in d.loc[ok].groupby("plant"):
        out["by_plant"][p] = {"n": int(len(g)), "baseline_mae_h": float((g["baseline_hours"] - g["y_hours"]).abs().mean())}
    return out


def trivial_median_mae(train_df: pd.DataFrame, eval_df: pd.DataFrame) -> float | None:
    """MAE of 'always predict the training median label' on the eval metric ticks (reference, not a model)."""
    tr = train_df[train_df["y_mask"] & train_df["y_hours"].notna()]
    ev = eval_df[eval_df["y_mask"] & eval_df["baseline_hours"].notna() & eval_df["y_hours"].notna()]
    if tr.empty or ev.empty:
        return None
    return float((ev["y_hours"] - tr["y_hours"].median()).abs().mean())


# --------------------------------------------------------------------------- unexplained-wetting report (A-032)
def unexplained_report(win: dict, fires: np.ndarray) -> dict:
    """How the detector reacts on generic (unexplained) wetting onsets, NOT part of precision/recall (A-032).
    `fires` is a boolean array aligned with the windows. Split by excluded sector 5 vs the other plants."""
    gen = (win["event"] == prep.EVENT_WETTING)
    s5 = np.isin(win["plant"], L.EXCLUDED_WETTING_PLANTS)
    out = {}
    for name, sel in (("sector5", gen & s5), ("other_sectors", gen & ~s5)):
        out[name] = {"onset_ticks": int(sel.sum()), "fired": int(fires[sel].sum())}
    return out

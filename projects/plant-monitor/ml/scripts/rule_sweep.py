"""Rule baseline swept over its threshold (task 4.AI2 fix round, review C1).

Usage: python -I scripts/rule_sweep.py <raw_dir> <out_json>
For rise thresholds 1..100 points/h: wetting recall (Wilson 95 %) and false alerts per unit-week on VAL and TEST,
using the same windows and ignore mask (A-032) as scripts/train_all.py. Rule only, no model, no TensorFlow.
The rule has one parameter, so at a low false-alert rate it degenerates to "fire only on a huge jump"; the table
shows exactly where recall collapses. No thresholds are chosen here; every row is listed.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import export, loaders, prep, train as T  # noqa: E402

THRESHOLDS = [8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 70, 80, 91, 100]


def main(raw_dir: str, out_json: str) -> None:
    raw, _ = loaders.load_mendeley(Path(raw_dir))
    sp = prep.preprocess(raw, inject=False, seed=0)
    sp.pop("_calibration")
    ds = export.build_dataset(sp)
    out = {"thresholds_pts_per_h": THRESHOLDS, "val": [], "test": []}
    for s in ("val", "test"):
        win = T.build_wetting_windows(ds[s])
        u = T.usable(win)
        X, y = win["X"][u], win["y"][u]
        for k in THRESHOLDS:
            m = T.per_class_metrics(y, T.rule_predict(X, float(k)))
            w = m["wetting"]
            out[s].append({"rise_pts": k, "n_pos": int((y == 1).sum()), "tp": w["tp"], "fp": w["fp"], "recall": w["recall"],
                           "recall_ci95": w["recall_ci95"], "fa_per_unit_week": m["false_alerts_per_unit_week"]})
    Path(out_json).write_text(json.dumps(out, indent=1, default=float))
    for s in ("val", "test"):
        print(s)
        for r in out[s]:
            lo, hi = r["recall_ci95"]
            print(f"  rise>={r['rise_pts']:3d}  TP {r['tp']:2d}/{r['n_pos']}  recall {100*r['recall']:5.1f} % ({100*lo:.1f}-{100*hi:.1f})  FP {r['fp']:3d}  FA/wk {r['fa_per_unit_week']:.2f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

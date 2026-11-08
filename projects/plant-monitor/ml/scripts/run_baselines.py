"""4.AI2 slice 1: baselines on the REAL Mendeley data. Usage: python -I scripts/run_baselines.py <raw_dir> <out_dir>
Prints markdown tables used in reports/4.AI2-s1.md. No model is trained; numbers are baselines, not results."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import numpy as np  # noqa: E402
import export, evaluate, loaders, prep  # noqa: E402


def main(raw_dir: str, out_dir: str) -> None:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    raw, _ = loaders.load_mendeley(Path(raw_dir))
    sp = prep.preprocess(raw, inject=False, seed=0)            # real data only: no synthetic faults
    sp.pop("_calibration")
    ds = export.build_dataset(sp)
    const = float(np.median(ds["train"].loc[ds["train"]["y_mask"], "y_hours"]))
    a = evaluate.thirst_baseline_table(ds, const)
    b = evaluate.event_detection_table(ds)
    a.to_csv(out / "model_a_baseline.csv", index=False); b.to_csv(out / "model_b_rule_detector.csv", index=False)
    print("train median y_hours (constant baseline):", const, " mean watering interval h (train):", ds["_meta"]["baseline_mean_interval_h"])
    print(a.round(3).to_string(index=False))
    print(b.round(3).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

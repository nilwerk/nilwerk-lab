"""Showcase image for 4.AI2 (caption C3): recall vs false alerts per unit-week on TEST, plus recall intervals.

Usage: python -I scripts/make_showcase_plot.py <model-b-wetting-v0.json> <rule-sweep.json> <out.png>
Inputs are the committed reports; nothing is retyped. Headline = int8 (shipped artefact), float and rule shown beside it.
"""
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main(rep_path: str, sweep_path: str, out_png: str) -> None:
    r = json.load(open(rep_path)); sw = json.load(open(sweep_path))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    a = ax[0]
    a.plot([x["fa_per_unit_week"] for x in sw["test"]], [100 * x["recall"] for x in sw["test"]], "-s", color="#c0392b", ms=4,
           label="Rule, threshold swept (8..100 pts/h)")
    fl = r["float"]
    a.scatter([e["test"]["model"]["false_alerts_per_unit_week"] for e in fl.values()],
              [100 * e["test"]["model"]["wetting"]["recall"] for e in fl.values()], color="#7fb3d5", s=30, label="MLP float, seeds 0-4")
    i = r["int8"]["test"]["model"]
    a.scatter([i["false_alerts_per_unit_week"]], [100 * i["wetting"]["recall"]], marker="*", s=220, color="#1f4e79", zorder=5,
              label="MLP int8 (shipped), seed 0")
    a.axvline(1, color="gray", ls="--"); a.axhline(95, color="gray", ls=":")
    a.text(1.3, 96.5, "target: recall 95 %, <= 1 FA/week", fontsize=8)
    a.set_xlabel("false alerts per unit-week (TEST)"); a.set_ylabel("wetting recall % (TEST, 20 positives)")
    a.set_ylim(0, 100); a.set_xlim(-1, 27); a.legend(loc="center right", fontsize=8)
    a.set_title("Model B wetting: target NOT met", fontsize=10)
    b = ax[1]
    for x, (name, m, c) in enumerate([("val int8", r["int8"]["val"]["model"], "#1f4e79"), ("test int8", r["int8"]["test"]["model"], "#1f4e79"),
                                      ("val float", fl["seed0"]["val"]["model"], "#7fb3d5"), ("test float", fl["seed0"]["test"]["model"], "#7fb3d5")]):
        w = m["wetting"]; lo, hi = w["recall_ci95"]
        b.errorbar(x, 100 * w["recall"], yerr=[[100 * (w["recall"] - lo)], [100 * (hi - w["recall"])]], fmt="o", color=c, capsize=6)
        b.text(x + 0.08, 100 * w["recall"], f"{m['false_alerts_per_unit_week']:.2f} FA/wk", fontsize=8)
    b.set_xticks(range(4)); b.set_xticklabels(["val int8", "test int8", "val float", "test float"])
    b.set_ylim(0, 100); b.set_ylabel("wetting recall %"); b.set_title("seed-0 recall with 95 % interval (15 val / 20 test positives)", fontsize=10)
    fig.tight_layout(); fig.savefig(out_png, dpi=100)


if __name__ == "__main__":
    main(*sys.argv[1:4])

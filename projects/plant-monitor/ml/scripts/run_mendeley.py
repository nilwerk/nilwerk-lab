"""Run the real Mendeley loader + preprocessing + labels; print data-card numbers, write the hand-check list.

Usage: python -I scripts/run_mendeley.py <raw_dir> <out_dir>
Raw data stays in the gitignored data/raw/. Output: counts.json + handcheck_50.csv in <out_dir>.
No model is trained here; the numbers are data counts, not results.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import export, loaders, prep  # noqa: E402


def triage(r) -> tuple[str, str]:
    """Rule-based triage of one hand-check row from the numbers alone (no plots were viewed)."""
    if r.event == "watering":
        return ("ok", "valve open within 45 min") if r.irrigation_within_3h else ("check", "watering without valve signal")
    if r.event == "rain":
        return ("ok", "ERA5 rain at tick") if r.rain > 0 else ("check", "rain label without rain")
    if r.event == "wetting":
        return ("unexplained", "rise with no valve/rain signal: probe jump, unrecorded irrigation or rain on an uncovered plot")
    if r.m <= 0.5:
        return ("check", "m clipped at 0: end-of-data flatline or calibration floor")
    big = [abs(x - r.m) >= 10 for x in (r.m_m3h, r.m_p3h) if x == x]
    if r.irrigation > 0 and not r.event == "watering":
        return ("check", "valve open at this tick but no event: probe lag or valve on another plot")
    if any(big):
        return ("check", "m moves >= 10 points within 3 h but no event")
    return ("ok", "quiet window, no event")


def main(raw_dir: str, out_dir: str) -> None:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    raw, st = loaders.load_mendeley(Path(raw_dir))
    print(st.to_string())
    sp = prep.preprocess(raw, inject=False, seed=0)          # real data only: no synthetic faults in the counts
    cal = sp.pop("_calibration")
    cnt = prep.split_counts(sp)
    print(cnt.T.to_string()); print(cal.to_string())
    allr = pd.concat(sp.values(), ignore_index=True)
    ev = allr[allr["event"] != prep.EVENT_NONE]
    base = {s: prep.mean_watering_interval_h(sp["train"]) for s in ("train",)}
    ds = export.build_dataset(sp)
    dc = export.dataset_counts(ds)
    print(dc.to_string())
    ect = export.event_class_table(ds)                       # A-032 month x sector table (data card)
    ect.to_csv(out / "event_class_table.csv", index=False)
    print(ect.to_string(index=False))
    res = {"rows_raw_valid": int(len(raw)), "devices": sorted(raw["plant"].unique()),
           "date_utc": [str(raw["time"].min()), str(raw["time"].max())],
           "ticks_after_split": {k: int(len(v)) for k, v in sp.items()},
           "events_by_class": ev["event"].value_counts().to_dict(),
           "baseline_mean_watering_interval_h_train": base["train"],
           "model_label": prep.model_label(sp["train"])}
    # 50-window hand-check list: stratified over events and a random sample of non-event ticks
    rng = np.random.default_rng(0)
    pick = []
    wet = ev.sample(min(30, len(ev)), random_state=0)
    for _, r in wet.iterrows():
        pick.append(r)
    quiet = allr[(allr["event"] == prep.EVENT_NONE) & allr["m"].notna()]
    for _, r in quiet.iloc[rng.choice(len(quiet), 20, replace=False)].iterrows():
        pick.append(r)
    hc = pd.DataFrame(pick)[["plant", "split", "time", "m", "moisture_raw", "event", "irrigation", "rain"]].reset_index(drop=True)
    # context: m 3 h before and 3 h after, to judge by eye whether the label is sane
    key = allr.set_index(["plant", "time"])["m"]
    def at(p, t, h):
        return key.get((p, t + pd.Timedelta(hours=h)), np.nan)
    for h in (-3, 3):
        hc[f"m_{'m' if h < 0 else 'p'}3h"] = [at(r.plant, r.time, h) for r in hc.itertuples()]
    hc["irrigation_within_3h"] = [bool(((allr["plant"] == r.plant) & (allr["time"].between(r.time - pd.Timedelta(hours=3), r.time)) & (allr["irrigation"] > 0)).any()) for r in hc.itertuples()]
    hc["verdict"], hc["note"] = zip(*[triage(r) for r in hc.itertuples()])
    hc.to_csv(out / "handcheck_50.csv", index=False)
    (out / "counts.json").write_text(json.dumps(res, indent=1, default=str))
    st.to_csv(out / "sector_stats.csv", index=False); cnt.to_csv(out / "split_counts.csv", index=False); dc.to_csv(out / "dataset_counts.csv", index=False)
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

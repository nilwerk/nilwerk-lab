"""Regenerate tests/golden/features_golden.json (inputs are frozen in the file; expected outputs come from
src/features.py). Run only when the feature DEFINITION changes on purpose, then port the change to C and
commit both. Traces to FR-E01, FR-E04. SYNTHETIC inputs only."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import features as F  # noqa: E402


def cases():
    rng = np.random.default_rng(20251105)
    n = F.HIST
    out = []
    ramp_down = [99 - i for i in range(n)]
    out.append(("constant_50", [50] * n, [40] * n, [128] * n, 0, 25, 288, 1))
    out.append(("ramp_down_1pp_per_tick", ramp_down, [40] * n, [100] * n, 13 * 60 + 45, 25, 100, 0))
    out.append(("ramp_up_1pp_per_tick", [4 + i for i in range(n)], [45] * n, [200] * n, 23 * 60 + 59, 30, 3, 2))
    out.append(("extremes_saturate", [0, 100] * (n // 2), [0] * n, [255] * n, 720, 0, 0, 1))
    out.append(("temp_high_saturates", [60] * n, [255] * n, [0] * n, 6 * 60, 100, 288, 1))
    for k in range(5):
        base = np.clip(np.cumsum(rng.integers(-3, 4, n)) + int(rng.integers(30, 70)), 0, 100)
        out.append((f"random_walk_{k}", base.tolist(), rng.integers(30, 70, n).tolist(), rng.integers(0, 256, n).tolist(),
                    int(rng.integers(0, 1440)), int(rng.integers(10, 50)), int(rng.integers(0, 289)), int(rng.integers(0, 3))))
    return out


def tracker_cases():
    rng = np.random.default_rng(7)
    a = [40] * 10 + [55] * 3 + [38] * 2 + [55] * 5 + [30] * 10 + [45] * 4 + [30] * 10 + [60] * 5 + [20] * 10   # 2nd rise inside refractory
    b = np.clip(np.cumsum(rng.integers(-9, 10, 120)) + 50, 0, 100).tolist()
    return [("two_rises_refractory", a, [True] * len(a)), ("random_walk", b, [True] * 60 + [False] * 5 + [True] * 55)]


def build():
    feats = []
    for name, m, t, lt, minute, T, since, soil in cases():
        feats.append({"name": name, "m_hist": m, "temp_hist": t, "light_hist": lt, "minute_of_day": minute, "T": T,
                      "ticks_since_event": since, "soil": soil,
                      "expected": F.feature_vector(m, t, lt, minute, T, since, soil)})
    trk = [{"name": n, "m": m, "valid": v, "expected_since": F.ticks_since_event_series(m, v).tolist()}
           for n, m, v in tracker_cases()]
    return {"_note": "SYNTHETIC golden vectors; contract between features.py and the C port (FR-E01, FR-E04)",
            "feature_names": list(F.FEATURE_NAMES), "features": feats, "tracker": trk}


if __name__ == "__main__":
    p = ROOT / "tests" / "golden" / "features_golden.json"
    p.write_text(json.dumps(build(), indent=1))
    print("wrote", p)

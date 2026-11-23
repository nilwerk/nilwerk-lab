#!/usr/bin/env python3
"""PR #187 review conditions (Theo, comment 7110809956), comment-level facts that must not drift.
C1: sdkconfig.defaults.bench-ci describes the real overlay order (local file before bench-ci, bench-ci last), not "outside the repo".
C2: bench/firmware/expect.txt matches the NWBENCH wake printf in main/main.c (the text grep looks for is in the source).
C4: the bench 70/h define names the contract line (openapi.yaml line 110, 6 requests per device per hour) and production stays 6.
`--selftest` proves each rule can fail on a mutated copy."""
import pathlib, sys

root = pathlib.Path(__file__).resolve().parents[2]   # projects/plant-monitor/firmware
repo = root.parents[2]

def check(t):
    errs = []
    bc = t["bench-ci"]
    if "outside the repo" in bc: errs.append("C1: bench-ci comment still says the URL file is outside the repo")
    if "sdkconfig.defaults.local;sdkconfig.defaults.bench-ci" not in bc: errs.append("C1: bench-ci comment does not state the real order (local before bench-ci)")
    ex = [l for l in t["expect"].splitlines() if l.strip() and not l.lstrip().startswith("#")]
    if not ex or ex[0].strip() not in t["main"]: errs.append("C2: first expect.txt line is not the NWBENCH text in main/main.c")
    if "printed only by the bench app" in t["expect"]: errs.append("C2: expect.txt still says the wake line is printed only by the bench app")
    if "openapi.yaml line 110" not in t["upload_h"]: errs.append("C4: bench 70/h define does not name openapi.yaml line 110")
    if "#define NW_UPLOAD_MAX_PER_HOUR 6 " not in t["upload_h"]: errs.append("C4: production NW_UPLOAD_MAX_PER_HOUR is not 6")
    if "max 6 requests per device per hour" not in t["openapi"].splitlines()[109]: errs.append("C4: openapi.yaml line 110 no longer states the 6/h contract")
    return errs

def load():
    return {
        "bench-ci": (root / "sdkconfig.defaults.bench-ci").read_text(),
        "expect": (repo / "bench" / "firmware" / "expect.txt").read_text(),
        "main": (root / "main" / "main.c").read_text(),
        "upload_h": (root / "components" / "upload" / "include" / "nw_upload.h").read_text(),
        "openapi": (repo / "projects" / "plant-monitor" / "docs" / "interfaces" / "openapi.yaml").read_text(),
    }

def selftest():
    base = load()
    if check(base): print("selftest: base tree fails", check(base)); return 1
    mutants = {
        "C1 outside-repo wording": ("bench-ci", "sdkconfig.defaults.local;sdkconfig.defaults.bench-ci", "outside the repo"),
        "C2 stale printed-only claim": ("expect", "NWBENCH wake=", "printed only by the bench app NWBENCH wake="),
        "C4 contract line not named": ("upload_h", "openapi.yaml line 110", "openapi.yaml"),
    }
    for name, (key, old, new) in mutants.items():
        t = dict(base); t[key] = t[key].replace(old, new, 1)
        if not check(t): print("selftest: mutant survived:", name); return 1
    print("selftest ok: 3 mutants killed"); return 0

if __name__ == "__main__":
    if "--selftest" in sys.argv: sys.exit(selftest())
    errs = check(load())
    for e in errs: print(e)
    sys.exit(1 if errs else 0)

#!/usr/bin/env python3
"""A-094 (bench only): the soil probe supply stays on between readings on the bench CI image, and only there.
B1: sdkconfig.defaults.bench-ci sets CONFIG_PLANT_BENCH_SOIL_POWER_ON=y. The check FAILS if the bench switch is off.
B2: main/Kconfig.projbuild defines PLANT_BENCH_SOIL_POWER_ON with default n and a BENCH CI IMAGE ONLY help text.
B3: components/sensors/src/hal_esp32.c forces the supply on only under #ifdef CONFIG_PLANT_BENCH_SOIL_POWER_ON.
B4: no production, v1, setup or upload overlay turns the switch on.
`--selftest` proves each rule can fail on a mutated copy."""
import pathlib, re, sys

root = pathlib.Path(__file__).resolve().parents[2]   # projects/plant-monitor/firmware
SWITCH = "CONFIG_PLANT_BENCH_SOIL_POWER_ON"
OVERLAYS_NOT_BENCH = ["sdkconfig.defaults", "sdkconfig.defaults.v1", "sdkconfig.defaults.setup", "sdkconfig.defaults.upload", "sdkconfig.defaults.sim-qemu", "sdkconfig.defaults.sim-setup"]

def check(t):
    errs = []
    if not re.search(r"^CONFIG_PLANT_BENCH_SOIL_POWER_ON=y$", t["bench-ci"], re.M):
        errs.append("B1: sdkconfig.defaults.bench-ci does not set CONFIG_PLANT_BENCH_SOIL_POWER_ON=y (bench switch off)")
    k = t["kconfig"]
    m = re.search(r"config PLANT_BENCH_SOIL_POWER_ON\n(.*?)\n\n", k + "\n\n", re.S)
    if not m:
        errs.append("B2: main/Kconfig.projbuild does not define PLANT_BENCH_SOIL_POWER_ON")
    else:
        body = m.group(1)
        if "default n" not in body: errs.append("B2: PLANT_BENCH_SOIL_POWER_ON default is not n")
        if "BENCH CI IMAGE ONLY" not in body: errs.append("B2: PLANT_BENCH_SOIL_POWER_ON help does not say BENCH CI IMAGE ONLY")
    if f"#ifdef {SWITCH}" not in t["hal"]: errs.append("B3: hal_esp32.c does not gate the soil supply on the bench switch")
    for name, text in t["overlays"].items():
        if re.search(rf"^{SWITCH}=y$", text, re.M):
            errs.append(f"B4: {name} turns the bench soil switch on (production, v1, setup or upload build)")
    return errs

def load():
    return {
        "bench-ci": (root / "sdkconfig.defaults.bench-ci").read_text(),
        "kconfig": (root / "main" / "Kconfig.projbuild").read_text(),
        "hal": (root / "components" / "sensors" / "src" / "hal_esp32.c").read_text(),
        "overlays": {n: (root / n).read_text() for n in OVERLAYS_NOT_BENCH if (root / n).exists()},
    }

def selftest():
    base = load()
    if check(base): print("selftest: base tree fails", check(base)); return 1
    mutants = {
        "B1 bench switch off": ("bench-ci", f"{SWITCH}=y", f"# {SWITCH} is not set"),
        "B2 Kconfig default y": ("kconfig", "default n\n        help\n            BENCH CI IMAGE ONLY (set by sdkconfig.defaults.bench-ci). The soil", "default y\n        help\n            BENCH CI IMAGE ONLY (set by sdkconfig.defaults.bench-ci). The soil"),
        "B3 HAL gate removed": ("hal", f"#ifdef {SWITCH}", "#if 0"),
        "B4 production overlay on": ("overlays", "sdkconfig.defaults.v1", None),
    }
    for name, (key, old, new) in mutants.items():
        t = dict(base)
        if key == "overlays":
            t["overlays"] = dict(base["overlays"]); t["overlays"]["sdkconfig.defaults.v1"] = base["overlays"]["sdkconfig.defaults.v1"] + f"\n{SWITCH}=y\n"
        else:
            t[key] = t[key].replace(old, new, 1)
        if not check(t): print("selftest: mutant survived:", name); return 1
    print("selftest ok: 4 mutants killed"); return 0

if __name__ == "__main__":
    if "--selftest" in sys.argv: sys.exit(selftest())
    errs = check(load())
    for e in errs: print(e)
    sys.exit(1 if errs else 0)

#!/usr/bin/env python3
"""Soil probe direction and calibration defaults (task 4.F5, FR-D10, FR-D01, NFR-02).
Owner bench facts (28 Nov): the raw count is LOW in dry air (15-25) and HIGH in water (about 360), so the calibration defaults are
dry 20 and wet 360, dry < wet, and the mock/QEMU expectations must agree with them.
Fails when a default is reversed or back at the old placeholders (2800/1200), when the QEMU expectation or the mock raw no longer
map to 50.0 % with the defaults, or when nw_soil.c stops refusing a swapped pair. `--selftest` proves each rule can fail."""
import re, sys, pathlib

root = pathlib.Path(__file__).resolve().parents[2]
EXPECT_DRY, EXPECT_WET = 20, 360

def check(kconfig, mock, qemu, soil):
    e = []
    def dflt(name):
        m = re.search(r"config %s\s+int[^\n]*\n(?:[^\n]*\n)*?\s+default (\d+)" % name, kconfig)
        return int(m.group(1)) if m else None
    dry, wet = dflt("PLANT_SOIL_DRY_RAW"), dflt("PLANT_SOIL_WET_RAW")
    if dry != EXPECT_DRY: e.append(f"PLANT_SOIL_DRY_RAW default is {dry}, expected {EXPECT_DRY} (owner bench, dry air reads low)")
    if wet != EXPECT_WET: e.append(f"PLANT_SOIL_WET_RAW default is {wet}, expected {EXPECT_WET} (owner bench, water reads high)")
    if dry is not None and wet is not None:
        if not (0 <= dry < wet <= 4095): e.append("calibration defaults must satisfy 0 <= dry < wet <= 4095 (the probe reads high when wet)")
    m = re.search(r"#define SIM_MOCK_SOIL_RAW\s+(\d+)", mock)
    if not m: e.append("sim_mock_hal.c has no SIM_MOCK_SOIL_RAW")
    elif dry is not None and wet is not None:
        raw = int(m.group(1))
        if not (dry < raw < wet) or round((raw - dry) * 1000 / (wet - dry)) != 500:
            e.append(f"SIM_MOCK_SOIL_RAW {raw} does not map to 50.0 % with dry {dry} / wet {wet}")
    if f"cal_dry={EXPECT_DRY} cal_wet={EXPECT_WET} " not in qemu: e.append("tests/qemu_boot_check.sh does not expect cal_dry=20 cal_wet=360")
    if "2800" in qemu or "1200" in qemu: e.append("tests/qemu_boot_check.sh still expects the old placeholders")
    if "if (cal->wet_raw - cal->dry_raw < NW_SOIL_MIN_SPAN_COUNTS) return NW_ERR_CAL;" not in soil:
        e.append("nw_soil.c no longer refuses a swapped (dry >= wet) calibration pair")
    if "dry reads high" in soil or "dry high" in soil: e.append("nw_soil comments still describe the probe as reading high when dry")
    return e

def load():
    return (root / "main/Kconfig.projbuild").read_text(), (root / "main/sim_mock_hal.c").read_text(), \
           (root / "tests/qemu_boot_check.sh").read_text(), (root / "components/sensors/src/nw_soil.c").read_text()

def main():
    kc, mk, qe, so = load()
    if "--selftest" in sys.argv:
        muts = [("kc", "default 20\n        range 0 4095", "default 2800\n        range 0 4095", "dry default back at placeholder"),
                ("kc", "default 360\n        range 0 4095", "default 1200\n        range 0 4095", "wet default back at placeholder"),
                ("kc", "default 20\n        range 0 4095", "default 400\n        range 0 4095", "dry above wet"),
                ("mk", "#define SIM_MOCK_SOIL_RAW        190 ", "#define SIM_MOCK_SOIL_RAW        2000", "mock raw outside the span"),
                ("qe", "cal_dry=20 cal_wet=360", "cal_dry=2800 cal_wet=1200", "QEMU expects old placeholders"),
                ("so", "if (cal->wet_raw - cal->dry_raw < NW_SOIL_MIN_SPAN_COUNTS) return NW_ERR_CAL;", "if (1) return NW_ERR_CAL;", "swap guard removed"),
                ("so", "/* Direction", "/* dry reads high: direction", "comment says the probe reads high when dry")]
        bad = 0
        for where, old, new, what in muts:
            vals = {"kc": kc, "mk": mk, "qe": qe, "so": so}
            if old not in vals[where]: print("SELFTEST invalid mutant:", what); bad += 1; continue
            vals[where] = vals[where].replace(old, new, 1)
            errs = check(vals["kc"], vals["mk"], vals["qe"], vals["so"])
            if not errs: print("SELFTEST survived:", what); bad += 1
        if bad: sys.exit(1)
        print(f"selftest ok: {len(muts)} mutants flagged")
        return
    errs = check(kc, mk, qe, so)
    for x in errs: print("FAIL:", x)
    if errs: sys.exit(1)
    print("soil direction and defaults: ok (dry 20 < wet 360)")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Mutation check for the sensor driver logic (task 4.F1): each mutant must make test_sensors fail.
Usage: mutate.py [cc]. Works on a temp copy, never edits the sources. Exit 1 when a mutant survives or does not compile."""
import pathlib, shutil, subprocess, sys, tempfile

here = pathlib.Path(__file__).resolve().parent
sens = here.parent.parent / "components" / "sensors"
cc = sys.argv[1] if len(sys.argv) > 1 else "cc"
SRC = ["nw_aht20.c", "nw_bh1750.c", "nw_soil.c", "nw_battery.c"]

# (file, original text, mutated text, what it breaks)
M = [
 ("nw_aht20.c", "^ 0x31)", "^ 0x32)", "ahtCRC polynomial"),
 ("nw_aht20.c", "uint8_t crc = 0xFF;", "uint8_t crc = 0x00;", "CRC init"),
 ("nw_aht20.c", "(crc & 0x80) ?", "(crc & 0x40) ?", "CRC msb test"),
 ("nw_aht20.c", "nw_aht20_crc8(frame, 6) != frame[6]", "nw_aht20_crc8(frame, 5) != frame[6]", "CRC covers 6 bytes"),
 ("nw_aht20.c", "return NW_ERR_CRC;", "return NW_OK;", "CRC error ignored"),
 ("nw_aht20.c", "(frame[0] & AHT20_STATUS_BUSY) return NW_ERR_BUSY", "(frame[0] & 0x40) return NW_ERR_BUSY", "busy bit position"),
 ("nw_aht20.c", "(uint32_t)frame[1] << 12", "(uint32_t)frame[1] << 11", "humidity bit packing"),
 ("nw_aht20.c", "(frame[3] >> 4)", "(frame[3] & 0x0F)", "humidity low nibble"),
 ("nw_aht20.c", "(frame[3] & 0x0F) << 16", "(frame[3] & 0x07) << 16", "temperature high nibble"),
 ("nw_aht20.c", "* 10000u + (1u << 19)", "* 1000u + (1u << 19)", "humidity scale"),
 ("nw_aht20.c", "* 20000u + (1u << 19)) >> 20) - 5000", "* 20000u + (1u << 19)) >> 20) - 4000", "temperature offset"),
 ("nw_aht20.c", "* 20000u + (1u << 19)) >> 20)", "* 10000u + (1u << 19)) >> 20)", "temperature span"),
 ("nw_aht20.c", "AHT20_WAIT_MS 80", "AHT20_WAIT_MS 20", "80 ms conversion wait"),
 ("nw_aht20.c", "{0xAC, 0x33, 0x00}", "{0xAC, 0x33, 0x01}", "trigger command"),
 ("nw_aht20.c", "{0xBE, 0x08, 0x00}", "{0xBE, 0x00, 0x00}", "init command"),
 ("nw_aht20.c", "tries <= AHT20_BUSY_RETRIES", "tries <= 100", "bounded busy retries"),
 ("nw_bh1750.c", "(uint32_t)raw * 25u + 1u) / 3u", "(uint32_t)raw * 10u + 1u) / 1u", "lux divisor 1.2"),
 ("nw_bh1750.c", "(raw == 0xFFFF)", "(raw >= 0xFFFE)", "saturation flag"),
 ("nw_bh1750.c", "(uint16_t)((b[0] << 8) | b[1])", "(uint16_t)((b[1] << 8) | b[0])", "byte order"),
 ("nw_bh1750.c", "NW_BH1750_CMD_ONE_TIME_H;", "0x10;", "one-time mode"),
 ("nw_bh1750.h", "NW_BH1750_MEAS_WAIT_MS 180", "NW_BH1750_MEAS_WAIT_MS 100", "measurement wait"),
 ("nw_soil.c", "(num + den / 2) / den", "num / den", "rounding"),
 ("nw_soil.c", "long long num = (long long)(v - cal->dry_raw) * 1000;", "long long num = (long long)(v - cal->wet_raw) * 1000;", "dry/wet swapped"),
 ("nw_soil.c", "if (raw < cal->dry_raw) { v = cal->dry_raw; out->flags |= NW_SOIL_F_CLAMPED_DRY; }", "if (raw < cal->dry_raw) { out->flags |= NW_SOIL_F_CLAMPED_DRY; }", "dry clamp"),
 ("nw_soil.c", "if (raw > cal->wet_raw) { v = cal->wet_raw; out->flags |= NW_SOIL_F_CLAMPED_WET; }", "if (raw > cal->wet_raw) { out->flags |= NW_SOIL_F_CLAMPED_WET; }", "wet clamp"),
 ("nw_soil.c", "if (raw > cal->wet_raw) { v = cal->wet_raw;", "if (raw < cal->wet_raw) { v = cal->wet_raw;", "wet clamp side (task 4.F5 direction)"),
 ("nw_soil.c", "long long num = (long long)(v - cal->dry_raw) * 1000;", "long long num = (long long)(cal->wet_raw - v) * 1000;", "direction inverted: pct counted from the wet end (task 4.F5)"),
 ("nw_soil.c", "if (cal->wet_raw - cal->dry_raw < NW_SOIL_MIN_SPAN_COUNTS) return NW_ERR_CAL;", "if (cal->wet_raw - cal->dry_raw < NW_SOIL_MIN_SPAN_COUNTS && cal->dry_raw < cal->wet_raw) return NW_ERR_CAL;", "swapped dry/wet pair accepted (task 4.F5)"),
 ("nw_soil.c", "if (raw <= 0 || raw >= 4095)", "if (raw < 0 || raw > 4095)", "rail flag boundaries"),
 ("nw_soil.c", "< NW_SOIL_MIN_SPAN_COUNTS) return NW_ERR_CAL", "<= 0) return NW_ERR_CAL", "minimum span"),
 ("nw_soil.c", "hal->soil_power(hal->ctx, false); /* NFR-12", "/* NFR-12", "supply left on (NFR-12)"),
 ("nw_soil.c", "if (hal->adc_read(hal->ctx, NW_ADC_SOIL, &s) != 0) { err = NW_ERR_IO; break; }", "if (hal->adc_read(hal->ctx, NW_ADC_SOIL, &s) != 0) { return NW_ERR_IO; }", "supply left on after ADC error"),
 ("nw_soil.h", "NW_SOIL_WARMUP_MS 1500", "NW_SOIL_WARMUP_MS 100", "warm-up time"),
 ("nw_soil.c", "(sum + NW_SOIL_SAMPLES / 2) / NW_SOIL_SAMPLES", "sum / NW_SOIL_SAMPLES", "average rounding"),
 ("nw_soil.c", "sum += s.raw;", "sum = s.raw;", "averaging"),
 ("nw_battery.c", "(cfg->r_top_ohm + cfg->r_bot_ohm);\n    return (uint32_t)((num", "(cfg->r_bot_ohm);\n    return (uint32_t)((num", "divider ratio 2:1"),
 ("nw_battery.c", "(num + cfg->r_bot_ohm / 2) / cfg->r_bot_ohm", "num / cfg->r_bot_ohm", "battery rounding"),
 ("nw_battery.c", "vbat_mv >= NW_BAT_PLAUSIBLE_MIN_MV", "vbat_mv > NW_BAT_PLAUSIBLE_MIN_MV", "plausible lower bound inclusive"),
 ("nw_battery.c", "vbat_mv <= NW_BAT_PLAUSIBLE_MAX_MV", "vbat_mv < NW_BAT_PLAUSIBLE_MAX_MV", "plausible upper bound inclusive"),
 ("nw_battery.h", "NW_BAT_PLAUSIBLE_MAX_MV 4250", "NW_BAT_PLAUSIBLE_MAX_MV 4200", "plausible max value"),
 ("nw_battery.c", "* 1000000u) / (cfg->r_top_ohm", "* 1000u) / (cfg->r_top_ohm", "divider current scale (2.1 uA note)"),
 ("nw_battery.c", "!s.calibrated || s.mv < 0", "s.mv < -5", "uncalibrated ADC rejected"),
 ("nw_battery.c", "if (hal->adc_read(hal->ctx, NW_ADC_BAT, &s) != 0) return NW_ERR_IO; /* dummy", "(void)0; /* dummy", "dummy conversion"),
 ("nw_battery.c", "NW_BAT_SAMPLES; i++) {\n        hal->delay_ms", "NW_BAT_SAMPLES - 1; i++) {\n        hal->delay_ms", "sample count"),
]

def build_and_run(workdir):
    exe = workdir / "t"
    cmd = [cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(workdir / "include"), "-I", str(here),
           str(here / "test_main.c")] + [str(workdir / "src" / s) for s in SRC] + ["-o", str(exe)]
    c = subprocess.run(cmd, capture_output=True, text=True)
    if c.returncode: return "compile", c.stderr
    r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=60)
    return ("pass" if r.returncode == 0 else "fail"), r.stdout

bad = 0
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    def fresh():
        w = td / "w"
        if w.exists(): shutil.rmtree(w)
        shutil.copytree(sens, w, ignore=shutil.ignore_patterns("hal_esp32.c", "CMakeLists.txt"))
        return w
    st, out = build_and_run(fresh())
    if st != "pass": print("baseline does not pass:", st, out); sys.exit(1)
    killed = 0
    for f, old, new, what in M:
        w = fresh()
        p = next(w.rglob(f))
        s = p.read_text()
        if s.count(old) != 1:
            print(f"INVALID mutant (pattern found {s.count(old)}x): {f}: {what}"); bad += 1; continue
        p.write_text(s.replace(old, new))
        st, out = build_and_run(w)
        if st == "fail": killed += 1; print(f"killed   {f}: {what}")
        elif st == "compile": print(f"COMPILE ERROR in mutant {f}: {what}\n{out}"); bad += 1
        else: print(f"SURVIVED {f}: {what}"); bad += 1
    print(f"{killed}/{len(M)} mutants killed")
sys.exit(1 if bad else 0)

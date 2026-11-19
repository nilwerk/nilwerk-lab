#!/usr/bin/env python3
"""Mutation check for nw_cycle.c (task 4.F3 slice 3). Each mutant changes one rule; test_cycle must fail.
Usage: mutate_cycle.py <cc>. A surviving mutant means a rule has no test."""
import pathlib, shutil, subprocess, sys, tempfile

cc = sys.argv[1] if len(sys.argv) > 1 else "cc"
here = pathlib.Path(__file__).resolve().parent
comp = here.parent.parent / "components"
DIRS = ("storage", "report", "power", "upload", "sensors", "provisioning")
SRC = ["storage/src/nw_sample_ring.c", "report/src/nw_report.c", "power/src/nw_sleep.c", "upload/src/nw_upload.c", "upload/src/nw_cycle.c",
       "sensors/src/nw_battery.c", "provisioning/src/nw_prov_proto.c"]

M = [  # (file, old, new, what)
 ("nw_cycle.c", "if (st->magic == NW_CYCLE_MAGIC) return false;", "if (0) return false;", "RTC state kept across deep sleep"),
 ("nw_cycle.c", "return now_unix >= NW_TS_MIN;", "return now_unix > NW_TS_MIN;", "clock floor inclusive"),
 ("nw_cycle.c", "return now_unix >= NW_TS_MIN;", "return now_unix != 0;", "1970 clock is not synced"),
 ("nw_cycle.c", "if (sl == 0 || sl > NW_PROV_SSID_MAX_BYTES)", "if (sl > NW_PROV_SSID_MAX_BYTES)", "empty SSID refused"),
 ("nw_cycle.c", "if (sl == 0 || sl > NW_PROV_SSID_MAX_BYTES)", "if (sl == 0 || sl > NW_PROV_SSID_MAX_BYTES + 1)", "SSID maximum 32 (unterminated refused)"),
 ("nw_cycle.c", "pl < NW_PROV_PASS_MIN", "pl < NW_PROV_PASS_MIN - 1", "passphrase minimum 8"),
 ("nw_cycle.c", "pl > NW_PROV_PASS_MAX", "pl > NW_PROV_PASS_MAX + 1", "passphrase maximum 63"),
 ("nw_cycle.c", "(pl != 0 && (pl <", "((pl <", "open network allowed"),
 ("nw_cycle.c", "return n < 0 ? NW_CREDS_BAD_TOKEN : NW_CREDS_OK;", "(void)n; return NW_CREDS_OK;", "bad token refused"),
 ("nw_cycle.c", "if (e_soil == NW_OK && soil && soil->pct_x10 >= 0 && soil->pct_x10 <= 1000)", "if (soil && soil->pct_x10 >= 0 && soil->pct_x10 <= 1000)", "failed soil sensor is null"),
 ("nw_cycle.c", "soil->pct_x10 <= 1000)", "soil->pct_x10 <= 1001)", "moisture upper bound"),
 ("nw_cycle.c", "soil->raw <= 4095)", "soil->raw <= 4096)", "raw upper bound"),
 ("nw_cycle.c", "if (e_aht == NW_OK && aht) {", "(void)e_aht; if (aht) {", "failed AHT20 is null"),
 ("nw_cycle.c", "aht->rh_x100 <= 10000)", "aht->rh_x100 <= 10001)", "RH upper bound"),
 ("nw_cycle.c", "if (e_bh == NW_OK && bh) {", "(void)e_bh; if (bh) {", "failed BH1750 is null"),
 ("nw_cycle.c", "if (e_bat == NW_OK && nw_battery_plausible(vbat_mv)) {", "(void)e_bat; if (nw_battery_plausible(vbat_mv)) {", "failed battery read is null"),
 ("nw_cycle.c", "if (e_bat == NW_OK && nw_battery_plausible(vbat_mv)) {", "if (e_bat == NW_OK) {", "implausible battery is null"),
 ("nw_cycle.c", "s.ts = now_unix;", "", "sample stamped with the RTC time"),
 ("nw_cycle.c", "p.pushed = nw_ring_push(&st->ring, &s, synced);", "p.pushed = nw_ring_push(&st->ring, &s, true);", "unsynced clock: no sample admitted"),
 ("nw_cycle.c", ".buffered = (uint32_t)nw_ring_count(&st->ring)", ".buffered = 0", "buffered count feeds the decision"),
 ("nw_cycle.c", ".low_battery_prev = st->low_battery", ".low_battery_prev = false", "low-battery state retained"),
 ("nw_cycle.c", ".outage_pending = st->outage_pending,", ".outage_pending = false,", "outage state fed to the decision"),
 ("nw_cycle.c", "st->low_battery = p.sleep.low_battery;", "", "low-battery state stored"),
 ("nw_cycle.c", "st->outage_pending = p.sleep.outage_pending;", "", "blocked report sets outage"),
 ("nw_cycle.c", "case NW_REPORT_CRITICAL: *t = NW_TRIG_CRITICAL; return true;", "case NW_REPORT_CRITICAL: *t = NW_TRIG_SCHEDULED; return true;", "critical trigger"),
 ("nw_cycle.c", "case NW_REPORT_RECONNECT: *t = NW_TRIG_RECONNECT; return true;", "case NW_REPORT_RECONNECT: *t = NW_TRIG_SCHEDULED; return true;", "reconnect trigger"),
 ("nw_cycle.c", "case NW_REPORT_SCHEDULED: *t = NW_TRIG_SCHEDULED; return true;", "case NW_REPORT_SCHEDULED: *t = NW_TRIG_CRITICAL; return true;", "scheduled trigger"),
 ("nw_cycle.c", "default: return false;", "default: return true;", "NONE sends nothing"),
 ("nw_cycle.c", "m.sent_at = now_unix;", "", "sent_at set"),
 ("nw_cycle.c", "m.fw = fw;", "(void)fw;", "fw sent"),
 ("nw_cycle.c", "st->outage_pending = r.outage_pending;\n    if (r.outcome", "if (r.outcome", "result updates outage state"),
 ("nw_cycle.c", "if (r.outcome == NW_UP_ACK) st->last_report_unix", "if (r.outcome != NW_UP_NOT_SENT) st->last_report_unix", "last report only on an ack"),
 ("nw_cycle.c", "r.server_time_valid ? r.server_time : now_unix", "now_unix", "ack time from the server"),
 ("nw_cycle.c", "return NW_SLEEP_SAMPLE_PERIOD_S - (now_unix % NW_SLEEP_SAMPLE_PERIOD_S);", "return NW_SLEEP_SAMPLE_PERIOD_S;", "wake aligned to the 15-min boundary"),
 ("nw_cycle.c", "if (!nw_cycle_clock_ok(now_unix)) return NW_SLEEP_SAMPLE_PERIOD_S;", "", "unsynced clock sleeps 15 min"),
 ("nw_cycle.c", "if (!value || !*value) return -1;", "if (!value) return -1;", "empty Retry-After is unusable"),
 ("nw_cycle.c", "value[n] < '0' || value[n] > '9' || n >= 9", "value[n] < '0' || value[n] > '9'", "Retry-After digit cap (no overflow)"),
 ("nw_cycle.c", "value[n] < '0' || value[n] > '9' || n >= 9", "value[n] < '0' || value[n] > '8' || n >= 9", "Retry-After digit range"),
 ("nw_cycle.c", "value[n] < '0' || value[n] > '9' || n >= 9", "value[n] <= '0' || value[n] > '9' || n >= 9", "Retry-After zero digit"),
 ("nw_cycle.c", "v = v * 10 + (value[n] - '0');", "v = v * 10 + (value[n] - '0') + 1;", "Retry-After value"),
]

with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    def fresh():
        w = td / "w"
        if w.exists(): shutil.rmtree(w)
        for name in DIRS: shutil.copytree(comp / name, w / name)
        return w
    def build(w):
        exe = w / "t"
        cmd = [cc, "-std=c11", "-Wall", "-Wextra", "-Werror"] + sum((["-I", str(w / d / "include")] for d in DIRS), []) + \
              ["-I", str(here), str(here / "test_cycle.c")] + [str(w / p) for p in SRC] + ["-o", str(exe)]
        c = subprocess.run(cmd, capture_output=True, text=True)
        if c.returncode: return "compile", c.stderr
        r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=60)
        return ("pass" if r.returncode == 0 else "fail"), r.stdout
    st, out = build(fresh())
    if st != "pass": print("baseline does not pass:", st, out); sys.exit(1)
    bad = killed = 0
    for f, old, new, what in M:
        w = fresh()
        p = next(w.rglob(f))
        s = p.read_text()
        if s.count(old) != 1:
            print(f"INVALID mutant (pattern found {s.count(old)}x): {f}: {what}"); bad += 1; continue
        p.write_text(s.replace(old, new))
        st, out = build(w)
        if st == "fail": killed += 1; print(f"killed   {f}: {what}")
        elif st == "compile": print(f"COMPILE ERROR in mutant {f}: {what}\n{out}"); bad += 1
        else: print(f"SURVIVED {f}: {what}"); bad += 1
    print(f"{killed}/{len(M)} mutants killed")
sys.exit(1 if bad else 0)

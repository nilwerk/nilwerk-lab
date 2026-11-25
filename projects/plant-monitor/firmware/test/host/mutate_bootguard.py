#!/usr/bin/env python3
"""Mutation check for the boot-loop guard and safe fallback (FR-D05, NFR-01, NFR-12).

Each mutant changes one rule in components/bootguard/src/nw_bootguard.c (on a temp copy, the source is never edited) and must make
test_bootguard fail. A surviving mutant means a rule has no test. A mutant that does not apply or does not compile is BAD.
Usage: mutate_bootguard.py [cc]. Exit 0 only when the baseline passes and every mutant is killed."""
import pathlib, subprocess, sys, tempfile

cc = sys.argv[1] if len(sys.argv) > 1 else "cc"
here = pathlib.Path(__file__).resolve().parent
fw = here.parents[1] / "components"
SRC = fw / "bootguard" / "src" / "nw_bootguard.c"
INCS = [fw / d / "include" for d in ("bootguard", "ota", "upload", "storage", "report", "power", "sensors", "provisioning")]
OTA_SRC = fw / "ota" / "src" / "nw_ota.c"

M = [  # (old, new, what)
 # counter increment and clear
 ("    st->failed_boots++;\n    seal(st);", "    seal(st);", "boot does not count itself"),
 ("    st->failed_boots++;\n    seal(st);", "    st->failed_boots++;", "counter changed but not re-sealed"),
 ("void nw_bootguard_confirm_good(nw_bootguard_t *st)\n{\n    nw_bootguard_init(st);\n}", "void nw_bootguard_confirm_good(nw_bootguard_t *st)\n{\n    (void)st;\n}", "confirmed good boot does not clear the counter"),
 ("void nw_bootguard_confirm_good(nw_bootguard_t *st)\n{\n    nw_bootguard_init(st);\n}", "void nw_bootguard_confirm_good(nw_bootguard_t *st)\n{\n    if (st->failed_boots > 0) st->failed_boots--;\n    seal(st);\n}", "confirmed good boot only decrements"),
 ("    st->magic = NW_BOOTGUARD_MAGIC;\n    seal(st);\n}", "    seal(st);\n}", "init forgets the magic"),
 # threshold -> fallback
 ("if (st->failed_boots >= NW_BOOTGUARD_MAX_FAILED_BOOTS) {", "if (st->failed_boots > NW_BOOTGUARD_MAX_FAILED_BOOTS) {", "threshold off by one (one retry too many)"),
 ("if (st->failed_boots >= NW_BOOTGUARD_MAX_FAILED_BOOTS) {", "if (st->failed_boots + 1u >= NW_BOOTGUARD_MAX_FAILED_BOOTS) {", "threshold off by one (one retry too few)"),
 ("        st->in_fallback = 1;\n        seal(st);\n        return out_of(NW_BG_FALLBACK, NW_BG_WHY_COUNT, st->failed_boots);", "        seal(st);\n        return out_of(NW_BG_FALLBACK, NW_BG_WHY_COUNT, st->failed_boots);", "fallback does not mark the probation boot"),
 ("        return out_of(NW_BG_FALLBACK, NW_BG_WHY_COUNT, st->failed_boots);", "        return out_of(NW_BG_FALLBACK, NW_BG_WHY_NONE, st->failed_boots);", "fallback reason lost"),
 # fallback does not retry radios, sleeps long
 ("o.allow_ble = (a == NW_BG_RUN);", "o.allow_ble = (a != NW_BG_ROLLBACK);", "fallback leaves BLE allowed"),
 ("o.allow_wifi = (a == NW_BG_RUN);", "o.allow_wifi = (a != NW_BG_ROLLBACK);", "fallback leaves Wi-Fi allowed"),
 ("o.allow_ble = (a == NW_BG_RUN);", "o.allow_ble = (a != NW_BG_FALLBACK);", "rollback allows BLE"),
 ("o.allow_wifi = (a == NW_BG_RUN);", "o.allow_wifi = (a != NW_BG_FALLBACK);", "rollback allows Wi-Fi"),
 ("o.allow_wifi = (a == NW_BG_RUN);", "o.allow_wifi = false;", "a normal boot may not use Wi-Fi"),
 ("o.sleep_s = (a == NW_BG_FALLBACK) ? NW_BOOTGUARD_FALLBACK_SLEEP_S : 0;", "o.sleep_s = 0;", "fallback has no long sleep"),
 ("o.sleep_s = (a == NW_BG_FALLBACK) ? NW_BOOTGUARD_FALLBACK_SLEEP_S : 0;", "o.sleep_s = (a != NW_BG_RUN) ? NW_BOOTGUARD_FALLBACK_SLEEP_S : 0;", "rollback also sleeps"),
 ("o.sleep_s = (a == NW_BG_FALLBACK) ? NW_BOOTGUARD_FALLBACK_SLEEP_S : 0;", "o.sleep_s = (a == NW_BG_FALLBACK) ? 900u : 0;", "fallback sleeps only one sample period"),
 # probation
 ("    if (st->in_fallback) {                            /* probation: the long sleep is over, one more normal attempt */\n        st->in_fallback = 0;\n        st->failed_boots = (uint8_t)(NW_BOOTGUARD_MAX_FAILED_BOOTS - 1u);\n    }", "", "no probation: a fallback never ends"),
 ("st->failed_boots = (uint8_t)(NW_BOOTGUARD_MAX_FAILED_BOOTS - 1u);", "st->failed_boots = 0;", "probation grants a full new budget (endless retries)"),
 ("st->failed_boots = (uint8_t)(NW_BOOTGUARD_MAX_FAILED_BOOTS - 1u);", "st->failed_boots = (uint8_t)(NW_BOOTGUARD_MAX_FAILED_BOOTS - 2u);", "probation grants two attempts"),
 # rollback when not confirmed (builds on nw_ota_boot_decide)
 ("        if (pending) {                                 /* the new image is the suspect: back to the previous slot (FR-D05) */\n            uint8_t seen = st->failed_boots;\n            nw_bootguard_init(st);\n            return out_of(NW_BG_ROLLBACK, NW_BG_WHY_OTA_LOOP, seen);\n        }\n", "", "looping unconfirmed image sleeps instead of rolling back"),
 ("    if (pending && nw_ota_boot_decide(ota) == NW_OTA_ROLLBACK) {", "    if (0 && pending && nw_ota_boot_decide(ota) == NW_OTA_ROLLBACK) {", "OTA window ignored"),
 ("    if (pending && nw_ota_boot_decide(ota) == NW_OTA_ROLLBACK) {", "    if (nw_ota_boot_decide(ota) == NW_OTA_ROLLBACK) {", "OTA window applied without the pending check (NULL deref)"),
 ("    bool pending = ota && ota->pending_verify;", "    bool pending = ota != NULL;", "any OTA state counts as pending"),
 ("        if (pending) {                                 /* the new image is the suspect: back to the previous slot (FR-D05) */\n            uint8_t seen = st->failed_boots;\n            nw_bootguard_init(st);", "        if (pending) {                                 /* the new image is the suspect: back to the previous slot (FR-D05) */\n            uint8_t seen = st->failed_boots;\n            st->in_fallback = 0;", "rollback keeps the failed count"),
 ("    if (pending && nw_ota_boot_decide(ota) == NW_OTA_ROLLBACK) {   /* the 4.F4 window rule, not repeated here */\n        uint8_t seen = st->failed_boots;\n        nw_bootguard_init(st);", "    if (pending && nw_ota_boot_decide(ota) == NW_OTA_ROLLBACK) {   /* the 4.F4 window rule, not repeated here */\n        uint8_t seen = st->failed_boots;", "window rollback keeps the failed count"),
 # corrupted counter fails safe
 ("        return out_of(NW_BG_FALLBACK, NW_BG_WHY_CORRUPT, st->failed_boots);", "        return out_of(NW_BG_RUN, NW_BG_WHY_CORRUPT, st->failed_boots);", "corrupt state runs normally"),
 ("        st->failed_boots = NW_BOOTGUARD_MAX_FAILED_BOOTS;\n        st->in_fallback = 1;\n        seal(st);\n        return", "        seal(st);\n        return", "corrupt state re-sealed without probation flag"),
 ("    } else if (!nw_bootguard_valid(st)) {", "    } else if (0) {", "corruption never detected (valid() unused)"),
 ("    if (st->failed_boots > NW_BOOTGUARD_MAX_FAILED_BOOTS) return false;", "", "range check on the count removed"),
 ("    if (st->in_fallback > 1) return false;", "", "range check on the fallback flag removed"),
 ("    if (st->reserved != 0) return false;", "", "reserved field not checked"),
 ("    return st->check == bg_check(st);", "    return true;", "check word not compared"),
 ("    uint32_t v = ((uint32_t)st->failed_boots) | ((uint32_t)st->in_fallback << 8) | ((uint32_t)st->reserved << 16);", "    uint32_t v = ((uint32_t)st->in_fallback << 8) | ((uint32_t)st->reserved << 16);", "check ignores the count"),
 ("    uint32_t v = ((uint32_t)st->failed_boots) | ((uint32_t)st->in_fallback << 8) | ((uint32_t)st->reserved << 16);", "    uint32_t v = ((uint32_t)st->failed_boots) | ((uint32_t)st->reserved << 16);", "check ignores the fallback flag"),
 ("    if (st->magic != NW_BOOTGUARD_MAGIC) return false;", "", "magic not checked in valid()"),
 # reset reason (magic mismatch is power-on only with a power-on reset)
 ("if (st->magic != NW_BOOTGUARD_MAGIC && reset == NW_BG_RESET_POWERON) {", "(void)reset;\n    if (st->magic != NW_BOOTGUARD_MAGIC) {", "magic mismatch always treated as power-on (reset reason ignored)"),
 ("if (st->magic != NW_BOOTGUARD_MAGIC && reset == NW_BG_RESET_POWERON) {", "if (st->magic != NW_BOOTGUARD_MAGIC && reset != NW_BG_RESET_OTHER) {", "unknown reset reason accepted as power-on"),
 ("if (st->magic != NW_BOOTGUARD_MAGIC && reset == NW_BG_RESET_POWERON) {", "(void)reset;\n    if (0) {", "power-on reset never accepted (new unit sleeps 6 h)"),
 ("uint8_t seen = st->failed_boots;\n            nw_bootguard_init(st);\n            return out_of(NW_BG_ROLLBACK, NW_BG_WHY_OTA_LOOP, seen);", "nw_bootguard_init(st);\n            return out_of(NW_BG_ROLLBACK, NW_BG_WHY_OTA_LOOP, st->failed_boots);", "loop rollback log shows the cleared count"),
 ("uint8_t seen = st->failed_boots;\n        nw_bootguard_init(st);\n        return out_of(NW_BG_ROLLBACK, NW_BG_WHY_OTA_WINDOW, seen);", "nw_bootguard_init(st);\n        return out_of(NW_BG_ROLLBACK, NW_BG_WHY_OTA_WINDOW, st->failed_boots);", "window rollback log shows the cleared count"),
 ("(unsigned)out->failed,", "(unsigned)0,", "log line hides the failed count"),
 # rollback failed (adapter rule b)
 ("    st->failed_boots = NW_BOOTGUARD_MAX_FAILED_BOOTS;\n    st->in_fallback = 1;\n    seal(st);\n    return out_of(NW_BG_FALLBACK, NW_BG_WHY_ROLLBACK_FAILED, st->failed_boots);", "    seal(st);\n    return out_of(NW_BG_FALLBACK, NW_BG_WHY_ROLLBACK_FAILED, st->failed_boots);", "failed rollback leaves a cleared counter (no probation, looping image retries at once)"),
 ("    return out_of(NW_BG_FALLBACK, NW_BG_WHY_ROLLBACK_FAILED, st->failed_boots);", "    return out_of(NW_BG_RUN, NW_BG_WHY_ROLLBACK_FAILED, st->failed_boots);", "failed rollback answers RUN"),
 ("    return out_of(NW_BG_FALLBACK, NW_BG_WHY_ROLLBACK_FAILED, st->failed_boots);", "    return out_of(NW_BG_FALLBACK, NW_BG_WHY_COUNT, st->failed_boots);", "failed rollback reason lost"),
 ("    st->in_fallback = 1;\n    seal(st);\n    return out_of(NW_BG_FALLBACK, NW_BG_WHY_ROLLBACK_FAILED", "    st->in_fallback = 1;\n    return out_of(NW_BG_FALLBACK, NW_BG_WHY_ROLLBACK_FAILED", "failed rollback state not re-sealed"),
 ("\"ota_loop\", \"ota_window\", \"rollback_failed\" };", "\"ota_loop\", \"ota_window\", \"rollback\" };", "rollback_failed log text wrong"),
 # one log line
 ("    if (out->action == NW_BG_RUN) return 0;", "", "a normal boot logs a fallback line"),
 ("\"NWBOOTGUARD %s why=%s failed=%u limit=%u sleep_s=%u ble=off wifi=off\"", "\"NWBOOTGUARD %s why=%s failed=%u limit=%u sleep_s=%u ble=off wifi=off\\n\"", "log line ends with a newline (two lines)"),
 ("ble=off wifi=off\"", "ble=off\"", "log line does not say Wi-Fi is off"),
 ("    return (size_t)n < cap ? (size_t)n : cap - 1;", "    return (size_t)n;", "log length not clamped to the buffer"),
]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


bad = 0
survived = 0
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)

    def build_and_run(src_text, tag):
        """Returns 'pass' / 'fail' / 'compile' for test_bootguard built against the given nw_bootguard.c text."""
        d = td / tag
        d.mkdir()
        (d / "nw_bootguard.c").write_text(src_text)
        exe = d / "t"
        inc = []
        for i in INCS:
            inc += ["-I", str(i)]
        c = run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", *inc, "-I", str(here),
                 str(here / "test_bootguard.c"), str(d / "nw_bootguard.c"), str(OTA_SRC), "-o", str(exe)])
        if c.returncode != 0:
            return "compile", c.stderr[-400:]
        r = run([str(exe)], timeout=60)
        return ("pass" if r.returncode == 0 else "fail"), r.stdout[-300:]

    original = SRC.read_text()
    verdict, out = build_and_run(original, "baseline")
    if verdict != "pass":
        print(f"BASELINE {verdict}: the unmutated nw_bootguard.c does not pass test_bootguard\n{out}")
        sys.exit(1)
    print(f"baseline: test_bootguard passes ({out.strip().splitlines()[-1]})")

    for i, (old, new, what) in enumerate(M):
        n = original.count(old)
        if n != 1:
            print(f"BAD      #{i:02d} {what}: pattern found {n}x (expected 1)")
            bad += 1
            continue
        try:
            verdict, out = build_and_run(original.replace(old, new), f"m{i:02d}")
        except subprocess.TimeoutExpired:
            verdict, out = "fail", "timeout"
        if verdict == "fail":
            print(f"KILLED   #{i:02d} {what}")
        elif verdict == "pass":
            print(f"SURVIVED #{i:02d} {what}")
            survived += 1
        else:
            print(f"BAD      #{i:02d} {what}: does not compile: {out.strip()}")
            bad += 1

    verdict, _ = build_and_run(SRC.read_text(), "restored")
    print(f"restored: {verdict}")
    if verdict != "pass":
        bad += 1

total = len(M)
killed = total - survived - bad
print(f"mutants: {total}, killed {killed}, survived {survived}, bad {bad}")
sys.exit(0 if (survived == 0 and bad == 0) else 1)

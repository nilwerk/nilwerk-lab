#!/usr/bin/env python3
"""Mutation check for the pure helpers of the boot-loop guard adapter (task 4.F7b): reset-reason mapping and sleep-path table.
Each mutant changes one rule in components/bootguard/src/nw_bootguard_map.c (on a temp copy) and must make test_bootguard_map fail.
Usage: mutate_bootguard_map.py [cc]. Exit 0 only when the baseline passes and every mutant is killed."""
import pathlib, subprocess, sys, tempfile

cc = sys.argv[1] if len(sys.argv) > 1 else "cc"
here = pathlib.Path(__file__).resolve().parent
fw = here.parents[1] / "components"
SRC = fw / "bootguard" / "src" / "nw_bootguard_map.c"
INCS = [fw / d / "include" for d in ("bootguard", "ota")]

M = [  # (old, new, what)
 ("return idf_reason == NW_BG_IDF_RST_POWERON ? NW_BG_RESET_POWERON : NW_BG_RESET_OTHER;", "(void)idf_reason; return NW_BG_RESET_OTHER;", "power-on never recognised (a new unit would sleep 6 h)"),
 ("return idf_reason == NW_BG_IDF_RST_POWERON ? NW_BG_RESET_POWERON : NW_BG_RESET_OTHER;", "(void)idf_reason; return NW_BG_RESET_POWERON;", "every reset reason treated as power-on (a looping unit hides behind a wiped magic)"),
 ("return idf_reason == NW_BG_IDF_RST_POWERON ? NW_BG_RESET_POWERON : NW_BG_RESET_OTHER;", "return idf_reason != 0 ? NW_BG_RESET_POWERON : NW_BG_RESET_OTHER;", "only UNKNOWN maps to the fail-safe value"),
 ("return idf_reason == NW_BG_IDF_RST_POWERON ? NW_BG_RESET_POWERON : NW_BG_RESET_OTHER;", "return (idf_reason & 0xff) == NW_BG_IDF_RST_POWERON ? NW_BG_RESET_POWERON : NW_BG_RESET_OTHER;", "reset reason truncated to a byte"),
 ("return idf_reason == NW_BG_IDF_RST_POWERON ? NW_BG_RESET_POWERON : NW_BG_RESET_OTHER;", "return idf_reason <= NW_BG_IDF_RST_POWERON ? NW_BG_RESET_POWERON : NW_BG_RESET_OTHER;", "UNKNOWN counted as power-on"),
 ("    case NW_BG_PATH_NORMAL_END:\n", "", "normal end does not confirm"),
 ("    case NW_BG_PATH_LOW_BATTERY_SKIP:\n", "", "low-battery skip does not confirm (adapter rule a)"),
 ("    case NW_BG_PATH_BLE_SETUP_TIMEOUT:\n", "", "BLE setup timeout does not confirm (adapter rule a)"),
 ("    case NW_BG_PATH_BEFORE_OTA_REBOOT:\n", "", "OTA reboot does not confirm (adapter rule a)"),
 ("    case NW_BG_PATH_RESET_BUTTON:\n", "    case NW_BG_PATH_RESET_BUTTON:\n        return true;\n", "reset button confirms"),
 ("    case NW_BG_PATH_TOKEN_REVOKED_RESTART:\n", "    case NW_BG_PATH_TOKEN_REVOKED_RESTART:\n        return true;\n", "revoked-token restart confirms"),
 ("    case NW_BG_PATH_FALLBACK_SLEEP:\n", "    case NW_BG_PATH_FALLBACK_SLEEP:\n        return true;\n", "fallback sleep confirms (probation lost)"),
 ("    case NW_BG_PATH_ROLLBACK_FAILED_SLEEP:\n", "    case NW_BG_PATH_ROLLBACK_FAILED_SLEEP:\n        return true;\n", "sleep after a failed rollback confirms"),
 ("    case NW_BG_PATH_COUNT:\n    default:\n        return false;", "    case NW_BG_PATH_COUNT:\n    default:\n        return true;", "unknown path confirms (not fail safe)"),
]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


bad = 0
survived = 0
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)

    def build_and_run(src_text, tag):
        """Returns 'pass' / 'fail' / 'compile' for test_bootguard_map built against the given nw_bootguard_map.c text."""
        d = td / tag
        d.mkdir()
        (d / "nw_bootguard_map.c").write_text(src_text)
        exe = d / "t"
        inc = []
        for i in INCS:
            inc += ["-I", str(i)]
        c = run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", *inc, "-I", str(here),
                 str(here / "test_bootguard_map.c"), str(d / "nw_bootguard_map.c"), "-o", str(exe)])
        if c.returncode != 0:
            return "compile", c.stderr[-400:]
        r = run([str(exe)], timeout=60)
        return ("pass" if r.returncode == 0 else "fail"), r.stdout[-300:]

    original = SRC.read_text()
    verdict, out = build_and_run(original, "baseline")
    if verdict != "pass":
        print(f"BASELINE {verdict}: the unmutated nw_bootguard_map.c does not pass test_bootguard_map\n{out}")
        sys.exit(1)
    print(f"baseline: test_bootguard_map passes ({out.strip().splitlines()[-1]})")

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

#!/usr/bin/env python3
"""Mutation check for the OTA image check and rollback decision (task 4.F4, FR-D05, ADR-009).

Each mutant changes one rule in components/ota/src/nw_ota.c (on a temp copy, the source is never edited) and must make
test_ota fail. A surviving mutant means a rule has no test. A mutant that does not apply or does not compile is BAD.
Usage: mutate_ota.py [cc]. Exit 0 only when the baseline passes and every mutant is killed."""
import pathlib, subprocess, sys, tempfile

cc = sys.argv[1] if len(sys.argv) > 1 else "cc"
here = pathlib.Path(__file__).resolve().parent
comp = here.parents[1] / "components" / "ota"
SRC = comp / "src" / "nw_ota.c"
INC = comp / "include"

M = [  # (old, new, what)
 # hash check (AC 1)
 ("i < NW_OTA_SHA256_LEN; i++) {\n        diff |=", "i < 1; i++) {\n        diff |=", "hash compare looks at the first byte only"),
 ("i < NW_OTA_SHA256_LEN; i++) {\n        diff |=", "i < NW_OTA_SHA256_LEN - 1; i++) {\n        diff |=", "hash compare skips the last byte"),
 ("return diff == 0;", "return true;", "digest compare always matches"),
 ("return nw_ota_digest_equal(digest, expected);", "(void)digest; return expected != NULL;", "image check ignores the computed hash"),
 ("if (!hex || len != NW_OTA_SHA256_HEX_LEN) return false;", "if (!hex || len < NW_OTA_SHA256_HEX_LEN) return false;", "manifest hash: longer strings accepted"),
 ("if (hi < 0 || lo < 0) return false;", "if (hi < 0 && lo < 0) return false;", "manifest hash: non-hex digit accepted"),
 ("size_t total = (n < 56) ? 64 : 128;", "size_t total = (n < 55) ? 64 : 128;", "SHA-256 padding boundary (55-byte message)"),
 ("0x428a2f98, 0x71374491", "0x428a2f99, 0x71374491", "SHA-256 round constant K[0]"),
 # rollback decision (AC 2)
 ("if (b->unconfirmed_boots >= b->max_unconfirmed_boots) return NW_OTA_ROLLBACK;", "if (b->unconfirmed_boots > b->max_unconfirmed_boots) return NW_OTA_ROLLBACK;", "window boundary off by one (rolls back one boot late)"),
 ("if (b->ingest_ok) return NW_OTA_CONFIRM;", "if (0) return NW_OTA_CONFIRM;", "successful ingest does not confirm"),
 ("if (!b->pending_verify) return NW_OTA_KEEP;", "if (0) return NW_OTA_KEEP;", "non-pending image is treated as pending"),
 ("if (b->ingest_ok) return NW_OTA_CONFIRM;\n    if (b->unconfirmed_boots >= b->max_unconfirmed_boots) return NW_OTA_ROLLBACK;",
  "if (b->unconfirmed_boots >= b->max_unconfirmed_boots) return NW_OTA_ROLLBACK;\n    if (b->ingest_ok) return NW_OTA_CONFIRM;",
  "window check before confirm: a late ingest is rolled back"),
]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


bad = 0
survived = 0
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    def build_and_run(src_text, tag):
        """Returns 'pass' / 'fail' / 'compile' for test_ota built against the given nw_ota.c text."""
        d = td / tag
        d.mkdir()
        (d / "nw_ota.c").write_text(src_text)
        exe = d / "t"
        c = run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(INC), "-I", str(here),
                 str(here / "test_ota.c"), str(d / "nw_ota.c"), "-o", str(exe)])
        if c.returncode != 0:
            return "compile", c.stderr[-400:]
        r = run([str(exe)])
        return ("pass" if r.returncode == 0 else "fail"), r.stdout[-300:]

    original = SRC.read_text()
    verdict, out = build_and_run(original, "baseline")
    if verdict != "pass":
        print(f"BASELINE {verdict}: the unmutated nw_ota.c does not pass test_ota\n{out}")
        sys.exit(1)
    print(f"baseline: test_ota passes ({out.strip().splitlines()[-1]})")

    for i, (old, new, what) in enumerate(M):
        n = original.count(old)
        if n != 1:
            print(f"BAD      #{i:02d} {what}: pattern found {n}x (expected 1)")
            bad += 1
            continue
        verdict, out = build_and_run(original.replace(old, new), f"m{i:02d}")
        if verdict == "fail":
            print(f"KILLED   #{i:02d} {what}")
        elif verdict == "pass":
            print(f"SURVIVED #{i:02d} {what}")
            survived += 1
        else:
            print(f"BAD      #{i:02d} {what}: does not compile: {out.strip()}")
            bad += 1

    # the restored source must pass again (the mutants never touched the repo copy)
    verdict, _ = build_and_run(SRC.read_text(), "restored")
    print(f"restored: {verdict}")
    if verdict != "pass":
        bad += 1

total = len(M)
killed = total - survived - bad
print(f"mutants: {total}, killed {killed}, survived {survived}, bad {bad}")
sys.exit(0 if (survived == 0 and bad == 0) else 1)

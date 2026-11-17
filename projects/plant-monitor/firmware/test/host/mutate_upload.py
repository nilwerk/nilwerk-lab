#!/usr/bin/env python3
"""Mutation check for the upload logic (task 4.F3 slice 2). Each mutant changes one rule in nw_upload.c/.h; test_upload must fail.
Usage: mutate_upload.py <cc>. A surviving mutant means a rule has no test."""
import pathlib, shutil, subprocess, sys, tempfile

cc = sys.argv[1] if len(sys.argv) > 1 else "cc"
here = pathlib.Path(__file__).resolve().parent
comp = here.parent.parent / "components"
SRC = [comp / "storage/src/nw_sample_ring.c", comp / "report/src/nw_report.c", comp / "power/src/nw_sleep.c", comp / "upload/src/nw_upload.c"]

M = [  # (file, old, new, what)
 ("nw_upload.c", 'memcmp(base, scheme, sl) != 0', 'memcmp(base, "http", 4) != 0', "TLS-only URL (https)"),
 ("nw_upload.c", "if (base[n - 1] == '/') return -1;", "", "trailing slash rejected"),
 ("nw_upload.c", "c <= ' ' || c == 0x7f || c == '?' || c == '#'", "c < ' ' || c == 0x7f || c == '?' || c == '#'", "space in URL rejected"),
 ("nw_upload.c", "c == 0x7f || c == '?' || c == '#'", "c == 0x7f || c == '#'", "query in URL rejected"),
 ("nw_upload.c", "n + pl + 1 > cap ||", "n + pl > cap ||", "URL capacity includes NUL"),
 ("nw_upload.c", "cap < NW_UPLOAD_AUTH_MAX", "cap < NW_UPLOAD_AUTH_MAX - 1", "auth capacity includes NUL"),
 ("nw_upload.c", "(c >= 'a' && c <= 'f'))) return -1;", "(c >= 'a' && c <= 'z'))) return -1;", "token hex charset"),
 ("nw_upload.c", "if (token[NW_UPLOAD_TOKEN_HEX] != 0) return -1;", "", "long token rejected"),
 ("nw_upload.c", 'memcpy(out, "Bearer ", 7);', 'memcpy(out, "Bearer:", 7);', "Bearer scheme"),
 ("nw_upload.c", "vbat_mv >= 0 && vbat_mv <= NW_VBAT_WIFI_CUTOFF_MV", "vbat_mv >= 0 && vbat_mv < NW_VBAT_WIFI_CUTOFF_MV", "cutoff inclusive (<=)"),
 ("nw_upload.c", "vbat_mv >= 0 && vbat_mv <= NW_VBAT_WIFI_CUTOFF_MV", "vbat_mv > 0 && vbat_mv <= NW_VBAT_WIFI_CUTOFF_MV", "vbat 0 blocked"),
 ("nw_upload.c", "if (now < s->next_attempt_unix) return", "if (now <= s->next_attempt_unix) return", "backoff boundary"),
 ("nw_upload.c", "now - t < NW_UPLOAD_RATE_WINDOW_S", "now - t <= NW_UPLOAD_RATE_WINDOW_S", "rate window boundary"),
 ("nw_upload.c", "(now < t || now - t", "(now - t", "clock moved back stays conservative"),
 ("nw_upload.c", "recent >= NW_UPLOAD_MAX_PER_HOUR", "recent > NW_UPLOAD_MAX_PER_HOUR", "rate limit count"),
 ("nw_upload.c", "s->att_head = (uint8_t)((s->att_head + 1) % NW_UPLOAD_MAX_PER_HOUR);", "s->att_head = 0;", "attempt ring advances"),
 ("nw_upload.c", "for (uint8_t i = 1; i < fails && b < NW_UPLOAD_BACKOFF_MAX_S; i++) b *= 2;", "for (uint8_t i = 1; i < fails && b < NW_UPLOAD_BACKOFF_MAX_S; i++) b += 900;", "exponential backoff"),
 ("nw_upload.c", "if (low_battery && b < NW_UPLOAD_LOWBAT_BACKOFF_S) b = NW_UPLOAD_LOWBAT_BACKOFF_S;", "if (low_battery && b < 1) b = 1;", "low-battery backoff floor"),
 ("nw_upload.c", "if (s->fails < 255) s->fails++;", "s->fails++;", "fails saturates"),
 ("nw_upload.c", "if (wait_s > NW_UPLOAD_RETRY_AFTER_MAX_S) wait_s = NW_UPLOAD_RETRY_AFTER_MAX_S;", "", "Retry-After clamp"),
 ("nw_upload.c", "if (wait_s > w) w = wait_s;", "w = wait_s ? wait_s : w;", "Retry-After never below backoff"),
 ("nw_upload.c", "if (st == 429 && resp->retry_after_s > 0)", "if (resp->retry_after_s > 0)", "Retry-After only on 429"),
 ("nw_upload.c", "t < NW_TS_MIN || t > UINT32_MAX", "t > UINT32_MAX", "server_time floor"),
 ("nw_upload.c", "if (!v || vl == 0 || vl > 10) return false;", "if (!v) return false;", "server_time digits bound"),
 ("nw_upload.c", "if (parse_server_time(resp->body, resp->body_len, &t)) {", "if (parse_server_time(resp->body, resp->body_len, &t) || st == 200) {", "ack needs server_time"),
 ("nw_upload.c", "r.drained = nw_ring_consume_upto(rg, last_seq);    /* seq based", "r.drained = 0;    /* seq based", "ack drains the ring"),
 ("nw_upload.c", "r.drained = nw_ring_consume_upto(rg, last_seq);    /* seq based", "r.drained = nw_ring_consume_upto(rg, UINT32_MAX);    /* seq based", "ack drains only the batch"),
 ("nw_upload.c", "r.server_time = t; r.server_time_valid = true;\n            r.outage_pending = false;", "r.server_time = t; r.server_time_valid = true;\n            r.outage_pending = true;", "ack clears outage"),
 ("nw_upload.c", "s->fails = 0; s->rejects = 0; s->reject_seq = 0; s->next_attempt_unix = 0;", "s->rejects = 0; s->reject_seq = 0; s->next_attempt_unix = 0;", "ack resets fails"),
 ("nw_upload.c", "s->fails = 0; s->rejects = 0; s->reject_seq = 0; s->next_attempt_unix = 0;", "s->fails = 0; s->reject_seq = 0; s->next_attempt_unix = 0;", "ack resets rejects"),
 ("nw_upload.c", "if (st == 400 || st == 413)", "if (st == 400)", "413 is a reject"),
 ("nw_upload.c", "s->rejects >= NW_UPLOAD_POISON_MAX", "s->rejects > NW_UPLOAD_POISON_MAX", "poison guard threshold"),
 ("nw_upload.c", "s->reject_seq == first_seq) {", "1) {", "poison counter is per batch"),
 ("nw_upload.c", "s->reject_seq == first_seq) {", "s->reject_seq == last_seq) {", "poison counter keyed on FIRST seq (C1: new sample each 900 s)"),
 ("nw_upload.c", "else { s->rejects = 1; s->reject_seq = first_seq; }", "else { s->rejects = 1; s->reject_seq = last_seq; }", "poison counter stores first seq"),
 ("nw_upload.c", "r.payload_too_large = (st == 413);", "r.payload_too_large = false;", "413 flagged distinctly (C3)"),
 ("nw_upload.c", "r.payload_too_large = (st == 413);", "r.payload_too_large = (st == 413 || st == 400);", "400 not flagged as too large"),
 ("nw_upload.c", "r.batch_dropped = true;", "r.batch_dropped = false;", "poison drop flagged"),
 ("nw_upload.c", 'error_is(resp->body, resp->body_len, "token_revoked")', 'error_is(resp->body, resp->body_len, "token_invalid")', "revoked code"),
 ("nw_upload.c", "return v && vl == strlen(code) && memcmp(v, code, vl) == 0;", "return v && memcmp(v, code, strlen(code)) == 0;", "error code compared exactly"),
 ("nw_upload.c", "r.drained = nw_ring_consume_upto(rg, UINT32_MAX);   /* the data", "r.drained = 0;   /* the data", "revoke discards the buffer"),
 ("nw_upload.c", "r.reenter_setup = true;", "r.reenter_setup = false;", "revoke re-enters setup"),
 ("nw_upload.c", "nw_upload_state_init(s);\n            r = result(s, NW_UP_REVOKED);", "r = result(s, NW_UP_REVOKED);", "revoke resets state"),
 ("nw_upload.c", "        fail(s, now, 0, low_battery);\n        return result(s, NW_UP_AUTH_FAILED);", "        return result(s, NW_UP_AUTH_FAILED);", "auth failure backs off"),
 ("nw_upload.c", "    record_attempt(s, now);", "    (void)record_attempt;", "attempt recorded"),
 ("nw_upload.c", "if (g != NW_UP_GATE_OK) {", "if (0) {", "gate stops the radio"),
 ("nw_upload.c", "if (len == 0) {", "if (len == 1) {", "empty payload not sent"),
 ("nw_upload.c", "if (rc < 0) { r = nw_upload_on_transport_error", "if (rc < -9) { r = nw_upload_on_transport_error", "transport error is a failure"),
 ("nw_upload.c", "if (!resp) return nw_upload_on_transport_error(s, now, low_battery);", "", "NULL response safe"),
]

with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    def fresh():
        w = td / "w"
        if w.exists(): shutil.rmtree(w)
        for name in ("storage", "report", "power", "upload"):
            shutil.copytree(comp / name, w / name)
        return w
    def build(w):
        exe = w / "t"
        cmd = [cc, "-std=c11", "-Wall", "-Wextra", "-Werror"] + sum((["-I", str(w / d / "include")] for d in ("storage", "report", "power", "upload")), []) + \
              ["-I", str(here), str(here / "test_upload.c")] + [str(w / p.parent.parent.name / "src" / p.name) for p in SRC] + ["-o", str(exe)]
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

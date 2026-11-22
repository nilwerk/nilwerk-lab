#!/usr/bin/env python3
"""Mutation check for the provisioning logic (task 4.F2): each mutant must make test_prov fail.
Usage: mutate_prov.py [cc]. Works on a temp copy, never edits the sources. Exit 1 when a mutant survives or does not compile."""
import pathlib, shutil, subprocess, sys, tempfile

here = pathlib.Path(__file__).resolve().parent
prov = here.parent.parent / "components" / "provisioning"
cc = sys.argv[1] if len(sys.argv) > 1 else "cc"

M = [
 ("nw_prov.h", "MAX_FAILED_HANDSHAKES 5", "MAX_FAILED_HANDSHAKES 6", "guess limit 5"),
 ("nw_prov.h", "(5u * 60u * 1000u)", "(6u * 60u * 1000u)", "5 minute window"),
 ("nw_prov.h", "BUTTON_RESET_MS 10000u", "BUTTON_RESET_MS 2000u", "reset hold time"),
 ("nw_prov_proto.h", "NW_PROV_NAME_MAX_CHARS 80", "NW_PROV_NAME_MAX_CHARS 81", "name max 80"),
 ("nw_prov_proto.h", "NW_PROV_NAME_MIN_CHARS 1 ", "NW_PROV_NAME_MIN_CHARS 0 ", "name min 1"),
 ("nw_prov_proto.h", "NW_PROV_CLAIM_TOKEN_LEN 22", "NW_PROV_CLAIM_TOKEN_LEN 23", "token length"),
 ("nw_prov_proto.h", "NW_PROV_PASS_MIN 8", "NW_PROV_PASS_MIN 7", "passphrase min"),
 ("nw_prov_proto.h", "NW_PROV_PASS_MAX 63", "NW_PROV_PASS_MAX 64", "passphrase max"),
 ("nw_prov_proto.h", "NW_PROV_SSID_MAX_BYTES 32", "NW_PROV_SSID_MAX_BYTES 33", "ssid max"),
 ("nw_prov_proto.h", "NW_PROV_REQ_MAX_BYTES 2048", "NW_PROV_REQ_MAX_BYTES 4096", "2 KiB request limit"),
 ("nw_prov_proto.c", "*c == '-' || *c == '_'", "*c == '-' || *c == '+'", "base64url alphabet"),
 ("nw_prov_proto.c", "if (cp == 0) return -1;", "", "reject \\u0000"),
 ("nw_prov_proto.c", "cp >= 0xD800 && cp <= 0xDFFF", "cp >= 0xD800 && cp <= 0xDFFE", "surrogate range in UTF-8 check"),
 ("nw_prov_proto.c", "if ((extra == 1 && cp < 0x80)", "if ((extra == 9 && cp < 0x80)", "overlong 2-byte"),
 ("nw_prov_proto.c", "if (c.p != c.end) return NW_PROV_ERR_BAD_REQUEST;", "", "trailing garbage"),
 ("nw_prov_proto.c", "if (have_v || c.end - c.p < 1 || *c.p != '1')", "if (have_v || c.end - c.p < 1)", "protocol version check"),
 ("nw_prov_proto.c", "if (have_name || parse_string", "if (parse_string", "duplicate name key"),
 ("nw_prov_proto.c", "\\\"error\\\":\\\"bad_request\\\"", "\\\"error\\\":\\\"bad_req\\\"", "error string"),
 ("nw_prov_proto.c", 'return "claim_failed"', 'return "claim_fail"', "state string"),
 ("nw_prov_proto.c", 'return "no_ap"', 'return "noap"', "reason string"),
 ("nw_prov_proto.c", "memcpy(out + 3, hw_id + NW_PROV_HWID_LEN - 6, 6);", "memcpy(out + 3, hw_id + 3, 6);", "advertised name = last 6 hex"),
 ("nw_prov.c", "    p->state = NW_PROV_S_ADVERTISING;\n    ble(p, true);", "    p->state = NW_PROV_S_ADVERTISING;", "BLE on in setup"),
 ("nw_prov.c", "    p->state = to;\n    ble(p, false);", "    p->state = to;", "BLE off when setup ends (FR-D09)"),
 ("nw_prov.c", "if (r == 1 || button_held_ms >= NW_PROV_BUTTON_SETUP_MS)", "if (button_held_ms >= NW_PROV_BUTTON_SETUP_MS)", "first boot enters setup"),
 ("nw_prov.c", "if (p->ops.store.erase(p->ops.store_ctx) != 0) return NW_PROV_ERR_STORE;", "p->ops.store.erase(p->ops.store_ctx);", "erase failure at boot"),
 ("nw_prov.c", "if (r < 0) return NW_PROV_ERR_STORE;", "", "load error at boot"),
 ("nw_prov.c", "if (in_flight(p) || held_ms < NW_PROV_BUTTON_SETUP_MS) return;", "if (held_ms < NW_PROV_BUTTON_SETUP_MS) return;", "button during claim"),
 ("nw_prov.c", "if (++p->failed_handshakes >= NW_PROV_MAX_FAILED_HANDSHAKES)", "if (++p->failed_handshakes > NW_PROV_MAX_FAILED_HANDSHAKES)", "off-by-one guess limit"),
 ("nw_prov.c", "    p->failed_handshakes = 0;\n    p->st", "    p->st", "button resets guess counter"),
 ("nw_prov.c", "if (ok) { p->state = NW_PROV_S_SESSION; return NW_PROV_OK; }", "if (ok) { p->state = NW_PROV_S_SESSION; p->failed_handshakes = 0; return NW_PROV_OK; }", "good handshake must not reset counter"),
 ("nw_prov.c", "    else p->state = NW_PROV_S_ADVERTISING;                   /* a failed", "    else p->state = NW_PROV_S_SESSION;                   /* a failed", "failed handshake drops session"),
 ("nw_prov.c", "if (p->state != NW_PROV_S_SESSION || !p->have_wifi || !p->have_claim)", "if (p->state != NW_PROV_S_SESSION || !p->have_wifi)", "apply needs claim"),
 ("nw_prov.c", "if (!nw_prov_valid_ssid(ssid) || !nw_prov_valid_passphrase(passphrase)) return NW_PROV_ERR_BAD_REQUEST;", "", "wifi validation"),
 ("nw_prov.c", "(uint32_t)(now_ms - p->setup_started_ms) >= window", "now_ms - p->setup_started_ms > window", "deadline boundary"),
 ("nw_prov.c", "if ((p->state == NW_PROV_S_ADVERTISING || p->state == NW_PROV_S_SESSION) &&", "if ((p->state == NW_PROV_S_ADVERTISING || p->state == NW_PROV_S_SESSION || in_flight(p)) &&", "no timeout while in flight"),
 ("nw_prov.c", "    p->have_wifi = false;\n    wipe(p->pending.ssid", "    wipe(p->pending.ssid", "wifi retry needs new config"),
 ("nw_prov.c", "    wipe(p->pending.passphrase, sizeof p->pending.passphrase);\n    p->st = NW_PROV_ST_WIFI_FAILED;", "    p->st = NW_PROV_ST_WIFI_FAILED;", "failed password wiped"),
 ("nw_prov.c", "r == NW_PROV_WIFI_AUTH ? NW_PROV_REASON_AUTH", "r == NW_PROV_WIFI_TIMEOUT ? NW_PROV_REASON_AUTH", "wifi reason mapping"),
 ("nw_prov.c", "r == NW_PROV_CLAIM_DEVICE_OWNED ? NW_PROV_REASON_DEVICE_OWNED", "r == NW_PROV_CLAIM_NETWORK ? NW_PROV_REASON_DEVICE_OWNED", "claim reason mapping"),
 ("nw_prov.c", "    p->have_claim = false;\n    wipe(p->claim_token", "    wipe(p->claim_token", "used token dropped after claim failure"),
 ("nw_prov.c", "strlen(device_token) >= sizeof p->pending.device_token", "0", "device token length"),
 ("nw_prov.c", "if (!p->ops.store.save || p->ops.store.save(p->ops.store_ctx, &p->pending) != 0) {", "if (0) {", "save failure must not report claimed"),
 ("nw_prov.c", "end_setup(p, NW_PROV_S_CLAIMED);", "p->state = NW_PROV_S_CLAIMED;", "claimed wipes RAM secrets and BLE off"),
 ("nw_prov.c", "p->ops.claim_post(p->ops.ctx, p->claim_token, p->pending.name);", "p->ops.claim_post(p->ops.ctx, p->pending.name, p->claim_token);", "claim args"),
 ("nw_prov.c", "p->ops.wifi_connect(p->ops.ctx, p->pending.ssid, p->pending.passphrase);", "p->ops.wifi_connect(p->ops.ctx, p->pending.passphrase, p->pending.ssid);", "wifi args"),
]
SRC = ["nw_prov_proto.c", "nw_prov.c"]

def run(workdir):
    exe = workdir / "t"
    cmd = [cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(workdir / "include"), "-I", str(here), str(here / "test_prov.c")] \
          + [str(workdir / "src" / s) for s in SRC] + ["-o", str(exe)]
    c = subprocess.run(cmd, capture_output=True, text=True)
    if c.returncode: return "compile", c.stderr[:300]
    r = subprocess.run([str(exe)], capture_output=True, text=True)
    return ("pass" if r.returncode == 0 else "fail"), r.stdout[-200:]

def main():
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td) / "base"
        shutil.copytree(prov, base)
        st, out = run(base)
        if st != "pass": print("baseline does not pass:", st, out); return 1
        for i, (f, old, new, what) in enumerate(M):
            d = pathlib.Path(td) / f"m{i}"
            shutil.copytree(prov, d)
            for sub in ("src", "include"):
                p = d / sub / f
                if p.exists(): break
            txt = p.read_text()
            if txt.count(old) != 1: print(f"MUTANT {i} ({what}): pattern found {txt.count(old)}x in {f}"); bad += 1; continue
            p.write_text(txt.replace(old, new))
            st, out = run(d)
            if st == "pass": print(f"SURVIVED {i}: {what}"); bad += 1
            elif st == "compile": print(f"DOES NOT COMPILE {i}: {what}\n{out}"); bad += 1
    print(f"{len(M) - bad}/{len(M)} mutants killed")
    return 1 if bad else 0

sys.exit(main())

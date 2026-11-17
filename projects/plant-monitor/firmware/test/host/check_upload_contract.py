#!/usr/bin/env python3
"""Drift check between nw_upload.h/.c and the deployed ingest contract (task 4.F3 slice 2).
Reads docs/interfaces/openapi.yaml and cloud/supabase/functions/_shared/handlers.ts and fails when the firmware constants or
error codes no longer match. `--selftest` proves each rule can fail."""
import re, sys, pathlib

root = pathlib.Path(__file__).resolve().parents[2]
pm = root.parent
def rd(p): return p.read_text()

def check(hdr, src, openapi, handlers):
    e = []
    def define(n):
        m = re.search(r"#define\s+%s\s+(\d+)" % n, hdr)
        return int(m.group(1)) if m else None
    ing = openapi.split("  /ingest:", 1)[1].split("\n  /", 1)[0] if "  /ingest:" in openapi else ""
    if not ing: e.append("openapi.yaml has no /ingest path")
    if '#define NW_UPLOAD_PATH "/ingest"' not in hdr: e.append("NW_UPLOAD_PATH is not /ingest")
    if "deviceToken: { type: http, scheme: bearer" not in openapi: e.append("openapi deviceToken is no longer an http bearer scheme")
    if 'memcpy(out, "Bearer ", 7);' not in src: e.append("nw_upload.c does not send 'Bearer '")
    m = re.search(r"max (\d+) requests per device per hour", ing)
    if not m: e.append("openapi /ingest no longer states the per-device hourly limit")
    elif define("NW_UPLOAD_MAX_PER_HOUR") != int(m.group(1)): e.append(f"NW_UPLOAD_MAX_PER_HOUR != openapi {m.group(1)}")
    if define("NW_UPLOAD_RATE_WINDOW_S") != 3600: e.append("rate window is not 3600 s")
    if define("NW_UPLOAD_TOKEN_HEX") != 64: e.append("token length is not 64")
    if not re.search(r"device_token: \{ type: string, pattern: \"\^\[0-9a-f\]\{64\}\$\"", openapi): e.append("openapi device_token pattern changed")
    for code in ("200", "400", "401", "405", "413", "429", "500"):
        if f'"{code}"' not in ing: e.append(f"openapi /ingest lost response {code}")
    for needle in ("token_revoked", "token_invalid"):
        if needle not in ing or needle not in handlers: e.append(f"{needle} missing in openapi /ingest or handlers.ts")
    if "server_time" not in ing or not re.search(r"required: \[server_time,", ing): e.append("server_time is no longer a required ack field")
    if "(more than 192 samples" not in ing: e.append("openapi 413 text (192 samples) changed")
    if "The device deletes a sample from its buffer only after" not in ing: e.append("openapi no longer states the delete-after-2xx rule")
    for needle in ("req.method !== \"POST\"", "bearer(req)"):
        if needle not in handlers: e.append(f"handlers.ts handleIngest changed ({needle})")
    for w in ("NW_UP_ACK", "NW_UP_REVOKED", "reenter_setup"):
        if w not in hdr: e.append(f"nw_upload.h lost {w}")
    if re.search(r"https?://(?!api\.invalid)[a-z0-9.-]+\.[a-z]{2,}", src + hdr.replace("https://host[:port]", "")):
        e.append("a real-looking URL is written into nw_upload.c/.h (A-082: base URL is a build setting)")
    return e

def main():
    hdr = rd(root / "components/upload/include/nw_upload.h"); src = rd(root / "components/upload/src/nw_upload.c")
    openapi = rd(pm / "docs/interfaces/openapi.yaml"); handlers = rd(pm / "cloud/supabase/functions/_shared/handlers.ts")
    if "--selftest" in sys.argv:
        muts = [("hdr", "#define NW_UPLOAD_MAX_PER_HOUR 6", "#define NW_UPLOAD_MAX_PER_HOUR 5"),
                ("hdr", '#define NW_UPLOAD_PATH "/ingest"', '#define NW_UPLOAD_PATH "/ingest2"'),
                ("src", 'memcpy(out, "Bearer ", 7);', 'memcpy(out, "Token  ", 7);'),
                ("api", "max 6 requests per device per hour", "max 9 requests per device per hour"),
                ("api", '"413":', '"414":'),
                ("hnd", "token_revoked", "token_gone"),
                ("src", "// x", "// see https://abc.supabase.co/functions/v1")]
        bad = 0
        for where, old, new in muts:
            h, s, o, k = hdr, src, openapi, handlers
            if where == "src" and old == "// x": s = s + new
            else:
                tgt = {"hdr": h, "src": s, "api": o, "hnd": k}[where]
                if old not in tgt: print("SELFTEST invalid mutant", old); bad += 1; continue
                tgt = tgt.replace(old, new)
                h, s, o, k = (tgt if where == "hdr" else h), (tgt if where == "src" else s), (tgt if where == "api" else o), (tgt if where == "hnd" else k)
            if not check(h, s, o, k): print("SELFTEST rule cannot fail:", where, old); bad += 1
        if check(hdr, src, openapi, handlers): print("SELFTEST baseline fails:", check(hdr, src, openapi, handlers)); bad += 1
        print("selftest", "FAILED" if bad else "ok"); sys.exit(1 if bad else 0)
    errs = check(hdr, src, openapi, handlers)
    for x in errs: print("DRIFT:", x)
    print("upload contract: OK" if not errs else f"{len(errs)} drift finding(s)")
    sys.exit(1 if errs else 0)
main()

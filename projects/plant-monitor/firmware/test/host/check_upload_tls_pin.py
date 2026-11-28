#!/usr/bin/env python3
"""Upload TLS is pinned to the ADR-004 CA, never the ESP-IDF bundle (security checklist 5.9, finding F-01; NFR-06).
Fails when nw_upload_idf.c uses the certificate bundle or skips verification, when the pinned PEM is not the only trust anchor,
when the empty-pin refusal is missing or runs after the client is created, or when nw_ingest_ca.h holds something that is not a PEM
certificate. `--selftest` proves each rule can fail. Host only: the ESP-IDF build is NOT run here."""
import re, sys, pathlib

root = pathlib.Path(__file__).resolve().parents[2]
FORBIDDEN = ["esp_crt_bundle", "crt_bundle_attach", "skip_cert_common_name_check", "use_global_ca_store", "skip_cert",
             "HTTP_TRANSPORT_OVER_TCP", "cert_pem = NULL", "crt_bundle"]

import base64, hashlib, shutil, subprocess
PINNED_SHA256 = "34:9D:FA:40:58:C5:E2:63:12:3B:39:8A:E7:95:57:3C:4E:13:13:C8:3F:E6:8F:93:55:6C:D5:E8:03:1B:3C:7D"

def pem_from_header(hdr):
    """Joined PEM text of the macro, or None when the macro is missing or not a sequence of string literals."""
    m = re.search(r"#define NW_INGEST_CA_PEM\s*\\\n((?:\s*\"[^\n]*\"\s*\\?\n?)+)", hdr)
    if not m: return None
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
    return "".join(parts).replace("\\n", "\n") if parts else None

def parse_pem(pem):
    """Returns (ok, fingerprint or reason). Uses openssl when present, else a DER sanity check."""
    if "-----BEGIN CERTIFICATE-----" not in pem or "-----END CERTIFICATE-----" not in pem:
        return False, "missing PEM markers"
    if pem.count("-----BEGIN CERTIFICATE-----") != 1 or pem.count("-----END CERTIFICATE-----") != 1:
        return False, "must hold exactly one certificate"
    head, rest = pem.split("-----BEGIN CERTIFICATE-----", 1)
    tail = rest.split("-----END CERTIFICATE-----", 1)[1]
    if head.strip() or tail.strip(): return False, "text outside the certificate block"
    body = "".join(pem.split("-----BEGIN CERTIFICATE-----")[1].split("-----END CERTIFICATE-----")[0].split())
    try: der = base64.b64decode(body, validate=True)
    except Exception: return False, "base64 body does not decode"
    if not der or der[0] != 0x30: return False, "body is not a DER SEQUENCE"
    if shutil.which("openssl"):
        r = subprocess.run(["openssl", "x509", "-noout", "-fingerprint", "-sha256"], input=pem.encode(), capture_output=True)
        if r.returncode != 0: return False, "openssl cannot parse the certificate"
        return True, r.stdout.decode().split("=", 1)[1].strip()
    return True, ":".join(f"{b:02X}" for b in hashlib.sha256(der).digest())

def check(src, hdr):
    e = []
    for bad in FORBIDDEN:
        if bad in src: e.append(f"nw_upload_idf.c contains '{bad}' (ADR-004 needs the pinned CA only)")
    if "cert_pem = NW_INGEST_CA_PEM" not in src: e.append("nw_upload_idf.c does not set cfg.cert_pem = NW_INGEST_CA_PEM")
    if '#include "nw_ingest_ca.h"' not in src: e.append("nw_upload_idf.c does not include nw_ingest_ca.h")
    refuse = src.find("NW_INGEST_CA_PEM[0] == '\\0'")
    init = src.find("esp_http_client_init(&cfg)")
    if refuse < 0: e.append("no empty-pin refusal (fail closed) in io_post")
    elif init < 0 or refuse > init: e.append("empty-pin refusal must run before esp_http_client_init")
    pem = pem_from_header(hdr)
    if pem is None: e.append("nw_ingest_ca.h does not define NW_INGEST_CA_PEM as a string-literal macro")
    elif pem.strip() == "": e.append("NW_INGEST_CA_PEM is empty: the pin must hold the owner-approved root")
    else:
        ok, info = parse_pem(pem)
        if not ok: e.append(f"NW_INGEST_CA_PEM does not parse: {info}")
        elif info.upper() != PINNED_SHA256.upper(): e.append(f"NW_INGEST_CA_PEM fingerprint {info} is not the pinned GTS Root R4 fingerprint")
    return e

def load():
    return ((root / "components/upload/src/nw_upload_idf.c").read_text(),
            (root / "components/upload/include/nw_ingest_ca.h").read_text())

def main():
    src, hdr = load()
    if "--selftest" in sys.argv:
        muts = [("src", "        .cert_pem = NW_INGEST_CA_PEM,", "        .crt_bundle_attach = esp_crt_bundle_attach,", "bundle restored"),
                ("src", "    if (NW_INGEST_CA_PEM[0] == '\\0') {", "    if (0) {", "empty pin no longer refuses"),
                ("src", "        .cert_pem = NW_INGEST_CA_PEM,", "        .cert_pem = NW_INGEST_CA_PEM,\n        .skip_cert_common_name_check = true,", "CN check skipped"),
                ("src", '#include "nw_ingest_ca.h"', '#include "esp_crt_bundle.h"', "pin header not included"),
                ("hdr", '    "MIICCTCCAY6gAwIBAgINAgPlwGjvYxqccpBQUjAKBggqhkjOPQQDAzBHMQswCQYD\\n" \\', '    "MIICCTCCAY6gAwIBAgINAgPlwGjvYxqccpBQUjAKBggqhkjOPQQDAzBHMQswCQY0\\n" \\', "one base64 character changed (fingerprint/parse)"),
                ("hdr", '    "-----END CERTIFICATE-----\\n"', '    "-----END CERTIFICATE-----\\n" \\\n    "junk\\n"', "junk line after the certificate"),
                ("hdr", '#define NW_INGEST_CA_PEM \\', '#define NW_INGEST_CA_PEM_OLD \\', "macro renamed")]
        bad = 0
        for where, old, new, what in muts:
            s, h = src, hdr
            tgt = s if where == "src" else h
            if old not in tgt: print("SELFTEST invalid mutant:", what); bad += 1; continue
            tgt = tgt.replace(old, new, 1)
            if where == "src": s = tgt
            else: h = tgt
            if not check(s, h): print("SELFTEST survived:", what); bad += 1
        if bad: sys.exit(1)
        print(f"selftest ok: {len(muts)} mutants flagged")
        return
    errs = check(src, hdr)
    for x in errs: print("FAIL:", x)
    if errs: sys.exit(1)
    print("upload TLS pinned to the ADR-004 CA: ok (GTS Root R4 PEM parses, fingerprint matches)")

if __name__ == "__main__":
    main()

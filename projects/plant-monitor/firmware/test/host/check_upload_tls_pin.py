#!/usr/bin/env python3
"""Upload TLS is pinned to the ADR-004 CA, never the ESP-IDF bundle (security checklist 5.9, finding F-01; NFR-06).
Fails when nw_upload_idf.c uses the certificate bundle or skips verification, when the pinned PEM is not the only trust anchor,
when the empty-pin refusal is missing or runs after the client is created, or when nw_ingest_ca.h holds something that is not a PEM
certificate. `--selftest` proves each rule can fail. Host only: the ESP-IDF build is NOT run here."""
import re, sys, pathlib

root = pathlib.Path(__file__).resolve().parents[2]
FORBIDDEN = ["esp_crt_bundle", "crt_bundle_attach", "skip_cert_common_name_check", "use_global_ca_store", "skip_cert",
             "HTTP_TRANSPORT_OVER_TCP", "cert_pem = NULL", "crt_bundle"]

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
    m = re.search(r'#define NW_INGEST_CA_PEM\s+"(.*)"', hdr)
    if not m: e.append("nw_ingest_ca.h does not define NW_INGEST_CA_PEM as a string")
    elif m.group(1) != "" and not ("-----BEGIN CERTIFICATE-----" in m.group(1) and "-----END CERTIFICATE-----" in m.group(1)):
        e.append("NW_INGEST_CA_PEM is set but is not a PEM certificate")
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
                ("hdr", '#define NW_INGEST_CA_PEM ""', '#define NW_INGEST_CA_PEM "not a certificate"', "pin is not a PEM")]
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
    print("upload TLS pinned to the ADR-004 CA: ok (placeholder pin is empty: upload refuses until the PEM is set)")

if __name__ == "__main__":
    main()

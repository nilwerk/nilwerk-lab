#!/usr/bin/env python3
"""Contract drift check (task 4.F2): the firmware constants and strings must match docs/interfaces/ble-provisioning.md,
and the app's ProvisioningService error codes (4.A3, app/src/provisioning/types.ts) must cover every device reason.
The app file is optional: if it is not in this checkout the app part prints SKIP (it is not silently counted as a pass)."""
import pathlib, re, sys

root = pathlib.Path(__file__).resolve().parents[2]          # .../firmware
pm = root.parent                                             # .../plant-monitor
doc = (pm / "docs/interfaces/ble-provisioning.md").read_text()
hdr = (root / "components/provisioning/include/nw_prov_proto.h").read_text()
src = (root / "components/provisioning/src/nw_prov_proto.c").read_text()
fails = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)

def const(name):
    m = re.search(r"#define\s+" + name + r"\s+(\S+)", hdr)
    return m.group(1).strip('"') if m else None

# 1. service UUID written in the contract == firmware constant
m = re.search(r"Service UUID \| \*{0,2}`?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})`?", doc)
check(bool(m) and m.group(1) == const("NW_PROV_SERVICE_UUID"), f"service UUID doc={m.group(1) if m else None} fw={const('NW_PROV_SERVICE_UUID')}")
# 1b. the byte array that the BLE scheme advertises (nw_prov_idf.c, big-endian order) must spell the same UUID
src_idf = (root / "components/provisioning/src/nw_prov_idf.c").read_text()
BE_RE = r"static const uint8_t be\[16\] = \{([^}]*)\}"
def adv_uuid(s):
    mb = re.search(BE_RE, s)
    bytes_be = [int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]{2})", mb.group(1))] if mb else []
    hx = "".join(f"{b:02x}" for b in bytes_be)
    return f"{hx[:8]}-{hx[8:12]}-{hx[12:16]}-{hx[16:20]}-{hx[20:]}" if len(hx) == 32 else None
def with_be(s, arr):
    return re.sub(BE_RE, lambda m: "static const uint8_t be[16] = {" + arr + "}", s)
as_uuid = adv_uuid(src_idf)
check(as_uuid == const("NW_PROV_SERVICE_UUID"), f"advertised UUID bytes (nw_prov_idf.c) = {as_uuid} fw={const('NW_PROV_SERVICE_UUID')}")
# self-tests (playbook rule 5, PR #212 review C1-C3): main's array (...6f836a588c4c) must be detected as drift, the PR's array must pass
MAIN_BE = "0xb5,0x36,0x72,0xdd,0x52,0x27,0x40,0xa0,0x8b,0x6f,0x6f,0x83,0x6a,0x58,0x8c,0x4c"
PR_BE = "0xb5,0x36,0x72,0xdd,0x52,0x27,0x40,0xa0,0x8b,0x6f,0x6f,0x83,0x6f,0x8a,0x58,0x4c"
check(adv_uuid(with_be(src_idf, PR_BE)) == const("NW_PROV_SERVICE_UUID"), "self-test: PR byte array passes (spells 6f8a584c)")
check(adv_uuid(with_be(src_idf, MAIN_BE)) != const("NW_PROV_SERVICE_UUID"), "self-test: main byte array (6a588c4c) is detected as drift")
# 2. numbers in the contract text
check("| `name` | 1-80 characters" in doc and const("NW_PROV_NAME_MIN_CHARS") == "1" and const("NW_PROV_NAME_MAX_CHARS") == "80", "name 1-80 characters")
check("22 characters base64url" in doc and const("NW_PROV_CLAIM_TOKEN_LEN") == "22", "claim_token 22 characters base64url")
check("max 2 KiB per request" in doc and const("NW_PROV_REQ_MAX_BYTES") == "2048", "2 KiB per request")
check("5 failed handshakes, or 5 minutes" in doc, "doc: 5 failed handshakes / 5 minutes")
chk = (root / "components/provisioning/include/nw_prov.h").read_text()
check("MAX_FAILED_HANDSHAKES 5" in chk and "(5u * 60u * 1000u)" in chk, "firmware: 5 handshakes / 5 minutes")
# 3. nw-status states and reasons
line = [l for l in doc.splitlines() if l.startswith("`wifi_connecting`")][0]
doc_words = set(re.findall(r"[a-z_]+", line)) - {"reason"}
fw_words = set(re.findall(r'return "([a-z_]+)"', src)) - {"idle"}
check(doc_words == fw_words, f"nw-status words doc-vs-firmware (diff {sorted(doc_words ^ fw_words)})")
# 4. app contract (optional)
app = pm / "app/src/provisioning/types.ts"
if app.exists():
    t = app.read_text()
    need = {"auth": "wifi_auth", "no_ap": "wifi_no_ap", "timeout": "wifi_timeout", "device_owned": "device_owned",
            "claim_token_invalid": "claim_token_invalid", "network": "claim_network", "server": "claim_server"}
    for dev, appcode in need.items():
        check(f"'{appcode}'" in t, f"app ProvisioningErrorCode has '{appcode}' for device reason '{dev}'")
    for st in ("wifi_connecting", "claiming", "claimed"):
        check(f"'{st}'" in t, f"app LinkState has '{st}'")
else:
    print("SKIP app types.ts not in this checkout (4.A3 not merged); compared by hand in the PR")
# 5. new contract text (PR #129): SRP user name, nw-claim before apply, NVS names; checked against the firmware sources
def contract_text_ok(d, nvs, idf):
    doc_ok = all(x in d for x in ("`wifiprov`", "`nw-claim` (any time after the handshake, before apply)",
                                  "namespace `nw_prov`", "blob `rec`", "Namespace `nw_sec2`"))
    fw_ok = '#define NS "nw_prov"' in nvs and '#define KEY "rec"' in nvs and 'nvs_open("nw_sec2"' in idf
    return doc_ok and fw_ok
nvs = (root / "components/provisioning/src/nw_prov_store_nvs.c").read_text()
idf = (root / "components/provisioning/src/nw_prov_idf.c").read_text()
check(contract_text_ok(doc, nvs, idf), "doc: wifiprov, nw-claim before apply, NVS nw_prov/rec/nw_sec2 (names also in firmware sources)")
# self-test: the check must fail when a name is wrong
check(not contract_text_ok(doc.replace("nw_sec2", "nw_xxx"), nvs, idf), "self-test: renamed nw_sec2 in doc is detected")
check(not contract_text_ok(doc, nvs.replace('"rec"', '"zzz"'), idf), "self-test: renamed rec in firmware is detected")
# 6. claim-logging tags (task 4.F2 logging, no behaviour change): the log lines exist, and no log line carries a secret
def log_tags_ok(s):
    return ('"NWSETUP claim post: status=%d"' in s and '"NWSETUP claim post: transport error=%d"' in s
            and '"NWSETUP end: reason=%s state=%s -> %s"' in s and "end_reason(" in s
            and "PROTOCOMM_SECURITY_SESSION_INVALID_SECURITY_PARAMS" in s)
SECRET_WORDS = re.compile(r"claim_token|device_token|password|passphrase|ssid|resp\b|job->body|\bbody\b", re.I)
def secret_in_logs(s):
    return [l.strip() for l in s.splitlines() if "ESP_LOG" in l and SECRET_WORDS.search(l.split("/*")[0])]
check(log_tags_ok(idf), "claim post status/transport, setup end reason, invalid-params session event are logged")
check(secret_in_logs(idf) == [], "no ESP_LOG line names a token, password, SSID or response body")
check(log_tags_ok(idf.replace('"NWSETUP claim post: status=%d"', '"x"')) is False, "self-test: missing claim post status tag is detected")
check(len(secret_in_logs(idf + '\nESP_LOGI(TAG, "%s", resp);\n')) == 1, "self-test: a log of the response body is detected")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)

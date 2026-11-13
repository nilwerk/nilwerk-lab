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
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)

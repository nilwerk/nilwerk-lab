#!/usr/bin/env python3
"""4.B2: the implemented edge functions must match docs/interfaces/openapi.yaml (and the report schema). Needs PyYAML.
Checks per operation: documented status codes == status codes the handler can return (minus the explicit [not in 4.B2] set),
error codes used in code are named in the spec, security scheme, size limits, hw_id pattern, response fields, requirement IDs."""
import json, os, re, sys, yaml
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(here, "..")
oa_path = os.path.join(root, "..", "docs", "interfaces", "openapi.yaml")
oa_text = open(oa_path).read(); oa = yaml.safe_load(oa_text)
schema = json.load(open(os.path.join(root, "..", "docs", "interfaces", "device-report.schema.json")))
han = open(os.path.join(root, "supabase", "functions", "_shared", "handlers.ts")).read()
lib = open(os.path.join(root, "supabase", "functions", "_shared", "lib.ts")).read()
sql = open(os.path.join(root, "supabase", "migrations", "20261108000004_device_api.sql")).read()
fails = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)

OPS = {"/claim-token": "handleClaimToken", "/device-claim": "handleDeviceClaim", "/ingest": "handleIngest", "/account": "handleDeleteAccount"}
METHOD = {"/account": "delete"}   # default post
NOT_BUILT = {("/device-claim", "429"), ("/ingest", "429")}
SECURITY = {"/claim-token": "userJwt", "/device-claim": None, "/ingest": "deviceToken", "/account": "userJwt"}

def body_of(fn):
    m = re.search(r"export async function %s\b.*?(?=\nexport async function |\Z)" % fn, han, re.S)
    return m.group(0)

for path, fn in OPS.items():
    op = oa["paths"][path][METHOD.get(path, "post")]
    body = body_of(fn)
    emitted = set(re.findall(r"\b(?:err|json)\((\d{3})", body))
    if "methodNotAllowed()" in body: emitted.add("405")
    if "internal()" in body: emitted.add("500")
    if "readJson(" in body: emitted |= {"400", "413"}
    if "validateReport(" in body: emitted |= {"400", "413"}
    if re.search(r"bad\(", body): emitted.add("400")
    emitted.add({"/claim-token": "201", "/account": "204"}.get(path, "200"))
    if "new Response(null, { status: 204 })" in body: emitted.add("204")
    documented = set(op["responses"].keys())
    check(emitted <= documented, f"{path}: every status the code can return is documented (code {sorted(emitted)}, spec {sorted(documented)})")
    missing = {c for c in documented - emitted if (path, c) not in NOT_BUILT}
    check(not missing, f"{path}: every documented status is produced by the code (unbuilt marked [not in 4.B2]: {sorted(documented - emitted)})")
    for _, c in [x for x in NOT_BUILT if x[0] == path]:
        check("[not in 4.B2]" in json.dumps(op["responses"][c]), f"{path}: {c} is marked [not in 4.B2]")
    sec = op.get("security") or []
    want = SECURITY[path]
    check((want is None and sec == []) or (want is not None and sec == [{want: []}]), f"{path}: security scheme = {want}")
    for req in op["x-requirements"]:
        check(req in han or req in lib or req in sql, f"{path}: {req} is cited in the code")

codes = set(re.findall(r'err\(\d{3}, "([a-z_]+)"', han + lib)) | set(re.findall(r'error: "([a-z_]+)"', han)) | {"internal", "method_not_allowed"}
check(all(c in oa_text for c in codes), f"error codes used in code are named in the spec: {sorted(codes)}")
check(str(schema["properties"]["samples"]["maxItems"]) in re.search(r"MAX_SAMPLES = (\d+)", lib).group(1), "MAX_SAMPLES == device-report.schema.json samples.maxItems")
check(schema["properties"]["events"]["maxItems"] == int(re.search(r"events must be an array of at most (\d+)", lib).group(1)), "events maxItems == schema")
check(re.search(r"MAX_BODY_BYTES = 64 \* 1024", lib) is not None and "64 KiB" in oa_text, "body limit 64 KiB in code and spec")
hw = oa["paths"]["/device-claim"]["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]["hw_id"]["pattern"]
check(f"/{hw}/" in han, "hw_id pattern in code == spec")
props = oa["paths"]["/device-claim"]["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]
check(set(re.search(r'\["hw_id", "claim_token", "name", "fw"\]', han) and props.keys()) == {"hw_id", "claim_token", "name", "fw"}, "device-claim request properties == spec")
check(f'maxLength' in json.dumps(props["name"]) and props["name"]["maxLength"] == 80 and "b.name.length > 80" in han, "name maxLength 80")
claim_req = oa["paths"]["/device-claim"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["required"]
check(all(re.search(r"\b%s\b" % k, body_of("handleDeviceClaim")) for k in claim_req), f"/device-claim 200 fields {claim_req} are produced")
ing_req = oa["paths"]["/ingest"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["required"]
ib = sql[sql.index("create or replace function public.ingest_batch"):]
check(all(f"'{k}'" in ib for k in ing_req + ["fw_target", "model_target"]), f"/ingest 200 fields {ing_req} are produced by ingest_batch")
cfg = oa["components"]["schemas"]["DeviceConfig"]["required"]
check(all(f"'{k}'" in sql[sql.index("device_config"):] for k in cfg), f"DeviceConfig fields {cfg} are produced by device_config()")
ct = oa["paths"]["/claim-token"]["post"]["responses"]["201"]["content"]["application/json"]["schema"]["required"]
check(all(k in body_of("handleClaimToken") for k in ct), f"/claim-token 201 fields {ct}")
for fn in ("ingest", "device-claim", "claim-token", "delete-account"):
    check(os.path.isfile(os.path.join(root, "supabase", "functions", fn, "index.ts")), f"supabase/functions/{fn}/index.ts exists")
acc = oa["paths"]["/account"]["delete"]
check("FR-A01" in acc["x-requirements"] and "FR-A08" in acc["x-requirements"] and "NFR-07" in acc["x-requirements"], "/account cites FR-A01, FR-A08, NFR-07")
check(acc["requestBody"]["content"]["application/json"]["schema"]["properties"]["confirm"]["enum"] == ["DELETE"] and 'b.confirm !== "DELETE"' in han, "/account confirm literal == spec")
check(re.search(r"\[functions\.delete-account\]\s*\nverify_jwt = false", open(os.path.join(root, "supabase", "config.toml")).read()) is not None, "config.toml: delete-account has verify_jwt = false (the handler verifies the JWT itself)")
sys.exit(1 if fails else 0)

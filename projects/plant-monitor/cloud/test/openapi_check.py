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
exp = open(os.path.join(root, "supabase", "functions", "_shared", "export.ts")).read()
lib = open(os.path.join(root, "supabase", "functions", "_shared", "lib.ts")).read()
sql = open(os.path.join(root, "supabase", "migrations", "20261108000004_device_api.sql")).read()
fails = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)

OPS = {"/claim-token": "handleClaimToken", "/device-claim": "handleDeviceClaim", "/ingest": "handleIngest", "/account": "handleDeleteAccount", "/export": "handleExport"}
METHOD = {"/account": "delete", "/export": "get"}   # default post
NOT_BUILT = {("/device-claim", "429"), ("/ingest", "429")}
SECURITY = {"/claim-token": "userJwt", "/device-claim": None, "/ingest": "deviceToken", "/account": "userJwt", "/export": "userJwt"}

def body_of(fn):
    m = re.search(r"export async function %s\b.*?(?=\nexport async function |\Z)" % fn, han + "\n" + exp, re.S)
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
        check(req in han or req in lib or req in sql or req in exp, f"{path}: {req} is cited in the code")

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
for fn in ("ingest", "device-claim", "claim-token", "delete-account", "export"):
    check(os.path.isfile(os.path.join(root, "supabase", "functions", fn, "index.ts")), f"supabase/functions/{fn}/index.ts exists")
acc = oa["paths"]["/account"]["delete"]
check("FR-A01" in acc["x-requirements"] and "FR-A08" in acc["x-requirements"] and "NFR-07" in acc["x-requirements"], "/account cites FR-A01, FR-A08, NFR-07")
check(acc["requestBody"]["content"]["application/json"]["schema"]["properties"]["confirm"]["enum"] == ["DELETE"] and 'b.confirm !== "DELETE"' in han, "/account confirm literal == spec")
check(re.search(r"\[functions\.delete-account\]\s*\nverify_jwt = false", open(os.path.join(root, "supabase", "config.toml")).read()) is not None, "config.toml: delete-account has verify_jwt = false (the handler verifies the JWT itself)")
# 4.B2c GET /export
ex = oa["paths"]["/export"]["get"]
cfg_toml = open(os.path.join(root, "supabase", "config.toml")).read()
check(re.search(r"\[functions\.export\]\s*\nverify_jwt = false", cfg_toml) is not None, "config.toml: export has verify_jwt = false (the handler verifies the JWT itself)")
check("edge function `export`" in ex["description"], "/export description names the edge function `export`")
check("FR-A01" in ex["x-requirements"] and "NFR-07" in ex["x-requirements"] and "NFR-06" in ex["x-requirements"], "/export cites NFR-07, FR-A01, NFR-06")
check("valid 7 days" in ex["description"] and re.search(r"PHOTO_URL_TTL_SECONDS = 7 \* 24 \* 3600", exp) is not None, "photo URL lifetime: 7 days in spec and code")
js = ex["responses"]["200"]["content"]["application/json"]["schema"]
check("plants" in js["required"] and js["properties"]["plants"]["type"] == "array", "/export JSON: plants is a required top-level array")
jb = body_of("handleExport")
check(all(re.search(r"\b%s\b" % k, exp) for k in js["required"] if k not in ("exported_at",)) and "exported_at" in jb, f"/export JSON top-level keys {js['required']} are produced")
photo_keys = list(js["properties"]["photos"]["items"]["required"])
check(re.search(r"\bphotos: \[%s\]" % ", ".join('"%s"' % k for k in photo_keys), exp) is not None, f"photo fields {photo_keys} == CSV_COLUMNS.photos")
check(all(k in exp for k in ("id: p.id", "plant_id: p.plant_id", "taken_at: p.taken_at", "url,", "expires_at:", "file:")), "photo objects carry the documented fields")
files = re.search(r"format=csv: application/zip with (.*?) \(id,", ex["description"], re.S).group(1)
spec_csv = [x.strip() for x in files.replace("\n", " ").replace(" and ", ",").split(",") if x.strip()]
code_csv = [m + ".csv" for m in re.findall(r"^  (\w+): \[", exp, re.M)]
check(spec_csv == code_csv, f"CSV files in the spec == CSV_COLUMNS ({code_csv})")
check("Cache-Control: no-store" in ex["description"] and '"cache-control": "no-store"' in exp, "no-store in spec and code")
# 4.B4 slice 2 GET /analytics (FR-P01, FR-P04): built, and the code's statuses and response fields match the spec exactly
an = oa["paths"]["/analytics"]["get"]
an_text = open(os.path.join(root, "supabase", "functions", "_shared", "analytics.ts")).read()
an_all = an_text + open(os.path.join(root, "analytics", "aggregate.ts")).read()
check("[built, 4.B4 slice 2]" in an["description"] and "[proposed, not built]" not in an["description"], "/analytics marker says built (no 'proposed' left)")
check(os.path.isfile(os.path.join(root, "supabase", "functions", "analytics", "index.ts")), "supabase/functions/analytics/index.ts exists")
an_emitted = set(re.findall(r"\b(?:err|json)\((\d{3})", an_text))
check(an_emitted == set(an["responses"].keys()), f"/analytics: statuses the code can return == spec (code {sorted(an_emitted)}, spec {sorted(an['responses'])})")
check(an["parameters"][0]["name"] == "window" and an["parameters"][0]["schema"]["enum"] == [30, 90] and an["parameters"][0]["required"], "/analytics: window is required, enum [30, 90]")
check('"window must be 30 or 90"' in an_text and '"30" ? 30 : raw === "90"' in an_text, "/analytics: invalid window -> 400 bad_request")
an_plant = an["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["plants"]["items"]
for k in an_plant["required"]:
    check(re.search(r"\b%s:" % k, an_text) is not None, f"/analytics: plant field '{k}' is produced")
for k in an_plant["properties"]["trend"]["required"]:
    check(re.search(r"\b%s:" % k, an_text) is not None, f"/analytics: trend field '{k}' is produced")
# 4.B4b ADR-018: the `daily` series is built: marker, required, bounds, and the four item fields are produced in code (wire names) and by the pure function
check("[proposed, 4.B4b" not in an["description"] and "[built, 4.B4b]" in an["description"], "/analytics: daily marker says built (no 'proposed, 4.B4b' left)")
daily = an_plant["properties"]["daily"]
check("[built, 4.B4b]" in daily["description"] and "[proposed" not in daily["description"], "/analytics: daily field description says built")
check("daily" in an_plant["required"], "/analytics: daily is in the plant's required list (built, ADR-018)")
check(daily["type"] == "array" and daily["maxItems"] == 90 and daily["minItems"] == 30, "/analytics: daily is an array of 30..90 items (at most 90)")
daily_fields = sorted(daily["items"]["required"])
check(daily_fields == sorted(daily["items"]["properties"].keys()) == ["battery_mv_mean", "date", "reading_count", "soil_pct_mean"], f"/analytics: daily item fields are exactly date, soil_pct_mean, battery_mv_mean, reading_count (spec {daily_fields})")
wire = re.search(r"daily: p\.daily\.map\(\(d\) => \(\{(.*?)\}\)\)", an_text, re.S)
check(wire is not None and sorted(re.findall(r"(\w+): d\.", wire.group(1))) == daily_fields, "/analytics: the code maps exactly these daily item fields (wire names)")
check("DailyPoint" in an_all and "dailySeries(samples, nowMs, windowDays)" in an_all and "reading_count: number" in an_text, "/analytics: daily is computed by dailySeries over the same samples as the aggregates (no second read)")
check(all(r in an_text for r in an["x-requirements"]), f"/analytics cites {an['x-requirements']} in code")
check("premium_required" in an_text and "err(403, \"premium_required\"" in an_text, "/analytics: 403 premium_required before any read (FR-P04)")
check(re.search(r"\[functions\.analytics\]\s*\nverify_jwt = false", open(os.path.join(root, "supabase", "config.toml")).read()) is not None, "config.toml: analytics has verify_jwt = false (the handler verifies the JWT itself)")
check("no-store" in an_text and "Cache-Control: no-store" in an["description"], "/analytics: no-store in spec and code")
sys.exit(1 if fails else 0)

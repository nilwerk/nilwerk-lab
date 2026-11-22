#!/usr/bin/env bash
# bench/cloud/check.sh: bench step e ("e. Cloud check"), read-only.
#
# Purpose: check that the bench device sent at least one reading row to the EU cloud project after the test started.
# Read-only: one HTTP GET on the PostgREST endpoint /rest/v1/readings. No write, no RPC, no delete.
# It prints no value from the rows, no URL and no key. It prints the HTTP status and a row count only.
#
# Sources (paths relative to the repository root):
#   projects/plant-monitor/cloud/supabase/migrations/20261107000001_core_schema.sql:188-200
#       table public.readings: device_id (uuid, references devices.id), ts, received_at (timestamptz, default now())
#   same file, line 90
#       public.devices.hw_id (text, '^nw-[0-9a-f]{12}$', unique): the board's hw_id
#   same file, line 211
#       readings_select_own (RLS, owner rows only). The secret key used here bypasses RLS (see owner input).
#   projects/plant-monitor/cloud/supabase/config.toml:3-5
#       production is ONE free Supabase project in an EU region (the README names Frankfurt as the planned region)
#   projects/plant-monitor/cloud/README.md
#       secret key name SUPABASE_SECRET_KEY (the key is never written here)
#   .github/workflows/bench.yml, step e
#       env: BENCH_CLOUD_CHECK_CONFIG (secret), BENCH_BOARD_HW_ID (repository variable), BENCH_TEST_START_UTC (step d)
#
# Inputs (names only; values are never printed):
#   BENCH_CLOUD_CHECK_CONFIG  secret: a JSON object {"url": "https://<project>.supabase.co", "secret_key": "<key>"}
#   BENCH_BOARD_HW_ID         repository variable: the board hw_id, nw-<12 lowercase hex>
#   BENCH_TEST_START_UTC      from step d, for example 2026-11-22T10:00:00Z
#
# Exit 1 if a variable is missing. Exit 1 with "cloud check not defined: owner input needed" if the config secret is not
# the JSON object above (the script defines that format; the owner sets the secret in it).
#
# Still an owner input (not in the repo):
#   - the owner sets BENCH_CLOUD_CHECK_CONFIG in the JSON form above;
#   - the owner approves one read with the secret key (it bypasses RLS). The key stays in the job environment only;
#   - the region of the project is not checked here (the workflow comment calls it the EU project).
set -euo pipefail

fail() { echo "::error::e. cloud check: $1"; exit 1; }

missing=""
for v in BENCH_CLOUD_CHECK_CONFIG BENCH_BOARD_HW_ID BENCH_TEST_START_UTC; do
  [ -n "${!v:-}" ] || missing="${missing} ${v}"
done
if [ -n "$missing" ]; then
  fail "not configured: nothing tested (variable(s) not set:${missing}; owner input needed)"
fi
[[ "$BENCH_BOARD_HW_ID" =~ ^nw-[0-9a-f]{12}$ ]] || fail "BENCH_BOARD_HW_ID does not match nw-<12 lowercase hex> (value not printed)"
[[ "$BENCH_TEST_START_UTC" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] || fail "BENCH_TEST_START_UTC is not a UTC time from step d"

work="$(mktemp -d "${RUNNER_TEMP:-/tmp}/bench-cloud.XXXXXX")"
chmod 700 "$work"
trap 'rm -rf "$work"' EXIT

# Build a curl config file (mode 600, inside the 0700 folder). The key is not put on the command line.
if ! python3 -I - "$work/req.cfg" <<'PY'
import json, os, sys, urllib.parse
try:
    cfg = json.loads(os.environ["BENCH_CLOUD_CHECK_CONFIG"])
except ValueError:
    sys.exit(2)
url = cfg.get("url") if isinstance(cfg, dict) else None
key = cfg.get("secret_key") if isinstance(cfg, dict) else None
if not isinstance(url, str) or not url.startswith("https://") or not isinstance(key, str) or not key:
    sys.exit(2)
if any(c in key for c in '"\\\r\n\t '):
    sys.exit(2)
hw = os.environ["BENCH_BOARD_HW_ID"]
start = os.environ["BENCH_TEST_START_UTC"]
query = urllib.parse.urlencode({
    "select": "ts,received_at,devices!inner(hw_id)",
    "devices.hw_id": "eq." + hw,
    "received_at": "gt." + start,
    "limit": "1",
}, safe=",()!.:")
full = url.rstrip("/") + "/rest/v1/readings?" + query
fd = os.open(sys.argv[1], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write('url = "' + full + '"\n')
    f.write('header = "apikey: ' + key + '"\n')
    f.write('header = "Authorization: Bearer ' + key + '"\n')
PY
then
  fail "BENCH_CLOUD_CHECK_CONFIG is not the JSON object {url, secret_key}: cloud check not defined: owner input needed"
fi

# One GET. Errors go to /dev/null: curl error text can contain the project host name.
code="$(curl -s -o "$work/rows.json" -w '%{http_code}' -K "$work/req.cfg" 2>/dev/null)" || code="000"
[ "$code" = "200" ] || fail "cloud read failed (HTTP ${code}); check the project and BENCH_CLOUD_CHECK_CONFIG (no value printed)"

rows="$(python3 -I -c 'import json, sys; print(len(json.load(open(sys.argv[1], encoding="utf-8"))))' "$work/rows.json")" \
  || fail "cloud reply is not a JSON list"
if [ "$rows" -ge 1 ]; then
  echo "e. cloud: row(s) from the bench device received after the test start (HTTP ${code}, count ${rows}; values not shown)"
else
  fail "no row from the bench device received after the test start (count 0)"
fi

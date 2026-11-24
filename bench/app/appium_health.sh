#!/usr/bin/env bash
# Appium health check, run by bench.yml step d before any phone command (no adb, no session).
# Asks <APPIUM_URL>/status a few times. Continues (exit 0) only when HTTP 200 and the JSON says ready true.
# Otherwise prints exactly one ::error:: line and exits 1. The URL itself is never printed.
# APPIUM_URL defaults to the same value as bench/app/run_appium.sh (http://localhost:4723).
# Tunables (defaults give at most 4 x 5 s + 3 x 3 s = 29 s): APPIUM_HEALTH_TRIES, APPIUM_HEALTH_TIMEOUT_S, APPIUM_HEALTH_PAUSE_S.
set -uo pipefail

appium_url="${APPIUM_URL:-http://localhost:4723}"
tries="${APPIUM_HEALTH_TRIES:-4}"
timeout_s="${APPIUM_HEALTH_TIMEOUT_S:-5}"
pause_s="${APPIUM_HEALTH_PAUSE_S:-3}"
body="$(mktemp "${RUNNER_TEMP:-/tmp}/appium-health.XXXXXX")"
trap 'rm -f "$body"' EXIT

code="000"
i=1
while [ "$i" -le "$tries" ]; do
  : > "$body"
  code="$(curl -sS --max-time "$timeout_s" -o "$body" -w '%{http_code}' "${appium_url%/}/status" 2>/dev/null)" || code="000"
  if [ "$code" = "200" ] && python3 -I -c '
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
v = d.get("value", d) if isinstance(d, dict) else {}
sys.exit(0 if isinstance(v, dict) and v.get("ready") is True else 1)
' "$body" 2>/dev/null; then
    echo "d. app flow: 0. Appium status: ready (try ${i} of ${tries})"
    exit 0
  fi
  echo "d. app flow: 0. Appium status: not ready (try ${i} of ${tries}, HTTP ${code})"
  [ "$i" -lt "$tries" ] && sleep "$pause_s"
  i=$((i + 1))
done
echo "::error::d. app flow: 0. Appium not ready at APPIUM_URL (HTTP ${code}): check the appium service on the Pi (systemctl status appium), then re-run"
exit 1

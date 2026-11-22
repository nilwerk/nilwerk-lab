#!/usr/bin/env bash
# bench/app/run_appium.sh: bench step d ("d. App flow on phone"), first check only.
#
# Purpose: open the Plant Monitor app on the bench phone through an Appium 2 server (UiAutomator2) and check that
# the first screen title exists. Read-only on the phone: no tap, no typing, no sign-in, no device scan.
# Session pattern: a W3C session with appium:automationName UiAutomator2 (the workflow sets APPIUM_AUTOMATION_NAME).
# The repo has no existing Appium smoke test: grep for UiAutomator2 / appium matches only bench.yml,
# docs/ci-bench-runner.md and this script itself, so no pattern is copied.
#
# Sources (paths relative to the repository root):
#   projects/plant-monitor/app/app.config.ts:16               android.package, the app package id (read at run time)
#   projects/plant-monitor/app/strings/en.json:7              "app.name", the first screen title (read at run time)
#   projects/plant-monitor/app/src/screens/WelcomeScreen.tsx:12  <Screen title={t('app.name')}>, the welcome screen
#   projects/plant-monitor/app/App.tsx:74                     the welcome route is shown when signed out (first screen)
#   .github/workflows/bench.yml, step d                       env: BENCH_ANDROID_SERIAL (secret, never printed),
#                                                             APPIUM_PLATFORM_NAME, APPIUM_AUTOMATION_NAME
#
# Fails closed: if the title cannot be read from the repo, the script stops with
#   "screen expectation missing: owner or app owner input needed"
# before it contacts the phone or the Appium server.
#
# Still an owner input (not in the repo):
#   - the app owner confirms that the first screen title is app.name (the welcome screen title);
#   - the device steps (scan, connect, write setup data, connected) and the test-account sign-in are NOT in this
#     script. Step d as documented in docs/ci-bench-runner.md needs them; they are an owner input;
#   - the Appium 2 server must run on the runner. APPIUM_URL defaults to http://localhost:4723 (Appium's default port).
#
# Secrets: BENCH_ANDROID_SERIAL is read from the environment, sent to Appium in a file that is deleted on exit,
# and never printed. No other secret is used here.
set -euo pipefail

fail() { echo "::error::d. app flow: $1"; exit 1; }

root="$(cd "$(dirname "$0")/../.." && pwd)"
app="$root/projects/plant-monitor/app"

# 1. The first screen title, from the app's strings. No text is typed in this file.
if ! title="$(python3 -I - "$app/strings/en.json" 2>/dev/null <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    value = json.load(f).get("app.name")
if not isinstance(value, str) or not value.strip():
    sys.exit(1)
print(value)
PY
)"; then
  fail "screen expectation missing: owner or app owner input needed (app.name not readable from projects/plant-monitor/app/strings/en.json)"
fi

# 2. The app package id, from app.config.ts (android.package).
pkg="$(sed -n "s/^ *package: '\([A-Za-z0-9_.]*\)',\{0,1\}$/\1/p" "$app/app.config.ts" | head -n 1)"
[ -n "$pkg" ] || fail "app package id not found in projects/plant-monitor/app/app.config.ts"

# 3. Device and server. The serial is checked for presence only.
[ -n "${BENCH_ANDROID_SERIAL:-}" ] || fail "secret BENCH_ANDROID_SERIAL is not set (value not printed)"
appium_url="${APPIUM_URL:-http://localhost:4723}"

work="$(mktemp -d "${RUNNER_TEMP:-/tmp}/bench-appium.XXXXXX")"
chmod 700 "$work"
sid=""
cleanup() {
  if [ -n "$sid" ]; then curl -sS -o /dev/null -X DELETE "$appium_url/session/$sid" || true; fi
  rm -rf "$work"
}
trap cleanup EXIT

# 4. Start a session (UiAutomator2). The request body is written to a file, not to the command line.
python3 -I - "$pkg" "$work/session.json" <<'PY'
import json, os, sys
caps = {
    "platformName": os.environ.get("APPIUM_PLATFORM_NAME", "Android"),
    "appium:automationName": os.environ.get("APPIUM_AUTOMATION_NAME", "UiAutomator2"),
    "appium:udid": os.environ["BENCH_ANDROID_SERIAL"],
    "appium:appPackage": sys.argv[1],
    "appium:newCommandTimeout": 120,
}
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump({"capabilities": {"alwaysMatch": caps}}, f)
PY
code="$(curl -sS -o "$work/new.json" -w '%{http_code}' -H 'Content-Type: application/json' \
  --data-binary @"$work/session.json" "$appium_url/session")" || code="000"
[ "$code" = "200" ] || fail "Appium did not start a session at APPIUM_URL (HTTP ${code})"
sid="$(python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["value"]["sessionId"])' "$work/new.json")" \
  || fail "Appium reply has no session id"

# 5. Look for the first screen title (exact text). Up to 30 tries, 2 s apart, while the app starts.
python3 -I -c 'import json, sys; json.dump({"using": "-android uiautomator", "value": "new UiSelector().text(" + json.dumps(sys.argv[1]) + ")"}, sys.stdout)' "$title" > "$work/find.json"
found=0
for _ in $(seq 1 30); do
  code="$(curl -sS -o "$work/find-reply.json" -w '%{http_code}' -H 'Content-Type: application/json' \
    --data-binary @"$work/find.json" "$appium_url/session/$sid/element")" || code="000"
  if [ "$code" = "200" ]; then found=1; break; fi
  sleep 2
done
[ "$found" = "1" ] || fail "first screen title '${title}' not found in ${pkg} after 30 tries"
echo "d. app flow: first screen title '${title}' found in the app package ${pkg} (launch check only; no device steps in this script)"

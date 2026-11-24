#!/usr/bin/env bash
# Appium session create, run by bench/app/run_appium.sh (step "0. launch"). Usage: appium_session.sh <app package> <work dir> <Appium URL>
# Writes the capabilities to <work dir>/session.json, POSTs them to <Appium URL>/session and saves the reply in <work dir>/new.json.
# Exit 0 on HTTP 200. Otherwise prints exactly one ::error:: line (never the URL or the phone serial) and exits 1.
# Time limit of this one request: SESSION_MAX_S = 120 s. The first start on the Pi is slow (the driver checks and installs its helper
# APKs; seen to run for minutes), so the old 30 s limit fired first (run 45434991511, HTTP 000). Every other curl limit stays 30 s.
# APPIUM_SESSION_TIMEOUT_S (whole seconds, 1 to 300) shortens or lengthens it for the offline test only; anything else means 120.
# The step has timeout-minutes 45 and run_appium.sh stops at STEP_MAX_S = 2400 s, so 120 s fits well inside both.
set -uo pipefail
pkg="${1:?package}"; work="${2:?work dir}"; appium_url="${3:?Appium URL}"

SESSION_MAX_S=120
t="${APPIUM_SESSION_TIMEOUT_S:-}"
if [[ "$t" =~ ^[0-9]+$ ]] && [ "$t" -ge 1 ] && [ "$t" -le 300 ]; then SESSION_MAX_S="$t"; fi

python3 -I - "$pkg" "$work/session.json" <<'PY' || { echo "::error::d. app flow: 0. launch: could not write the session capabilities (python3 and BENCH_ANDROID_SERIAL are needed)"; exit 1; }
import json, os, sys
caps = {
    "platformName": os.environ.get("APPIUM_PLATFORM_NAME", "Android"),
    "appium:automationName": os.environ.get("APPIUM_AUTOMATION_NAME", "UiAutomator2"),
    "appium:udid": os.environ["BENCH_ANDROID_SERIAL"],
    "appium:appPackage": sys.argv[1],
    # The launch activity must be named: without it Appium sends "am start -a MAIN -c LAUNCHER" with no package and the
    # device answers "Intent does not match any activities" (run 45219867846, step d).
    "appium:appActivity": os.environ.get("APPIUM_APP_ACTIVITY", ".MainActivity"),
    # The app's Bluetooth and location permissions are granted by Appium, so no system dialog has to be tapped.
    "appium:autoGrantPermissions": True,
    "appium:newCommandTimeout": 120,
    # Start timeouts (ms) for a slow first start: Appium's defaults are 30000 (server launch), 20000 (server install) and
    # 20000 (adb commands). Without aapt2 the driver cannot read the helper APKs' versions and reinstalls them (seen on the Pi).
    "appium:uiautomator2ServerLaunchTimeout": 60000,
    "appium:uiautomator2ServerInstallTimeout": 60000,
    "appium:adbExecTimeout": 60000,
}
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump({"capabilities": {"alwaysMatch": caps}}, f)
PY

code="$(curl -sS --max-time "$SESSION_MAX_S" -o "$work/new.json" -w '%{http_code}' -H 'Content-Type: application/json' \
  --data-binary @"$work/session.json" "${appium_url%/}/session" 2>/dev/null)" || code="000"
if [ "$code" = "200" ]; then exit 0; fi
if [ "$code" = "000" ]; then
  echo "::error::d. app flow: 0. launch: no reply from Appium within ${SESSION_MAX_S} s while starting the session: the server answered /status, so check the phone (adb devices), the Appium journal (journalctl -u appium -n 50) and whether aapt2/Android build-tools are installed on the Pi"
else
  echo "::error::d. app flow: 0. launch: Appium did not start a session at APPIUM_URL (HTTP ${code})"
fi
exit 1

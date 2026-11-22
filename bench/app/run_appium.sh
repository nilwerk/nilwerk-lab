#!/usr/bin/env bash
# App end-to-end flow on the bench phone (Appium 2.x, UiAutomator2). Step d of .github/workflows/bench.yml.
# Communication only: scan, connect, Wi-Fi and name are written, the app shows the sensor as linked,
# and the plant appears in the list. No sensor value is read or asserted.
# Fails closed: exits 1 before any device step if an input is missing. Secret values are never printed.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
result="$here/result.json"

rm -f "$result"
fail() { echo "app flow: $1" >&2; exit 1; }

# 1. Environment (names only).
for name in BENCH_ANDROID_SERIAL BENCH_TEST_EMAIL BENCH_TEST_EMAIL_PASSWORD BENCH_BOARD_POP BENCH_WIFI_SSID BENCH_WIFI_PASSWORD; do
  if [ -z "${!name:-}" ]; then
    fail "not configured: ${name} is not set. Nothing tested."
  fi
done

# 2. Appium 2.x server on localhost:4723.
if ! status="$(curl -fsS --max-time 5 http://localhost:4723/status 2>/dev/null)"; then
  fail "not configured: Appium server not reachable at localhost:4723. Start Appium 2.x. Nothing tested."
fi
if ! grep -Eq '"ready"[[:space:]]*:[[:space:]]*true' <<<"$status"; then
  fail "not configured: Appium server at localhost:4723 is not ready. Nothing tested."
fi

# 3. Phone attached over adb.
command -v adb >/dev/null 2>&1 || fail "not configured: adb is not installed. Nothing tested."
if ! adb devices | tr -d '\r' | awk -v s="$BENCH_ANDROID_SERIAL" 'NR>1 && $1==s && $2=="device" {ok=1} END {exit ok ? 0 : 1}'; then
  fail "device not attached: the configured phone is not in state 'device' in adb devices. Nothing tested."
fi

# 4. BLE device name prefix: first non-empty line of bench/ble/expect.txt, whitespace removed.
expect="$repo/bench/ble/expect.txt"
[ -f "$expect" ] || fail "not configured: bench/ble/expect.txt is missing. Nothing tested."
BENCH_BLE_PREFIX="$(grep -m1 -E '[^[:space:]]' "$expect" | tr -d '[:space:]' || true)"
[ -n "$BENCH_BLE_PREFIX" ] || fail "not configured: bench/ble/expect.txt has no prefix line. Nothing tested."
export BENCH_BLE_PREFIX
export BENCH_RESULT_FILE="$result"

# 5. Run the flow. It exits 1 on any failed step and writes result.json (step names and pass/fail only).
cd "$repo"
node "$here/flow/run.js"

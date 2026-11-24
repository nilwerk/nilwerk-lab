#!/usr/bin/env bash
# Offline test for bench/app/appium_health.sh. Needs bash, curl, python3. No Pi, phone or Appium.
# Starts a local fake HTTP server per case and checks exit code, the single ::error:: line, and that the success case has none.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"
trap 'kill "${srv:-}" 2>/dev/null; rm -rf "$tmp"' EXIT

cat > "$tmp/fake.py" <<'PY'
import sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
mode = sys.argv[1]
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if mode == "hang":
            time.sleep(30); return
        code, body = {"ready": (200, b'{"value":{"build":{"version":"2.0.0"},"ready":true,"message":"ok"}}'),
                      "notready": (200, b'{"value":{"ready":false}}'),
                      "500": (500, b'{"value":{"error":"unknown error"}}')}[mode]
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
srv = HTTPServer(("127.0.0.1", 0), H)
print(srv.server_address[1], flush=True)
srv.serve_forever()
PY

fails=0
run_case() { # name mode expect_exit expect_code
  local name="$1" mode="$2" want="$3" wcode="$4" port out rc errs
  if [ "$mode" = "refused" ]; then
    port="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"; srv=""
  else
    python3 "$tmp/fake.py" "$mode" > "$tmp/port" & srv=$!
    for _ in $(seq 50); do [ -s "$tmp/port" ] && break; sleep 0.1; done
    port="$(cat "$tmp/port")"; : > "$tmp/port"
  fi
  echo "--- case: $name"
  out="$(APPIUM_URL="http://127.0.0.1:${port}" APPIUM_HEALTH_TRIES=3 APPIUM_HEALTH_TIMEOUT_S=1 APPIUM_HEALTH_PAUSE_S=1 bash "$here/appium_health.sh" 2>&1)"; rc=$?
  echo "$out"; echo "exit: $rc"
  [ -n "$srv" ] && kill "$srv" 2>/dev/null
  errs="$(printf '%s\n' "$out" | grep -c '^::error::')"
  local ok=1
  [ "$rc" = "$want" ] || ok=0
  if [ "$want" = "0" ]; then [ "$errs" = "0" ] || ok=0
  else [ "$errs" = "1" ] && printf '%s\n' "$out" | grep -qF "::error::d. app flow: 0. Appium not ready at APPIUM_URL (HTTP ${wcode}): check the appium service on the Pi (systemctl status appium), then re-run" || ok=0; fi
  printf '%s\n' "$out" | grep -q "127.0.0.1" && ok=0   # host must not be printed
  if [ "$ok" = 1 ]; then echo "PASS: $name"; else echo "FAIL: $name"; fails=$((fails + 1)); fi
}

run_case "ready true" ready 0 200
run_case "ready false" notready 1 200
run_case "HTTP 500" 500 1 500
run_case "connection refused" refused 1 000
run_case "hang past timeout" hang 1 000
[ "$fails" = 0 ] && echo "ALL PASS" || { echo "$fails FAILED"; exit 1; }

#!/usr/bin/env bash
# Offline test for bench/app/appium_session.sh. Needs bash, curl, python3. No Pi, phone or Appium.
# A local fake server answers POST /session. The time limit is shortened with APPIUM_SESSION_TIMEOUT_S (test only).
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"
trap 'kill "${srv:-}" 2>/dev/null; rm -rf "$tmp"' EXIT

cat > "$tmp/fake.py" <<'PY'
import sys, time, json
from http.server import BaseHTTPRequestHandler, HTTPServer
mode = sys.argv[1]
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = self.rfile.read(n)
        open(sys.argv[2], "wb").write(body)
        if mode == "hang":
            time.sleep(30); return
        if mode == "slow":
            time.sleep(3)
        code, out = (500, b'{"value":{"error":"session not created"}}') if mode == "500" else (200, b'{"value":{"sessionId":"abc","capabilities":{}}}')
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(out)
srv = HTTPServer(("127.0.0.1", 0), H)
print(srv.server_address[1], flush=True)
srv.serve_forever()
PY

fails=0
run_case() { # name mode limit_s expect_exit expect_text
  local name="$1" mode="$2" lim="$3" want="$4" wtext="$5" port out rc errs ok=1 t0 t1
  python3 "$tmp/fake.py" "$mode" "$tmp/req.json" > "$tmp/port" & srv=$!
  for _ in $(seq 50); do [ -s "$tmp/port" ] && break; sleep 0.1; done
  port="$(cat "$tmp/port")"; : > "$tmp/port"; rm -f "$tmp/req.json"
  mkdir -p "$tmp/w"; rm -f "$tmp/w/"*
  echo "--- case: $name"
  t0=$(date +%s)
  out="$(BENCH_ANDROID_SERIAL=SERIAL123 APPIUM_SESSION_TIMEOUT_S="$lim" bash "$here/appium_session.sh" com.example.app "$tmp/w" "http://127.0.0.1:${port}" 2>&1)"; rc=$?
  t1=$(date +%s)
  echo "$out"; echo "exit: $rc, took $((t1 - t0)) s"
  kill "$srv" 2>/dev/null
  errs="$(printf '%s\n' "$out" | grep -c '^::error::')"
  [ "$rc" = "$want" ] || ok=0
  if [ "$want" = "0" ]; then
    [ "$errs" = "0" ] || ok=0
    grep -q '"sessionId"' "$tmp/w/new.json" || ok=0
  else
    [ "$errs" = "1" ] || ok=0
    printf '%s\n' "$out" | grep -qF "$wtext" || ok=0
  fi
  printf '%s\n' "$out" | grep -qE "127\.0\.0\.1|SERIAL123|Appium down" && ok=0   # no host, serial, or "down"
  if [ "$ok" = 1 ]; then echo "PASS: $name"; else echo "FAIL: $name"; fails=$((fails + 1)); fi
}

run_case "reply after 3 s, limit 10 s: session starts" slow 10 0 ""
run_case "never replies, limit 2 s: one ::error:: line" hang 2 1 "::error::d. app flow: 0. launch: no reply from Appium within 2 s while starting the session: the server answered /status, so check the phone (adb devices), the Appium journal (journalctl -u appium -n 50) and whether aapt2/Android build-tools are installed on the Pi"
run_case "session create HTTP 500: one ::error:: line" 500 10 1 "::error::d. app flow: 0. launch: Appium did not start a session at APPIUM_URL (HTTP 500)"

# Effective --max-time: a curl shim records its arguments (the fast fake server cannot tell 120 from any other default).
mkdir -p "$tmp/shim"
cat > "$tmp/shim/curl" <<'SH'
#!/usr/bin/env bash
out=""; prev=""
for a in "$@"; do
  [ "$prev" = "--max-time" ] && echo "$a" > "$SHIM_LOG"
  [ "$prev" = "-o" ] && out="$a"
  prev="$a"
done
echo '{"value":{"sessionId":"abc"}}' > "$out"
printf 200
SH
chmod +x "$tmp/shim/curl"
limit_case() { # label APPIUM_SESSION_TIMEOUT_S-value expected --max-time ("unset" = variable not set)
  local label="$1" val="$2" want="$3" got
  mkdir -p "$tmp/w"; rm -f "$tmp/shim.log"
  if [ "$val" = "unset" ]; then
    got="$(env -u APPIUM_SESSION_TIMEOUT_S PATH="$tmp/shim:$PATH" SHIM_LOG="$tmp/shim.log" BENCH_ANDROID_SERIAL=S bash "$here/appium_session.sh" p "$tmp/w" http://x >/dev/null 2>&1; cat "$tmp/shim.log" 2>/dev/null)"
  else
    got="$(PATH="$tmp/shim:$PATH" SHIM_LOG="$tmp/shim.log" APPIUM_SESSION_TIMEOUT_S="$val" BENCH_ANDROID_SERIAL=S bash "$here/appium_session.sh" p "$tmp/w" http://x >/dev/null 2>&1; cat "$tmp/shim.log" 2>/dev/null)"
  fi
  echo "--- case: $label (--max-time $got)"
  if [ "$got" = "$want" ]; then echo "PASS: $label"; else echo "FAIL: $label (want $want)"; fails=$((fails + 1)); fi
}
limit_case "limit unset: --max-time 120" unset 120
limit_case "limit abc falls back to 120" abc 120
limit_case "limit 0 falls back to 120" 0 120
limit_case "limit 301 falls back to 120" 301 120
limit_case "limit 99999 falls back to 120" 99999 120
limit_case "limit 300 is kept" 300 300
limit_case "limit 1 is kept" 1 1

# capabilities: the three start timeouts are sent, the old ones are unchanged
python3 -I - "$tmp/req.json" <<'PY' && echo "PASS: capabilities" || { echo "FAIL: capabilities"; fails=$((fails + 1)); }
import json, sys
c = json.load(open(sys.argv[1]))["capabilities"]["alwaysMatch"]
assert c["appium:uiautomator2ServerLaunchTimeout"] == 60000
assert c["appium:uiautomator2ServerInstallTimeout"] == 60000
assert c["appium:adbExecTimeout"] == 60000
assert c["appium:newCommandTimeout"] == 120 and c["appium:autoGrantPermissions"] is True
assert c["appium:appActivity"] == ".MainActivity" and c["appium:appPackage"] == "com.example.app" and c["platformName"] == "Android"
assert len(c) == 10, len(c)
PY
[ "$fails" = 0 ] && echo "ALL PASS" || { echo "$fails FAILED"; exit 1; }

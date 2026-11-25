#!/usr/bin/env bash
# Offline test for bench/firmware/wait_setup_window.sh. Needs bash only. No Pi, board or network.
# A stub `date` returns FAKE_NOW for "+%s", and a stub `sleep` logs its argument instead of sleeping.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/stubs"
cat > "$tmp/stubs/date" <<'SH'
#!/usr/bin/env bash
if [ "$1" = "+%s" ]; then echo "$FAKE_NOW"; else /bin/date "$@"; fi
SH
cat > "$tmp/stubs/sleep" <<'SH'
#!/usr/bin/env bash
echo "$1" >> "$SLEEP_LOG"
SH
chmod +x "$tmp/stubs/date" "$tmp/stubs/sleep"

R=1800000000   # fake reset epoch of step 3
fails=0
# run_case name epoch_value now want_exit want_sleep  (want_sleep "none" = no sleep call)
run_case() {
  local name="$1" epoch="$2" now="$3" want_rc="$4" want_sleep="$5" rc got
  : > "$tmp/sleep.log"
  out="$(PATH="$tmp/stubs:$PATH" FAKE_NOW="$now" SLEEP_LOG="$tmp/sleep.log" BENCH_RESET_EPOCH="$epoch" bash "$here/wait_setup_window.sh" 2>&1)"; rc=$?
  got="$(cat "$tmp/sleep.log")"; [ -z "$got" ] && got="none"
  echo "--- case: $name (exit $rc, sleep $got)"
  echo "$out"
  local ok=1
  [ "$rc" = "$want_rc" ] || ok=0
  [ "$got" = "$want_sleep" ] || ok=0
  if [ "$want_rc" = "1" ]; then printf '%s\n' "$out" | grep -q '^::error::' || ok=0; fi
  if [ "$ok" = 1 ]; then echo "PASS: $name"; else echo "FAIL: $name"; fails=$((fails + 1)); fi
}

run_case "(a) now R+200 waits 110 s" "$R" "$((R + 200))" 0 110
run_case "(b) now R+400 does not wait" "$R" "$((R + 400))" 0 none
run_case "(c1) epoch missing fails closed" "" "$R" 1 none
run_case "(c2) epoch abc fails closed" "abc" "$R" 1 none
run_case "(d) epoch in the future (now R-5000, wait 5310 s) fails closed, no sleep" "$R" "$((R - 5000))" 1 none
run_case "(e) now R+310 exact, no wait" "$R" "$((R + 310))" 0 none
run_case "(f) now R (wait 310 s, at the limit) sleeps 310" "$R" "$R" 0 310
run_case "(g1) 19-digit epoch 9999999999999999999 fails closed, no sleep" "9999999999999999999" "$R" 1 none
run_case "(g2) 20-digit epoch fails closed, no sleep" "99999999999999999999" "$R" 1 none
run_case "(g3) 11-digit epoch (valid length, far future) fails closed by the 310 s cap, not the digit check" "99999999999" "$R" 1 none
run_case "(g4) leading zero 01700000000 (octal misread) fails closed, no sleep" "01700000000" "$R" 1 none
run_case "(g5) 12-digit epoch fails closed by the digit check, no sleep" "123456789012" "$R" 1 none
run_case "(g6) zero epoch 0 fails closed, no sleep" "0" "$R" 1 none
run_case "(g7) 11-digit epoch, valid, waits 110 s" "10000000001" "$((10000000001 + 200))" 0 110
[ "$fails" = 0 ] && echo "ALL PASS" || { echo "$fails FAILED"; exit 1; }

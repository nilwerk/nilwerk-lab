#!/usr/bin/env bash
# Step b wait (A-139). Sleeps until BENCH_RESET_EPOCH + 310 s: the 300 s setup window (sdkconfig.defaults.bench-ci) closes
# about then, plus a 10 s margin. Called by bench.yml step b. Sends no reset and reads no serial data.
# Fails closed (exit 1, no sleep) if the epoch is missing or not a whole number of at most 11 digits, or if the wait would be longer than 310 s
# (that means the epoch is in the future, so it is wrong). Offline test: bench/firmware/test_wait_setup_window.sh.
set -uo pipefail
reset_epoch="${BENCH_RESET_EPOCH:-}"
# No leading zero: bash reads a 0-prefixed number as octal (01700000000 is another number, 08 is an error), so such a value is refused.
if ! [[ "$reset_epoch" =~ ^[1-9][0-9]*$ ]]; then
  echo "::error::b. serial check: reset time of step 3 not recorded (missing, or not a whole number without a leading zero), nothing tested"
  exit 1
fi
# At most 11 digits (year 5138 or so): checked before any arithmetic, because bash arithmetic wraps silently on a 19-digit value.
if [ "${#reset_epoch}" -gt 11 ]; then
  echo "::error::b. serial check: reset time of step 3 has more than 11 digits, not a time, nothing tested, nothing slept"
  exit 1
fi
wait_s=$(( reset_epoch + 310 - $(date +%s) ))
if [ "$wait_s" -gt 310 ]; then
  echo "::error::b. serial check: wait of ${wait_s} s is longer than 310 s (reset time of step 3 is in the future), nothing tested, nothing slept"
  exit 1
fi
if [ "$wait_s" -gt 0 ]; then
  echo "b. serial: waiting ${wait_s} s until the setup window has closed (no reset sent)"
  sleep "$wait_s"
fi
exit 0

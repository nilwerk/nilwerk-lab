#!/usr/bin/env bash
# Offline test for bench/app/check_setup_session.sh. Needs bash and grep only. No Pi, board, phone or network.
# Fixtures are in bench/app/fixtures/setup-session/. Each case checks the exit code, the ::error:: line and that the
# checker never prints log content (no firmware line text is echoed back).
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
fx="$here/fixtures/setup-session"
fails=0

# run_case name log-path want_exit want_error_substring
run_case() {
  local name="$1" log="$2" want_rc="$3" want_err="$4" out rc ok=1
  out="$(bash "$here/check_setup_session.sh" "$log" 2>&1)"; rc=$?
  echo "--- case: $name (exit $rc)"
  echo "$out"
  [ "$rc" = "$want_rc" ] || ok=0
  if [ "$want_rc" = "1" ]; then
    printf '%s\n' "$out" | grep -q '^::error::' || ok=0
    [ -z "$want_err" ] || printf '%s\n' "$out" | grep -q -F -- "$want_err" || ok=0
  else
    [ -z "$want_err" ] || printf '%s\n' "$out" | grep -q -F -- "$want_err" || ok=0
  fi
  # Log text must never be echoed (a firmware line or its values).
  printf '%s\n' "$out" | grep -q -E 'wifi cred|claim in: len=|plant_monitor' && ok=0
  if [ "$ok" = 1 ]; then echo "PASS: $name"; else echo "FAIL: $name"; fails=$((fails + 1)); fi
}

run_case "expected lines pass" "$fx/pass.log" 0 "ok"
run_case "claim accepted missing fails" "$fx/claim_not_accepted.log" 1 "NWSETUP claim accepted not seen"
run_case "setup ok after wrong PoP fails" "$fx/setup_ok_after_wrong_pop.log" 1 "comes after wrong proof of possession"
run_case "wrong PoP only fails (no setup ok)" "$fx/wrong_pop_only.log" 1 "NWSETUP session: setup ok not seen"
run_case "setup ok missing fails" "$fx/setup_ok_missing.log" 1 "NWSETUP session: setup ok not seen"
run_case "empty log fails closed" "$fx/empty.log" 1 "capture missing"
run_case "missing log fails closed" "$fx/does-not-exist.log" 1 "capture missing"
run_case "no log path fails closed" "" 1 "capture missing"

[ "$fails" = 0 ] && echo "ALL PASS" || { echo "$fails FAILED"; exit 1; }

#!/usr/bin/env bash
# bench/app/check_setup_session.sh <serial-log>: asserts the setup session and claim lines of a bench app flow (PR #215,
# task 4.F2). Needs bash and grep only. Offline: it reads a file, never the Pi, a board or the network.
#
# Lines checked (exact text from projects/plant-monitor/firmware/components/provisioning/src/nw_prov_idf.c):
#   SETUP_OK    "NWSETUP session: setup ok"                       correct PoP, must be seen exactly once, before any claim line
#   CLAIM_IN    "NWSETUP claim in: len="                          must be seen, before the claim result
#   CLAIM_OK    "NWSETUP claim accepted"                          must be seen
#   WRONG_POP   "NWSETUP session: wrong proof of possession"      if seen, no SETUP_OK and no CLAIM_IN may come after it
#
# Exit 0 when every rule holds. Otherwise prints one ::error:: line naming the rule and exits 1.
# The log content is never printed, and neither is any PoP, passphrase, token or name value: only the rule names and line numbers.
# A missing or empty log is a capture failure and fails closed.
set -uo pipefail

log="${1:-}"
fail() { echo "::error::d2. setup session check: $1"; exit 1; }

[ -n "$log" ] || fail "capture missing: no serial log path given (nothing tested)"
[ -e "$log" ] || fail "capture missing: serial log not found (nothing tested)"
[ -s "$log" ] || fail "capture missing: serial log is empty (nothing tested)"

# first_line <fixed text>: prints the line number of the first match, or nothing.
first_line() { grep -n -F -m1 -- "$1" "$log" | cut -d: -f1; }
count_of()   { grep -c -F -- "$1" "$log" || true; }

setup_ok_n="$(count_of 'NWSETUP session: setup ok')"
setup_ok_at="$(first_line 'NWSETUP session: setup ok')"
claim_in_at="$(first_line 'NWSETUP claim in: len=')"
claim_ok_at="$(first_line 'NWSETUP claim accepted')"
wrong_pop_at="$(first_line 'NWSETUP session: wrong proof of possession')"

# 1. Setup ok: seen once.
[ -n "$setup_ok_at" ] || fail "NWSETUP session: setup ok not seen (correct PoP expected)"
[ "$setup_ok_n" = "1" ] || fail "NWSETUP session: setup ok seen ${setup_ok_n} times, expected exactly once"

# 2. Claim in, then claim accepted.
[ -n "$claim_in_at" ] || fail "NWSETUP claim in: len= not seen"
[ -n "$claim_ok_at" ] || fail "NWSETUP claim accepted not seen (the claim did not succeed)"
[ "$claim_in_at" -lt "$claim_ok_at" ] || fail "NWSETUP claim accepted at line ${claim_ok_at} is not after NWSETUP claim in at line ${claim_in_at}"

# 3. Setup ok comes before any claim line.
[ "$setup_ok_at" -lt "$claim_in_at" ] || fail "NWSETUP session: setup ok at line ${setup_ok_at} is not before the first claim line ${claim_in_at}"

# 4. Wrong PoP: nothing that needs a correct session may follow it.
if [ -n "$wrong_pop_at" ]; then
  [ "$wrong_pop_at" -lt "$setup_ok_at" ] && fail "NWSETUP session: setup ok at line ${setup_ok_at} comes after wrong proof of possession at line ${wrong_pop_at}"
  [ "$wrong_pop_at" -lt "$claim_in_at" ] && fail "NWSETUP claim in at line ${claim_in_at} comes after wrong proof of possession at line ${wrong_pop_at}"
  echo "d2. setup session: wrong proof of possession seen at line ${wrong_pop_at} and no session or claim line after it"
fi

echo "d2. setup session: setup ok once (line ${setup_ok_at}), claim in (line ${claim_in_at}), claim accepted (line ${claim_ok_at}): ok"
exit 0

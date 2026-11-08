#!/usr/bin/env bash
# Mutation check for the 4.B2 token-hash, token-auth, claim and idempotency logic.
# openapi_check.py is skipped here (NW_SKIP_OPENAPI) so that it cannot mask a mutant the TypeScript/SQL tests should kill.
# Each mutant changes one expression, runs the edge-function stage (NW_ONLY=api test.sh) and MUST make it fail ("killed").
# A surviving mutant means the tests do not protect that logic: exit 1. Files are always restored. Same DB env as test.sh.
set -uo pipefail
cd "$(dirname "$0")/.."
SQL=supabase/migrations/20261108000004_device_api.sql
SQL5=supabase/migrations/20261108000005_devices_plant_check.sql
LIB=supabase/functions/_shared/lib.ts
HAN=supabase/functions/_shared/handlers.ts
BK="$(mktemp -d)"; cp "$SQL" "$BK/sql"; cp "$SQL5" "$BK/sql5"; cp "$LIB" "$BK/lib"; cp "$HAN" "$BK/han"
restore() { cp "$BK/sql" "$SQL"; cp "$BK/sql5" "$SQL5"; cp "$BK/lib" "$LIB"; cp "$BK/han" "$HAN"; }
trap 'restore; rm -rf "$BK"' EXIT
survived=0; total=0
mutant() { # name file old new
  local name="$1" file="$2" old="$3" new="$4" stage="${5:-api}"
  restore
  OLD="$old" NEW="$new" python3 - "$file" <<'PY' || { echo "BAD MUTANT (pattern not found): $name"; exit 2; }
import os, sys
p = sys.argv[1]; s = open(p).read(); o = os.environ["OLD"]
if s.count(o) != 1: sys.exit(1)
open(p, "w").write(s.replace(o, os.environ["NEW"]))
PY
  total=$((total+1))
  if NW_SKIP_OPENAPI=1 NW_ONLY="$stage" bash ./test.sh >"$BK/out.txt" 2>&1; then echo "SURVIVED  $name"; survived=$((survived+1))
  else echo "killed    $name  ($(grep -m1 -e '^✖' -e 'ERROR:' -e 'FAIL' "$BK/out.txt" | cut -c1-110))"; fi
}
echo "baseline (no mutation) must pass:"; restore
NW_SKIP_OPENAPI=1 NW_ONLY=api bash ./test.sh >"$BK/out.txt" 2>&1 && echo "baseline ok" || { echo "baseline FAILS"; grep -A12 "^✖" "$BK/out.txt" | head -40; exit 1; }

# token-hash logic (NFR-06, ADR-004)
mutant "TS-1 sha256Hex returns plaintext (no hashing)"   "$LIB" 'const d = await crypto.subtle.digest' 'return s; const d = await crypto.subtle.digest'
mutant "TS-2 ingest sends plaintext token to the DB"     "$HAN" '{ p_token_hash: await sha256Hex(token), p_report: r.body }' '{ p_token_hash: token, p_report: r.body }'
mutant "TS-3 device token = hash of different input (claim stores hash of claim token)" "$HAN" 'p_claim_hash: await sha256Hex(b.claim_token), p_token_hash: await sha256Hex(token),' 'p_claim_hash: await sha256Hex(b.claim_token), p_token_hash: await sha256Hex(b.claim_token),'
mutant "SQL-1 claim stores plaintext-decoded token not the digest" "$SQL" "insert into public.device_credentials(device_id, token_hash) values (d.id, decode(p_token_hash, 'hex'))" "insert into public.device_credentials(device_id, token_hash) values (d.id, convert_to(p_token_hash, 'UTF8'))"
# token auth / isolation
mutant "SQL-2 ingest accepts any token (auth bypass, writes to first credential's device)" "$SQL" "select * into c from public.device_credentials where token_hash = decode(p_token_hash, 'hex');" "select * into c from public.device_credentials order by created_at limit 1;"
mutant "SQL-3 revoked credential still accepted"        "$SQL" "if c.revoked_at is not null or d.owner_id is null then" "if d.owner_id is null then"
mutant "SQL-4 readings stamped with a fixed other owner (isolation)" "$SQL" "select d.id, ts, d.owner_id, d.plant_id, m, mr" "select d.id, ts, '00000000-0000-0000-0000-00000000000b'::uuid, d.plant_id, m, mr"
# claim
mutant "SQL-5 claim token reusable"                      "$SQL" "if not found or ct.used_at is not null or ct.expires_at <= now() then" "if not found or ct.expires_at <= now() then"
mutant "SQL-6 claim token never expires"                 "$SQL" "if not found or ct.used_at is not null or ct.expires_at <= now() then" "if not found or ct.used_at is not null then"
mutant "SQL-7 device owned by another user is taken over" "$SQL" "if found and d.owner_id is not null and d.owner_id <> ct.user_id then" "if false then"
mutant "SQL-8 re-claim does not rotate the credential"   "$SQL" "on conflict (device_id) do update set token_hash = excluded.token_hash, created_at = now(), revoked_at = null;" "on conflict (device_id) do nothing;"
mutant "SQL-9 open claim token cap removed"              "$SQL" "and expires_at > now()) >= 10 then" "and expires_at > now()) >= 10000 then"
# idempotency (FR-D04)
mutant "SQL-10 readings: duplicate ts overwrites and is counted as accepted" "$SQL" "    on conflict (device_id, ts) do nothing
    returning plausible" "    on conflict (device_id, ts) do update set moisture_pct = excluded.moisture_pct
    returning plausible"
mutant "SQL-11 readings duplicate ts updates the stored row" "$SQL" "on conflict (device_id, ts) do nothing" "on conflict (device_id, ts) do update set received_at = excluded.received_at"
mutant "SQL-12 event replay overwrites the stored row (critical flag)" "$SQL" "  on conflict (device_id, ts, type) do nothing;" "  on conflict (device_id, ts, type) do update set critical = false;"
mutant "SQL-13 duplicates reported as 0"                 "$SQL" "'duplicates', v_total - v_acc" "'duplicates', 0"
mutant "TS-4 batch cap 192 raised to 100000"             "$LIB" "export const MAX_SAMPLES = 192;" "export const MAX_SAMPLES = 100000;"
# boundary values named in the QA review of PR #45 (Ines, mutants I-5..I-12) + plant link on re-claim
mutant "QA-1 claim token lifetime 15 min -> 150 min"     "$SQL" "now() + interval '15 minutes'" "now() + interval '150 minutes'"
mutant "QA-2 claim token lifetime 15 min -> 14 min"      "$SQL" "now() + interval '15 minutes'" "now() + interval '14 minutes'"
mutant "QA-3 clock-skew tolerance 120 s -> 121 s"        "$SQL" "if abs(v_skew) <= 120 then" "if abs(v_skew) <= 121 then"
mutant "QA-4 clock-skew tolerance 120 s -> 119 s"        "$SQL" "if abs(v_skew) <= 120 then" "if abs(v_skew) <= 119 then"
mutant "QA-5 events cap 32 -> 33"                        "$LIB" "r.events.length > 32" "r.events.length > 33"
mutant "QA-6 events cap 32 -> 31"                        "$LIB" "r.events.length > 32" "r.events.length > 31"
mutant "QA-7 MIN_TS 1700000000 -> 1700000001"            "$LIB" "const MIN_TS = 1700000000;" "const MIN_TS = 1700000001;"
mutant "QA-8 MIN_TS 1700000000 -> 1699999999"            "$LIB" "const MIN_TS = 1700000000;" "const MIN_TS = 1699999999;"
mutant "SQL-14 new owner inherits the old owner's plant link" "$SQL" "plant_id = case when d.owner_id = ct.user_id then plant_id else null end" "plant_id = plant_id"
# N2: devices_update_own must check that the new plant_id belongs to the caller (RLS stage)
mutant "RLS-1 devices_update_own without plant ownership check" "$SQL5" "    and (plant_id is null or exists (select 1 from public.plants p where p.id = plant_id and p.owner_id = auth.uid())));" "    );" rls
mutant "RLS-2 policy forbids clearing the plant link (plant_id is null branch removed)" "$SQL5" "(plant_id is null or exists (select 1 from public.plants p where p.id = plant_id and p.owner_id = auth.uid()))" "(exists (select 1 from public.plants p where p.id = plant_id and p.owner_id = auth.uid()))" rls
# not a mutant: dropping `p.owner_id = auth.uid()` is equivalent for authenticated users, because plants_select_own already hides foreign plants from the subquery; the explicit check is defence in depth.
restore
echo "mutants: $total, survived: $survived"
[ "$survived" = 0 ] && echo "MUTATION CHECK PASSED (all mutants killed)" || { echo "MUTATION CHECK FAILED"; exit 1; }

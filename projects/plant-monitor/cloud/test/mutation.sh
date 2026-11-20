#!/usr/bin/env bash
# Mutation check for the 4.B2 token-hash, token-auth, claim and idempotency logic.
# openapi_check.py is skipped here (NW_SKIP_OPENAPI) so that it cannot mask a mutant the TypeScript/SQL tests should kill.
# Each mutant changes one expression, runs the edge-function stage (NW_ONLY=api test.sh) and MUST make it fail ("killed").
# A surviving mutant means the tests do not protect that logic: exit 1. Files are always restored. Same DB env as test.sh.
set -uo pipefail
cd "$(dirname "$0")/.."
SQL=supabase/migrations/20261108000004_device_api.sql
SQL5=supabase/migrations/20261108000005_devices_plant_check.sql
SQL6=supabase/migrations/20261110000006_delete_account.sql
SQL8=supabase/migrations/20261117000008_export_account.sql
EXP=supabase/functions/_shared/export.ts
LIB=supabase/functions/_shared/lib.ts
HAN=supabase/functions/_shared/handlers.ts
BK="$(mktemp -d)"; cp "$SQL" "$BK/sql"; cp "$SQL5" "$BK/sql5"; cp "$SQL6" "$BK/sql6"; cp "$SQL8" "$BK/sql8"; cp "$EXP" "$BK/exp"; cp "$LIB" "$BK/lib"; cp "$HAN" "$BK/han"
restore() { cp "$BK/sql" "$SQL"; cp "$BK/sql5" "$SQL5"; cp "$BK/sql6" "$SQL6"; cp "$BK/sql8" "$SQL8"; cp "$BK/exp" "$EXP"; cp "$BK/lib" "$LIB"; cp "$BK/han" "$HAN"; }
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
# 4.B2b DELETE /account (FR-A01, FR-A08, NFR-07, NFR-06)
mutant "DA-1 no token check (any caller is treated as the user)"   "$HAN" 'if (!uid) return err(401, "unauthorized", "missing or invalid user JWT");
  const r = await readJson(req);
  if ("fail" in r) return r.fail;
  const b = r.body as Record<string, unknown>;
  if (typeof b !== "object" || b === null || Array.isArray(b) || Object.keys(b)' 'if (false) return err(401, "unauthorized", "missing or invalid user JWT");
  const r = await readJson(req);
  if ("fail" in r) return r.fail;
  const b = r.body as Record<string, unknown>;
  if (typeof b !== "object" || b === null || Array.isArray(b) || Object.keys(b)'
mutant "DA-2 confirm literal not checked"                           "$HAN" ' || b.confirm !== "DELETE") {' ') {'
mutant "DA-3 body may carry extra properties (e.g. a user id)"      "$HAN" 'Object.keys(b).some((k) => k !== "confirm")' 'false'
mutant "DA-4 any HTTP method deletes"                               "$HAN" 'if (req.method !== "DELETE") return methodNotAllowed();' ''
mutant "DA-5 auth user is not deleted"                              "$HAN" 'if (await deps.deleteAuthUser(uid)) return internal();' ''
mutant "DA-6 photo failure ignored (account deleted anyway)"        "$HAN" 'if (await deps.deleteUserPhotos(uid, paths as string[])) return internal();' 'await deps.deleteUserPhotos(uid, paths as string[]);'
mutant "DA-7 photos not deleted"                                    "$HAN" 'if (await deps.deleteUserPhotos(uid, paths as string[])) return internal();' ''
mutant "DA-8 devices not released before deletion"                  "$SQL6" 'update public.devices set owner_id = null, plant_id = null where owner_id = p_user;' 'select 1;'
mutant "DA-9 device credentials not revoked"                        "$SQL6" 'update public.device_credentials set revoked_at = coalesce(revoked_at, now())' 'update public.device_credentials set revoked_at = revoked_at'
mutant "DA-10 releases every user's devices (cross-user)"           "$SQL6" 'update public.devices set owner_id = null, plant_id = null where owner_id = p_user;' 'update public.devices set owner_id = null, plant_id = null;'
mutant "DA-11 revokes every device token (cross-user)"              "$SQL6" 'where device_id in (select id from public.devices where owner_id = p_user);' ';'
mutant "DA-12 open claim tokens survive"                            "$SQL6" 'delete from public.claim_tokens where user_id = p_user;' 'select 1;'
mutant "DA-13 photo paths of all users returned (cross-user)"       "$SQL6" 'from public.plant_images where owner_id = p_user;' 'from public.plant_images;'
# 4.B2c GET /export (NFR-07, FR-A01, NFR-06)
mutant "EX-1 no token check (any caller is treated as the user)"   "$EXP" 'if (!uid) return err(401, "unauthorized", "missing or invalid user JWT");' ''
mutant "EX-2 any HTTP method exports"                               "$EXP" 'if (req.method !== "GET") return err(405, "method_not_allowed");' ''
mutant "EX-3 format not validated"                                  "$EXP" 'if (format !== "json" && format !== "csv") return err(400, "bad_request", "format must be json or csv");' ''
mutant "EX-4 user taken from a query parameter (cross-user)"        "$EXP" '{ p_user: uid }' '{ p_user: new URL(req.url).searchParams.get("user_id") ?? uid }'
mutant "EX-5 photo URL lifetime 7 days -> 1 day"                    "$EXP" '7 * 24 * 3600' '24 * 3600'
mutant "EX-6 signing failure ignored (export without photo links)"  "$EXP" 'if ("error" in s) return err(500, "internal");
    urls = s.urls;' 'urls = "urls" in s ? s.urls : {};'
mutant "EX-7 foreign storage path is signed" "$EXP" 'isSafePhotoPath(uid, p.storage_path));' 'typeof p.storage_path === "string");'
mutant "EX-14 path guard removed (any path with the uid prefix is signed, '..' too)" "$EXP" 'isSafePhotoPath(uid, p.storage_path));' 'typeof p.storage_path === "string" && p.storage_path.startsWith(`${uid}/`));'
mutant "EX-15 path guard accepts '..'"                               "$EXP" 'path.includes("..") || ' ''
mutant "EX-16 path guard: segment character check removed (backslash, %2e, control chars)" "$EXP" ' && seg.every((x) => /^[A-Za-z0-9._-]+$/.test(x) && x !== ".")' ''
mutant "EX-17 path guard: segment count not checked" "$EXP" 'seg.length === 3 && ' ''
mutant "EX-18 path guard accepts a foreign/near user prefix"         "$EXP" 'seg[0] === uid' 'seg[0].startsWith(uid.slice(0, 8))'
mutant "EX-19 path guard: % allowed in a segment (encoded traversal not refused by the character class)" "$EXP" '/^[A-Za-z0-9._-]+$/.test(x)' '/^[A-Za-z0-9._%-]+$/.test(x)'
mutant "EX-8 expires_at not exported_at + 7 days"                   "$EXP" 'new Date(now.getTime() + PHOTO_URL_TTL_SECONDS * 1000)' 'new Date(now.getTime())'
mutant "EX-9 Cache-Control: no-store dropped"                       "$EXP" 'const common = { "cache-control": "no-store" };' 'const common = {};'
mutant "EX-10 CSV formula-injection guard removed"                  "$EXP" '/^[=+\-@\t\r]/.test(s)' '/^$/.test(s)'
mutant "EX-11 CSV guard also mangles numbers (-3.5 -> '-3.5)"       "$EXP" 'if (typeof v === "string" && /^' 'if (/^'
mutant "EX-12 CSV cells never quoted"                               "$EXP" '/[",\r\n]/.test(s) ? ' 'false ? '
mutant "EX-13 zip CRC not written"                                  "$EXP" 'lv.setUint32(14, crc, true);' ''
mutant "EX-S1 readings of ALL users exported (cross-user)"          "$SQL8" 'from public.readings x where x.owner_id = p_user' 'from public.readings x'
mutant "EX-S2 plants of ALL users exported (cross-user)"            "$SQL8" 'from public.plants x where x.owner_id = p_user' 'from public.plants x'
mutant "EX-S3 photo rows of ALL users exported (cross-user)"        "$SQL8" 'from public.plant_images x where x.owner_id = p_user' 'from public.plant_images x'
mutant "EX-S4 export limited to the 7-day free window"              "$SQL8" 'from public.readings x where x.owner_id = p_user' "from public.readings x where x.owner_id = p_user and x.ts > now() - interval '7 days'"
mutant "EX-S5 tips only for premium (RLS policy leaks into export)" "$SQL8" 'from public.tips x where x.owner_id = p_user' 'from public.tips x where x.owner_id = p_user and public.is_premium()'
mutant "EX-S6 hourly roll-up missing owner filter (cross-user)"     "$SQL8" 'from public.readings_hourly x where x.owner_id = p_user' 'from public.readings_hourly x'
mutant "EX-S7 API roles may execute export_account"                 "$SQL8" 'grant execute on function public.export_account(uuid) to service_role;' 'grant execute on function public.export_account(uuid) to service_role, authenticated, anon;'
# not mutants (equivalent here): DA-14 dropping `authenticated` from the revoke in migration 6 changes nothing in plain Postgres, because the test harness never grants function execute to API roles (Supabase default privileges do; the grants test in api.test.ts "API roles cannot call" covers the revoke on the real roles only as far as the harness allows); deleteAuthUser idempotency lives in supabase.ts (404 tolerated), which no test can reach without a live project.
# not a mutant: dropping `p.owner_id = auth.uid()` is equivalent for authenticated users, because plants_select_own already hides foreign plants from the subquery; the explicit check is defence in depth.
restore
echo "mutants: $total, survived: $survived"
[ "$survived" = 0 ] && echo "MUTATION CHECK PASSED (all mutants killed)" || { echo "MUTATION CHECK FAILED"; exit 1; }

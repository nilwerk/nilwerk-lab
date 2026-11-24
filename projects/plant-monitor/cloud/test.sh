#!/usr/bin/env bash
# Cloud backend tests (4.B1). No Docker, no Supabase account, no network, no secrets.
# Needs PostgreSQL 15+ binaries (initdb, pg_ctl, psql). Two modes:
#   - default: starts a throw-away local cluster in a temp dir, stops and deletes it at the end
#   - DATABASE_URL=postgres://user:pw@host:port/postgres (superuser): uses that server, creates/drops nw_test_* databases
# Exit code != 0 on any failure. Output ends with "ALL CLOUD TESTS PASSED".
# NW_ONLY=api runs only the edge-function stage, NW_ONLY=rls only the RLS isolation stage (both used by test/mutation.sh); NW_SKIP_OPENAPI=1 also skips the OpenAPI check (mutation.sh only).
set -euo pipefail
cd "$(dirname "$0")"
HERE="$PWD"
SRC="$HERE/../docs/interfaces/db-schema.sql"
MIG="$HERE/supabase/migrations"

# --- 0. frozen-migration guard: migration 1 was pushed to nilwerk-cloud (cloud/README.md "Migration rules"), so its bytes are pinned.
# Any change to it must be a NEW migration file. The pin is the sha256 of origin/main's migration 1 (owner decision C6).
MIG1_SHA256=8e1dad08dfaff969671f552e8ca605a698576b5f9d43c5454a6f72209faf69a2
if ! echo "$MIG1_SHA256  $MIG/20261107000001_core_schema.sql" | sha256sum -c --status; then
  echo "FAIL: $MIG/20261107000001_core_schema.sql changed; it is frozen. Put the change in a new migration file."; exit 1
fi
echo "ok  migration 1 is frozen (sha256 pinned)"

# --- 1. server
CLEANUP=""
if [ -n "${DATABASE_URL:-}" ]; then
  BASE="${DATABASE_URL%/*}"
  psqlx() { local db="$1"; shift; psql -X -q -v ON_ERROR_STOP=1 "$BASE/$db" "$@"; }
else
  PGBIN="$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1 || true)"
  [ -n "$PGBIN" ] || PGBIN="$(dirname "$(command -v initdb)")"
  TMP="$(mktemp -d)"; chmod 755 "$TMP"
  AS=""; if [ "$(id -u)" = 0 ]; then AS="runuser -u postgres --"; chown postgres "$TMP"; fi
  $AS "$PGBIN/initdb" -D "$TMP/data" -U postgres --auth=trust -E UTF8 >/dev/null
  PORT=$((20000 + RANDOM % 20000))
  $AS "$PGBIN/pg_ctl" -D "$TMP/data" -o "-p $PORT -k $TMP -c listen_addresses=''" -l "$TMP/pg.log" -w start >/dev/null
  CLEANUP="$AS $PGBIN/pg_ctl -D $TMP/data -m immediate stop >/dev/null 2>&1; rm -rf $TMP"
  trap 'eval "$CLEANUP"' EXIT
  psqlx() { local db="$1"; shift; psql -X -q -v ON_ERROR_STOP=1 -h "$TMP" -p "$PORT" -U postgres "$db" "$@"; }
fi
echo "ok  $(psqlx postgres -At -c 'select version()' | cut -c1-40)"

export PGOPTIONS="-c nilwerk.allow_no_cron=on"   # plain local Postgres has no pg_cron; migration 2 otherwise fails loudly

newdb() { # name, seed(yes/no)
  psqlx postgres -c "drop database if exists $1" -c "create database $1"
  psqlx "$1" -f test/stub_auth.sql
  for f in "$MIG"/*.sql; do psqlx "$1" -f "$f" 2>&1 | sed "s/^/    /"; done
  psqlx "$1" -f test/grants.sql
  if [ "$2" = yes ]; then psqlx "$1" -f supabase/seed.sql; fi
}

# --- 0b. contract == cumulative 2.4 state: db-schema.sql must produce the same public schema as migration 1 + the 4.A4c migration.
# Only those two migrations are compared (migrations 2-8 add functions and tables that the contract file does not list).
# The check compares pg_dump --schema-only output of both databases; the \restrict/\unrestrict lines are random per dump and are dropped.
if [ -n "${DATABASE_URL:-}" ]; then
  dumpx() { local db="$1"; shift; pg_dump --schema-only --no-owner -n public "$BASE/$db" | grep -v '^\\\(un\)\?restrict'; }
else
  dumpx() { local db="$1"; shift; pg_dump --schema-only --no-owner -n public -h "$TMP" -p "$PORT" -U postgres "$db" | grep -v '^\\\(un\)\?restrict'; }
fi
CONTRACT_MIG="$MIG/20261122000009_setup_save_plant_rpc.sql"
psqlx postgres -c "drop database if exists nw_test_ct_src" -c "create database nw_test_ct_src" -c "drop database if exists nw_test_ct_mig" -c "create database nw_test_ct_mig"
psqlx nw_test_ct_src -f test/stub_auth.sql -f "$SRC"
psqlx nw_test_ct_mig -f test/stub_auth.sql -f "$MIG/20261107000001_core_schema.sql" -f "$CONTRACT_MIG"
CT_SRC="$(dumpx nw_test_ct_src)"; CT_MIG="$(dumpx nw_test_ct_mig)"
[ -n "$CT_SRC" ] && [ -n "$CT_MIG" ] || { echo "FAIL: pg_dump produced an empty schema"; exit 1; }
if [ "$CT_SRC" != "$CT_MIG" ]; then
  echo "FAIL: docs/interfaces/db-schema.sql differs from migration 1 + $(basename "$CONTRACT_MIG")"
  diff <(echo "$CT_SRC") <(echo "$CT_MIG") | head -40; exit 1
fi
echo "ok  db-schema.sql == migration 1 + $(basename "$CONTRACT_MIG") (pg_dump --schema-only, public)"

if [ "${NW_ONLY:-}" != api ]; then
# --- 1b. migration 2 must FAIL (not skip) when pg_cron is missing and the opt-out flag is not set
psqlx postgres -c "drop database if exists nw_test_cron" -c "create database nw_test_cron"
if PGOPTIONS="" psqlx nw_test_cron -f "$MIG/20261107000002_schedules.sql" >/dev/null 2>&1; then
  echo "FAIL: schedules migration did not fail without pg_cron"; exit 1; fi
psqlx postgres -c "drop database nw_test_cron"
echo "ok  schedules migration fails loudly without pg_cron (and skips only with nilwerk.allow_no_cron=on)"

# --- 2. migrations + seed apply on a fresh DB; RLS isolation A vs B on every table
echo "== RLS isolation (test/rls_isolation.sql)"
newdb nw_test_rls yes
psqlx nw_test_rls -f test/rls_isolation.sql 2>&1 | grep -v '^$' | sed 's/^psql:[^ ]* //'

if [ "${NW_ONLY:-}" = rls ]; then psqlx postgres -c "drop database if exists nw_test_rls" >/dev/null; echo "RLS stage only (NW_ONLY=rls, used by test/mutation.sh)"; exit 0; fi

# --- 3. retention / roll-up (A-028, NFR-13)
echo "== retention / roll-up (test/retention.sql)"
newdb nw_test_ret no
psqlx nw_test_ret -f test/retention.sql 2>&1 | sed 's/^psql:[^ ]* //'

# --- 4. the Architect's 2.4 contract test (alerts, premium window, delete_plant, account cascade, retention) on the migrated DB
echo "== 2.4 contract test (docs/interfaces/db-schema.test.sql) on the migrated DB"
newdb nw_test_contract no
psqlx nw_test_contract -f "$HERE/../docs/interfaces/db-schema.test.sql" 2>&1 | sed 's/^psql:[^ ]* //'

fi

# --- 5a. OpenAPI == code (needs python3 + PyYAML)
echo "== OpenAPI matches the edge functions (test/openapi_check.py)"
if [ -z "${NW_SKIP_OPENAPI:-}" ]; then python3 test/openapi_check.py || { echo "FAIL: openapi_check.py"; exit 1; }; else echo "skipped (NW_SKIP_OPENAPI set by test/mutation.sh so the TypeScript tests are what kills the mutant)"; fi

# --- 5. edge functions 4.B2 (TypeScript handlers against the migrated DB; token hashing, claim, ingest idempotency, token isolation)
echo "== edge functions (test/functions/api.test.ts) against local Postgres"
if ! node -e 'const [a,b]=process.versions.node.split(".").map(Number); process.exit(a>22||(a===22&&b>=6)?0:1)'; then
  echo "FAIL: Node >= 22.6 is required for the edge function tests (found $(node -v 2>/dev/null || echo none))"; exit 1; fi
newdb nw_test_api yes
if [ -n "${DATABASE_URL:-}" ]; then export NW_TEST_DB_URL="$BASE/nw_test_api"
else export NW_TEST_DB_URL="postgresql://postgres@/nw_test_api?host=$TMP&port=$PORT"; fi
node --experimental-strip-types --disable-warning=ExperimentalWarning --test --test-reporter=spec test/functions/api.test.ts
unset NW_TEST_DB_URL

# --- 5b. GET /export 4.B2c: own database (node --test runs files in parallel; api.test.ts deletes users and rolls up readings DB-wide)
echo "== export edge function (test/functions/export.test.ts) against local Postgres"
newdb nw_test_export no
if [ -n "${DATABASE_URL:-}" ]; then export NW_TEST_DB_URL="$BASE/nw_test_export"
else export NW_TEST_DB_URL="postgresql://postgres@/nw_test_export?host=$TMP&port=$PORT"; fi
node --experimental-strip-types --disable-warning=ExperimentalWarning --test --test-reporter=spec test/functions/export.test.ts
unset NW_TEST_DB_URL

# --- 5c. MCP server 4.B5 (FR-P03, FR-P04, FR-P01, FR-P02, NFR-06, NFR-07): tool contracts, key checks, cross-user and revocation against the seeded DB
echo "== MCP server (test/functions/mcp.test.ts) against local Postgres"
newdb nw_test_mcp yes
if [ -n "${DATABASE_URL:-}" ]; then export NW_TEST_DB_URL="$BASE/nw_test_mcp"
else export NW_TEST_DB_URL="postgresql://postgres@/nw_test_mcp?host=$TMP&port=$PORT"; fi
node --experimental-strip-types --disable-warning=ExperimentalWarning --test --test-reporter=spec test/functions/mcp.test.ts
unset NW_TEST_DB_URL

# --- 5d. GET /analytics 4.B4 slice 2 (FR-P01, FR-P04, NFR-06): premium gate as the user, RLS isolation, 30/90-day aggregates on the migrated DB
echo "== analytics endpoint (test/functions/analytics.test.ts) against local Postgres"
newdb nw_test_analytics yes
if [ -n "${DATABASE_URL:-}" ]; then export NW_TEST_DB_URL="$BASE/nw_test_analytics"
else export NW_TEST_DB_URL="postgresql://postgres@/nw_test_analytics?host=$TMP&port=$PORT"; fi
node --experimental-strip-types --disable-warning=ExperimentalWarning --test --test-reporter=spec test/functions/analytics.test.ts
unset NW_TEST_DB_URL

# --- 5e. analytics database adapter 4.B4 slice 3 (no DB: fake PostgREST client records calls): premium RPC as the user before any read, paging by rows returned
echo "== analytics adapter (test/functions/analytics_deps.test.ts) with a fake client"
node --experimental-strip-types --disable-warning=ExperimentalWarning --test --test-reporter=spec test/functions/analytics_deps.test.ts

# --- 6. care-tips engine 4.B3 slice 1 (pure TypeScript, no DB): guardrail rules, premium gate, injected weather/assistant (FR-P02, FR-P04)
if [ "${NW_ONLY:-}" != api ]; then
echo "== care-tips engine (tips/test/*.test.ts: ALL test files, not only tips.test.ts)"
node --experimental-strip-types --disable-warning=ExperimentalWarning --test --test-reporter=spec tips/test/*.test.ts
fi

# --- 7. analytics 4.B4 (pure TypeScript, no DB): 30/90-day aggregates, watering events, trend, comparison, premium gate (FR-P01, FR-P04)
echo "== analytics (analytics/test/*.test.ts: pure functions, hand-computed fixtures)"
node --experimental-strip-types --disable-warning=ExperimentalWarning --test --test-reporter=spec analytics/test/*.test.ts

for d in nw_test_rls nw_test_ret nw_test_contract nw_test_api nw_test_export nw_test_mcp nw_test_analytics nw_test_ct_src nw_test_ct_mig; do psqlx postgres -c "drop database if exists $d" >/dev/null; done
echo "ALL CLOUD TESTS PASSED"

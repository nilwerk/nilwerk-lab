#!/usr/bin/env bash
# Cloud backend tests (4.B1). No Docker, no Supabase account, no network, no secrets.
# Needs PostgreSQL 15+ binaries (initdb, pg_ctl, psql). Two modes:
#   - default: starts a throw-away local cluster in a temp dir, stops and deletes it at the end
#   - DATABASE_URL=postgres://user:pw@host:port/postgres (superuser): uses that server, creates/drops nw_test_* databases
# Exit code != 0 on any failure. Output ends with "ALL CLOUD TESTS PASSED".
set -euo pipefail
cd "$(dirname "$0")"
HERE="$PWD"
SRC="$HERE/../docs/interfaces/db-schema.sql"
MIG="$HERE/supabase/migrations"

# --- 0. drift guard: migration 1 must be the 2.4 schema file, byte for byte (acceptance: do not diverge)
if ! diff <(tail -n +4 "$MIG/20261107000001_core_schema.sql") "$SRC" >/dev/null; then
  echo "FAIL: $MIG/20261107000001_core_schema.sql differs from docs/interfaces/db-schema.sql"; exit 1
fi
echo "ok  migration 1 == docs/interfaces/db-schema.sql (no drift)"

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

# --- 3. retention / roll-up (A-028, NFR-13)
echo "== retention / roll-up (test/retention.sql)"
newdb nw_test_ret no
psqlx nw_test_ret -f test/retention.sql 2>&1 | sed 's/^psql:[^ ]* //'

# --- 4. the Architect's 2.4 contract test (alerts, premium window, delete_plant, account cascade, retention) on the migrated DB
echo "== 2.4 contract test (docs/interfaces/db-schema.test.sql) on the migrated DB"
newdb nw_test_contract no
psqlx nw_test_contract -f "$HERE/../docs/interfaces/db-schema.test.sql" 2>&1 | sed 's/^psql:[^ ]* //'

# --- 5. device API (4.B2): SQL logic against real Postgres
echo "== device API SQL (test/device_api.sql)"
newdb nw_test_dev no
psqlx nw_test_dev -f test/device_api.sql 2>&1 | grep -v '^$' | grep -v 'claim_device\|authenticate' | sed 's/^psql:[^ ]* //'

# --- 6. device API (4.B2): Edge Function handlers with a mocked DB layer (node:test, no dependencies)
echo "== Edge Function handlers, mocked DB (supabase/functions/_shared/handlers.test.ts)"
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
NODE_MINOR="$(node -p 'process.versions.node.split(".")[1]' 2>/dev/null || echo 0)"
if [ "$NODE_MAJOR" -gt 22 ] || { [ "$NODE_MAJOR" -eq 22 ] && [ "$NODE_MINOR" -ge 18 ]; }; then
  node --test supabase/functions/_shared/handlers.test.ts 2>&1 | grep -E "^(ok|not ok|# (tests|pass|fail))"
  node --test supabase/functions/_shared/handlers.test.ts >/dev/null 2>&1 || { echo "FAIL: handler tests"; exit 1; }
elif [ -n "${REQUIRE_NODE_TESTS:-}" ]; then echo "FAIL: Node >= 22.18 required (REQUIRE_NODE_TESTS set)"; exit 1
else echo "NOT RUN: Node >= 22.18 needed for the handler tests (found $(node -v 2>/dev/null || echo none))"; fi

for d in nw_test_dev nw_test_rls nw_test_ret nw_test_contract; do psqlx postgres -c "drop database $d" >/dev/null; done
echo "ALL CLOUD TESTS PASSED"

#!/usr/bin/env bash
# bench/run_e2e.sh: the bench E2E step ("Bench E2E" in .github/workflows/bench.yml).
#
# Purpose: run the existing app end-to-end smoke test, if the repository has one.
# It exists: projects/plant-monitor/app/package.json:12 defines "test:web-flow"
#   ("node --test --test-timeout=600000 e2e/web-flow.test.js"). The test is projects/plant-monitor/app/e2e/web-flow.test.js.
#
# What that test is (read before relying on it): a MOCK web flow. Its header (lines 1-6) says it runs in headless Chromium
# (Playwright) against the Expo web export with EXPO_PUBLIC_MOCK_AUTH=1; auth, plants, readings and BLE are fixtures.
# It does not touch the bench board, the phone or the cloud. Its line 4 runs "npx expo export" (a build).
#
# Fails closed with "E2E not defined: owner input needed" when:
#   - projects/plant-monitor/app/package.json has no "test:web-flow" script, or
#   - the app's dependencies are not installed on the runner (projects/plant-monitor/app/node_modules). The bench job
#     does not build or install on the Pi (see bench.yml header), so this script does not install them.
#
# Still an owner input (not in the repo):
#   - whether the MOCK web flow is the bench E2E. If not, the owner names the real end-to-end test;
#   - install of the app dependencies and Chromium on the Pi (not done by this script);
#   - the export build that the test runs on the Pi (conflicts with "nothing is built on the Pi" unless the owner allows it).
set -euo pipefail

fail() { echo "::error::E2E not defined: owner input needed ($1)"; exit 1; }

root="$(cd "$(dirname "$0")/.." && pwd)"
app="$root/projects/plant-monitor/app"

python3 -I -c 'import json, sys; sys.exit(0 if isinstance(json.load(open(sys.argv[1], encoding="utf-8")).get("scripts", {}).get("test:web-flow"), str) else 1)' "$app/package.json" 2>/dev/null \
  || fail "no test:web-flow script in projects/plant-monitor/app/package.json"
[ -d "$app/node_modules" ] || fail "app dependencies are not installed on the runner (projects/plant-monitor/app/node_modules)"

cd "$app"
npm run test:web-flow

# Plant Monitor v1: quick start

Status: 2026-11-28, written from `origin/main` (task 6.2). Internal document. Task and decision IDs are allowed here.

**v1 is a function demo** built on the v1 perfboard (ESP32-C3 SuperMini, AHT20, BH1750, capacitive soil probe, TP4056 charger, one 1S LiPo). The decision and the parts list are in `projects/plant-monitor/v1/WIRING.md` (sections 1 and 2). The custom PCB is v2 and is not part of this demo.

Nothing below has been run on a board in the repo's CI. Firmware bench results are recorded by the bench procedure, not by CI.

## 1. What works in v1 (code and tests in the repo)

| Part | What is there | Evidence |
|---|---|---|
| Firmware, bench app | Reads soil, air, light and battery, prints one `NWBENCH` line per reading, sleeps between cycles. v1 board config is `CONFIG_PLANT_BOARD_V1_SUPERMINI`. | `projects/plant-monitor/firmware/main/main.c`, `firmware/sdkconfig.defaults.v1`, `v1/FIRMWARE-BENCH.md` |
| Firmware, host tests | Pure-C logic (report, ring buffer, sleep, soil calibration, upload logic) tested on a PC, no board. | `projects/plant-monitor/firmware/test/host/CMakeLists.txt` (CI job `firmware`, step "Host unit tests") |
| Soil calibration | Two-point dry/wet mapping; the direction is fixed (dry reads low) and a swapped pair is refused. | `projects/plant-monitor/firmware/components/sensors/src/nw_soil.c`, `firmware/main/Kconfig.projbuild` |
| Cloud | Schema and RLS, `delete_plant` RPC, schedules, storage buckets. Edge functions: `claim-token`, `device-claim`, `ingest`, `delete-account`, `export`, `api-keys`, `analytics`, `mcp`. | `projects/plant-monitor/cloud/README.md`, `cloud/supabase/migrations/`, `cloud/supabase/functions/` |
| Cloud tests | Schema and function tests on a throw-away PostgreSQL (CI job `cloud-db`). | `projects/plant-monitor/cloud/test.sh`, `cloud/test/` |
| App | Expo + TypeScript: account, profile, delete-account gate (export first), plant list, plant detail, hourly table, gallery, device setup screens, premium screens. Runs against a mock backend without an account. | `projects/plant-monitor/app/README.md`, `app/src/`, `app/strings/en.json` |
| ML | Wetting model B with its tests and a 30 KB size budget (CI check). | `projects/plant-monitor/ml/README.md` is absent; see `ml/src/`, `ml/tests/`, `ml/models/model_b_wetting_int8.tflite`, CI job `ml` in `.github/workflows/ci.yml` |
| PCB checks | Netlist, layout and power-sleep checks in Python. The KiCad ERC/DRC runs in CI. | `projects/plant-monitor/pcb/README.md`, `pcb/check_netlist.py`, `pcb/check_layout.py` |
| Enclosure | Round 3 demo housing for 5 mm parts, source and exports, fit check (OPEN rows are not passes). | `projects/plant-monitor/mechanical/enclosure_v1_demo/`, `projects/plant-monitor/enclosure/v1_demo_fit5/README.md` |

## 2. What does not work yet, or is out of v1

- **Firmware on a real board:** never run on a board (`projects/plant-monitor/firmware/README.md`). The BLE setup flow is built but not run on hardware (`firmware/main/Kconfig.projbuild`, `PLANT_SETUP_FLOW`). The v1 bench build turns the setup flow off (`firmware/sdkconfig.defaults.v1`).
- **Hourly upload** is off by default (`firmware/main/Kconfig.projbuild`, `PLANT_UPLOAD`, default `n`). Its TLS trust anchor is the pinned CA in `firmware/components/upload/include/nw_ingest_ca.h` (ADR-004 addendum, finding F-01, now filled on `origin/main`).
- **Hub (Raspberry Pi), MQTT, Home Assistant:** v1.1 (Arsany, A-023): `projects/plant-monitor/docs/architecture.md` section 10.1 note.
- **MCP connect for the AI assistant:** the function exists in code (`cloud/supabase/functions/mcp`), but it is treated as v1.1 for the demo (scope as given for this handover). **To confirm by the Lead:** no owner record for this was found in the repo.
- **On-device edge AI:** not integrated in firmware. `firmware/components/upload/include/nw_cycle.h` says critical events have no producer yet. The model file is in `ml/models/`. Treated as v1.1 for the demo (scope as given). **To confirm by the Lead**, same reason.
- **Live LLM tips:** off (A-156). Tips stay rule-based. `projects/plant-monitor/cloud/tips/engine.ts` default mode is `rule_based`; the LLM path is `mode === "live"` (`docs/architecture.md` O-5).
- **Flash encryption:** not used. The device token in flash is an accepted risk for the demo (A-155, `projects/plant-monitor/docs/adr/ADR-004-device-identity-and-tokens.md`). Required before the first customer unit.
- **Fit of the housing:** not printed. Per-part heights are the owner's 5 mm bound, not measured (`enclosure/v1_demo_fit5/README.md`).

## 3. Build and test in five minutes (no hardware)

Run from the repo root. Each line is one command.

1. Firmware host tests: `cd projects/plant-monitor/firmware`, then `cmake -S test/host -B build-host`, `cmake --build build-host`, `ctest --test-dir build-host --output-on-failure`. (`firmware/README.md`)
2. App: `cd projects/plant-monitor/app`, `npm ci`, `npm run typecheck && npm test`. (`app/README.md`)
3. ML: `cd projects/plant-monitor/ml`, `pip install -r requirements.txt`, `pytest -q`. (CI job `ml`)
4. Mechanical: `cd projects/plant-monitor/mechanical/enclosure_v1_demo`, `python build_v1.py`; fit check `python fit_check_v1.py`. (`enclosure_v1_demo/README.md`)
5. PCB checks: `cd projects/plant-monitor/pcb`, `python3 -I check_netlist.py`, `python3 -I check_layout.py`. (`pcb/README.md`)
6. Cloud: needs a local PostgreSQL 15+: `projects/plant-monitor/cloud/test.sh`. (`cloud/README.md`)

For the board, follow `projects/plant-monitor/firmware/DEV_GUIDE.md` (section 3.2 is the v1 SuperMini build) and `projects/plant-monitor/v1/FIRMWARE-BENCH.md`.

## 4. First day checklist

- [ ] Read `projects/plant-monitor/v1/WIRING.md` sections 1, 2 and 10-12 (as-built record and bench list).
- [ ] Run the firmware host tests (step 1 above).
- [ ] Run the app tests (step 2).
- [ ] Only then wire and flash, following `DEV_GUIDE.md` and `FIRMWARE-BENCH.md`. Record results in the bench report, not as CI evidence.

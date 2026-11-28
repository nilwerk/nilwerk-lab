# Plant Monitor: handover index (v1)

Status: 2026-11-28, from `origin/main` (task 6.3). Internal document. Paths are relative to the repo root; the project root is `projects/plant-monitor/`. Start with `v1-quickstart.md` and `v1-architecture.md` in this folder.

## Folder map

| What | Folder | Start with | Build or test |
|---|---|---|---|
| Firmware (ESP32-C3, ESP-IDF v5.4) | `projects/plant-monitor/firmware/` | `firmware/README.md`, `firmware/DEV_GUIDE.md` | host: `cmake -S test/host -B build-host`, `cmake --build build-host`, `ctest --test-dir build-host --output-on-failure`. Board: `DEV_GUIDE.md` section 3 (v1 build in 3.2). CI job `firmware` |
| v1 perfboard (wiring, bench) | `projects/plant-monitor/v1/` | `v1/WIRING.md`, `v1/FIRMWARE-BENCH.md` | `python3 v1/gen_wiring.py --check` (WIRING generated tables) |
| App (Expo, TypeScript) | `projects/plant-monitor/app/` | `app/README.md`, `app/TRY_IT.md` | `npm ci`, `npm run typecheck && npm test`; web on the mock: `EXPO_PUBLIC_MOCK_AUTH=1 npx expo start --web`. CI job `app` |
| Cloud (Supabase: schema, edge functions, tips, analytics) | `projects/plant-monitor/cloud/` | `cloud/README.md` | `cloud/test.sh` (needs PostgreSQL 15+). Tips: `node --experimental-strip-types --test tips/test/tips.test.ts`. CI jobs `cloud`, `cloud-db`, `cloud-mutation` |
| Interface contracts (source of truth) | `projects/plant-monitor/docs/interfaces/` | `docs/interfaces/README.md`, `db-schema.sql`, `openapi.yaml` | CI job `interfaces` (JSON schema and YAML checks) |
| ML (wetting model, data, reports) | `projects/plant-monitor/ml/` | `ml/src/`, `ml/data-cards/`, `ml/reports/` | `pip install -r requirements.txt`, `pytest -q`; model size budget 30 KB (CI job `ml`) |
| PCB (KiCad schematic and layout, generated) | `projects/plant-monitor/pcb/` | `pcb/README.md`, `pcb/layout-brief.md` | `python3 -I check_netlist.py`, `python3 -I check_layout.py`; ERC/DRC in CI job `pcb` (KiCad 9) |
| Enclosure, v1 demo (CadQuery source) | `projects/plant-monitor/mechanical/enclosure_v1_demo/` | `enclosure_v1_demo/README.md` | `pip install cadquery trimesh numpy matplotlib networkx pytest`; `python build_v1.py`; `python fit_check_v1.py` |
| Enclosure, v1 demo (exports and renders) | `projects/plant-monitor/enclosure/` (`v1_demo`, `v1_demo_compact`, `v1_demo_fit5`) | the `README.md` in each folder | exports come from the source above; do not edit by hand |
| Enclosure v3 (stopped, 4.E3) | `projects/plant-monitor/mechanical/enclosure_v3/`, `enclosure/v3/` | `enclosure/v3/` README | kept for reference; not for v1 |
| Hardware data (BOM, power budget) | `projects/plant-monitor/hardware/` | `hardware/bom/`, `hardware/power-budget/power-budget.md` | `python -m unittest discover -v` in `hardware/power-budget` (CI job `powerbudget`) |
| Tests and QA | `projects/plant-monitor/tests/` | `tests/test-plan.md`, `tests/acceptance-matrix.md` | results in `tests/results/`; bench procedures in `tests/procedures/` |
| Architecture and decisions | `projects/plant-monitor/docs/` | `docs/architecture.md`, `docs/adr/` (ADR index in `v1-architecture.md`) | none |
| Requirements | `projects/plant-monitor/docs/` | `docs/requirements-v1.0-delta.md`, `tests/acceptance-matrix.md` | none |
| Work orders for hardware (Peter) | `projects/plant-monitor/docs/work-orders/` | `WO-firmware-4.F1.md` | none |

## Where each part is in CI

The workflow is `.github/workflows/ci.yml`. Jobs and what they check:

- `firmware`: ESP-IDF build for esp32c3 and host unit tests (`firmware/test/host`).
- `firmware-sim`: QEMU boot check with mocked sensors (`firmware/tests/qemu_boot_check.sh`).
- `app`: lint, `tsc --noEmit`, `npm test`.
- `cloud`: Deno lint and typecheck of the edge functions.
- `cloud-db`: `cloud/test.sh` on a migrated PostgreSQL.
- `cloud-mutation`: mutation suite for the cloud tests.
- `ml`: pytest and the model size budget.
- `pcb`: layout checks, ERC/DRC and fabrication exports in a KiCad 9 container.
- `sim`: ngspice checks (`pcb/sim`).
- `mechanical`: CadQuery build and geometry tests.
- `interfaces`: contract checks.
- `powerbudget`, `costs`: Python unit tests.
- `bench-tests`: shell tests for the bench scripts.

Each job runs only when its path changed (job `detect`).

## Who owns what (roles)

Roles and owners are in `team/roles/` and `team/TEAM.md` (section 2). Human decisions are in the Needs Arsany list and recorded in `projects/plant-monitor/docs/adr/` (for example ADR-016).

## Open items to hand over

- Bench run of the firmware on the v1 perfboard (`v1/FIRMWARE-BENCH.md`, `tests/procedures/`).
- Per-part heights for the enclosure (`enclosure/v1_demo_fit5/README.md`, owner caliper inputs).
- Confirm MCP and on-device edge AI are v1.1 (see `v1-quickstart.md` section 2).
- Remaining app work on the real backend and the device setup on a phone (`app/README.md`).

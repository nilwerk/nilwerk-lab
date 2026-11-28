# Plant Monitor v1: architecture summary (as built in the repo)

Status: 2026-11-28, from `origin/main` (task 6.2). Internal document. The full design is `projects/plant-monitor/docs/architecture.md`; this page says what the code does for v1 and which parts are v1.1.

## 1. Data path for v1

```
ESP32-C3 SuperMini (perfboard)
  sensors (soil, AHT20, BH1750, battery)  -> firmware/components/sensors/
  report, ring buffer, sleep              -> firmware/components/report/, storage/, power/
  hourly upload (OFF by default)          -> firmware/components/upload/ (POST /ingest, bearer device token, pinned CA)
        |
        v  HTTPS
Supabase EU: edge functions               -> cloud/supabase/functions/
  ingest, device-claim, claim-token, delete-account, export, api-keys, analytics, mcp
  Postgres with RLS on every table        -> cloud/supabase/migrations/
        |
        v  HTTPS, user JWT (RLS)
App (Expo, TypeScript)                    -> app/src/
  plants, detail, gallery, premium, setup, profile
```

- Device side: one reading per 15 min, a 24 h buffer, one upload per hour when the upload build is on (`firmware/main/Kconfig.projbuild`, `PLANT_UPLOAD`). Source of the timing constants: `firmware/components/power/src/nw_sleep.c` and `firmware/components/upload/include/nw_upload.h`.
- Device identity: a per-device bearer token, stored hashed in the database (`cloud/README.md`, edge function `device-claim`). The token is stored in flash without flash encryption: accepted risk for the demo (A-155, ADR-004).
- Transport to the cloud: HTTPS only. The upload trusts only the pinned CA in `firmware/components/upload/include/nw_ingest_ca.h` (the ESP-IDF bundle is not used, ADR-004 addendum).
- Premium: a server-side flag on the profile (`profiles.is_premium`, `cloud/README.md`, ADR-008). The app mirrors it and the server decides (`app/src/screens/ProfileScreen.tsx`).
- Tips: `cloud/tips/` is a pure module with the rule layer; default mode `rule_based` (`cloud/tips/engine.ts`). No `/tips` endpoint yet (`cloud/README.md`, care-tips section). Live LLM mode is off (A-156).
- Delete: the app's delete-account gate requires export first (`app/src/export/`, `cloud/supabase/functions/delete-account`).

## 2. What is v1.1 (not in the demo)

| Item | Where it is decided or described | State in the repo |
|---|---|---|
| Raspberry Pi hub, MQTT, local dashboard, Home Assistant bridge | `docs/architecture.md` section 10.1 note (A-023); ADR-012, ADR-010 | Design and contract (`docs/interfaces/hub-mqtt.md`); not built |
| MCP connect for the AI assistant | ADR-007; `cloud/supabase/functions/mcp` | Function in code; treated as v1.1 for the demo. **Lead to confirm** |
| On-device edge AI | ADR-001; `firmware/components/upload/include/nw_cycle.h` | Not integrated in firmware; model in `ml/models/`. Treated as v1.1 for the demo. **Lead to confirm** |
| OTA with signed images | ADR-009; `docs/architecture.md` O-3, O-15 | OTA code exists (`firmware/components/ota/`); signing not planned for v1 |

## 3. ADR index

Status as written in each ADR file (`projects/plant-monitor/docs/adr/`). Files ADR-001 to ADR-018.

| ADR | Title | Status | File |
|---|---|---|---|
| 001 | ESP32-C3-MINI-1, ESP-IDF, on-device TFLite Micro | Accepted for G2 review | `ADR-001-device-platform-and-edge-ai.md` |
| 002 | BLE provisioning with proof-of-possession and one-time claim token | Accepted for G2 review; amended by ADR-011 | `ADR-002-ble-provisioning-and-claim.md` |
| 003 | Supabase EU as the standalone backend; ingest as an edge function | Accepted | `ADR-003-supabase-backend-and-ingest.md` |
| 004 | Per-device bearer token, stored hashed | Accepted for G2 review; addendum 2026-11-28 (A-155, pinned CA) | `ADR-004-device-identity-and-tokens.md` |
| 005 | React Native (Expo) + TypeScript, supabase-js under RLS | Accepted | `ADR-005-mobile-app-expo.md` |
| 006 | Tips = weather API + LLM API + deterministic safety rules | Proposed for G2 | `ADR-006-tips-engine-claude-with-guardrails.md` |
| 007 | MCP server as an edge function with personal API keys | Accepted for G2 review | `ADR-007-mcp-server.md` |
| 008 | Premium is a server-side per-user flag, no payments | Accepted | `ADR-008-premium-flag.md` |
| 009 | OTA via ingest manifest, dual slot, rollback; models in own partition | Accepted for G2 review | `ADR-009-ota-and-model-updates.md` |
| 010 | Optional Home Assistant bridge as a cloud-side MQTT publisher | Proposed | `ADR-010-home-assistant-bridge.md` |
| 011 | BLE-only setup with encrypted credential provisioning; Wi-Fi-only operation | Accepted (A-080) | `ADR-011-ble-provisioning-encrypted-credentials.md` |
| 012 | Raspberry Pi local hub | Proposed | `ADR-012-raspberry-pi-local-hub.md` |
| 013 | Data model and API conventions | Proposed for G2 | `ADR-013-data-model-and-api-conventions.md` |
| 014 | App palette, brand mark and status colours | Accepted (A-040) | `ADR-014-app-palette-and-brand-mark.md` |
| 015 | NFR-01 flexed: scenario-based battery life | Accepted (A-051) | `ADR-015-nfr-01-flexed-scenario-based-battery-life.md` |
| 016 | Owner decisions A-105, A-106, A-107 | Accepted (2026-11-17) | `ADR-016-owner-decisions-A105-A107.md` |
| 017 | Setup "save plant" as one RPC, and the plant check in devices_update_own | Accepted (merged 2026-11-22) | `ADR-017-setup-save-plant-rpc-and-device-link-policy.md` |
| 018 | Per-plant daily series in GET /analytics | Proposed (contract only; nothing built) | `ADR-018-analytics-daily-series.md` |

## 4. Requirement IDs

FR and NFR IDs and their criteria are in `projects/plant-monitor/tests/acceptance-matrix.md` (tables 1 and 2). The v1.0 changes are in `projects/plant-monitor/docs/requirements-v1.0-delta.md`. The traceability table is `projects/plant-monitor/docs/traceability.md`.

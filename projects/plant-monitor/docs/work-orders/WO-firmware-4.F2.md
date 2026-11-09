# [WO-xxx] DRAFT - Bench test of BLE setup mode (task 4.F2) - NOT READY TO ISSUE

Draft by Mira (Firmware + Edge AI) for Nora (TEAM.md section 12). Theo checks it before it is opened. The WO number is Nora's.

**Why this is a draft and cannot be issued yet.** The 4.F2 slice contains the setup state machine, the protocol rules and the NVS store, tested on a PC only (`firmware/components/provisioning/`). It contains **no BLE stack glue** (ESP-IDF `wifi_provisioning` + NimBLE, security 2, the `nw-claim` / `nw-status` endpoints wired to `nw_prov_on_claim` / `nw_prov_status_json`), and `main.c` does not call it. There is nothing on a board to test until that glue slice exists. Issue this work order after the glue is merged and its PR says "builds in CI". **Nothing here has run on hardware.**

## Why
Prove on a real board that setup mode starts on first boot and on button hold, that the phone can find it, that a wrong code is refused 5 times and then setup ends, and that credentials survive a reboot (FR-D03, FR-D07, FR-D09, NFR-06; contract `docs/interfaces/ble-provisioning.md`).

## Inputs (what you get)
- Firmware binary + flashing steps from the glue PR (to be linked by Mira); dev kit ESP32-C3-DevKitM-1; USB cable.
- Contract: https://github.com/nilwerk/nilwerk-lab/blob/main/projects/plant-monitor/docs/interfaces/ble-provisioning.md (service UUID `b53672dd-5227-40a0-8b6f-6f836f8a584c`, advertised name `NW-<last 6 hex of hw_id>`).
- Phone with Bluetooth; the free app "nRF Connect" (to see the advertisement). ESP-IDF `esp_prov.py` on a PC with Bluetooth is optional (check the exact security-2 arguments in the ESP-IDF v5.4 docs first; Mira has not verified them).
- Buttons: the dev kit BOOT button (GPIO9, per Theo's review, unverified on the board) stands in for the pinhole button until the custom board exists.

## Steps (to be completed by Mira when the glue exists; skeleton)
1. Flash a board whose flash was fully erased (`idf.py erase-flash flash monitor`). Expected log line on boot: setup mode, BLE advertising (exact text comes from the glue slice).
2. In nRF Connect: scan, find `NW-xxxxxx`, note the full name and whether service `b53672dd-...` is listed. Photo of the screen.
3. Do NOT complete setup. Connect with a wrong code 5 times (app or `esp_prov.py`). Expected: after the 5th, the advertisement disappears. Note the time.
4. Reset the board (not erase). Expected: setup mode again (no credentials stored). Wait 5 minutes without connecting. Expected: advertisement disappears at 5:00 (+- a few seconds). Note the measured time.
5. After a successful provisioning (needs the app or Arsany's test claim token), reset: expected NO advertisement (normal mode, FR-D09). Hold BOOT 3 s at power-up: advertisement is back and the stored Wi-Fi is kept. Hold 10 s: stored data wiped, setup mode (FR-D07).
6. Report the measured hold times that felt right: the 3 s / 10 s values are proposals.

## Expected output
Table: step, expected, observed, PASS/FAIL; 2-3 photos (nRF Connect screen, serial log); one 10-20 s video of step 5; OK to use publicly (TEAM.md section 13).

## Acceptance criteria
1. Setup mode on first boot and on 3 s hold (FR-D03). 2. Advertised name matches `NW-` + last 6 hex of hw_id (contract section 1). 3. 5 wrong codes end setup (ADR-011). 4. 5 minutes ends setup (ADR-011). 5. BLE not advertising in normal mode (FR-D09). 6. Factory reset wipes the record (FR-D07).

## Acceptance criteria for the BLE glue slice (draft; the glue PR must show each item in its tests or PR text)
Not started. Source: Theo's review (PR #66, issuecomment-6734214782, C2-C4) and Ines's QA (issuecomment-6741609811). These are the conditions the glue PR must meet before it can be merged.
1. **In-flight timeouts (Theo C2).** The glue starts a Wi-Fi join timeout and an HTTP timeout for `POST /device-claim`. When one fires it calls `nw_prov_on_wifi_result(..., NW_PROV_WIFI_TIMEOUT)` or `nw_prov_on_claim_result(..., NW_PROV_CLAIM_NETWORK)`. `nw_prov_tick` does not time out WIFI_CONNECTING or CLAIMING, so these two timers are the only bound. Host test: a fake that never answers ends in `wifi_failed/timeout` or `claim_failed/network`, never in a hang. Timer values are set in the glue PR and marked as proposals until a bench check.
2. **`claim_post` carries `hw_id` and `fw` (Theo C3).** The body must contain `hw_id` (pattern `^nw-[0-9a-f]{12}$`), `claim_token`, `name` and `fw` (max 32 chars), as `projects/plant-monitor/docs/interfaces/openapi.yaml` requires (`required: [hw_id, claim_token, fw]`, `additionalProperties: false`). Host test checks each field in the request body.
3. **HTTP to app reason mapping (Theo C3).** `200` gives `NW_PROV_CLAIM_OK` and stores the 64-hex `device_token`. `401` gives `TOKEN_INVALID` (`claim_token_invalid`). `409` gives `DEVICE_OWNED` (`device_owned`). `400`, `413` (`payload_too_large`), `429` (`rate_limited`; openapi marks it "not in 4.B2") and `500` give `CLAIM_SERVER` (`server`). A transport failure, TLS error or timeout gives `CLAIM_NETWORK` (`network`). Any other status also gives `server`. Every case has a host test, so the app never receives an unmapped reason.
4. **Behaviour after `CLOSED` (Theo C4; NFR-01 battery budget).** `CLOSED` on a never-provisioned device has no exit except the button. The glue PR states what the device does next (deep sleep until the button, or another rule), and BLE and Wi-Fi are off in that state (FR-D09). The PR includes a per-state current table (setup mode, CLOSED, normal) marked as datasheet-sourced or estimate, and shows the effect on the NFR-01 budget (at least 3 months, typical case). Setup-mode current is only an estimate until measured.
5. **Traceability of the 5-attempt / 5-minute limits.** The glue PR cites ADR-011 (Proposed) for them, not NFR-03. NFR-03 is the 3-minute setup budget, and the 5-minute window is not reconciled with it yet (open point for the Lead).
6. **Scope.** The glue does not change the state machine logic or the button hold times (3 s / 10 s, proposals). nw-hub (A-023) and real OTA stay out of scope. If a state-machine change is needed, it goes in a separate PR.

## Due / How to report / Glossary
Set by Nora when issued. Report in the issue; BLOCKED after 4 hours. Glossary: PoP = proof of possession, the 8-character code on the sensor label; NVS = non-volatile storage, the small key-value area in flash; advertising = the board announcing itself over Bluetooth.

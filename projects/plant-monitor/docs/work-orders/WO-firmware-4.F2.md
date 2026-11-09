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

## Due / How to report / Glossary
Set by Nora when issued. Report in the issue; BLOCKED after 4 hours. Glossary: PoP = proof of possession, the 8-character code on the sensor label; NVS = non-volatile storage, the small key-value area in flash; advertising = the board announcing itself over Bluetooth.

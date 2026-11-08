# 4.A3 Device setup flow: find sensor, connect, Wi-Fi, name, photo, plant details (UI only, against a fake sensor)

**What it shows:** the six setup screens of the app in the aligned brand set (S10 find, S11 connect, S12 Wi-Fi, S13e Wi-Fi error, S14 photo, S15 plant details with plain errors, S16 done with the setup timer), 390 px web export against an in-memory fake sensor. No Bluetooth, no hub step (hub pairing is v1.1, A-023). The code talks to a `ProvisioningService` interface; the real BLE version is a later slice that needs a dev build. `test-output.txt` has the typecheck and the passing tests.

- Task: 4.A3 (UI skeleton) · Persona: Leo (Full-stack Developer) · Requirements: FR-A03, FR-D03, FR-A04, FR-A05, FR-A02, FR-D02, NFR-03
- Stacked on `agent/fullstack/a052-legal-line`, which is stacked on `agent/fullstack/a048-contact` (PR #52): merge order #52, A-052, then this.
- Mutants checked (each fails a test): Wi-Fi password kept in state after linking, setup closes after 6 instead of 5 wrong codes, cancelled camera treated as a photo
- Agent minutes and human estimate: see PR text (about 35 min agent time, about 3 days of human work incl. design review)
- Unverified: never run with Bluetooth or on a phone; the "0:07" timer in the done screenshot is a scripted run, not a measured first-time user; Wi-Fi password field is a plain secure text input (no OS keychain/autofill test); screens follow the wireframes S10-S16 text but were not compared pixel by pixel; the BLE service UUID is TBD in the contract.

# 4.A3b slice 1: real BLE ProvisioningService (code + mock tests, no hardware)

**What it shows:** `test-output.txt` is the real output of `tsc --noEmit` and `jest` (261 tests, 20 suites green; 41 of them are new for the real BLE service, the library glue and the claim API) plus four mutation-style checks and the `expo prebuild` permission result. No screenshots: nothing visual changed.

- Task: 4.A3b slice 1 · Persona: Leo (Full-stack Developer) · PR: "[4.A3b] Slice 1: real BLE ProvisioningService (dev build)" (branch `agent/fullstack/4.A3b-real-ble-slice1`)
- Requirements: FR-A03, FR-D03, FR-D07, NFR-06. Library: `@orbital-systems/react-native-esp-idf-provisioning` 0.7.1; `expo-dev-client` ~58.0.21.
- **Not hardware-verified, anywhere.** No dev build was compiled, nothing ran on a phone or a sensor; test 5.5 is NOT done and 4.A3 is not Done. Library vs React Native 0.88 compatibility is UNVERIFIED (peer deps are `*`, library built on 0.84). SRP user name `wifiprov` is a proposal not in the contract.

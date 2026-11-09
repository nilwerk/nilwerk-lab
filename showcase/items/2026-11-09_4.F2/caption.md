# 4.F2 Setup flow (BLE provisioning): state machine and protocol rules, tested on a PC, not on a board

What it shows: the sensor-side setup logic (setup mode on first boot or button hold, 5 wrong codes or 5 minutes end it, Wi-Fi + name + claim token accepted and kept on the device only) passing 530 host checks, with 45 deliberate code mutations all caught and a drift check against the app's contract.

- Task: 4.F2 (Firmware: setup flow), PR: PR_URL. Persona: Mira (Firmware + Edge AI).
- Agent minutes: AGENT_MIN (own clock, first to last command); the Lead's Agent Log figure wins once logged.
- Own human-hour estimate: about 14 h for an experienced embedded engineer (state machine, strict JSON/UTF-8 parser, NVS adapter, 530 checks, mutation harness, contract check, work-order draft).
- Unverified: nothing ran on hardware. No BLE stack glue exists yet (separate slice), so setup cannot be run on a board. The ESP-IDF build of the new component is only proven when CI's `firmware` job is green (see PR). Button hold times (3 s / 10 s) are proposals. The flash/RAM figures in the PR are estimates.

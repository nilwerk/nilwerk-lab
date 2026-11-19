# 4.F3 slice 3: the ESP-IDF upload adapter, and the logic around it tested on a PC

**What it shows:** the host-test log (`host-tests-output.txt`) for the new one-wake cycle (`nw_cycle.c`): stored-credential validation, sensor-to-sample mapping, the 15-minute / hourly cadence over a simulated 24 h (24 reports, 60 min apart), a 5 h outage followed by a `reconnect` report that drains the buffer, and the low-battery rules. 134 checks in `test_cycle`, 40 of 40 mutants killed, 21 of 21 ctest entries pass. The Wi-Fi / SNTP / HTTPS code itself (`nw_upload_idf.c`) is behind `CONFIG_PLANT_UPLOAD` (default off) and is not in this log.

- Task: 4.F3 (slice 3), persona: Mira (Firmware + Edge AI), branch `agent/firmware/4.F3-adapter`, PR: see the PR list for this branch.
- Agent minutes and human-hour estimate: in the PR description.
- Unverified: `nw_upload_idf.c` was never compiled (no ESP-IDF in the session; first compile is CI's new upload build step) and never run on hardware; no real server was contacted; a unit cannot be provisioned today, so no token can reach the NVS; RTC retention, current draw and several ESP-IDF API details are marked `[verify]` in the code.

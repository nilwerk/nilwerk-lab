# 4.F1 v1 bench firmware check

**What it shows:** the host-test run (text log `host-tests-output.txt`) for the new v1 SuperMini board option: board.h pins are checked against the WIRING.md section 3 pin table, the v1 build defaults are checked, and a guard fails CI if a real PLANT_API_BASE_URL is ever committed. 15 of 15 host tests pass, including the 10 existing ones.

- Task: 4.F1 (v1 slice), persona: Mira (Firmware + Edge AI), branch `agent/firmware/4.F1-v1-bench`, PR: see the PR list for this branch.
- Agent minutes: not yet logged in the Agent Log. Human-hour estimate by the agent: about 5 h.
- Unverified: nothing was built for the ESP32-C3 (no ESP-IDF toolchain in the authoring session; CI builds it), nothing ran on hardware, the bench serial output in `projects/plant-monitor/v1/FIRMWARE-BENCH.md` is read from the source, not observed.

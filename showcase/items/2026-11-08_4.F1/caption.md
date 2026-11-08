# 4.F1 Sensor drivers: first firmware slice, tested on a PC, not on a board

What it shows: the AHT20, BH1750, soil-probe calibration and battery-divider logic written behind a small hardware layer so that 41 deliberate code mutations are caught by the host tests, plus a bench procedure for Peter.

- Task: 4.F1 (Firmware: sensor drivers), PR: to be opened by Arsany/Lead, branch `agent/firmware/4.F1`. Persona: Mira (Firmware + Edge AI).
- Agent minutes: see Agent Log (measured by the Lead).
- Own human-hour estimate: about 10 h for an experienced embedded engineer (drivers, host tests with mutation check, pin cite check, bench procedure).
- Unverified: nothing ran on hardware. The ESP-IDF layer (`hal_esp32.c`, `main.c`) was not compiled by the author (no ESP-IDF toolchain in the session); CI is the first build. Soil calibration values in Kconfig are placeholders. No datasheet was re-read for current figures.

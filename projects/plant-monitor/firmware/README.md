# Plant Monitor firmware

ESP-IDF v5.4 firmware (C) for the ESP32-C3. Today it is a sensor bench app: it prints the five readings (soil, temperature, humidity, light, battery) as `NWBENCH` lines and deep-sleeps for 60 s after 5 lines. It has never run on a board. With the opt-in `CONFIG_PLANT_UPLOAD` build (default off) it also buffers 96 samples in RTC memory, reports hourly and deep-sleeps; that path is host-tested and CI-compiled only, never run on a board (see DEV_GUIDE 7.4).

**New here? Start with the [developer guide](DEV_GUIDE.md)**: install ESP-IDF, pick the board config (DevKitM-1 or v1 SuperMini), build, flash, run the PC tests, first-run bench check, troubleshooting, and how to report results.

| | |
|---|---|
| PC tests (no hardware) | from this folder, one command per line (no `&&`, so Windows PowerShell 5.1 works too; on Windows use the "ESP-IDF 5.4 PowerShell"): see below |
| v1 perfboard docs | [`../v1/WIRING.md`](../v1/WIRING.md), [`../v1/FIRMWARE-BENCH.md`](../v1/FIRMWARE-BENCH.md) |
| Pin map (the truth) | [`main/board.h`](main/board.h) |
| Never commit | secrets, tokens, the real `PLANT_API_BASE_URL` (guide section 7) |

PC tests, run from this folder, one line at a time:

```
cmake -S test/host -B build-host
cmake --build build-host
ctest --test-dir build-host --output-on-failure
```

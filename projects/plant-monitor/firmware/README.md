# Plant Monitor firmware

ESP-IDF v5.4 firmware (C) for the ESP32-C3. Today it is a sensor bench app: it prints the five readings (soil, temperature, humidity, light, battery) as `NWBENCH` lines and deep-sleeps for 60 s after 5 lines. It has never run on a board.

**New here? Start with the [developer guide](DEV_GUIDE.md)**: install ESP-IDF, pick the board config (DevKitM-1 or v1 SuperMini), build, flash, run the PC tests, first-run bench check, troubleshooting, and how to report results.

| | |
|---|---|
| PC tests (no hardware) | `cmake -S test/host -B build-host && cmake --build build-host && ctest --test-dir build-host --output-on-failure` |
| v1 perfboard docs | [`../v1/WIRING.md`](../v1/WIRING.md), [`../v1/FIRMWARE-BENCH.md`](../v1/FIRMWARE-BENCH.md) |
| Pin map (the truth) | [`main/board.h`](main/board.h) |
| Never commit | secrets, tokens, the real `PLANT_API_BASE_URL` (guide section 7) |

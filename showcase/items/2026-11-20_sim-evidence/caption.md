# Simulator evidence: app web flow and firmware boot (mocked sensors)

**What it shows.** The app's main screens run in a headless browser against a fake Bluetooth scan and fixed test readings, and the firmware boots in Espressif's ESP32-C3 simulator and prints five mock sensor readings. Every screen with fake data carries a MOCK label. Nothing here is real sensor data, real Bluetooth, or a real phone.

**Task.** Simulator tests, no Plan task ID yet (to be assigned Monday).

**Images.** 01 welcome, 02 sign-up error, 03 profile with fake sensor scan, 04 plant list, 05 plant detail (all web build, stand-in backend). 06 firmware boot log rendered from the simulator serial output.

**Caveats.** The firmware simulator image is v1 with a sim overlay (serial on UART0, mock sensors), not the exact bench image. QEMU has no USB serial, so the bench console is not simulated. The app runs on a web build, not a phone.

**Time.** Agent minutes: app ~6.5, firmware ~18.5 (incl. toolchain install). Own human estimates: app ~4 h, firmware ~4 h.

**Unverified.** Real Bluetooth pairing, real sensors and soil probe, Wi-Fi, deep-sleep wake, live Supabase, phone builds.

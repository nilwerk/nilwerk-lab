# Firmware tests

## QEMU boot check (simulator, mocked sensors): `tests/qemu_boot_check.sh`

Boots the v1 SuperMini image in Espressif's QEMU ESP32-C3 model and checks the boot lines and the sensor code path.
Simulator only: no board, no sensors, no Wi-Fi, no BLE.

Run from any shell with ESP-IDF v5.4 loaded (`. $IDF_PATH/export.sh`):

```
tests/qemu_boot_check.sh                  # build the simulator image, run 45 s, check
tests/qemu_boot_check.sh --no-build       # reuse build-sim-qemu/
tests/qemu_boot_check.sh --log PATH       # also keep the serial log at PATH
```

Exit codes: 0 all checks passed; 1 a boot or sensor check failed; 2 setup problem (no `idf.py`, no QEMU, build failed).

### What the image is

- v1 build (`sdkconfig.defaults` + `sdkconfig.defaults.v1`, board `v1_supermini`) plus `sdkconfig.defaults.sim-qemu`.
- The overlay makes two changes, both needed for QEMU:
  1. Console on UART0. Espressif's QEMU ESP32-C3 has no USB Serial/JTAG model. Measured: the unmodified v1 image printed
     no `NWBENCH` line in a 45 s run (only the bootloader and the app entry line).
  2. `CONFIG_PLANT_SIM_MOCK_SENSORS=y`: the sensor HAL is replaced by `main/sim_mock_hal.c`. Its values are fixed MOCK
     constants, and the log starts with a `NWSIMMOCK ... MOCK ...` line. The drivers still run their own code (CRC, 20-bit
     decoding, lux, soil normalisation, battery divider).

### What the checks prove, and what they do not

- Proves: the image boots to `app_main`, the five-reading loop runs with `err=0` on all drivers, the mock inputs decode to the
  expected values (23.45 C, 41.25 %RH, 250.0 lx, 50.0 % soil, 4200 mV battery), the sleep call is reached, no crash.
- Does not prove: real sensors, I2C/ADC wiring, the ESP-IDF I2C/ADC drivers (`hal_esp32.c`), IO3 (soil power) levels in
  sleep (NFR-12), current draw, timing on hardware, USB console on the SuperMini, Wi-Fi, BLE, OTA.

### Requirements

- ESP-IDF v5.4, `python $IDF_PATH/tools/idf_tools.py install qemu-riscv32` (installs Espressif QEMU 9.0.0 to `~/.espressif`).
- Linux: `apt-get install libslirp0` (QEMU loads it at run time; the tool install check fails without it).
- Run time measured locally: about 45 s run plus build (incremental build about 1 min here).

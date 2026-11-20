#!/usr/bin/env bash
# QEMU boot check for the v1 SuperMini firmware (simulator boot test, sim-qemu). SIMULATOR ONLY, with MOCKED sensor values.
#
# What it does: builds the v1 image plus the simulator overlay (sdkconfig.defaults.sim-qemu), runs it in Espressif's QEMU
# ESP32-C3 for a fixed time, saves the serial log, and checks the boot lines and the sensor code path.
# What it proves: the firmware boots, the driver code decodes the MOCKED sensor inputs to the expected values, the
# loop and the sleep call run. What it does NOT prove: anything about real sensors, wiring, Wi-Fi, BLE, power or the
# ESP-IDF I2C/ADC drivers (see tests/README.md). The sensor values in the log are MOCK values (main/sim_mock_hal.c).
#
# Exit codes: 0 = all checks passed, 1 = a boot/sensor check failed (expected line missing or forbidden line present),
#             2 = setup or build problem (no ESP-IDF, no QEMU, build failed). Exit 2 is not a firmware verdict.
#
# Usage: tests/qemu_boot_check.sh [--no-build] [--run-seconds N] [--log PATH]
# Needs: ESP-IDF v5.4 loaded in this shell (". $IDF_PATH/export.sh"), with qemu-riscv32 installed
#        (python $IDF_PATH/tools/idf_tools.py install qemu-riscv32; on Linux also apt package libslirp0).

set -u -o pipefail

FW_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="build-sim-qemu"
SDKCONFIG="sdkconfig.sim-qemu"
DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.v1;sdkconfig.defaults.sim-qemu"
RUN_SECONDS=45        # boot + 5 readings (~10 s) + sleep line (~1 s) with margin for a slow CI runner
DO_BUILD=1
LOG=""

while [ $# -gt 0 ]; do
    case "$1" in
        --no-build) DO_BUILD=0; shift ;;
        --run-seconds) RUN_SECONDS="$2"; shift 2 ;;
        --log) LOG="$2"; shift 2 ;;
        -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
        *) echo "SETUP: unknown argument: $1" >&2; exit 2 ;;
    esac
done

command -v idf.py >/dev/null 2>&1 || { echo "SETUP: idf.py not found. Load ESP-IDF v5.4 first: . \$IDF_PATH/export.sh" >&2; exit 2; }
cd "$FW_DIR" || { echo "SETUP: cannot enter $FW_DIR" >&2; exit 2; }

if [ "$DO_BUILD" -eq 1 ]; then
    echo "BUILD: idf.py -B $BUILD_DIR (v1 defaults + sdkconfig.defaults.sim-qemu, mocked sensors)"
    if ! idf.py -B "$BUILD_DIR" -DIDF_TARGET=esp32c3 -DSDKCONFIG="$SDKCONFIG" "-DSDKCONFIG_DEFAULTS=$DEFAULTS" build; then
        echo "SETUP: build failed" >&2
        exit 2
    fi
fi

# The image must really be the labelled simulator build (the CI grep trick, see DEV_GUIDE 3.2).
grep -q '^CONFIG_PLANT_SIM_MOCK_SENSORS=y' "$SDKCONFIG" || { echo "SETUP: $SDKCONFIG lacks CONFIG_PLANT_SIM_MOCK_SENSORS=y" >&2; exit 2; }
grep -q '^CONFIG_PLANT_BOARD_V1_SUPERMINI=y' "$SDKCONFIG" || { echo "SETUP: $SDKCONFIG is not the v1 board" >&2; exit 2; }

[ -n "$LOG" ] || { mkdir -p "$BUILD_DIR"; LOG="$FW_DIR/$BUILD_DIR/qemu_boot.log"; }
mkdir -p "$(dirname "$LOG")"

echo "NOTE: sensor values are MOCKED (main/sim_mock_hal.c). This checks the driver code path, not hardware."
echo "RUN: QEMU esp32c3 for ${RUN_SECONDS} s, serial log -> $LOG"
# idf.py qemu generates the flash and eFuse images in the build dir and starts QEMU with the serial port on stdio.
# timeout ends the run after RUN_SECONDS; exit status 124 is the normal end of a run.
timeout "$RUN_SECONDS" idf.py -B "$BUILD_DIR" -DSDKCONFIG="$SDKCONFIG" qemu > "$LOG" 2>&1
run_status=$?
if [ "$run_status" -ne 124 ] && [ "$run_status" -ne 0 ]; then
    echo "SETUP: QEMU run ended with status $run_status (see $LOG)" >&2
    grep -E "is not installed|error while loading|No such file" "$LOG" >&2
    exit 2
fi

# The serial port gives CRLF line endings; the checks below expect plain LF lines.
tr -d '\r' < "$LOG" > "$LOG.lf" && mv "$LOG.lf" "$LOG"

fails=0; passes=0
check() {   # check <name> <extended regex that must match some line>
    if grep -E -q -- "$2" "$LOG"; then
        passes=$((passes + 1)); echo "PASS  $1"
    else
        fails=$((fails + 1)); echo "FAIL  $1   (no line matches: $2)"
    fi
}
forbid() {  # forbid <name> <extended regex that must match no line>
    if grep -E -q -- "$2" "$LOG"; then
        fails=$((fails + 1)); echo "FAIL  $1   (found: $(grep -E -m1 -- "$2" "$LOG"))"
    else
        passes=$((passes + 1)); echo "PASS  $1"
    fi
}

# Boot lines (from main/main.c, expected values from the mock constants in main/sim_mock_hal.c)
check "mock banner (labelled MOCK)"       '^NWSIMMOCK sensors=MOCK fixed values, NOT sensor data'
check "boot line, v1 board, wake 1"       'NWBENCH start board=v1_supermini wake=1 cal_dry=2800 cal_wet=1200 divider=100000/100000'
for i in 0 1 2 3 4; do
    check "reading i=$i, all drivers err=0" "^NWBENCH wake=1 i=$i .*err=soil:0,aht:0,bh:0,bat:0\$"
done
# Sensor code path: the drivers decode the mock inputs to the expected values (every reading must show them)
check "AHT20 decode: 23.45 C, 41.25 %RH"  'temp_c=23\.45 rh_pct=41\.25'
check "BH1750 decode: raw 300 -> 250.0 lx" 'lux=250\.0 lux_raw=300'
check "soil normalise: raw 2000 -> 50.0 %" 'soil_raw=2000 soil_pct=50\.0 soil_flags=0x00'
check "battery: 2100 mV pin -> 4200 mV, plausible" 'vbat_mv=4200 vbat_adc_mv=2100 vbat_plausible=1 divider_na=21000'
check "sleep call reached"                'NWBENCH sleep s=60 '
# Forbidden lines
forbid "no setup flow on the v1 build"    '^NWSETUP'
forbid "no crash / panic"                 'Guru Meditation|abort\(\)|panic'
forbid "no sensor error code"             'err=soil:-|aht:-|bh:-|bat:-'

echo "----"
if [ "$fails" -eq 0 ]; then
    echo "RESULT: PASS ($passes checks). Serial log: $LOG"
    exit 0
fi
echo "RESULT: FAIL ($fails failed, $passes passed). Serial log: $LOG"
exit 1

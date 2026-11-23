#!/usr/bin/env bash
# QEMU setup-flow check (scenario 2 of the simulator summary). SIMULATOR ONLY.
#
# What it does: builds the setup flow image (v1 defaults + setup overlay + sim-setup overlay), runs it in Espressif's QEMU
# ESP32-C3 for a fixed time, saves the serial log, and checks the boot decision and the start path of the setup flow.
# What it proves: on a cold start the firmware opens the setup window and takes the setup-mode path; a boot decision failure or a
# crash is not reported; without security-2 data in NVS the firmware refuses to advertise and says so; the setup flow then ends.
# What it does NOT prove: BLE advertising (QEMU has no Bluetooth), the real NVS record, the real board, its power or its USB
# behaviour. Those need the bench (bench/ble/expect.txt and step c of .github/workflows/bench.yml).
#
# Exit codes: 0 = all checks passed, 1 = a check failed (expected line missing or forbidden line present),
#             2 = setup or build problem (no ESP-IDF, no QEMU, build failed). Exit 2 is not a firmware verdict.
#
# Usage: tests/qemu_setup_check.sh [--no-build] [--run-seconds N] [--log PATH]
# Needs: ESP-IDF v5.4 loaded in this shell (". $IDF_PATH/export.sh"), with qemu-riscv32 installed.

set -u -o pipefail

FW_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="build-sim-setup"
SDKCONFIG="sdkconfig.sim-setup"
DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.v1;sdkconfig.defaults.setup;sdkconfig.defaults.sim-setup"
RUN_SECONDS=40        # boot, the 60 s setup window is not waited for: the setup flow ends when BLE is refused (no sec2 in this image)
DO_BUILD=1
LOG=""

while [ $# -gt 0 ]; do
    case "$1" in
        --no-build) DO_BUILD=0; shift ;;
        --run-seconds) RUN_SECONDS="$2"; shift 2 ;;
        --log) LOG="$2"; shift 2 ;;
        -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
        *) echo "SETUP: unknown argument: $1" >&2; exit 2 ;;
    esac
done

command -v idf.py >/dev/null 2>&1 || { echo "SETUP: idf.py not found. Load ESP-IDF v5.4 first: . \$IDF_PATH/export.sh" >&2; exit 2; }
cd "$FW_DIR" || { echo "SETUP: cannot enter $FW_DIR" >&2; exit 2; }

if [ "$DO_BUILD" -eq 1 ]; then
    echo "BUILD: idf.py -B $BUILD_DIR (v1 + setup + sim-setup overlays, mocked sensors)"
    if ! idf.py -B "$BUILD_DIR" -DIDF_TARGET=esp32c3 -DSDKCONFIG="$SDKCONFIG" "-DSDKCONFIG_DEFAULTS=$DEFAULTS" build; then
        echo "SETUP: build failed" >&2
        exit 2
    fi
fi

# The image must really be the labelled simulator build with the setup flow on.
grep -q '^CONFIG_PLANT_SIM_MOCK_SENSORS=y' "$SDKCONFIG" || { echo "SETUP: $SDKCONFIG lacks CONFIG_PLANT_SIM_MOCK_SENSORS=y" >&2; exit 2; }
grep -q '^CONFIG_PLANT_SETUP_FLOW=y' "$SDKCONFIG" || { echo "SETUP: $SDKCONFIG lacks CONFIG_PLANT_SETUP_FLOW=y" >&2; exit 2; }

[ -n "$LOG" ] || { mkdir -p "$BUILD_DIR"; LOG="$FW_DIR/$BUILD_DIR/qemu_setup.log"; }
mkdir -p "$(dirname "$LOG")"

echo "NOTE: QEMU has no Bluetooth and this NVS has no security-2 data. This checks the boot decision and the start path only."
echo "RUN: QEMU esp32c3 for ${RUN_SECONDS} s, serial log -> $LOG"
timeout "$RUN_SECONDS" idf.py -B "$BUILD_DIR" -DSDKCONFIG="$SDKCONFIG" qemu > "$LOG" 2>&1
run_status=$?
if [ "$run_status" -ne 124 ] && [ "$run_status" -ne 0 ]; then
    echo "SETUP: QEMU run ended with status $run_status (see $LOG)" >&2
    grep -E "is not installed|error while loading|No such file" "$LOG" >&2
    exit 2
fi

passes=0
fails=0
check() {   # check NAME REGEX: the regex must appear in the log
    if grep -E -q -- "$2" "$LOG"; then
        passes=$((passes + 1)); echo "PASS  $1"
    else
        fails=$((fails + 1)); echo "FAIL  $1   (no line matches: $2)"
    fi
}
forbid() {  # forbid NAME REGEX: the regex must NOT appear in the log
    if grep -E -q -- "$2" "$LOG"; then
        fails=$((fails + 1)); echo "FAIL  $1   (found: $(grep -E -m1 -- "$2" "$LOG"))"
    else
        passes=$((passes + 1)); echo "PASS  $1"
    fi
}

# The serial port gives CRLF line endings; the checks below expect plain LF lines.
tr -d '\r' < "$LOG" > "$LOG.lf" && mv "$LOG.lf" "$LOG"

check  "cold start opens the bench setup window"  'NWSETUP bench auto setup'
check  "boot decision: setup mode"                'NWSETUP boot: setup mode'
forbid "boot decision: not normal mode"           'NWSETUP boot: normal mode'
forbid "boot decision did not fail"               'NWSETUP boot decision failed'
check  "start path reached: refused or ended"     'NWSETUP (no security-2 salt/verifier|end:)'
forbid "no advertising without security-2 data"   'NWSETUP ble advertising'
forbid "no crash or abort during setup"           'Guru Meditation|abort\(\)|panic'

if [ "$fails" -eq 0 ]; then
    echo "RESULT: PASS ($passes checks). Serial log: $LOG"
    exit 0
fi
echo "RESULT: FAIL ($fails failed, $passes passed). Serial log: $LOG"
echo "== serial log tail (last 80 lines of $LOG) =="
tail -n 80 "$LOG"
echo "== end of serial log tail =="
exit 1

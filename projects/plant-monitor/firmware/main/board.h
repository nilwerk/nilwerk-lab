/* Board definition for the Plant Monitor (ESP32-C3-MINI-1). FR-D01, NFR-12.
 *
 * The pin assignment is NOT retyped here as a table: every macro below cites the row of pcb/pinmap-sleep.md
 * (generated from pcb/design.py) it was taken from, as `pcb/pinmap-sleep.md:<line> <net>`.
 * test/host/check_board_pins.py (run by CI, ctest) opens that file and fails when a cited line no longer holds the
 * IO number and net name written here. If the PCB changes, regenerate the pinmap and fix the cite, not the test.
 *
 * Variants (Kconfig "Plant Monitor", main/Kconfig.projbuild):
 *  - PLANT_BOARD_DEVKIT (default): ESP32-C3-DevKitM-1 + breakouts as ordered in hardware/devkit-order-list.md.
 *    Same GPIOs as the custom board, so one wiring serves both. Only the divider resistors and the soil read differ.
 *  - PLANT_BOARD_V1_SUPERMINI: the v1 perfboard function demo (ESP32-C3 SuperMini), pins cited from v1/WIRING.md section 3
 *    (generated pin table). Same GPIO numbers as the dev kit, analog soil probe, 2 x 100 kOhm divider. Select it with
 *    sdkconfig.defaults.v1 (see v1/FIRMWARE-BENCH.md). test/host/check_board_v1.py compares this block with that table.
 *  - PLANT_BOARD_CUSTOM: the custom PCB. Its soil probe is a relaxation oscillator counted with PCNT on IO4
 *    (pinmap line 15), NOT an analog voltage. That reader is not written yet: soil reads return NW_ERR_UNSUPPORTED.
 *
 * Soil calibration (PR #57 C3): the dry/wet numbers measured on the dev kit (analog probe, 12-bit ADC counts, WO-firmware-4.F1
 * Step 8) do NOT apply to the custom board. There the probe is a relaxation oscillator read with PCNT, so its numbers
 * (pulses per window) are a different quantity and must be calibrated again on the custom board (task 5.x).
 */
#ifndef BOARD_H
#define BOARD_H

#include "sdkconfig.h"

#ifdef CONFIG_PLANT_BOARD_V1_SUPERMINI
/* v1 perfboard, ESP32-C3 SuperMini. Each macro cites its row of the generated pin table: v1/WIRING.md section 3 (BEGIN:pins block).
 * GPIO6/GPIO7 are set explicitly: the SuperMini listing labels GPIO8 = SDA and GPIO9 = SCL (Arduino defaults), which we do NOT use (WIRING.md section 3).
 * GPIO8 (board LED, strap pin) is unused. GPIO9 = BOOT key. IO1 is not wired in v1 either. */
#define NW_PIN_BAT_SENS 0   /* v1/WIRING.md section 3: GPIO0 BAT_SENS (ADC1_CH0), divider midpoint, on the switched side of J1 */
#define NW_PIN_SOIL_PWR 3   /* v1/WIRING.md section 3: GPIO3 SOIL_PWR, soil VCC switch, LOW in deep sleep */
#define NW_PIN_SOIL_OUT 4   /* v1/WIRING.md section 3: GPIO4 SOIL_OUT (ADC1_CH4), soil AOUT; dry end may clip above about 2.4 V (WIRING.md section 4.5, A-094 item 7) */
#define NW_PIN_BUTTON 9     /* v1/WIRING.md section 3: GPIO9 BOOT_N, on-board BOOT key, nothing wired */
#define NW_PIN_I2C_SDA 6    /* v1/WIRING.md section 3: GPIO6 I2C_SDA, BH1750 0x23 + AHT20 0x38 */
#define NW_PIN_I2C_SCL 7    /* v1/WIRING.md section 3: GPIO7 I2C_SCL */
#define NW_BOARD_NAME "v1_supermini"
#else
#define NW_PIN_BAT_SENS 0   /* pcb/pinmap-sleep.md:11 BAT_SENS  (ADC1_CH0) */
#define NW_PIN_SOIL_PWR 3   /* pcb/pinmap-sleep.md:14 SOIL_PWR  (must be LOW in deep sleep, NFR-12) */
#define NW_PIN_SOIL_OUT 4   /* pcb/pinmap-sleep.md:15 SOIL_OUT  (custom board: PCNT; dev kit: analog probe on ADC1_CH4) */
#define NW_PIN_BUTTON 9     /* pcb/pinmap-sleep.md:20 BOOT_N  (setup button; dev kit BOOT key; NOT an RTC pin: cannot wake deep sleep) */
#define NW_PIN_I2C_SDA 6    /* pcb/pinmap-sleep.md:17 I2C_SDA */
#define NW_PIN_I2C_SCL 7    /* pcb/pinmap-sleep.md:18 I2C_SCL */
#ifdef CONFIG_PLANT_BOARD_CUSTOM
#define NW_BOARD_NAME "custom"
#else
#define NW_BOARD_NAME "devkit"
#endif
#endif
/* IO1 is NOT connected and must not be driven (pcb/pinmap-sleep.md:12, A-045 Option A: Q2/R6 removed). No NW_PIN_ for it on purpose. */

/* ADC1 channel numbers of the ESP32-C3: GPIO0..GPIO4 are ADC1_CH0..CH4 (the cited rows name ADC1_0 for IO0). */
#define NW_ADC1_CH_BAT NW_PIN_BAT_SENS
#define NW_ADC1_CH_SOIL NW_PIN_SOIL_OUT

#define NW_I2C_HZ 100000

#ifdef CONFIG_PLANT_BOARD_CUSTOM
/* R7 + R8, permanent divider (pcb/pinmap-sleep.md:36: 4.2 V / 2 MOhm = 2.1 uA, also in deep sleep) */
#define NW_BAT_R_TOP_OHM 1000000u
#define NW_BAT_R_BOT_OHM 1000000u
#define NW_SOIL_ANALOG 0
#else
/* Dev kit and v1 SuperMini (v1/WIRING.md section 4.2: R1 = R2 = 100 kOhm 1 %, ratio 2:1): own-stock 2 x 100 kOhm 1 % (hardware/devkit-order-list.md section 3 note 5): same 2:1 ratio, 21 uA at 4.2 V.
 * Bench only: never quote a dev-kit current as the product figure. */
#define NW_BAT_R_TOP_OHM 100000u
#define NW_BAT_R_BOT_OHM 100000u
#define NW_SOIL_ANALOG 1
#endif

#endif

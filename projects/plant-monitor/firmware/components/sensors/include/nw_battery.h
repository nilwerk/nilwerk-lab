/* Battery voltage via the PERMANENT divider R7+R8 on IO0 (ADC1_CH0). A-045 Option A: no switch, IO1 is free.
 * Divider current: V / (R_top + R_bot), 4.2 V / 2 MOhm = 2.1 uA (pcb/pinmap-sleep.md, divider row); it flows in deep sleep too. */
#ifndef NW_BATTERY_H
#define NW_BATTERY_H
#include "nw_hal.h"

#define NW_BAT_PLAUSIBLE_MIN_MV 3000 /* FR-D01 plausible range (requirements-v1.0-delta.md), schema x-plausible */
#define NW_BAT_PLAUSIBLE_MAX_MV 4250
#define NW_BAT_SAMPLES 4
#define NW_BAT_SPACING_MS 100 /* 500 k source impedance with the 100 nF reservoir C11: tau = 50 ms */

typedef struct { uint32_t r_top_ohm; uint32_t r_bot_ohm; } nw_battery_cfg_t;

/* Cell voltage in mV from the calibrated ADC millivolts at the pin (rounded to nearest). 0 on bad config. */
uint32_t nw_battery_mv_from_adc(uint32_t adc_mv, const nw_battery_cfg_t *cfg);
bool nw_battery_plausible(uint32_t vbat_mv);
/* Divider current in nA for a cell voltage: mV * 1e6 / (R_top + R_bot). */
uint32_t nw_battery_divider_na(uint32_t vbat_mv, const nw_battery_cfg_t *cfg);
/* One dummy conversion (settles the sample cap), then NW_BAT_SAMPLES averaged. Needs a calibrated ADC. */
nw_err_t nw_battery_measure(const nw_hal_t *hal, const nw_battery_cfg_t *cfg, uint32_t *vbat_mv, uint32_t *adc_mv);
#endif

/* Capacitive soil probe: two-point calibration to 0-100 % relative moisture (FR-D10 procedure, FR-D01, NFR-02).
 * Calibration points are raw 12-bit ADC counts, as in docs/interfaces/device-report.schema.json (cal.dry_raw/wet_raw).
 * Direction: on the dev-kit analog probe the raw count is LOW in dry air and HIGH in water, so dry_raw < wet_raw is required
 * (owner bench 28 Nov, A-094/A-154). nw_soil_normalise refuses a swapped pair with NW_ERR_CAL. */
#ifndef NW_SOIL_H
#define NW_SOIL_H
#include "nw_hal.h"

#define NW_SOIL_MIN_SPAN_COUNTS 50 /* |dry - wet| below this is treated as "not calibrated" */
#define NW_SOIL_WARMUP_MS 1500     /* playbook: >= 1.5 s warm-up after power-on */
#define NW_SOIL_SAMPLES 5
#define NW_SOIL_SPACING_MS 50

#define NW_SOIL_F_CLAMPED_DRY 0x01 /* raw drier than the dry point, result clamped to 0 % */
#define NW_SOIL_F_CLAMPED_WET 0x02 /* raw wetter than the wet point, result clamped to 100 % */
#define NW_SOIL_F_RAIL 0x04        /* raw at 0 or 4095: probe disconnected or shorted, treat as sensor fault */

typedef struct { int dry_raw; int wet_raw; } nw_soil_cal_t;

typedef struct {
    int raw;          /* average raw counts */
    int pct_x10;      /* 0..1000 = 0.0..100.0 % */
    uint8_t flags;
} nw_soil_t;

nw_err_t nw_soil_normalise(const nw_soil_cal_t *cal, int raw, nw_soil_t *out);
/* Power on, warm up, average NW_SOIL_SAMPLES readings, ALWAYS power off again (also on error), normalise. */
nw_err_t nw_soil_measure(const nw_hal_t *hal, const nw_soil_cal_t *cal, nw_soil_t *out);
#endif

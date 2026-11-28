/* Soil probe calibration and measurement. FR-D10 (2-point dry/wet calibration), FR-D01 (moisture 0-100 %), NFR-02 (accuracy after calibration),
 * NFR-12 (IO3 supply low unless measuring). */
#include "nw_soil.h"

nw_err_t nw_soil_normalise(const nw_soil_cal_t *cal, int raw, nw_soil_t *out)
{
    if (!cal || !out) return NW_ERR_ARG;
    /* Direction (owner bench, 28 Nov; A-094, A-154): this probe reads LOW in dry air (about 15-25 counts) and HIGH in water (about 360).
     * So dry_raw must be the lower count. A swapped pair has a negative span and is refused, never silently inverted. */
    if (cal->wet_raw - cal->dry_raw < NW_SOIL_MIN_SPAN_COUNTS) return NW_ERR_CAL;
    out->raw = raw;
    out->flags = 0;
    if (raw <= 0 || raw >= 4095) out->flags |= NW_SOIL_F_RAIL;
    /* pct = (raw - dry) / (wet - dry) x 100 with dry < wet. Clamp first, flag the end that was hit. */
    int v = raw;
    if (raw < cal->dry_raw) { v = cal->dry_raw; out->flags |= NW_SOIL_F_CLAMPED_DRY; }
    if (raw > cal->wet_raw) { v = cal->wet_raw; out->flags |= NW_SOIL_F_CLAMPED_WET; }
    long long num = (long long)(v - cal->dry_raw) * 1000;   /* 0 .. span x 1000, never negative after clamping */
    long long den = (long long)(cal->wet_raw - cal->dry_raw); /* > 0 */
    out->pct_x10 = (int)((num + den / 2) / den);             /* rounds to nearest 0.1 % */
    return NW_OK;
}

nw_err_t nw_soil_measure(const nw_hal_t *hal, const nw_soil_cal_t *cal, nw_soil_t *out)
{
    if (!hal || !cal || !out) return NW_ERR_ARG;
    hal->soil_power(hal->ctx, true);
    hal->delay_ms(hal->ctx, NW_SOIL_WARMUP_MS);
    long sum = 0;
    nw_err_t err = NW_OK;
    for (int i = 0; i < NW_SOIL_SAMPLES; i++) {
        nw_adc_sample_t s;
        if (hal->adc_read(hal->ctx, NW_ADC_SOIL, &s) != 0) { err = NW_ERR_IO; break; }
        sum += s.raw;
        if (i + 1 < NW_SOIL_SAMPLES) hal->delay_ms(hal->ctx, NW_SOIL_SPACING_MS);
    }
    hal->soil_power(hal->ctx, false); /* NFR-12: every path ends with the supply off */
    if (err != NW_OK) return err;
    return nw_soil_normalise(cal, (int)((sum + NW_SOIL_SAMPLES / 2) / NW_SOIL_SAMPLES), out);
}

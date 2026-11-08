/* Soil probe calibration and measurement. FR-D01 (moisture 0-100 %), NFR-02, NFR-12 (IO3 supply low unless measuring). */
#include "nw_soil.h"

static int iabs(int v) { return v < 0 ? -v : v; }

nw_err_t nw_soil_normalise(const nw_soil_cal_t *cal, int raw, nw_soil_t *out)
{
    if (!cal || !out) return NW_ERR_ARG;
    if (iabs(cal->dry_raw - cal->wet_raw) < NW_SOIL_MIN_SPAN_COUNTS) return NW_ERR_CAL;
    out->raw = raw;
    out->flags = 0;
    if (raw <= 0 || raw >= 4095) out->flags |= NW_SOIL_F_RAIL;
    /* pct = (raw - dry) / (wet - dry); works whichever of dry/wet is the larger count. Clamp first, flag the side. */
    int dry_side = (cal->dry_raw > cal->wet_raw) ? (raw > cal->dry_raw) : (raw < cal->dry_raw);
    int wet_side = (cal->dry_raw > cal->wet_raw) ? (raw < cal->wet_raw) : (raw > cal->wet_raw);
    int v = raw;
    if (dry_side) { v = cal->dry_raw; out->flags |= NW_SOIL_F_CLAMPED_DRY; }
    if (wet_side) { v = cal->wet_raw; out->flags |= NW_SOIL_F_CLAMPED_WET; }
    long long num = (long long)(v - cal->dry_raw) * 1000;
    long long den = (long long)(cal->wet_raw - cal->dry_raw);
    /* num and den always have the same sign after clamping (dry>wet: both <= 0), so C truncation rounds to nearest */
    long long p = (num + den / 2) / den;
    out->pct_x10 = (int)p;
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

/* Battery voltage through the 2:1 divider. FR-D01 (battery plausible 3.0..4.25 V), NFR-01/NFR-12 (divider is permanent). */
#include "nw_battery.h"

uint32_t nw_battery_mv_from_adc(uint32_t adc_mv, const nw_battery_cfg_t *cfg)
{
    if (!cfg || cfg->r_bot_ohm == 0) return 0;
    uint64_t num = (uint64_t)adc_mv * (cfg->r_top_ohm + cfg->r_bot_ohm);
    return (uint32_t)((num + cfg->r_bot_ohm / 2) / cfg->r_bot_ohm);
}

bool nw_battery_plausible(uint32_t vbat_mv)
{
    return vbat_mv >= NW_BAT_PLAUSIBLE_MIN_MV && vbat_mv <= NW_BAT_PLAUSIBLE_MAX_MV;
}

uint32_t nw_battery_divider_na(uint32_t vbat_mv, const nw_battery_cfg_t *cfg)
{
    if (!cfg || cfg->r_top_ohm + cfg->r_bot_ohm == 0) return 0;
    return (uint32_t)(((uint64_t)vbat_mv * 1000000u) / (cfg->r_top_ohm + cfg->r_bot_ohm));
}

nw_err_t nw_battery_measure(const nw_hal_t *hal, const nw_battery_cfg_t *cfg, uint32_t *vbat_mv, uint32_t *adc_mv)
{
    if (!hal || !cfg || !vbat_mv || cfg->r_bot_ohm == 0) return NW_ERR_ARG;
    nw_adc_sample_t s;
    if (hal->adc_read(hal->ctx, NW_ADC_BAT, &s) != 0) return NW_ERR_IO; /* dummy: charges the sample cap */
    uint64_t sum = 0;
    for (int i = 0; i < NW_BAT_SAMPLES; i++) {
        hal->delay_ms(hal->ctx, NW_BAT_SPACING_MS);
        if (hal->adc_read(hal->ctx, NW_ADC_BAT, &s) != 0) return NW_ERR_IO;
        if (!s.calibrated || s.mv < 0) return NW_ERR_CAL;
        sum += (uint32_t)s.mv;
    }
    uint32_t avg = (uint32_t)((sum + NW_BAT_SAMPLES / 2) / NW_BAT_SAMPLES);
    if (adc_mv) *adc_mv = avg;
    *vbat_mv = nw_battery_mv_from_adc(avg, cfg);
    return NW_OK;
}

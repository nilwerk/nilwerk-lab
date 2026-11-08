/* BH1750 driver logic. FR-D01. One-time H-resolution mode: the chip powers down by itself after the measurement,
 * so it does not sit in the 120 uA measuring state between samples (NFR-12 budget row "BH1750 power-down"). */
#include "nw_bh1750.h"

nw_err_t nw_bh1750_convert(uint16_t raw, nw_bh1750_t *out)
{
    if (!out) return NW_ERR_ARG;
    out->raw = raw;
    out->lux_x10 = ((uint32_t)raw * 25u + 1u) / 3u; /* raw / 1.2 * 10 = raw * 25 / 3, rounded */
    out->saturated = (raw == 0xFFFF);
    return NW_OK;
}

nw_err_t nw_bh1750_read(const nw_hal_t *hal, nw_bh1750_t *out)
{
    if (!hal || !out) return NW_ERR_ARG;
    const uint8_t on = NW_BH1750_CMD_POWER_ON, meas = NW_BH1750_CMD_ONE_TIME_H;
    if (hal->i2c_write(hal->ctx, NW_BH1750_ADDR, &on, 1) != 0) return NW_ERR_IO;
    if (hal->i2c_write(hal->ctx, NW_BH1750_ADDR, &meas, 1) != 0) return NW_ERR_IO;
    hal->delay_ms(hal->ctx, NW_BH1750_MEAS_WAIT_MS);
    uint8_t b[2];
    if (hal->i2c_read(hal->ctx, NW_BH1750_ADDR, b, 2) != 0) return NW_ERR_IO;
    return nw_bh1750_convert((uint16_t)((b[0] << 8) | b[1]), out);
}

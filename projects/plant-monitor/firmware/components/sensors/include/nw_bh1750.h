/* BH1750 ambient light, I2C 0x23 (ADDR pin low). FR-D01 (light). */
#ifndef NW_BH1750_H
#define NW_BH1750_H
#include "nw_hal.h"

#define NW_BH1750_ADDR 0x23
#define NW_BH1750_CMD_POWER_ON 0x01
#define NW_BH1750_CMD_ONE_TIME_H 0x20 /* one-time H-resolution mode: chip powers itself down afterwards */
#define NW_BH1750_MEAS_WAIT_MS 180    /* datasheet max measurement time, H-resolution mode */

typedef struct {
    uint16_t raw;
    uint32_t lux_x10;  /* lux * 10 = raw / 1.2 * 10 (datasheet, MTreg 69) */
    bool saturated;    /* raw == 0xFFFF: reading at or above the range limit */
} nw_bh1750_t;

nw_err_t nw_bh1750_convert(uint16_t raw, nw_bh1750_t *out);
nw_err_t nw_bh1750_read(const nw_hal_t *hal, nw_bh1750_t *out);
#endif

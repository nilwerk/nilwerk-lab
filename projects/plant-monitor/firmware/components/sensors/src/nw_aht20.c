/* AHT20 driver logic. FR-D01. Command bytes and timing from the AHT20 datasheet (ASAIR, 2024-07):
 * status read, init 0xBE 0x08 0x00 if bits 0x18 are not both set, trigger 0xAC 0x33 0x00, wait 80 ms, read 7 bytes. */
#include "nw_aht20.h"

#define AHT20_STATUS_BUSY 0x80
#define AHT20_STATUS_CAL 0x08
#define AHT20_STATUS_MODE 0x10 /* with CAL: the datasheet's 0x18 check */
#define AHT20_WAIT_MS 80
#define AHT20_BUSY_RETRIES 5
#define AHT20_BUSY_RETRY_MS 10

uint8_t nw_aht20_crc8(const uint8_t *data, size_t len)
{
    uint8_t crc = 0xFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int b = 0; b < 8; b++) {
            crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x31) : (uint8_t)(crc << 1);
        }
    }
    return crc;
}

nw_err_t nw_aht20_decode(const uint8_t frame[NW_AHT20_FRAME_LEN], nw_aht20_t *out)
{
    if (!frame || !out) return NW_ERR_ARG;
    if (frame[0] & AHT20_STATUS_BUSY) return NW_ERR_BUSY;
    if (nw_aht20_crc8(frame, 6) != frame[6]) return NW_ERR_CRC;
    uint32_t rh_raw = ((uint32_t)frame[1] << 12) | ((uint32_t)frame[2] << 4) | (frame[3] >> 4);
    uint32_t t_raw = ((uint32_t)(frame[3] & 0x0F) << 16) | ((uint32_t)frame[4] << 8) | frame[5];
    /* RH = raw / 2^20 * 100 %, T = raw / 2^20 * 200 - 50 degC, in x100 integers, rounded to nearest */
    out->rh_x100 = (int32_t)(((uint64_t)rh_raw * 10000u + (1u << 19)) >> 20);
    out->temp_c_x100 = (int32_t)(((uint64_t)t_raw * 20000u + (1u << 19)) >> 20) - 5000;
    return NW_OK;
}

nw_err_t nw_aht20_read(const nw_hal_t *hal, nw_aht20_t *out)
{
    if (!hal || !out) return NW_ERR_ARG;
    uint8_t status = 0;
    if (hal->i2c_read(hal->ctx, NW_AHT20_ADDR, &status, 1) != 0) return NW_ERR_IO;
    if ((status & (AHT20_STATUS_CAL | AHT20_STATUS_MODE)) != (AHT20_STATUS_CAL | AHT20_STATUS_MODE)) {
        const uint8_t init[3] = {0xBE, 0x08, 0x00};
        if (hal->i2c_write(hal->ctx, NW_AHT20_ADDR, init, 3) != 0) return NW_ERR_IO;
        hal->delay_ms(hal->ctx, 10);
    }
    const uint8_t trig[3] = {0xAC, 0x33, 0x00};
    if (hal->i2c_write(hal->ctx, NW_AHT20_ADDR, trig, 3) != 0) return NW_ERR_IO;
    hal->delay_ms(hal->ctx, AHT20_WAIT_MS);
    uint8_t frame[NW_AHT20_FRAME_LEN];
    for (int tries = 0; tries <= AHT20_BUSY_RETRIES; tries++) {
        if (hal->i2c_read(hal->ctx, NW_AHT20_ADDR, frame, NW_AHT20_FRAME_LEN) != 0) return NW_ERR_IO;
        if (!(frame[0] & AHT20_STATUS_BUSY)) return nw_aht20_decode(frame, out);
        hal->delay_ms(hal->ctx, AHT20_BUSY_RETRY_MS);
    }
    return NW_ERR_BUSY;
}

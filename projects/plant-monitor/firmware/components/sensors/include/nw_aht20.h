/* AHT20 temperature/humidity, I2C 0x38 (datasheet ASAIR AHT20, 2024-07). FR-D01 (air temperature, humidity). */
#ifndef NW_AHT20_H
#define NW_AHT20_H
#include "nw_hal.h"

#define NW_AHT20_ADDR 0x38
#define NW_AHT20_FRAME_LEN 7 /* status, 5 data bytes, CRC */

typedef struct {
    int32_t temp_c_x100; /* degC * 100, e.g. 2345 = 23.45 degC */
    int32_t rh_x100;     /* %RH * 100, 0..10000 */
} nw_aht20_t;

/* CRC-8, poly 0x31, init 0xFF, no reflection, no final xor (AHT20 datasheet). */
uint8_t nw_aht20_crc8(const uint8_t *data, size_t len);
/* Checks busy bit and CRC of a 7-byte frame, converts the 20-bit raw values. Pure function. */
nw_err_t nw_aht20_decode(const uint8_t frame[NW_AHT20_FRAME_LEN], nw_aht20_t *out);
/* Status check (calibrated bits), trigger, wait 80 ms, read, decode. Blocks about 100 ms. */
nw_err_t nw_aht20_read(const nw_hal_t *hal, nw_aht20_t *out);
#endif

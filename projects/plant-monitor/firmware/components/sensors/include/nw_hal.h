/* Hardware abstraction layer for the sensor drivers (task 4.F1, FR-D01).
 * The driver logic (AHT20, BH1750, soil calibration, battery divider) only talks to this struct, so it builds and
 * is unit-tested on the host with a fake (test/host). The ESP-IDF implementation is hal_esp32.c.
 * No ESP-IDF header may be included from this file or from the pure driver sources. */
#ifndef NW_HAL_H
#define NW_HAL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef enum {
    NW_OK = 0,
    NW_ERR_IO = -1,          /* bus / ADC call failed */
    NW_ERR_CRC = -2,         /* AHT20 CRC mismatch */
    NW_ERR_BUSY = -3,        /* AHT20 still busy after the retry budget */
    NW_ERR_ARG = -4,
    NW_ERR_CAL = -5,         /* calibration missing / dry == wet / ADC not calibrated */
    NW_ERR_UNSUPPORTED = -6, /* e.g. soil read on the custom board (PCNT variant not written yet) */
} nw_err_t;

typedef enum { NW_ADC_BAT = 0, NW_ADC_SOIL = 1 } nw_adc_ch_t;

typedef struct {
    int raw;          /* 12-bit counts, 0..4095 */
    int mv;           /* calibrated millivolts at the pin, -1 when the ADC has no calibration */
    bool calibrated;
} nw_adc_sample_t;

typedef struct nw_hal {
    void *ctx;
    /* I2C: return 0 on success, negative on error. 7-bit address. */
    int (*i2c_write)(void *ctx, uint8_t addr, const uint8_t *buf, size_t len);
    int (*i2c_read)(void *ctx, uint8_t addr, uint8_t *buf, size_t len);
    void (*delay_ms)(void *ctx, uint32_t ms);
    /* Soil probe supply (IO3). NFR-12: must be LOW whenever no measurement is running. */
    void (*soil_power)(void *ctx, bool on);
    int (*adc_read)(void *ctx, nw_adc_ch_t ch, nw_adc_sample_t *out);
} nw_hal_t;

#endif

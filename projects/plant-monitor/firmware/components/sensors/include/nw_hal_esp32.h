/* ESP-IDF v5.4 implementation of nw_hal_t (I2C master driver, ADC oneshot + curve-fitting calibration, GPIO).
 * NOT unit-tested on the host and, in task 4.F1, never run on hardware: only built by CI. */
#ifndef NW_HAL_ESP32_H
#define NW_HAL_ESP32_H
#include "nw_hal.h"

typedef struct {
    int sda_gpio;
    int scl_gpio;
    int soil_pwr_gpio;     /* IO3, SOIL_PWR */
    int adc_bat_channel;   /* ADC1 channel number of the battery divider (IO0 = channel 0) */
    int adc_soil_channel;  /* ADC1 channel number of the analog soil probe (dev kit: IO4 = channel 4); -1 = not available */
    uint32_t i2c_hz;
} nw_hal_esp32_cfg_t;

/* Fills *hal; ctx points to static storage (one instance only). Returns 0 on success. Leaves IO3 low. */
int nw_hal_esp32_init(const nw_hal_esp32_cfg_t *cfg, nw_hal_t *hal);
/* NFR-12: drive IO3 low and hold it through deep sleep. Call right before esp_deep_sleep_start(). */
void nw_hal_esp32_prepare_deep_sleep(void);
#endif

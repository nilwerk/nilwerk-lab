/* SIMULATOR ONLY (CONFIG_PLANT_SIM_MOCK_SENSORS). MOCKED sensor HAL for the Espressif QEMU ESP32-C3 boot test.
 *
 * What is mocked, and why: QEMU does not model the AHT20 / BH1750 sensors on I2C or the ADC readings of the soil probe and
 * battery divider. This file answers the drivers' own calls (nw_hal_t callbacks) with FIXED values, so the real driver code
 * (CRC check, 20-bit decoding, lux conversion, soil normalisation, battery divider) still runs on known inputs.
 * What is NOT tested: the ESP-IDF I2C/ADC drivers (hal_esp32.c), the wiring, the real sensors, the soil power timing (IO3 is a no-op here).
 *
 * Every value below is a MOCK constant, not sensor data. The CRC is taken from the driver (nw_aht20_crc8), so a CRC bug there is not
 * caught by this mock; the host tests cover it. */
#include "sdkconfig.h"

#ifdef CONFIG_PLANT_SIM_MOCK_SENSORS

#include <stdio.h>
#include <string.h>
#include "sim_mock_hal.h"
#include "nw_aht20.h"
#include "nw_bh1750.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

/* MOCK values. Their decoded results are what the NWBENCH line is expected to show (tests/qemu_boot_check.sh). */
#define SIM_MOCK_AHT20_TEMP_X100 2345   /* MOCK 23.45 degC */
#define SIM_MOCK_AHT20_RH_X100   4125   /* MOCK 41.25 %RH */
#define SIM_MOCK_BH1750_RAW      300    /* MOCK raw 300 -> 250.0 lux (raw / 1.2) */
#define SIM_MOCK_SOIL_RAW        190    /* MOCK 12-bit counts, halfway between dry 20 and wet 360 -> 50.0 % */
#define SIM_MOCK_BAT_ADC_MV      2100   /* MOCK pin voltage; with the 100k/100k divider -> 4200 mV cell, plausible */

/* Encodes the MOCK temperature and humidity as the AHT20 frame the driver expects (datasheet formulas, inverted). */
static void encode_aht20_frame(uint8_t frame[NW_AHT20_FRAME_LEN])
{
    uint32_t rh_raw = (uint32_t)((SIM_MOCK_AHT20_RH_X100 * (1ull << 20) + 5000) / 10000);
    uint32_t t_raw = (uint32_t)(((uint64_t)(SIM_MOCK_AHT20_TEMP_X100 + 5000) * (1ull << 20) + 10000) / 20000);
    frame[0] = 0x18;                                   /* MOCK status: calibrated, mode bits set, not busy */
    frame[1] = (uint8_t)(rh_raw >> 12);
    frame[2] = (uint8_t)(rh_raw >> 4);
    frame[3] = (uint8_t)(((rh_raw & 0x0F) << 4) | ((t_raw >> 16) & 0x0F));
    frame[4] = (uint8_t)(t_raw >> 8);
    frame[5] = (uint8_t)t_raw;
    frame[6] = nw_aht20_crc8(frame, 6);
}

static int sim_i2c_write(void *ctx, uint8_t addr, const uint8_t *buf, size_t len)
{
    (void)ctx; (void)buf; (void)len;
    /* MOCK: every write is accepted (AHT20 trigger/init, BH1750 power-on/measure commands). */
    return addr == NW_AHT20_ADDR || addr == NW_BH1750_ADDR ? 0 : -1;
}

static int sim_i2c_read(void *ctx, uint8_t addr, uint8_t *buf, size_t len)
{
    (void)ctx;
    if (addr == NW_AHT20_ADDR && len == 1) { buf[0] = 0x18; return 0; }     /* MOCK status byte only */
    if (addr == NW_AHT20_ADDR && len == NW_AHT20_FRAME_LEN) { encode_aht20_frame(buf); return 0; }
    if (addr == NW_BH1750_ADDR && len == 2) {                                 /* MOCK two-byte raw, big endian */
        buf[0] = (uint8_t)(SIM_MOCK_BH1750_RAW >> 8);
        buf[1] = (uint8_t)(SIM_MOCK_BH1750_RAW & 0xFF);
        return 0;
    }
    return -1;                                                                /* any other address: no device (NAK) */
}

static void sim_delay_ms(void *ctx, uint32_t ms)
{
    (void)ctx;
    vTaskDelay(pdMS_TO_TICKS(ms));     /* real delay on the simulated CPU: the driver's timing is kept */
}

static void sim_soil_power(void *ctx, bool on)
{
    (void)ctx; (void)on;     /* MOCK: no GPIO. NFR-12 (IO3 low in sleep) is NOT checked by the simulator. */
}

static int sim_adc_read(void *ctx, nw_adc_ch_t ch, nw_adc_sample_t *out)
{
    (void)ctx;
    if (!out) return -1;
    if (ch == NW_ADC_SOIL) {                                                  /* MOCK soil counts, calibrated flag set */
        out->raw = SIM_MOCK_SOIL_RAW;
        out->mv = (int)(SIM_MOCK_SOIL_RAW * 3300 / 4095);
        out->calibrated = true;
        return 0;
    }
    if (ch == NW_ADC_BAT) {                                                   /* MOCK battery pin, calibrated flag set */
        out->raw = (int)(SIM_MOCK_BAT_ADC_MV * 4095 / 3300);
        out->mv = SIM_MOCK_BAT_ADC_MV;
        out->calibrated = true;
        return 0;
    }
    return -1;
}

/* SIMULATOR ONLY: answers adc_hal_self_calibration() (see main/CMakeLists.txt, --wrap). QEMU's SAR ADC never raises the ONESHOT_DONE
 * event, so the real self-calibration spins forever in the ADC2 constructor before app_main. MOCK init code 0 (not a calibration value);
 * the mock HAL never reads the ADC through the driver, so no sensor value depends on it. */
uint32_t __wrap_adc_hal_self_calibration(int adc_n, int atten, bool internal_gnd)
{
    (void)adc_n; (void)atten; (void)internal_gnd;
    return 0;
}

static nw_hal_t mock_hal;

int nw_sim_mock_hal_init(nw_hal_t *hal)
{
    if (!hal) return -1;
    mock_hal.ctx = NULL;
    mock_hal.i2c_write = sim_i2c_write;
    mock_hal.i2c_read = sim_i2c_read;
    mock_hal.delay_ms = sim_delay_ms;
    mock_hal.soil_power = sim_soil_power;
    mock_hal.adc_read = sim_adc_read;
    *hal = mock_hal;
    printf("NWSIMMOCK sensors=MOCK fixed values, NOT sensor data: aht20 t=%d rh=%d bh1750 raw=%d soil_raw=%d bat_adc_mv=%d\n",
           SIM_MOCK_AHT20_TEMP_X100, SIM_MOCK_AHT20_RH_X100, SIM_MOCK_BH1750_RAW, SIM_MOCK_SOIL_RAW, SIM_MOCK_BAT_ADC_MV);
    fflush(stdout);
    return 0;
}

void nw_sim_mock_prepare_deep_sleep(void)
{
    /* MOCK: nothing to hold (no GPIO in the simulator). */
}

#else
/* Option off: this file compiles to nothing, so every board build is unchanged. */
#endif

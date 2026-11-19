/* Plant Monitor firmware: sensor bench application (task 4.F1, FR-D01).
 * Reads soil, AHT20, BH1750 and battery every 2 s and prints one `NWBENCH ...` line per cycle on the USB Serial/JTAG
 * console. It is the procedure target of docs/work-orders/WO-firmware-4.F1.md. It has NOT been run on hardware.
 * Reporting, ring buffer, Wi-Fi and the real 15-min sleep schedule are other tasks (4.F2 ...). */
#include <stdio.h>
#include <stdlib.h>

#include "board.h"
#include "esp_log.h"
#include "esp_sleep.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nw_aht20.h"
#include "nw_battery.h"
#include "nw_bh1750.h"
#include "nw_hal_esp32.h"
#include "nw_soil.h"
#ifdef CONFIG_PLANT_UPLOAD
#include "nw_upload_idf.h"
#endif
#ifdef CONFIG_PLANT_SETUP_FLOW
#include "driver/gpio.h"
#include "esp_system.h"
#include "nw_prov.h"
#include "nw_prov_idf.h"
#endif

static const char *TAG = "plant_monitor";
static RTC_DATA_ATTR int wake_count;

#ifdef CONFIG_PLANT_BENCH_SLEEP_CYCLE
#define CYCLES_BEFORE_SLEEP 5
#else
#define CYCLES_BEFORE_SLEEP 0x7fffffff /* never sleeps */
#endif
#define SLEEP_S 60

/* "-12.34" style output without float printf */
static void fmt_x(char *dst, size_t n, long v, int decimals)
{
    long div = decimals == 2 ? 100 : 10;
    snprintf(dst, n, "%s%ld.%0*ld", v < 0 ? "-" : "", labs(v) / div, decimals, labs(v) % div);
}

#ifdef CONFIG_PLANT_SETUP_FLOW
/* Button hold measured after a cold start (power-on / reset), FR-D03, FR-D07. NOT "held at power-up": IO9 is the boot strap, low at reset
 * means ROM download mode (pcb/pinmap-sleep.md:20), so the user presses AFTER the reset releases. [proposed] window 3 s to start pressing,
 * then the hold is measured up to the factory-reset time. Deep-sleep wakes (15-min samples) skip the window: no battery cost there. */
#define BUTTON_PRESS_WINDOW_MS 3000
static uint32_t button_held_ms_after_cold_start(void)
{
    if (esp_reset_reason() == ESP_RST_DEEPSLEEP) return 0;
    gpio_config_t io = {.pin_bit_mask = 1ULL << NW_PIN_BUTTON, .mode = GPIO_MODE_INPUT};   /* external pull-up R5 on the custom board; dev kit has one too */
    gpio_config(&io);
    printf("NWSETUP press window: hold BOOT now for 3 s = setup, 10 s = factory reset\n");
    for (int waited = 0; waited < BUTTON_PRESS_WINDOW_MS && gpio_get_level(NW_PIN_BUTTON); waited += 20) vTaskDelay(pdMS_TO_TICKS(20));
    uint32_t held = 0;
    while (!gpio_get_level(NW_PIN_BUTTON) && held < NW_PROV_BUTTON_RESET_MS) { vTaskDelay(pdMS_TO_TICKS(20)); held += 20; }
    return held;
}
#endif

void app_main(void)
{
    wake_count++;
#ifdef CONFIG_PLANT_SETUP_FLOW
    if (esp_reset_reason() != ESP_RST_DEEPSLEEP) {          /* setup decision only on a cold start; a sample wake never opens BLE (FR-D09) */
        if (nw_setup_run(button_held_ms_after_cold_start()) == NW_SETUP_SLEEP_UNTIL_RESET) {
            printf("NWSETUP closed, never provisioned: deep sleep with no timer; reset to try again\n");
            fflush(stdout);
            /* nw_hal_esp32_prepare_deep_sleep() is NOT called: it needs nw_hal_esp32_init first (it reads the HAL's pin copy). IO3 (SOIL_PWR)
             * was never configured in this path, so its level in sleep depends on the board pull-down: bench check for NFR-12 (WO step). */
            esp_deep_sleep_start();
        }
    }
#endif
    nw_hal_esp32_cfg_t cfg = {
        .sda_gpio = NW_PIN_I2C_SDA,
        .scl_gpio = NW_PIN_I2C_SCL,
        .soil_pwr_gpio = NW_PIN_SOIL_PWR,
        .adc_bat_channel = NW_ADC1_CH_BAT,
        .adc_soil_channel = NW_SOIL_ANALOG ? NW_ADC1_CH_SOIL : -1,
        .i2c_hz = NW_I2C_HZ,
    };
    nw_hal_t hal;
    if (nw_hal_esp32_init(&cfg, &hal) != 0) {
        ESP_LOGE(TAG, "HAL init failed");
        return;
    }
    const nw_soil_cal_t cal = {.dry_raw = CONFIG_PLANT_SOIL_DRY_RAW, .wet_raw = CONFIG_PLANT_SOIL_WET_RAW};
    const nw_battery_cfg_t bat = {.r_top_ohm = NW_BAT_R_TOP_OHM, .r_bot_ohm = NW_BAT_R_BOT_OHM};
    ESP_LOGI(TAG, "NWBENCH start board=%s wake=%d cal_dry=%d cal_wet=%d divider=%u/%u (CALIBRATION IS A PLACEHOLDER UNTIL SET ON THE BENCH)",
             NW_BOARD_NAME, wake_count, cal.dry_raw, cal.wet_raw, (unsigned)bat.r_top_ohm, (unsigned)bat.r_bot_ohm);

#ifdef CONFIG_PLANT_UPLOAD
    {   /* 4.F3 slice 3 (UNVERIFIED on hardware): one wake = read once, buffer, maybe report, deep sleep to the next 15-min boundary. */
        nw_soil_t soil = {0};
        nw_aht20_t aht = {0};
        nw_bh1750_t bh = {0};
        uint32_t vbat = 0, vadc = 0;
        nw_err_t e_soil = NW_SOIL_ANALOG ? nw_soil_measure(&hal, &cal, &soil) : NW_ERR_UNSUPPORTED;
        nw_err_t e_aht = nw_aht20_read(&hal, &aht);
        nw_err_t e_bh = nw_bh1750_read(&hal, &bh);
        nw_err_t e_bat = nw_battery_measure(&hal, &bat, &vbat, &vadc);
        uint32_t sleep_s = nw_upload_idf_wake(&soil, e_soil, &aht, e_aht, &bh, e_bh, vbat, e_bat);
        ESP_LOGI(TAG, "NWUPLOAD sleep s=%u", (unsigned)sleep_s);
        fflush(stdout);
        nw_hal_esp32_prepare_deep_sleep();
        esp_sleep_enable_timer_wakeup((uint64_t)sleep_s * 1000000ULL);
        esp_deep_sleep_start();
    }
#endif

    for (int i = 0; i < CYCLES_BEFORE_SLEEP; i++) {
        nw_soil_t soil = {0};
        nw_aht20_t aht = {0};
        nw_bh1750_t bh = {0};
        uint32_t vbat = 0, vadc = 0;
        nw_err_t e_soil = NW_SOIL_ANALOG ? nw_soil_measure(&hal, &cal, &soil) : NW_ERR_UNSUPPORTED;
        nw_err_t e_aht = nw_aht20_read(&hal, &aht);
        nw_err_t e_bh = nw_bh1750_read(&hal, &bh);
        nw_err_t e_bat = nw_battery_measure(&hal, &bat, &vbat, &vadc);
        char pct[16], t[16], rh[16], lux[16];
        fmt_x(pct, sizeof pct, soil.pct_x10, 1);
        fmt_x(t, sizeof t, aht.temp_c_x100, 2);
        fmt_x(rh, sizeof rh, aht.rh_x100, 2);
        fmt_x(lux, sizeof lux, bh.lux_x10, 1);
        printf("NWBENCH wake=%d i=%d soil_raw=%d soil_pct=%s soil_flags=0x%02x temp_c=%s rh_pct=%s lux=%s lux_raw=%u "
               "vbat_mv=%u vbat_adc_mv=%u vbat_plausible=%d divider_na=%u err=soil:%d,aht:%d,bh:%d,bat:%d\n",
               wake_count, i, soil.raw, pct, soil.flags, t, rh, lux, bh.raw, (unsigned)vbat, (unsigned)vadc,
               nw_battery_plausible(vbat), (unsigned)nw_battery_divider_na(vbat, &bat), e_soil, e_aht, e_bh, e_bat);
        vTaskDelay(pdMS_TO_TICKS(2000));
    }

    printf("NWBENCH sleep s=%d (IO3 must read 0 V now)\n", SLEEP_S);
    fflush(stdout);
    nw_hal_esp32_prepare_deep_sleep();
    esp_sleep_enable_timer_wakeup((uint64_t)SLEEP_S * 1000000ULL);
    esp_deep_sleep_start();
}

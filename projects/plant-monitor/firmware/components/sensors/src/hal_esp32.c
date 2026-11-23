/* ESP-IDF v5.4 HAL for the sensor drivers. Written against the v5.4 docs from memory of the API, built by CI only:
 * no ESP-IDF toolchain was available in the authoring session, so this file has NOT been compiled by its author. */
#include "nw_hal_esp32.h"
#include "nw_aht20.h"
#include "nw_bh1750.h"

#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "nw_hal";

static struct {
    i2c_master_bus_handle_t bus;
    i2c_master_dev_handle_t aht20;
    i2c_master_dev_handle_t bh1750;
    adc_oneshot_unit_handle_t adc;
    adc_cali_handle_t cali[2];
    int chan[2];
    int soil_pwr;
} s;

#define I2C_TIMEOUT_MS 100

static i2c_master_dev_handle_t dev_for(uint8_t addr)
{
    if (addr == NW_AHT20_ADDR) return s.aht20;
    if (addr == NW_BH1750_ADDR) return s.bh1750;
    return NULL;
}

static int i2c_write(void *ctx, uint8_t addr, const uint8_t *buf, size_t len)
{
    (void)ctx;
    i2c_master_dev_handle_t d = dev_for(addr);
    return (d && i2c_master_transmit(d, buf, len, I2C_TIMEOUT_MS) == ESP_OK) ? 0 : -1;
}

static int i2c_read(void *ctx, uint8_t addr, uint8_t *buf, size_t len)
{
    (void)ctx;
    i2c_master_dev_handle_t d = dev_for(addr);
    return (d && i2c_master_receive(d, buf, len, I2C_TIMEOUT_MS) == ESP_OK) ? 0 : -1;
}

static void delay_ms(void *ctx, uint32_t ms)
{
    (void)ctx;
    TickType_t t = pdMS_TO_TICKS(ms);
    vTaskDelay(t ? t : 1);
}

static void soil_power(void *ctx, bool on)
{
    (void)ctx;
#ifdef CONFIG_PLANT_BENCH_SOIL_POWER_ON
    /* BENCH CI IMAGE ONLY (A-094): the supply stays on after the first reading. NFR-12 is not met on this image. */
    on = true;
#endif
    gpio_set_level((gpio_num_t)s.soil_pwr, on ? 1 : 0);
}

static int adc_read(void *ctx, nw_adc_ch_t ch, nw_adc_sample_t *out)
{
    (void)ctx;
    if ((int)ch < 0 || (int)ch > 1 || s.chan[ch] < 0 || !s.adc) return -1;
    int raw = 0;
    if (adc_oneshot_read(s.adc, (adc_channel_t)s.chan[ch], &raw) != ESP_OK) return -1;
    out->raw = raw;
    out->calibrated = false;
    out->mv = -1;
    if (s.cali[ch]) {
        int mv = 0;
        if (adc_cali_raw_to_voltage(s.cali[ch], raw, &mv) == ESP_OK) { out->mv = mv; out->calibrated = true; }
    }
    return 0;
}

static int adc_setup_channel(int idx, int channel)
{
    s.chan[idx] = channel;
    if (channel < 0) return 0;
    adc_oneshot_chan_cfg_t cc = {.atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_DEFAULT};
    if (adc_oneshot_config_channel(s.adc, (adc_channel_t)channel, &cc) != ESP_OK) return -1;
#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
    adc_cali_curve_fitting_config_t cf = {
        .unit_id = ADC_UNIT_1, .chan = (adc_channel_t)channel, .atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_DEFAULT};
    if (adc_cali_create_scheme_curve_fitting(&cf, &s.cali[idx]) != ESP_OK) {
        s.cali[idx] = NULL;
        ESP_LOGW(TAG, "ADC channel %d: no eFuse calibration, mV not available", channel);
    }
#endif
    return 0;
}

int nw_hal_esp32_init(const nw_hal_esp32_cfg_t *cfg, nw_hal_t *hal)
{
    if (!cfg || !hal) return -1;
    s.soil_pwr = cfg->soil_pwr_gpio;
    /* After deep sleep the pad is still held: release, then drive low (NFR-12: low unless measuring). */
    gpio_hold_dis((gpio_num_t)s.soil_pwr);
    gpio_config_t io = {.pin_bit_mask = 1ULL << s.soil_pwr, .mode = GPIO_MODE_OUTPUT};
    if (gpio_config(&io) != ESP_OK) return -1;
    gpio_set_level((gpio_num_t)s.soil_pwr, 0);

    i2c_master_bus_config_t bc = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = (gpio_num_t)cfg->sda_gpio,
        .scl_io_num = (gpio_num_t)cfg->scl_gpio,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true, /* breakouts / the board have their own 4.7 k pull-ups (R13, R14) */
    };
    if (i2c_new_master_bus(&bc, &s.bus) != ESP_OK) return -1;
    i2c_device_config_t dc = {.dev_addr_length = I2C_ADDR_BIT_LEN_7, .scl_speed_hz = cfg->i2c_hz ? cfg->i2c_hz : 100000};
    dc.device_address = NW_AHT20_ADDR;
    if (i2c_master_bus_add_device(s.bus, &dc, &s.aht20) != ESP_OK) return -1;
    dc.device_address = NW_BH1750_ADDR;
    if (i2c_master_bus_add_device(s.bus, &dc, &s.bh1750) != ESP_OK) return -1;

    adc_oneshot_unit_init_cfg_t uc = {.unit_id = ADC_UNIT_1};
    if (adc_oneshot_new_unit(&uc, &s.adc) != ESP_OK) return -1;
    if (adc_setup_channel(NW_ADC_BAT, cfg->adc_bat_channel) != 0) return -1;
    if (adc_setup_channel(NW_ADC_SOIL, cfg->adc_soil_channel) != 0) return -1;

    hal->ctx = &s;
    hal->i2c_write = i2c_write;
    hal->i2c_read = i2c_read;
    hal->delay_ms = delay_ms;
    hal->soil_power = soil_power;
    hal->adc_read = adc_read;
    return 0;
}

void nw_hal_esp32_prepare_deep_sleep(void)
{
    gpio_set_level((gpio_num_t)s.soil_pwr, 0);
    gpio_hold_en((gpio_num_t)s.soil_pwr);
    gpio_deep_sleep_hold_en();
}

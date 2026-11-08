/* Fake HAL: scripted I2C reads, recorded writes/delays/soil power, scripted ADC samples. */
#ifndef FAKE_HAL_H
#define FAKE_HAL_H
#include <string.h>
#include "nw_hal.h"

#define FK_MAX 64
typedef struct {
    /* I2C read script: each read pops the next entry (data, len) */
    uint8_t rd[FK_MAX][8]; size_t rd_len[FK_MAX]; int rd_n, rd_i;
    int rd_fail_at;            /* read index that fails (-1 none) */
    int wr_fail;               /* every write fails when set */
    /* recorded writes */
    uint8_t wr[FK_MAX][4]; size_t wr_len[FK_MAX]; uint8_t wr_addr[FK_MAX]; int wr_n;
    /* time and soil supply */
    uint32_t delays[FK_MAX]; int delay_n; uint32_t total_ms;
    int soil_on; int soil_toggles; int soil_on_at_adc_read_min_ms; uint32_t soil_on_since;
    int soil_was_on_at_read; int soil_ms_at_first_read;
    /* ADC script per channel */
    nw_adc_sample_t adc[2][16]; int adc_n[2], adc_i[2]; int adc_fail;
    int adc_reads[2];
} fake_t;

static inline int fk_wr(void *c, uint8_t a, const uint8_t *b, size_t n) {
    fake_t *f = c; if (f->wr_fail) return -1;
    if (f->wr_n < FK_MAX) { memcpy(f->wr[f->wr_n], b, n > 4 ? 4 : n); f->wr_len[f->wr_n] = n; f->wr_addr[f->wr_n++] = a; }
    return 0;
}
static inline int fk_rd(void *c, uint8_t a, uint8_t *b, size_t n) {
    fake_t *f = c; (void)a; int i = f->rd_i++;
    if (i == f->rd_fail_at || i >= f->rd_n) return -1;
    memcpy(b, f->rd[i], n < f->rd_len[i] ? n : f->rd_len[i]); return 0;
}
static inline void fk_dl(void *c, uint32_t ms) { fake_t *f = c; if (f->delay_n < FK_MAX) f->delays[f->delay_n++] = ms; f->total_ms += ms; }
static inline void fk_pw(void *c, bool on) { fake_t *f = c; if (on != (bool)f->soil_on) { f->soil_toggles++; if (on) f->soil_on_since = f->total_ms; } f->soil_on = on; }
static inline int fk_adc(void *c, nw_adc_ch_t ch, nw_adc_sample_t *o) {
    fake_t *f = c; if (f->adc_fail) return -1;
    if (ch == NW_ADC_SOIL) { if (f->adc_reads[ch] == 0) { f->soil_ms_at_first_read = (int)(f->total_ms - f->soil_on_since); } f->soil_was_on_at_read |= f->soil_on ? 0 : 0x100; }
    f->adc_reads[ch]++;
    int i = f->adc_i[ch]; if (i >= f->adc_n[ch]) i = f->adc_n[ch] - 1; f->adc_i[ch]++;
    *o = f->adc[ch][i]; return 0;
}
static inline void fk_init(fake_t *f, nw_hal_t *h) {
    memset(f, 0, sizeof *f); f->rd_fail_at = -1;
    h->ctx = f; h->i2c_write = fk_wr; h->i2c_read = fk_rd; h->delay_ms = fk_dl; h->soil_power = fk_pw; h->adc_read = fk_adc;
}
static inline void fk_push_rd(fake_t *f, const uint8_t *d, size_t n) { memcpy(f->rd[f->rd_n], d, n); f->rd_len[f->rd_n++] = n; }
static inline void fk_push_adc(fake_t *f, nw_adc_ch_t ch, int raw, int mv, bool cal) {
    nw_adc_sample_t s = {raw, mv, cal}; f->adc[ch][f->adc_n[ch]++] = s;
}
#endif

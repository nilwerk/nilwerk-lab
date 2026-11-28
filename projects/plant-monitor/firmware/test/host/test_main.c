#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "nwtest.h"
#include "fake_hal.h"
#include "nw_aht20.h"
#include "nw_bh1750.h"
#include "nw_soil.h"
#include "nw_battery.h"

int nwtest_failed, nwtest_checked;

/* ---------- AHT20 (FR-D01) ---------- */
static void frame(uint8_t *f, uint8_t status, uint32_t rh20, uint32_t t20) {
    f[0] = status; f[1] = rh20 >> 12; f[2] = rh20 >> 4; f[3] = (uint8_t)(((rh20 & 0xF) << 4) | (t20 >> 16));
    f[4] = t20 >> 8; f[5] = t20; f[6] = nw_aht20_crc8(f, 6);
}
static void test_aht20_crc(void) {
    const uint8_t v1[] = "123456789";                     /* CRC-8/NRSC-5 (poly 0x31, init 0xFF) check value 0xF7 */
    CHECK_EQ(nw_aht20_crc8(v1, 9), 0xF7);
    const uint8_t v2[] = {0xBE, 0xEF};                      /* Sensirion datasheet example: CRC(0xBEEF) = 0x92 */
    CHECK_EQ(nw_aht20_crc8(v2, 2), 0x92);
    CHECK_EQ(nw_aht20_crc8(v2, 0), 0xFF);                   /* init value */
}
static void test_aht20_decode(void) {
    uint8_t f[7]; nw_aht20_t r;
    frame(f, 0x1C, 0x80000, 0x80000);                       /* mid scale: 50 %RH, 50 degC */
    CHECK_EQ(nw_aht20_decode(f, &r), NW_OK); CHECK_EQ(r.rh_x100, 5000); CHECK_EQ(r.temp_c_x100, 5000);
    frame(f, 0x1C, 0, 0);                                   /* 0 %RH, -50 degC */
    CHECK_EQ(nw_aht20_decode(f, &r), NW_OK); CHECK_EQ(r.rh_x100, 0); CHECK_EQ(r.temp_c_x100, -5000);
    frame(f, 0x1C, 0xFFFFF, 0xFFFFF);                       /* full scale: 100 %RH, 150 degC */
    CHECK_EQ(nw_aht20_decode(f, &r), NW_OK); CHECK_EQ(r.rh_x100, 10000); CHECK_EQ(r.temp_c_x100, 15000);
    /* 23.45 degC -> raw = (23.45+50)/200 * 2^20 = 385,090 (0x5E0C2); 41.25 %RH -> raw = 0.4125 * 2^20 = 432,538 (0x69A5A) */
    frame(f, 0x1C, 432538, 385090);
    CHECK_EQ(nw_aht20_decode(f, &r), NW_OK);
    CHECK(r.temp_c_x100 >= 2344 && r.temp_c_x100 <= 2346); CHECK(r.rh_x100 >= 4124 && r.rh_x100 <= 4126);
    /* nibble split: RH low nibble sits in the high nibble of byte 3, T high nibble in its low nibble */
    frame(f, 0x1C, 0x0000F, 0x00000);  CHECK_EQ(nw_aht20_decode(f, &r), NW_OK); CHECK_EQ(r.temp_c_x100, -5000);
    frame(f, 0x1C, 0x40038, 0);  CHECK_EQ(nw_aht20_decode(f, &r), NW_OK); CHECK_EQ(r.rh_x100, 2501); /* low nibble 8 decides the rounding: 25.0100 not 25.0000 */
    frame(f, 0x1C, 0x00000, 0xF0000);  CHECK_EQ(nw_aht20_decode(f, &r), NW_OK); CHECK_EQ(r.rh_x100, 0);
    CHECK(r.temp_c_x100 > 9000);
}
static void test_aht20_decode_errors(void) {
    uint8_t f[7]; nw_aht20_t r;
    frame(f, 0x1C, 0x80000, 0x80000); f[6] ^= 0x01;
    CHECK_EQ(nw_aht20_decode(f, &r), NW_ERR_CRC);
    frame(f, 0x1C, 0x80000, 0x80000); f[2] ^= 0x10;         /* data bit flip */
    CHECK_EQ(nw_aht20_decode(f, &r), NW_ERR_CRC);
    frame(f, 0x9C, 0x80000, 0x80000);                       /* busy bit */
    CHECK_EQ(nw_aht20_decode(f, &r), NW_ERR_BUSY);
    CHECK_EQ(nw_aht20_decode(NULL, &r), NW_ERR_ARG);
}
static void test_aht20_read_flow(void) {
    fake_t f; nw_hal_t h; fk_init(&f, &h); nw_aht20_t r; uint8_t fr[7], st = 0x18;
    fk_push_rd(&f, &st, 1); frame(fr, 0x1C, 0x80000, 0x80000); fk_push_rd(&f, fr, 7);
    CHECK_EQ(nw_aht20_read(&h, &r), NW_OK); CHECK_EQ(r.temp_c_x100, 5000);
    CHECK_EQ(f.wr_n, 1);                                    /* calibrated: no init command, only the trigger */
    CHECK(f.wr_len[0] == 3 && f.wr[0][0] == 0xAC && f.wr[0][1] == 0x33 && f.wr[0][2] == 0x00 && f.wr_addr[0] == 0x38);
    CHECK(f.delays[0] >= 80);                               /* datasheet: wait 80 ms before reading */
    /* not calibrated: init 0xBE 0x08 0x00 first */
    fk_init(&f, &h); st = 0x00; fk_push_rd(&f, &st, 1); fk_push_rd(&f, fr, 7);
    CHECK_EQ(nw_aht20_read(&h, &r), NW_OK); CHECK_EQ(f.wr_n, 2);
    CHECK(f.wr[0][0] == 0xBE && f.wr[0][1] == 0x08 && f.wr[0][2] == 0x00 && f.wr[1][0] == 0xAC);
    /* busy twice, then ready */
    fk_init(&f, &h); st = 0x18; fk_push_rd(&f, &st, 1);
    uint8_t busy[7]; frame(busy, 0x9C, 0, 0); fk_push_rd(&f, busy, 7); fk_push_rd(&f, busy, 7); fk_push_rd(&f, fr, 7);
    CHECK_EQ(nw_aht20_read(&h, &r), NW_OK);
    /* busy forever -> NW_ERR_BUSY after a bounded number of tries */
    fk_init(&f, &h); fk_push_rd(&f, &st, 1); for (int i = 0; i < 12; i++) fk_push_rd(&f, busy, 7);
    CHECK_EQ(nw_aht20_read(&h, &r), NW_ERR_BUSY); CHECK(f.rd_i <= 8);
    /* I2C errors */
    fk_init(&f, &h); fk_push_rd(&f, &st, 1); f.wr_fail = 1; CHECK_EQ(nw_aht20_read(&h, &r), NW_ERR_IO);
    fk_init(&f, &h); CHECK_EQ(nw_aht20_read(&h, &r), NW_ERR_IO);   /* no device answers */
    fk_init(&f, &h); fk_push_rd(&f, &st, 1); fk_push_rd(&f, fr, 7); f.rd_fail_at = 1; CHECK_EQ(nw_aht20_read(&h, &r), NW_ERR_IO);
    /* CRC error is passed up */
    fk_init(&f, &h); fk_push_rd(&f, &st, 1); fr[6] ^= 0xFF; fk_push_rd(&f, fr, 7); CHECK_EQ(nw_aht20_read(&h, &r), NW_ERR_CRC);
}

/* ---------- BH1750 (FR-D01) ---------- */
static void test_bh1750_convert(void) {
    nw_bh1750_t r;
    CHECK_EQ(nw_bh1750_convert(0, &r), NW_OK); CHECK_EQ(r.lux_x10, 0); CHECK(!r.saturated);
    nw_bh1750_convert(12, &r);    CHECK_EQ(r.lux_x10, 100);     /* 12 / 1.2 = 10.0 lx */
    nw_bh1750_convert(120, &r);   CHECK_EQ(r.lux_x10, 1000);    /* 100.0 lx */
    nw_bh1750_convert(1, &r);     CHECK_EQ(r.lux_x10, 8);       /* 0.833 lx -> 0.8 */
    nw_bh1750_convert(54612, &r); CHECK(r.lux_x10 >= 455099 && r.lux_x10 <= 455101); /* 45510 lx */
    nw_bh1750_convert(0xFFFF, &r); CHECK(r.saturated); CHECK(r.lux_x10 / 10 <= 100000); /* FR-D01 range limit */
    nw_bh1750_convert(0xFFFE, &r); CHECK(!r.saturated);
    CHECK_EQ(nw_bh1750_convert(1, NULL), NW_ERR_ARG);
}
static void test_bh1750_flow(void) {
    fake_t f; nw_hal_t h; fk_init(&f, &h); nw_bh1750_t r; uint8_t d[2] = {0x01, 0x2C}; /* 300 -> 250.0 lx */
    fk_push_rd(&f, d, 2);
    CHECK_EQ(nw_bh1750_read(&h, &r), NW_OK); CHECK_EQ(r.raw, 0x012C); CHECK_EQ(r.lux_x10, 2500);
    CHECK_EQ(f.wr_n, 2); CHECK(f.wr[0][0] == 0x01 && f.wr[1][0] == 0x20 && f.wr_addr[0] == 0x23 && f.wr_len[0] == 1);
    CHECK(f.delays[0] >= 180);                              /* max measurement time, H-resolution */
    fk_init(&f, &h); fk_push_rd(&f, d, 2); f.wr_fail = 1; CHECK_EQ(nw_bh1750_read(&h, &r), NW_ERR_IO);
    fk_init(&f, &h); CHECK_EQ(nw_bh1750_read(&h, &r), NW_ERR_IO);
}

/* ---------- soil calibration (FR-D10, FR-D01, NFR-02) ----------
 * Direction (owner bench, 28 Nov): raw is LOW in dry air (15-25 counts) and HIGH in water (about 360). Calibration defaults 20 / 360. */
static void test_soil_normalise(void) {
    nw_soil_t r; nw_soil_cal_t c = {20, 360};
    CHECK_EQ(nw_soil_normalise(&c, 20, &r), NW_OK); CHECK_EQ(r.pct_x10, 0); CHECK_EQ(r.flags, 0);
    CHECK_EQ(nw_soil_normalise(&c, 360, &r), NW_OK); CHECK_EQ(r.pct_x10, 1000); CHECK_EQ(r.flags, 0);
    nw_soil_normalise(&c, 190, &r); CHECK_EQ(r.pct_x10, 500);                /* midpoint */
    nw_soil_normalise(&c, 100, &r); CHECK_EQ(r.pct_x10, 235);                /* 80/340 = 23.5 % */
    nw_soil_normalise(&c, 300, &r); CHECK_EQ(r.pct_x10, 824);                /* 280/340 = 82.35 % */
    nw_soil_normalise(&c, 25, &r);  CHECK_EQ(r.pct_x10, 15);                 /* owner air reading: 1.5 %, not clamped */
    CHECK_EQ(r.flags, 0);
    nw_soil_normalise(&c, 15, &r);  CHECK_EQ(r.pct_x10, 0); CHECK_EQ(r.flags, NW_SOIL_F_CLAMPED_DRY);
    nw_soil_normalise(&c, 400, &r); CHECK_EQ(r.pct_x10, 1000); CHECK_EQ(r.flags, NW_SOIL_F_CLAMPED_WET);
    nw_soil_normalise(&c, 4095, &r); CHECK_EQ(r.pct_x10, 1000); CHECK(r.flags & NW_SOIL_F_RAIL); CHECK(r.flags & NW_SOIL_F_CLAMPED_WET);
    nw_soil_normalise(&c, 0, &r);    CHECK_EQ(r.pct_x10, 0);    CHECK(r.flags & NW_SOIL_F_RAIL); CHECK(r.flags & NW_SOIL_F_CLAMPED_DRY);
    /* direction: wetter (higher count) must never read drier; checked on every count from dry to wet */
    int prev = -1;
    for (int raw = 20; raw <= 360; raw++) {
        nw_soil_normalise(&c, raw, &r);
        CHECK(r.pct_x10 >= prev && r.pct_x10 >= 0 && r.pct_x10 <= 1000);
        prev = r.pct_x10;
    }
    /* a swapped pair (dry above wet, e.g. the old 2800/1200 placeholders) is refused, not inverted */
    nw_soil_cal_t swapped = {360, 20}; CHECK_EQ(nw_soil_normalise(&swapped, 190, &r), NW_ERR_CAL);
    nw_soil_cal_t old_placeholder = {2800, 1200}; CHECK_EQ(nw_soil_normalise(&old_placeholder, 2000, &r), NW_ERR_CAL);
    /* bad calibration */
    nw_soil_cal_t bad = {200, 200};    CHECK_EQ(nw_soil_normalise(&bad, 200, &r), NW_ERR_CAL);
    nw_soil_cal_t near = {100, 149};   CHECK_EQ(nw_soil_normalise(&near, 120, &r), NW_ERR_CAL);   /* span 49 < 50 */
    nw_soil_cal_t ok = {100, 150};     CHECK_EQ(nw_soil_normalise(&ok, 125, &r), NW_OK); CHECK_EQ(r.pct_x10, 500);
    CHECK_EQ(nw_soil_normalise(NULL, 1, &r), NW_ERR_ARG);
}
static void test_soil_measure(void) {
    fake_t f; nw_hal_t h; fk_init(&f, &h); nw_soil_t r; nw_soil_cal_t c = {20, 360};
    int raws[5] = {190, 200, 180, 195, 185};
    for (int i = 0; i < 5; i++) fk_push_adc(&f, NW_ADC_SOIL, raws[i], 0, true);
    CHECK_EQ(nw_soil_measure(&h, &c, &r), NW_OK); CHECK_EQ(r.raw, 190); CHECK_EQ(r.pct_x10, 500);
    CHECK_EQ(f.adc_reads[NW_ADC_SOIL], 5);
    CHECK_EQ(f.soil_on, 0);                                  /* NFR-12: supply off after the measurement */
    CHECK_EQ(f.soil_toggles, 2);                             /* on once, off once */
    CHECK(f.soil_ms_at_first_read >= 1500);                  /* >= 1.5 s warm-up before the first conversion */
    CHECK_EQ(f.soil_was_on_at_read & 0x100, 0);              /* supply was on at every conversion */
    /* ADC error: still powers off */
    fk_init(&f, &h); f.adc_fail = 1; CHECK_EQ(nw_soil_measure(&h, &c, &r), NW_ERR_IO); CHECK_EQ(f.soil_on, 0); CHECK_EQ(f.soil_toggles, 2);
    /* bad calibration: powered off, error reported after the read */
    fk_init(&f, &h); for (int i = 0; i < 5; i++) fk_push_adc(&f, NW_ADC_SOIL, 190, 0, true);
    nw_soil_cal_t bad = {1000, 1000}; CHECK_EQ(nw_soil_measure(&h, &bad, &r), NW_ERR_CAL); CHECK_EQ(f.soil_on, 0);
    /* averaging rounds to nearest */
    fk_init(&f, &h); int r2[5] = {190, 190, 190, 190, 193}; for (int i = 0; i < 5; i++) fk_push_adc(&f, NW_ADC_SOIL, r2[i], 0, true);
    nw_soil_measure(&h, &c, &r); CHECK_EQ(r.raw, 191);
}

/* ---------- battery (FR-D01, NFR-01, NFR-12) ---------- */
static void test_battery(void) {
    nw_battery_cfg_t c = {1000000u, 1000000u};
    CHECK_EQ(nw_battery_mv_from_adc(2100, &c), 4200);        /* 2:1 divider */
    CHECK_EQ(nw_battery_mv_from_adc(1850, &c), 3700);
    CHECK_EQ(nw_battery_mv_from_adc(0, &c), 0);
    CHECK_EQ(nw_battery_mv_from_adc(1500, &c), 3000);
    nw_battery_cfg_t u = {1000000u, 500000u};                /* ratio 3: not 2, so the formula uses the config */
    CHECK_EQ(nw_battery_mv_from_adc(1000, &u), 3000);
    nw_battery_cfg_t odd = {1u, 2u};                         /* rounding: 1001 * 3 / 2 = 1501.5 -> 1502 */
    CHECK_EQ(nw_battery_mv_from_adc(1001, &odd), 1502);
    nw_battery_cfg_t z = {1000, 0}; CHECK_EQ(nw_battery_mv_from_adc(1000, &z), 0);
    CHECK_EQ(nw_battery_mv_from_adc(1000, NULL), 0);
    /* plausible range 3.0 .. 4.25 V, inclusive (docs/requirements-v1.0-delta.md FR-D01) */
    CHECK(!nw_battery_plausible(2999)); CHECK(nw_battery_plausible(3000)); CHECK(nw_battery_plausible(4250)); CHECK(!nw_battery_plausible(4251));
    /* divider current: 4.2 V / 2 MOhm = 2.1 uA = 2100 nA (pcb/pinmap-sleep.md:36); 3.7 V -> 1.85 uA; dev kit 2 x 100 k = 21 uA */
    CHECK_EQ(nw_battery_divider_na(4200, &c), 2100);
    CHECK_EQ(nw_battery_divider_na(3700, &c), 1850);
    nw_battery_cfg_t dk = {100000u, 100000u}; CHECK_EQ(nw_battery_divider_na(4200, &dk), 21000);
    CHECK_EQ(nw_battery_divider_na(4200, &z), 4200u * 1000000u / 1000u);
    /* measure: dummy read + 4 averaged, needs calibrated mV */
    fake_t f; nw_hal_t h; fk_init(&f, &h); uint32_t v = 0, a = 0;
    fk_push_adc(&f, NW_ADC_BAT, 2500, 9999, true);           /* dummy, must be discarded */
    int mv[4] = {1990, 1994, 1996, 2000};
    for (int i = 0; i < 4; i++) fk_push_adc(&f, NW_ADC_BAT, 2400, mv[i], true);
    CHECK_EQ(nw_battery_measure(&h, &c, &v, &a), NW_OK); CHECK_EQ(a, 1995); CHECK_EQ(v, 3990);
    CHECK_EQ(f.adc_reads[NW_ADC_BAT], 5); CHECK(f.delay_n >= 4 && f.delays[0] >= 100);
    CHECK_EQ(f.soil_toggles, 0);                             /* battery read does not touch the soil supply; IO1 has no driver at all */
    fk_init(&f, &h); for (int i = 0; i < 5; i++) fk_push_adc(&f, NW_ADC_BAT, 2400, -1, false);
    CHECK_EQ(nw_battery_measure(&h, &c, &v, &a), NW_ERR_CAL);
    fk_init(&f, &h); f.adc_fail = 1; CHECK_EQ(nw_battery_measure(&h, &c, &v, &a), NW_ERR_IO);
    CHECK_EQ(nw_battery_measure(&h, &z, &v, &a), NW_ERR_ARG);
}

int main(void) {
    test_aht20_crc(); test_aht20_decode(); test_aht20_decode_errors(); test_aht20_read_flow();
    test_bh1750_convert(); test_bh1750_flow();
    test_soil_normalise(); test_soil_measure();
    test_battery();
    printf("%d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}

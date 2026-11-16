/* Offline sample buffer (task 4.F3, FR-D04). 96 slots = 24 h at one sample per 15 min (FR-D01, FR-D02).
 * When full, the OLDEST sample is overwritten (wrap), so the NEWEST sample is always kept. Samples leave the buffer
 * only through nw_ring_consume(), which the caller calls after a 2xx for the batch that held them (openapi.yaml
 * /ingest: "The device deletes a sample from its buffer only after a 2xx for the batch containing it").
 * Pure C, no ESP-IDF; host-tested in firmware/test/host. */
#ifndef NW_SAMPLE_RING_H
#define NW_SAMPLE_RING_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define NW_RING_CAP 96            /* FR-D04: 24 h of 15-min samples (96 x 15 min = 24 h) */
#define NW_SAMPLE_PERIOD_S 900    /* FR-D01 / FR-D02: 15 min */

/* present bits: a clear bit = no valid reading for that field -> JSON null in the report (schema: "null = sensor failed") */
#define NW_HAS_MOISTURE     0x01
#define NW_HAS_MOISTURE_RAW 0x02
#define NW_HAS_TEMP         0x04
#define NW_HAS_RH           0x08
#define NW_HAS_LUX          0x10
#define NW_HAS_VBAT         0x20

typedef struct {
    uint32_t ts;            /* unix seconds from the RTC at the sample (schema samples[].ts, FR-D01) */
    uint8_t  present;       /* NW_HAS_* bits */
    uint16_t moisture_x10;  /* 0..1000 = 0.0..100.0 % (nw_soil_t.pct_x10) */
    uint16_t moisture_raw;  /* 0..4095 12-bit ADC counts (nw_soil_t.raw) */
    int32_t  temp_x100;     /* air degC * 100 (nw_aht20_t.temp_c_x100) */
    int32_t  rh_x100;       /* air %RH * 100 (nw_aht20_t.rh_x100) */
    uint32_t lux_x10;       /* lux * 10 (nw_bh1750_t.lux_x10) */
    uint16_t vbat_mv;       /* battery mV (nw_battery_measure) */
} nw_sample_t;

typedef struct {
    nw_sample_t slot[NW_RING_CAP];
    uint16_t head;          /* index of the next write */
    uint16_t count;         /* samples stored, 0..NW_RING_CAP */
    uint32_t overwritten;   /* samples lost to wrap since init (diagnostic; shown in the Agent Log, not sent) */
} nw_ring_t;

void nw_ring_init(nw_ring_t *r);
/* Appends s. When the ring is full the oldest sample is overwritten. The new sample is always stored.
 * Returns true when an older sample was overwritten. */
bool nw_ring_push(nw_ring_t *r, const nw_sample_t *s);
size_t nw_ring_count(const nw_ring_t *r);
/* i = 0 is the oldest stored sample. NULL when i >= count. */
const nw_sample_t *nw_ring_at(const nw_ring_t *r, size_t i);
/* The most recent sample, NULL when empty. */
const nw_sample_t *nw_ring_newest(const nw_ring_t *r);
/* Removes the n oldest samples (after a 2xx for a batch that held them). Removes at most count. Returns how many were removed. */
size_t nw_ring_consume(nw_ring_t *r, size_t n);

#endif

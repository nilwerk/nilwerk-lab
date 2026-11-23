/* Offline sample buffer (task 4.F3, FR-D04). 96 slots = 24 h at one sample per 15 min (FR-D01, FR-D02).
 * When full, the OLDEST sample is overwritten (wrap), so the NEWEST sample is always kept.
 *
 * Acknowledgement (openapi.yaml /ingest: "The device deletes a sample from its buffer only after a 2xx for the batch
 * containing it"): every stored sample has a sequence number. A batch is identified by the seq of its LAST sample
 * (nw_report_build returns it). After a 2xx, nw_ring_consume_upto(last_seq) removes only samples with seq <= last_seq.
 * Samples that arrived during the upload have a larger seq and are never removed by the ack, even when the ring wrapped
 * during the upload (review C1: a count-based consume would drop unsent samples in that case).
 *
 * Admission (review C2): nw_ring_push refuses a sample while the clock is not synced and refuses a sample outside the
 * schema ranges, so no invalid sample can make a whole batch fail with 400 later.
 * Pure C, no ESP-IDF; host-tested in firmware/test/host. */
#ifndef NW_SAMPLE_RING_H
#define NW_SAMPLE_RING_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define NW_RING_CAP 96            /* FR-D04: 24 h of 15-min samples (96 x 15 min = 24 h) */
#define NW_SAMPLE_PERIOD_S 900    /* FR-D01 / FR-D02: 15 min */
#ifdef CONFIG_PLANT_BENCH_UPLOAD_MINUTE
#undef NW_SAMPLE_PERIOD_S
#define NW_SAMPLE_PERIOD_S 60     /* BENCH CI IMAGE ONLY: 1 min, must equal NW_SLEEP_SAMPLE_PERIOD_S (nw_sleep.c static assert) */
#endif

/* Single source for the unix-time floor: schema minimum of samples[].ts, sent_at and events[].ts
 * (docs/interfaces/device-report.schema.json). Nov 2023. A clock below this has not been SNTP-synced. */
#define NW_TS_MIN 1700000000u

/* present bits: a clear bit = no valid reading for that field -> JSON null in the report (schema: "null = sensor failed") */
#define NW_HAS_MOISTURE     0x01
#define NW_HAS_MOISTURE_RAW 0x02
#define NW_HAS_TEMP         0x04
#define NW_HAS_RH           0x08
#define NW_HAS_LUX          0x10
#define NW_HAS_VBAT         0x20
#define NW_PRESENT_MASK     0x3F

typedef struct {
    uint32_t seq;           /* set by nw_ring_push: 1, 2, 3, ... never reused. Orders samples across wraps and acks. */
    uint32_t ts;            /* unix seconds from the RTC at the sample (schema samples[].ts, FR-D01) */
    uint8_t  present;       /* NW_HAS_* bits */
    uint16_t moisture_x10;  /* 0..1000 = 0.0..100.0 % (nw_soil_t.pct_x10) */
    uint16_t moisture_raw;  /* 0..4095 12-bit ADC counts (nw_soil_t.raw) */
    int32_t  temp_x100;     /* air degC * 100 (nw_aht20_t.temp_c_x100) */
    int32_t  rh_x100;       /* air %RH * 100 (nw_aht20_t.rh_x100), 0..10000 when present */
    uint32_t lux_x10;       /* lux * 10 (nw_bh1750_t.lux_x10) */
    uint16_t vbat_mv;       /* battery mV (nw_battery_measure) */
} nw_sample_t;

typedef enum {
    NW_PUSH_STORED = 0,
    NW_PUSH_STORED_OVERWROTE,    /* stored; the oldest sample was lost to the wrap */
    NW_PUSH_REJECTED_UNSYNCED,   /* time_synced false: nothing stored */
    NW_PUSH_REJECTED_INVALID     /* outside the schema ranges (see nw_ring_push), or NULL argument */
} nw_push_t;

typedef struct {
    nw_sample_t slot[NW_RING_CAP];
    uint16_t head;          /* index of the next write */
    uint16_t count;         /* samples stored, 0..NW_RING_CAP */
    uint32_t next_seq;      /* last seq handed out (0 before the first push) */
    uint32_t overwritten;   /* samples lost to wrap since init (diagnostic; shown in the Agent Log, not sent) */
    uint32_t rejected;      /* samples refused by nw_ring_push (diagnostic) */
} nw_ring_t;

void nw_ring_init(nw_ring_t *r);
/* Admits and appends s, assigning s->seq in the ring. Refused (nothing stored) when time_synced is false or the sample is
 * outside the schema ranges: ts < NW_TS_MIN, present bits outside NW_PRESENT_MASK, moisture_x10 > 1000 (when present),
 * moisture_raw > 4095 (when present), rh_x100 outside 0..10000 (when present). When full, the oldest sample is
 * overwritten and NW_PUSH_STORED_OVERWROTE is returned. */
nw_push_t nw_ring_push(nw_ring_t *r, const nw_sample_t *s, bool time_synced);
size_t nw_ring_count(const nw_ring_t *r);
/* i = 0 is the oldest stored sample. NULL when i >= count. */
const nw_sample_t *nw_ring_at(const nw_ring_t *r, size_t i);
/* The most recent sample, NULL when empty. */
const nw_sample_t *nw_ring_newest(const nw_ring_t *r);
/* Removes stored samples with seq <= last_seq, oldest first, and stops at the first newer one. Returns how many were
 * removed. Pass the last_seq of the batch that was acknowledged (2xx), never a count. */
size_t nw_ring_consume_upto(nw_ring_t *r, uint32_t last_seq);

/* RTC-memory integrity check (FR-D04, NFR-01): after a brown-out or a flash/reset the retained ring can hold garbage that still carries a valid
 * magic. True only when head < NW_RING_CAP, count <= NW_RING_CAP, every stored sample passes the admission rules, seq runs strictly up from the
 * oldest to the newest and the newest seq equals next_seq. A false result means: nw_ring_init() and start again (samples lost, never replayed). */
bool nw_ring_valid(const nw_ring_t *r);

#endif

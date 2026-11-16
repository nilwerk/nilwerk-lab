/* Hourly report payload (task 4.F3, FR-D02, FR-D04). Builds the POST /ingest body from the offline buffer.
 * Contract: projects/plant-monitor/docs/interfaces/device-report.schema.json (v1) and openapi.yaml /ingest.
 * Pure C, no ESP-IDF, no network: the upload (HTTPS client, Wi-Fi) is NOT in this component and NOT working yet.
 *
 * Field by field (JSON key -> source on the device):
 *   v            constant 1                                   (schema const 1)
 *   sent_at      meta.sent_at, RTC unix s after SNTP sync    (schema: min 1700000000, never before SNTP)
 *   trigger      meta.trigger: scheduled | critical | reconnect (schema enum)
 *   fw           meta.fw, running firmware version string    (maxLength 32)
 *   model        meta.model, edge-AI model-set version       (maxLength 32, optional: omitted when NULL)
 *   forecast_h   meta.forecast_x10 / 10, Model A output; null until the model has one (0..72)
 *   cal          meta.cal {dry_raw, wet_raw, at}: sent whenever changed (optional: omitted when NULL)
 *   samples[]    the buffered samples, oldest first, up to 192 (schema maxItems); fields below
 *     ts           sample.ts, RTC unix s at the sample
 *     moisture_pct sample.moisture_x10 / 10 (nw_soil pct_x10), null if NW_HAS_MOISTURE clear
 *     moisture_raw sample.moisture_raw (12-bit ADC), null if NW_HAS_MOISTURE_RAW clear
 *     temp_c       sample.temp_x100 / 100 (AHT20), null if NW_HAS_TEMP clear
 *     rh_pct       sample.rh_x100 / 100 (AHT20), null if NW_HAS_RH clear
 *     lux          sample.lux_x10 / 10 (BH1750), null if NW_HAS_LUX clear
 *     vbat_mv      sample.vbat_mv (divider ADC), null if NW_HAS_VBAT clear
 *   events[]     meta.events: type and ts (schema enum; max 32)
 *   ota          NOT emitted: OTA is out of scope for 4.F3 (FR-D05, server returns fw_target null in 4.B2)
 */
#ifndef NW_REPORT_H
#define NW_REPORT_H

#include <stddef.h>
#include <stdint.h>
#include "nw_sample_ring.h"

#define NW_REPORT_V 1                    /* schema const v */
#define NW_REPORT_MAX_SAMPLES 192        /* schema samples.maxItems; openapi 413 above this */
#define NW_REPORT_MAX_EVENTS 32          /* schema events.maxItems */
#define NW_REPORT_TS_MIN 1700000000u     /* schema minimum for sent_at, ts, events[].ts (unix s, Nov 2023) */
#define NW_REPORT_VERSION_MAX 32         /* schema fw/model/maxLength */
#define NW_REPORT_FORECAST_MAX_X10 720   /* schema forecast_h maximum 72.0 h */
#define NW_REPORT_FORECAST_NULL INT32_MIN /* meta.forecast_x10 value meaning "null, no forecast yet" */

typedef enum {                           /* order = schema enum order */
    NW_TRIG_SCHEDULED = 0,               /* hourly, FR-D02 */
    NW_TRIG_CRITICAL = 1,                /* immediate, FR-E03 */
    NW_TRIG_RECONNECT = 2                /* first report after offline, FR-D04 */
} nw_trigger_t;

typedef enum {                           /* order = schema enum order (device-report.schema.json events[].type) */
    NW_EV_WETTING = 0,
    NW_EV_WETTING_UNEXPECTED,
    NW_EV_FAST_DRYING,
    NW_EV_WATERLOGGED,
    NW_EV_SENSOR_OUT_OF_SOIL,
    NW_EV_SENSOR_FAULT
} nw_event_type_t;

typedef struct {
    uint32_t ts;
    nw_event_type_t type;
} nw_event_t;

typedef struct {                         /* calibration raw counts, schema cal.* */
    uint16_t dry_raw;                    /* 0..4095 */
    uint16_t wet_raw;                    /* 0..4095 */
    uint32_t at;                         /* unix s of the calibration; 0 = omit */
} nw_report_cal_t;

typedef struct {
    uint32_t sent_at;                    /* device unix s, must be >= NW_REPORT_TS_MIN */
    nw_trigger_t trigger;
    const char *fw;                      /* [A-Za-z0-9._-], at most 32 chars */
    const char *model;                   /* same charset; NULL = omit */
    int32_t forecast_x10;                /* hours * 10, 0..720, or NW_REPORT_FORECAST_NULL */
    const nw_report_cal_t *cal;          /* NULL = omit */
    const nw_event_t *events;            /* may be NULL when n_events == 0 */
    size_t n_events;
} nw_report_meta_t;

/* Writes the JSON body into out (NUL-terminated, cap bytes incl. NUL). Takes the buffered samples oldest first,
 * at most NW_REPORT_MAX_SAMPLES. *n_samples receives how many were written (0 on error): the caller must call
 * nw_ring_consume(r, *n_samples) only after a 2xx, so samples that arrive during the upload are kept.
 * Returns the length without the NUL, or 0 on error: buffer too small, empty buffer, a value outside the schema
 * (fw/model/forecast/event/cal range, sent_at or any sample ts before NW_REPORT_TS_MIN, e.g. RTC never synced). */
size_t nw_report_build(char *out, size_t cap, const nw_ring_t *r, const nw_report_meta_t *m, size_t *n_samples);

#endif

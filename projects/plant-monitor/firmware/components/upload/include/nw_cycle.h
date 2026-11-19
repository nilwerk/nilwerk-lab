/* One wake of the upload build (task 4.F3 slice 3, FR-D01, FR-D02, FR-D04, FR-D06, NFR-01, NFR-06). Pure C, no ESP-IDF.
 * Everything the ESP-IDF adapter (nw_upload_idf.c) needs to DECIDE lives here so it runs on the host; the adapter only does I/O.
 * Order per wake (the adapter follows it):
 *   1. clock: if !nw_cycle_clock_ok(now) -> Wi-Fi + SNTP first (the ring refuses unsynced samples), then read the clock again
 *   2. nw_cycle_begin(): admit this wake's sample into the RTC ring, decide report / sleep (nw_sleep_decide)
 *   3. plan.sleep.report != NONE -> Wi-Fi up, nw_cycle_report() (nw_upload_attempt), apply the result, Wi-Fi off
 *   4. deep sleep for nw_cycle_sleep_s()
 * NOT RUN ON HARDWARE. Critical events (FR-E03) have no producer yet (edge AI is not integrated), so critical_pending is always false. */
#ifndef NW_CYCLE_H
#define NW_CYCLE_H

#include <stdbool.h>
#include <stdint.h>
#include "nw_hal.h"
#include "nw_battery.h"
#include "nw_soil.h"
#include "nw_aht20.h"
#include "nw_bh1750.h"
#include "nw_prov.h"
#include "nw_sleep.h"
#include "nw_upload.h"

#define NW_CYCLE_MAGIC 0x4E574331u   /* "NWC1": bump when nw_cycle_state_t changes layout; a mismatch re-initialises the RTC copy */

/* Retained across deep sleep (RTC_DATA_ATTR in the adapter). Roughly 3 KB, mostly the 96-slot ring (RTC memory budget: check idf.py size). */
typedef struct {
    uint32_t magic;
    nw_ring_t ring;
    nw_upload_state_t up;
    uint32_t last_report_unix;   /* 0 = no report yet */
    bool low_battery;            /* FR-D06 state */
    bool outage_pending;         /* FR-D04: next report is trigger=reconnect */
} nw_cycle_state_t;

/* RTC memory budget (NFR-12: retained RTC memory counts against the deep-sleep current, so keep it small; ESP32-C3 has 8 KB of RTC fast memory
 * shared with the bootloader/Wi-Fi stack). The struct must stay under this; checked at compile time in nw_cycle.c. [proposed] limit, check idf.py size. */
#define NW_CYCLE_RTC_BUDGET_BYTES 4096u

/* Power-on RTC memory is not trustworthy: re-initialise unless the magic matches AND the content is self-consistent (FR-D04): ring invariants
 * (nw_ring_valid), bool fields 0/1, last_report_unix 0 or a synced time. Returns true when it (re)initialised (retained samples are then lost). */
bool nw_cycle_state_ensure(nw_cycle_state_t *st);
/* A clock below the schema floor (NW_TS_MIN, Nov 2023) has not been SNTP-synced (1970 after power-on). */
bool nw_cycle_clock_ok(uint32_t now_unix);

/* Stored credentials usable for an upload? 0 = yes. Wi-Fi SSID 1-32 bytes, passphrase empty (open) or 8-63, device token 64 lowercase hex.
 * The token itself is never copied or printed here. Record layout and NVS location: nw_prov_store_nvs.h (namespace "nw_prov", blob "rec"). */
typedef enum { NW_CREDS_OK = 0, NW_CREDS_NO_SSID, NW_CREDS_BAD_PASSPHRASE, NW_CREDS_BAD_TOKEN } nw_creds_check_t;
nw_creds_check_t nw_cycle_creds_check(const nw_prov_record_t *rec);

/* Sensor readings (each with its nw_err_t) -> one ring sample. A field is "present" only when its sensor returned NW_OK and the value is
 * inside the schema range (moisture 0..100 %, raw 0..4095, RH 0..100 %, battery plausible 3000..4250 mV); a failed sensor becomes null. */
void nw_cycle_make_sample(nw_sample_t *out, uint32_t ts, const nw_soil_t *soil, nw_err_t e_soil, const nw_aht20_t *aht, nw_err_t e_aht,
                          const nw_bh1750_t *bh, nw_err_t e_bh, uint32_t vbat_mv, nw_err_t e_bat);

typedef struct {
    nw_sleep_out_t sleep;        /* .report != NONE: bring Wi-Fi up and call nw_cycle_report */
    nw_push_t pushed;            /* result of the ring admission; NW_PUSH_REJECTED_INVALID also when sample == NULL */
} nw_cycle_plan_t;

/* Admit the sample (when the clock is ok), run nw_sleep_decide, retain low_battery and outage_pending in st.
 * sample may be NULL (all sensors failed). vbat_mv < 0 = unknown. */
nw_cycle_plan_t nw_cycle_begin(nw_cycle_state_t *st, uint32_t now_unix, const nw_sample_t *sample, int32_t vbat_mv);

/* One upload attempt for plan.sleep.report (kind). NW_REPORT_NONE sends nothing. Updates st: outage_pending from the result, last_report_unix on
 * an ack (the ack's server_time when valid, else now). The caller acts on r.server_time (re-sync the clock) and r.reenter_setup (erase the token
 * record, restart into setup). buf/cap: JSON scratch, see nw_upload_attempt. */
nw_upload_result_t nw_cycle_report(nw_cycle_state_t *st, const nw_upload_io_t *io, nw_report_kind_t kind, const char *fw, const char *base_url,
                                   const char *device_token, uint32_t now_unix, int32_t vbat_mv, char *buf, size_t cap);

/* Retry-After header value (delta-seconds form only, RFC 9110) -> seconds, or -1 when absent, empty, not all digits, longer than 9 digits or
 * in the HTTP-date form (the contract's -1 = "no usable value"; nw_upload clamps and applies it only on 429). */
int32_t nw_cycle_parse_retry_after(const char *value);

/* Deep-sleep seconds until the next 15-min boundary (900 s when the clock is not ok). Call after the report with the clock read again. */
uint32_t nw_cycle_sleep_s(uint32_t now_unix);

#endif

/* Deep-sleep and report decision (task 4.F3, FR-D01, FR-D02, FR-D04, FR-D06, FR-E03, NFR-01).
 * Called once per wake. Pure function: the caller keeps last_report_unix, low_battery and outage_pending in RTC/NVS
 * (retained across deep sleep) and passes them in. Deep sleep between samples, Wi-Fi only for a report (NFR-01).
 *
 * VBAT THRESHOLDS: the numbers below are the requirement values, but the device-side reading (divider R7/R8 through the
 * ADC, calibration) has NOT been measured on hardware. Each threshold is therefore marked ASSUMED until the bench check
 * in tests/procedures/4.F3-vbat-thresholds.md measures it. Do not treat them as verified.
 *
 * SINGLE SOURCE (review C7): NW_VBAT_LOW_MV and NW_VBAT_LOW_CLEAR_MV are defined ONLY here. The same numbers appear as
 * prose in tests/acceptance-matrix.md (row FR-D06, A-008.2 / A-018) and in test_sleep.c, which asserts these macros
 * against the literal 3400 / 3500. Change the matrix, this header and the test together.
 *
 * LOCAL ONLY (review C6): low_battery_event is produced here for the caller and is NOT sent to the server in this slice.
 * The events enum in device-report.schema.json has no battery type; the cloud is expected to derive the low-battery alert
 * from vbat_mv. Open question for the Lead (see the 4.F3 handoff).
 *
 * KNOWN DEVIATION (review C8): below NW_VBAT_WIFI_CUTOFF_MV no Wi-Fi report starts, so a critical event (FR-E03) waits
 * in the buffer until the cell recovers above the cutoff. It is delayed, not dropped. Open item for Arsany: FR-E03 says
 * immediate. */
#ifndef NW_SLEEP_H
#define NW_SLEEP_H

#include <stdbool.h>
#include <stdint.h>

/* Sampling: FR-D01 / FR-D02, one sample per 15 min. The wake is aligned to :00 :15 :30 :45 of the RTC when time is synced. */
#define NW_SLEEP_SAMPLE_PERIOD_S 900

/* Hourly report: FR-D02 (24 +/- 1 reports per day, gap 60 +/- 5 min). Due when at least REPORT_PERIOD - TOLERANCE has
 * passed since the last report, so one early wake (RTC drift) does not push the report to the next wake (75 min gap).
 * TOLERANCE is ASSUMED (wake-jitter allowance, not measured). */
#define NW_REPORT_PERIOD_S 3600
#define NW_REPORT_DUE_TOLERANCE_S 120 /* ASSUMED until measured */

/* Low battery, FR-D06 (acceptance matrix, A-008.2 and A-018): event when the voltage falls below 3.4 V, cleared at 3.5 V or above,
 * no re-fire while it stays between. Values are the requirement; the ADC reading that the comparison uses is ASSUMED
 * until measured on the bench. */
#define NW_VBAT_LOW_MV 3400       /* ASSUMED until measured */
#define NW_VBAT_LOW_CLEAR_MV 3500 /* ASSUMED until measured */

/* Wi-Fi cutoff (NOT in FR-D06, a design proposal, review C5): at or below this cell voltage the 3.3 V rail sags under
 * Wi-Fi TX. Source: projects/plant-monitor/pcb/layout-brief.md (ngspice LDO sim: the rail fails at a <= 3.3 V cell with
 * the 0.30 ohm trace). No Wi-Fi report starts at or below it; samples keep being buffered (FR-D04).
 * ASSUMED until measured on the bench (procedure step 7). */
#define NW_VBAT_WIFI_CUTOFF_MV 3300

typedef struct {
    bool time_synced;          /* SNTP done. Never upload before (schema sent_at rule). */
    uint32_t now_unix;         /* RTC unix s, only meaningful when time_synced */
    uint32_t last_report_unix; /* RTC unix s of the last successful report; 0 = none yet */
    uint32_t buffered;         /* samples waiting in the offline ring (nw_ring_count) */
    bool critical_pending;     /* a critical event waits for upload (FR-E03) */
    int32_t vbat_mv;           /* battery mV from this wake; -1 = unknown (sensor failed) */
    bool low_battery_prev;     /* low-battery state from the previous wake (retained) */
    bool outage_pending;       /* retained. True after a due report was blocked or an upload failed; the caller clears it on a 2xx */
} nw_sleep_in_t;

typedef enum {
    NW_REPORT_NONE = 0,
    NW_REPORT_SCHEDULED,       /* hourly, FR-D02 */
    NW_REPORT_CRITICAL,        /* immediate, FR-E03 */
    NW_REPORT_RECONNECT        /* first report after an outage, FR-D04 (trigger=reconnect in the payload) */
} nw_report_kind_t;

typedef struct {
    uint32_t sleep_s;          /* deep sleep before the next wake */
    nw_report_kind_t report;   /* bring Wi-Fi up and upload now */
    bool low_battery;          /* state to retain for the next wake */
    bool low_battery_event;    /* true only on the wake where the low-battery event fires (FR-D06), local only (C6) */
    bool wifi_blocked_low_vbat; /* a report was due or critical, but the cell is at or below NW_VBAT_WIFI_CUTOFF_MV */
    bool outage_pending;       /* state to retain: the caller stores it, clears it after a 2xx */
} nw_sleep_out_t;

nw_sleep_out_t nw_sleep_decide(const nw_sleep_in_t *in);

#endif

/* Deep-sleep and report decision (task 4.F3). Requirement IDs and ASSUMED values: see nw_sleep.h. Pure C. */
#include "nw_sleep.h"
#include "nw_sample_ring.h" /* NW_SAMPLE_PERIOD_S must equal NW_SLEEP_SAMPLE_PERIOD_S */

_Static_assert(NW_SAMPLE_PERIOD_S == NW_SLEEP_SAMPLE_PERIOD_S, "sample period must match the ring contract");

nw_sleep_out_t nw_sleep_decide(const nw_sleep_in_t *in)
{
    nw_sleep_out_t out = { NW_SLEEP_SAMPLE_PERIOD_S, NW_REPORT_NONE, in->low_battery_prev, false, false };

    /* 1. Wake time: next 15-min boundary of the RTC (FR-D01). Unsynced clock: plain 15 min, never a 0 s sleep. */
    if (in->time_synced && in->now_unix != 0) {
        out.sleep_s = NW_SLEEP_SAMPLE_PERIOD_S - (in->now_unix % NW_SLEEP_SAMPLE_PERIOD_S);
    }

    /* 2. Low battery with hysteresis (FR-D06). Unknown voltage keeps the previous state. */
    if (in->vbat_mv >= 0) {
        if (!out.low_battery && in->vbat_mv < NW_VBAT_LOW_MV) {
            out.low_battery = true;
            out.low_battery_event = true;
        } else if (out.low_battery && in->vbat_mv >= NW_VBAT_LOW_CLEAR_MV) {
            out.low_battery = false;
        }
    }

    /* 3. Report decision. Nothing to upload, or no synced clock: no Wi-Fi. */
    if (!in->time_synced || in->buffered == 0) return out;

    bool critical = in->critical_pending;
    bool due = (in->last_report_unix == 0) ||
               (in->now_unix < in->last_report_unix) ||                 /* clock went back: report and resync */
               (in->now_unix - in->last_report_unix >= NW_REPORT_PERIOD_S - NW_REPORT_DUE_TOLERANCE_S);
    if (!critical && !due) return out;

    /* Battery below the Wi-Fi cutoff: the rail would sag under TX. Keep buffering, do not start Wi-Fi. */
    if (in->vbat_mv >= 0 && in->vbat_mv < NW_VBAT_WIFI_CUTOFF_MV) {
        out.wifi_blocked_low_vbat = true;
        return out;
    }

    out.report = critical ? NW_REPORT_CRITICAL : NW_REPORT_SCHEDULED;
    return out;
}

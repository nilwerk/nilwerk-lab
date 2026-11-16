/* Host tests for the deep-sleep and report decision (task 4.F3): FR-D01 (15-min samples), FR-D02 (hourly report,
 * 24 +/- 1 per day), FR-D06 (low-battery event with hysteresis), FR-E03 (critical report), NFR-01 (Wi-Fi only for a
 * report). The vbat numbers are the requirement values and are ASSUMED until measured (see nw_sleep.h). No hardware. */
#include <stdio.h>
#include <string.h>
#include "nwtest.h"
#include "nw_sleep.h"

int nwtest_failed, nwtest_checked;

#define ALIGNED_NOW 1767225600u /* divisible by 900: a :00 wake */

static nw_sleep_in_t base(void)
{
    nw_sleep_in_t in;
    memset(&in, 0, sizeof in);
    in.time_synced = true;
    in.now_unix = ALIGNED_NOW;
    in.last_report_unix = ALIGNED_NOW - 1800;
    in.buffered = 2;
    in.vbat_mv = 3900;
    return in;
}

/* ---------- wake interval, FR-D01 ---------- */
static void test_wake_interval(void)
{
    nw_sleep_in_t in = base();
    CHECK_EQ(NW_SLEEP_SAMPLE_PERIOD_S, 900);
    CHECK_EQ(nw_sleep_decide(&in).sleep_s, 900);            /* on a boundary: next one is 15 min away, not 0 */
    in.now_unix = ALIGNED_NOW + 1;
    CHECK_EQ(nw_sleep_decide(&in).sleep_s, 899);            /* aligned to :00 :15 :30 :45 */
    in.now_unix = ALIGNED_NOW + 899;
    CHECK_EQ(nw_sleep_decide(&in).sleep_s, 1);
    in.time_synced = false; in.now_unix = ALIGNED_NOW + 17;
    CHECK_EQ(nw_sleep_decide(&in).sleep_s, 900);            /* unsynced RTC: plain 15 min */
    in.time_synced = true; in.now_unix = 0;
    CHECK_EQ(nw_sleep_decide(&in).sleep_s, 900);
}

/* ---------- hourly report, FR-D02 ---------- */
static void test_hourly_due_and_not_due(void)
{
    nw_sleep_in_t in = base();
    in.last_report_unix = ALIGNED_NOW - (NW_REPORT_PERIOD_S - NW_REPORT_DUE_TOLERANCE_S) + 1;
    CHECK(nw_sleep_decide(&in).report == NW_REPORT_NONE);   /* one second short of the due point */
    in.last_report_unix = ALIGNED_NOW - (NW_REPORT_PERIOD_S - NW_REPORT_DUE_TOLERANCE_S);
    CHECK(nw_sleep_decide(&in).report == NW_REPORT_SCHEDULED);
    in.last_report_unix = 0;                                /* never reported: due at the first synced wake */
    CHECK(nw_sleep_decide(&in).report == NW_REPORT_SCHEDULED);
    in.last_report_unix = ALIGNED_NOW + 60;                 /* clock went back: report and resync */
    CHECK(nw_sleep_decide(&in).report == NW_REPORT_SCHEDULED);
}

static void test_no_report_without_data_or_sync(void)
{
    nw_sleep_in_t in = base();
    in.last_report_unix = 0;
    in.buffered = 0;                                        /* nothing to upload: no Wi-Fi even if due */
    CHECK(nw_sleep_decide(&in).report == NW_REPORT_NONE);
    in.buffered = 3; in.time_synced = false; in.critical_pending = true;   /* never before SNTP */
    CHECK(nw_sleep_decide(&in).report == NW_REPORT_NONE);
}

static void test_critical_report(void)
{
    nw_sleep_in_t in = base();                              /* not due: 30 min since last report */
    in.critical_pending = true;
    nw_sleep_out_t o = nw_sleep_decide(&in);
    CHECK(o.report == NW_REPORT_CRITICAL);                  /* FR-E03: immediate report */
    CHECK_EQ(o.sleep_s, 900);
}

/* Simulated day: one wake every sleep_s, buffer always holds 4 samples, the report resets last_report.
 * FR-D02: 24 +/- 1 reports per day, gaps 60 +/- 5 min (here exactly 60 min on a 15-min wake grid). */
static void test_24h_cadence(void)
{
    uint32_t t = ALIGNED_NOW;
    uint32_t last = 0, prev_report = 0;
    int reports = 0, wakes = 0, bad_gap = 0;
    while (t < ALIGNED_NOW + 86400u) {
        nw_sleep_in_t in = base();
        in.now_unix = t;
        in.last_report_unix = last;
        in.buffered = 4;
        nw_sleep_out_t o = nw_sleep_decide(&in);
        wakes++;
        if (o.report != NW_REPORT_NONE) {
            if (prev_report && (t - prev_report < 3600 - 300 || t - prev_report > 3600 + 300)) bad_gap++;
            prev_report = t;
            last = t;
            reports++;
        }
        t += o.sleep_s;
    }
    CHECK_EQ(wakes, 96);                                    /* 96 x 15 min = 24 h of samples (FR-D01) */
    CHECK(reports >= 23 && reports <= 25);                  /* FR-D02 */
    CHECK_EQ(reports, 24);
    CHECK_EQ(bad_gap, 0);
}

/* ---------- low battery, FR-D06 (hysteresis 3.4 V fires, 3.5 V clears) ---------- */
static void test_low_battery_hysteresis(void)
{
    nw_sleep_in_t in = base();
    nw_sleep_out_t o;
    in.vbat_mv = 3450;                                      /* above 3.4 V, not low: no event */
    o = nw_sleep_decide(&in);
    CHECK(!o.low_battery && !o.low_battery_event);
    in.vbat_mv = 3399;                                      /* falls below 3.4 V: event fires once */
    o = nw_sleep_decide(&in);
    CHECK(o.low_battery && o.low_battery_event);
    in.low_battery_prev = o.low_battery;
    in.vbat_mv = 3450;                                      /* between 3.4 and 3.5 V: still low, no re-fire */
    o = nw_sleep_decide(&in);
    CHECK(o.low_battery && !o.low_battery_event);
    in.low_battery_prev = o.low_battery;
    in.vbat_mv = 3499;
    o = nw_sleep_decide(&in);
    CHECK(o.low_battery && !o.low_battery_event);
    in.low_battery_prev = o.low_battery;
    in.vbat_mv = 3500;                                      /* 3.5 V or above: cleared */
    o = nw_sleep_decide(&in);
    CHECK(!o.low_battery && !o.low_battery_event);
    in.low_battery_prev = o.low_battery;
    in.vbat_mv = 3450;                                      /* back between: not low again, no event */
    o = nw_sleep_decide(&in);
    CHECK(!o.low_battery && !o.low_battery_event);
}

static void test_low_battery_unknown_voltage_keeps_state(void)
{
    nw_sleep_in_t in = base();
    in.low_battery_prev = true;
    in.vbat_mv = -1;                                        /* ADC failed this wake */
    nw_sleep_out_t o = nw_sleep_decide(&in);
    CHECK(o.low_battery && !o.low_battery_event);
    in.low_battery_prev = false;
    o = nw_sleep_decide(&in);
    CHECK(!o.low_battery && !o.low_battery_event);
}

/* Low battery does not change the sleep or the report cadence (no silent workaround: FR-D02 still holds). */
static void test_low_battery_keeps_hourly_report(void)
{
    nw_sleep_in_t in = base();
    in.vbat_mv = NW_VBAT_LOW_MV - 1;                        /* low (3399 mV), but above the Wi-Fi cutoff */
    in.last_report_unix = ALIGNED_NOW - 3600;
    nw_sleep_out_t o = nw_sleep_decide(&in);
    CHECK(o.low_battery && o.low_battery_event);
    CHECK(o.report == NW_REPORT_SCHEDULED);
    CHECK_EQ(o.sleep_s, 900);
}

/* Below the Wi-Fi cutoff (ASSUMED 3.3 V): a due report is held back, samples keep being buffered. */
static void test_wifi_cutoff(void)
{
    nw_sleep_in_t in = base();
    nw_sleep_out_t o;
    in.last_report_unix = ALIGNED_NOW - 3600;
    in.vbat_mv = NW_VBAT_WIFI_CUTOFF_MV - 50;
    o = nw_sleep_decide(&in);
    CHECK(o.report == NW_REPORT_NONE && o.wifi_blocked_low_vbat);
    in.critical_pending = true;                             /* critical also blocked: Wi-Fi would brown out */
    o = nw_sleep_decide(&in);
    CHECK(o.report == NW_REPORT_NONE && o.wifi_blocked_low_vbat);
    in.vbat_mv = NW_VBAT_WIFI_CUTOFF_MV;                    /* at the cutoff: allowed */
    o = nw_sleep_decide(&in);
    CHECK(o.report == NW_REPORT_CRITICAL && !o.wifi_blocked_low_vbat);
    in.critical_pending = false;
    in.vbat_mv = -1;                                        /* unknown voltage: cannot prove low, not blocked */
    o = nw_sleep_decide(&in);
    CHECK(o.report == NW_REPORT_SCHEDULED);
}

static void test_threshold_values(void)
{
    /* Requirement values (FR-D06, A-008.2, A-018). Changing them is a requirement change: test must be updated too. */
    CHECK_EQ(NW_VBAT_LOW_MV, 3400);
    CHECK_EQ(NW_VBAT_LOW_CLEAR_MV, 3500);
    CHECK(NW_VBAT_WIFI_CUTOFF_MV < NW_VBAT_LOW_MV);
    CHECK(NW_VBAT_WIFI_CUTOFF_MV > 3000);                   /* above the schema plausibility floor 3000 mV */
}

int main(void)
{
    test_wake_interval();
    test_hourly_due_and_not_due();
    test_no_report_without_data_or_sync();
    test_critical_report();
    test_24h_cadence();
    test_low_battery_hysteresis();
    test_low_battery_unknown_voltage_keeps_state();
    test_low_battery_keeps_hourly_report();
    test_wifi_cutoff();
    test_threshold_values();
    printf("%d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}

/* Host tests for one wake of the upload build (task 4.F3 slice 3): FR-D01 (15-min samples), FR-D02 (hourly report), FR-D04 (offline buffer,
 * reconnect), FR-D06 (low battery), NFR-06 (token validation). Fake transport, no network, no hardware, no ESP-IDF. */
#include <stdio.h>
#include <string.h>
#include "nwtest.h"
#include "nw_cycle.h"

int nwtest_failed, nwtest_checked;

#define T0 1800000000u              /* a multiple of 900 */
#define TOKEN "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
#define BASE "https://api.invalid"

typedef struct { int status; int rc; int calls; char sent[20000]; } fake_t;
static int fake_post(void *ctx, const char *url, const char *auth, const char *body, size_t len, nw_upload_http_resp_t *resp)
{
    fake_t *f = ctx; (void)url; (void)auth;
    f->calls++;
    size_t n = len < sizeof f->sent - 1 ? len : sizeof f->sent - 1;
    memcpy(f->sent, body, n); f->sent[n] = 0;
    if (f->rc < 0) return f->rc;
    static char ok[96];
    snprintf(ok, sizeof ok, "{\"server_time\":%u,\"accepted\":1}", (unsigned)(T0 + 5));
    resp->status = f->status; resp->retry_after_s = -1; resp->body = f->status == 200 ? ok : ""; resp->body_len = strlen(resp->body);
    return 0;
}

static nw_sample_t good_sample(void)
{
    nw_soil_t so = {2000, 412, 0}; nw_aht20_t a = {2150, 5500}; nw_bh1750_t b = {1200, 10000, false};
    nw_sample_t s; nw_cycle_make_sample(&s, 0, &so, NW_OK, &a, NW_OK, &b, NW_OK, 3900, NW_OK);
    return s;
}

static nw_prov_record_t rec(const char *ssid, const char *pass, const char *tok)
{
    nw_prov_record_t r; memset(&r, 0, sizeof r);
    strncpy(r.ssid, ssid, sizeof r.ssid - 1); strncpy(r.passphrase, pass, sizeof r.passphrase - 1); strncpy(r.device_token, tok, sizeof r.device_token - 1);
    return r;
}

static void test_creds(void)   /* NFR-06: only a well-formed stored record is used; the token is never hard-coded */
{
    nw_prov_record_t r = rec("home", "secret-pass", TOKEN);
    CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_OK);
    r = rec("home", "", TOKEN);                                  CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_OK);        /* open network */
    r = rec("", "secret-pass", TOKEN);                           CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_NO_SSID);
    r = rec("home", "short", TOKEN);                             CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_BAD_PASSPHRASE);
    r = rec("home", "12345678", TOKEN);                          CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_OK);        /* 8 = minimum */
    r = rec("home", "1234567", TOKEN);                           CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_BAD_PASSPHRASE);
    r = rec("home", "secret-pass", "");                          CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_BAD_TOKEN); /* never claimed */
    r = rec("home", "secret-pass", "0123");                      CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_BAD_TOKEN);
    r = rec("home", "secret-pass", "ABCDEF0123456789abcdef0123456789abcdef0123456789abcdef0123456789"); CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_BAD_TOKEN);
    r = rec("home", "secret-pass", TOKEN);
    memset(r.ssid, 'a', sizeof r.ssid);                          CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_NO_SSID);   /* not NUL-terminated */
    r = rec("home", "secret-pass", TOKEN);
    memset(r.passphrase, 'p', sizeof r.passphrase);              CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_BAD_PASSPHRASE);  /* not NUL-terminated */
    memset(r.passphrase, 'p', 63); r.passphrase[63] = 0;         CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_OK);              /* 63 = maximum */
    r = rec("home", "secret-pass", TOKEN);
    memset(r.ssid, 'a', 32); r.ssid[32] = 0;                     CHECK_EQ(nw_cycle_creds_check(&r), NW_CREDS_OK);        /* 32 bytes = maximum */
    CHECK_EQ(nw_cycle_creds_check(NULL), NW_CREDS_NO_SSID);
}

static void test_state_and_clock(void)
{
    nw_cycle_state_t st; memset(&st, 0xA5, sizeof st);           /* power-on RTC garbage */
    CHECK(nw_cycle_state_ensure(&st));
    CHECK_EQ(st.magic, NW_CYCLE_MAGIC); CHECK_EQ(nw_ring_count(&st.ring), 0); CHECK_EQ(st.last_report_unix, 0); CHECK(!st.outage_pending);
    nw_sample_t s = good_sample(); st.last_report_unix = 77;
    CHECK(!nw_cycle_state_ensure(&st));                          /* deep-sleep wake: kept */
    CHECK_EQ(st.last_report_unix, 77);
    (void)s;
    CHECK(!nw_cycle_clock_ok(0)); CHECK(!nw_cycle_clock_ok(NW_TS_MIN - 1)); CHECK(nw_cycle_clock_ok(NW_TS_MIN));
    CHECK_EQ(nw_cycle_sleep_s(T0), 900); CHECK_EQ(nw_cycle_sleep_s(T0 + 1), 899); CHECK_EQ(nw_cycle_sleep_s(T0 + 899), 1);
    CHECK_EQ(nw_cycle_sleep_s(5), 900);                          /* unsynced: plain 15 min, never 0 */
}

static void test_retry_after(void)
{
    CHECK_EQ(nw_cycle_parse_retry_after("120"), 120); CHECK_EQ(nw_cycle_parse_retry_after("0"), 0);
    CHECK_EQ(nw_cycle_parse_retry_after("999999999"), 999999999);
    CHECK_EQ(nw_cycle_parse_retry_after("1000000000"), -1);          /* 10 digits: would overflow int32 range checks */
    CHECK_EQ(nw_cycle_parse_retry_after(NULL), -1); CHECK_EQ(nw_cycle_parse_retry_after(""), -1);
    CHECK_EQ(nw_cycle_parse_retry_after("-5"), -1); CHECK_EQ(nw_cycle_parse_retry_after("12s"), -1);
    CHECK_EQ(nw_cycle_parse_retry_after("Wed, 21 Oct 2026 07:28:00 GMT"), -1);   /* HTTP-date form is not used */
}

static void test_make_sample(void)
{
    nw_sample_t s = good_sample();
    CHECK_EQ(s.present, NW_PRESENT_MASK); CHECK_EQ(s.moisture_x10, 412); CHECK_EQ(s.moisture_raw, 2000); CHECK_EQ(s.temp_x100, 2150);
    CHECK_EQ(s.rh_x100, 5500); CHECK_EQ(s.lux_x10, 10000); CHECK_EQ(s.vbat_mv, 3900);
    nw_soil_t so = {2000, 412, 0}; nw_aht20_t a = {2150, 5500}; nw_bh1750_t b = {1200, 10000, false};
    nw_cycle_make_sample(&s, 5, &so, NW_ERR_IO, &a, NW_OK, &b, NW_OK, 3900, NW_OK);   CHECK_EQ(s.present & (NW_HAS_MOISTURE | NW_HAS_MOISTURE_RAW), 0); CHECK_EQ(s.ts, 5);
    nw_cycle_make_sample(&s, 0, &so, NW_OK, &a, NW_ERR_CRC, &b, NW_OK, 3900, NW_OK);  CHECK_EQ(s.present & (NW_HAS_TEMP | NW_HAS_RH), 0);
    nw_cycle_make_sample(&s, 0, &so, NW_OK, &a, NW_OK, &b, NW_ERR_IO, 3900, NW_OK);   CHECK_EQ(s.present & NW_HAS_LUX, 0);
    nw_cycle_make_sample(&s, 0, &so, NW_OK, &a, NW_OK, &b, NW_OK, 3900, NW_ERR_CAL);  CHECK_EQ(s.present & NW_HAS_VBAT, 0);
    nw_cycle_make_sample(&s, 0, &so, NW_OK, &a, NW_OK, &b, NW_OK, 2900, NW_OK);       CHECK_EQ(s.present & NW_HAS_VBAT, 0);          /* implausible cell */
    nw_cycle_make_sample(&s, 0, &so, NW_OK, &a, NW_OK, &b, NW_OK, 3000, NW_OK);       CHECK(s.present & NW_HAS_VBAT);
    so.pct_x10 = 1001; nw_cycle_make_sample(&s, 0, &so, NW_OK, &a, NW_OK, &b, NW_OK, 3900, NW_OK); CHECK_EQ(s.present & NW_HAS_MOISTURE, 0);
    so.pct_x10 = 1000; nw_cycle_make_sample(&s, 0, &so, NW_OK, &a, NW_OK, &b, NW_OK, 3900, NW_OK); CHECK(s.present & NW_HAS_MOISTURE);
    so.pct_x10 = 412; so.raw = 4096; nw_cycle_make_sample(&s, 0, &so, NW_OK, &a, NW_OK, &b, NW_OK, 3900, NW_OK); CHECK_EQ(s.present & NW_HAS_MOISTURE_RAW, 0);
    a.rh_x100 = 10001; nw_cycle_make_sample(&s, 0, &so, NW_OK, &a, NW_OK, &b, NW_OK, 3900, NW_OK); CHECK_EQ(s.present & NW_HAS_RH, 0); CHECK(s.present & NW_HAS_TEMP);
    /* every sensor failed: an empty-but-valid sample, still admitted (all fields null) */
    nw_cycle_make_sample(&s, 0, NULL, NW_ERR_IO, NULL, NW_ERR_IO, NULL, NW_ERR_IO, 0, NW_ERR_IO); CHECK_EQ(s.present, 0);
}

static void test_begin(void)
{
    nw_cycle_state_t st; memset(&st, 0, sizeof st); nw_cycle_state_ensure(&st);
    nw_sample_t s = good_sample();
    nw_cycle_plan_t p = nw_cycle_begin(&st, 100, &s, 3900);      /* clock not synced (1970) */
    CHECK_EQ(p.pushed, NW_PUSH_REJECTED_UNSYNCED); CHECK_EQ(nw_ring_count(&st.ring), 0); CHECK_EQ(p.sleep.report, NW_REPORT_NONE);
    p = nw_cycle_begin(&st, T0, &s, 3900);                       /* first sample after SNTP, no report yet: due at once (FR-D02) */
    CHECK_EQ(p.pushed, NW_PUSH_STORED); CHECK_EQ(nw_ring_at(&st.ring, 0)->ts, T0); CHECK_EQ(p.sleep.report, NW_REPORT_SCHEDULED);
    st.last_report_unix = T0;
    p = nw_cycle_begin(&st, T0 + 900, &s, 3900);                 CHECK_EQ(p.sleep.report, NW_REPORT_NONE);
    p = nw_cycle_begin(&st, T0 + 2700, &s, 3900);                CHECK_EQ(p.sleep.report, NW_REPORT_NONE);
    p = nw_cycle_begin(&st, T0 + 3600, &s, 3900);                CHECK_EQ(p.sleep.report, NW_REPORT_SCHEDULED); CHECK_EQ(nw_ring_count(&st.ring), 4);
    p = nw_cycle_begin(&st, T0 + 3600 + 900, NULL, 3900);        CHECK_EQ(p.pushed, NW_PUSH_REJECTED_INVALID);   /* no sample this wake: nothing pushed */
    CHECK_EQ(nw_ring_count(&st.ring), 4);
    /* low battery: no radio at or below the cutoff, the blocked report makes the next one a reconnect (FR-D04); state retained */
    st.last_report_unix = T0; st.outage_pending = false;
    p = nw_cycle_begin(&st, T0 + 3600, &s, 3300);
    CHECK_EQ(p.sleep.report, NW_REPORT_NONE); CHECK(p.sleep.wifi_blocked_low_vbat); CHECK(st.outage_pending); CHECK(st.low_battery);
    p = nw_cycle_begin(&st, T0 + 4500, &s, 3900);
    CHECK_EQ(p.sleep.report, NW_REPORT_RECONNECT);
    /* FR-D06 hysteresis needs the retained state: low at 3.3 V, still low at 3.45 V, cleared at 3.5 V */
    nw_cycle_state_t b; memset(&b, 0, sizeof b); nw_cycle_state_ensure(&b);
    p = nw_cycle_begin(&b, T0, &s, 3390);  CHECK(b.low_battery); CHECK(p.sleep.low_battery_event);
    p = nw_cycle_begin(&b, T0 + 900, &s, 3450); CHECK(b.low_battery); CHECK(!p.sleep.low_battery_event);
    p = nw_cycle_begin(&b, T0 + 1800, &s, 3500); CHECK(!b.low_battery);
}

static void test_report_ack_and_failure(void)
{
    static char buf[20000];
    nw_cycle_state_t st; memset(&st, 0, sizeof st); nw_cycle_state_ensure(&st);
    nw_sample_t s = good_sample();
    for (int i = 0; i < 4; i++) nw_cycle_begin(&st, T0 + i * 900, &s, 3900);
    fake_t f; memset(&f, 0, sizeof f); f.status = 500;
    nw_upload_io_t io = { &f, fake_post };
    nw_upload_result_t r = nw_cycle_report(&st, &io, NW_REPORT_SCHEDULED, "0.4.2-dev", BASE, TOKEN, T0 + 2700, 3900, buf, sizeof buf);
    CHECK_EQ(r.outcome, NW_UP_RETRY); CHECK(st.outage_pending); CHECK_EQ(st.last_report_unix, 0); CHECK_EQ(nw_ring_count(&st.ring), 4);
    CHECK(strstr(f.sent, "\"trigger\":\"scheduled\"") != NULL);
    f.status = 200;
    r = nw_cycle_report(&st, &io, NW_REPORT_RECONNECT, "0.4.2-dev", BASE, TOKEN, st.up.next_attempt_unix, 3900, buf, sizeof buf);
    CHECK_EQ(r.outcome, NW_UP_ACK); CHECK(!st.outage_pending); CHECK_EQ(nw_ring_count(&st.ring), 0);
    CHECK_EQ(st.last_report_unix, T0 + 5);                       /* the ack's server_time, not the local clock */
    CHECK(strstr(f.sent, "\"trigger\":\"reconnect\"") != NULL);
    CHECK(strstr(f.sent, "\"fw\":\"0.4.2-dev\"") != NULL);
    for (int i = 0; i < 2; i++) nw_cycle_begin(&st, T0 + 6000 + i * 900, &s, 3900);   /* data waits, so a wrong NONE would send it */
    int calls = f.calls;
    r = nw_cycle_report(&st, &io, NW_REPORT_NONE, "0.4.2-dev", BASE, TOKEN, T0 + 9000, 3900, buf, sizeof buf);
    CHECK_EQ(r.outcome, NW_UP_NOT_SENT); CHECK_EQ(f.calls, calls);  /* NONE never touches the network */
    for (int i = 0; i < 2; i++) nw_cycle_begin(&st, T0 + 9000 + i * 900, &s, 3900);
    nw_cycle_report(&st, &io, NW_REPORT_CRITICAL, "0.4.2-dev", BASE, TOKEN, T0 + 20000, 3900, buf, sizeof buf);
    CHECK(strstr(f.sent, "\"trigger\":\"critical\"") != NULL);
    f.status = 401;                                              /* a revoked token must reach the caller: this fake sends no body, so AUTH_FAILED */
    for (int i = 0; i < 2; i++) nw_cycle_begin(&st, T0 + 30000 + i * 900, &s, 3900);
    r = nw_cycle_report(&st, &io, NW_REPORT_SCHEDULED, "0.4.2-dev", BASE, TOKEN, T0 + 40000, 3900, buf, sizeof buf);
    CHECK_EQ(r.outcome, NW_UP_AUTH_FAILED); CHECK(st.outage_pending);
    r = nw_cycle_report(&st, &io, NW_REPORT_SCHEDULED, "0.4.2-dev", BASE, "not-a-token", T0 + 50000, 3900, buf, sizeof buf);
    CHECK_EQ(r.outcome, NW_UP_NOT_SENT); CHECK_EQ(r.why, NW_UP_WHY_BAD_CONFIG);
}

/* FR-D02: over 24 h of 15-min wakes with a healthy network there are 24 +/- 1 reports, 60 min apart (+/- 5). */
static void test_24h_cadence(void)
{
    static char buf[20000];
    nw_cycle_state_t st; memset(&st, 0, sizeof st); nw_cycle_state_ensure(&st);
    nw_sample_t s = good_sample();
    fake_t f; memset(&f, 0, sizeof f); f.status = 200; nw_upload_io_t io = { &f, fake_post };
    int reports = 0; uint32_t prev = 0, min_gap = ~0u, max_gap = 0;
    for (int w = 0; w < 96; w++) {
        uint32_t now = T0 + (uint32_t)w * 900;
        nw_cycle_plan_t p = nw_cycle_begin(&st, now, &s, 3900);
        if (p.sleep.report == NW_REPORT_NONE) continue;
        f.status = 200;
        /* the fake always answers server_time = T0+5: neutralise it so the cadence is measured on the local clock */
        nw_upload_result_t r = nw_cycle_report(&st, &io, p.sleep.report, "0.4.2-dev", BASE, TOKEN, now, 3900, buf, sizeof buf);
        CHECK_EQ(r.outcome, NW_UP_ACK);
        st.last_report_unix = now;
        reports++;
        if (prev) { if (now - prev < min_gap) min_gap = now - prev; if (now - prev > max_gap) max_gap = now - prev; }
        prev = now;
    }
    CHECK(reports >= 23 && reports <= 25); CHECK_EQ(reports, 24);
    CHECK(min_gap >= 3300 && max_gap <= 3900); CHECK_EQ(min_gap, 3600);
    CHECK(nw_ring_count(&st.ring) <= 3);                         /* only the samples since the last report wait */
}

/* FR-D04: 5 h without network (all attempts fail), then it recovers: the first report is trigger=reconnect and drains the buffer. */
static void test_outage_then_reconnect(void)
{
    static char buf[20000];
    nw_cycle_state_t st; memset(&st, 0, sizeof st); nw_cycle_state_ensure(&st);
    nw_sample_t s = good_sample();
    fake_t f; memset(&f, 0, sizeof f); f.rc = -1; nw_upload_io_t io = { &f, fake_post };
    unsigned attempts = 0;
    for (int w = 0; w < 20; w++) {                               /* 5 h */
        uint32_t now = T0 + (uint32_t)w * 900;
        nw_cycle_plan_t p = nw_cycle_begin(&st, now, &s, 3900);
        if (p.sleep.report == NW_REPORT_NONE) continue;
        nw_upload_result_t r = nw_cycle_report(&st, &io, p.sleep.report, "0.4.2-dev", BASE, TOKEN, now, 3900, buf, sizeof buf);
        if (r.outcome != NW_UP_NOT_SENT) attempts++;
    }
    CHECK_EQ(nw_ring_count(&st.ring), 20); CHECK(st.outage_pending); CHECK(attempts >= 3 && attempts <= 8);   /* backoff keeps the radio off for most of the 20 wakes (observed 7) */
    f.rc = 0; f.status = 200;
    uint32_t now = T0 + 20 * 900 + 3600;                         /* well past any backoff */
    nw_cycle_plan_t p = nw_cycle_begin(&st, now, &s, 3900);
    CHECK_EQ(p.sleep.report, NW_REPORT_RECONNECT);
    nw_upload_result_t r = nw_cycle_report(&st, &io, p.sleep.report, "0.4.2-dev", BASE, TOKEN, now, 3900, buf, sizeof buf);
    CHECK_EQ(r.outcome, NW_UP_ACK); CHECK_EQ(r.n_samples, 21); CHECK_EQ(nw_ring_count(&st.ring), 0); CHECK(!st.outage_pending);
}

int main(void)
{
    test_creds();
    test_state_and_clock();
    test_retry_after();
    test_make_sample();
    test_begin();
    test_report_ack_and_failure();
    test_24h_cadence();
    test_outage_then_reconnect();
    printf("%d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}

/* Host tests for the hourly upload logic (task 4.F3 slice 2): FR-D02 (hourly report), FR-D04 (24 h offline buffer, drain on
 * ack), FR-D06 (low battery), NFR-06 (TLS-only URL, per-device bearer token). Fake transport, no network, no hardware.
 * The response table under test is the one in nw_upload.h; the contract is docs/interfaces/openapi.yaml /ingest. */
#include <stdio.h>
#include <string.h>
#include "nwtest.h"
#include "nw_upload.h"
#include "nw_sleep.h"

int nwtest_failed, nwtest_checked;

#define NOW 1800000000u
#define TOKEN "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
#define BASE "https://api.invalid"
#define OKBODY "{\"server_time\":1800000005,\"accepted\":3,\"duplicates\":0,\"implausible\":0,\"config\":{}}"

static void push_n(nw_ring_t *r, unsigned n, uint32_t first_ts)
{
    for (unsigned i = 0; i < n; i++) {
        nw_sample_t s;
        memset(&s, 0, sizeof s);
        s.ts = first_ts + i * NW_SAMPLE_PERIOD_S;
        s.present = NW_HAS_MOISTURE | NW_HAS_VBAT;
        s.moisture_x10 = 412;
        s.vbat_mv = 3900;
        CHECK(nw_ring_push(r, &s, true) <= NW_PUSH_STORED_OVERWROTE);
    }
}

static nw_report_meta_t meta(void)
{
    nw_report_meta_t m;
    memset(&m, 0, sizeof m);
    m.sent_at = NOW; m.trigger = NW_TRIG_SCHEDULED; m.fw = "0.4.2-dev"; m.forecast_x10 = NW_REPORT_FORECAST_NULL;
    return m;
}

/* Fake transport: scripted answer, records the last request. During the call it can push extra samples (ring wrap test). */
typedef struct {
    int rc, status, retry_after;
    const char *body;
    int calls;
    char url[NW_UPLOAD_URL_MAX], auth[NW_UPLOAD_AUTH_MAX], sent[20000];
    size_t sent_len;
    nw_ring_t *push_ring; unsigned push_n;
} fake_t;

static int fake_post(void *ctx, const char *url, const char *auth, const char *body, size_t len, nw_upload_http_resp_t *resp)
{
    fake_t *f = ctx;
    f->calls++;
    strncpy(f->url, url, sizeof f->url - 1);
    strncpy(f->auth, auth, sizeof f->auth - 1);
    f->sent_len = len < sizeof f->sent - 1 ? len : sizeof f->sent - 1;
    memcpy(f->sent, body, f->sent_len); f->sent[f->sent_len] = 0;
    if (f->push_ring) push_n(f->push_ring, f->push_n, NOW - 100000);   /* samples arrive during the upload */
    if (f->rc < 0) return f->rc;
    resp->status = f->status; resp->retry_after_s = f->retry_after;
    resp->body = f->body; resp->body_len = f->body ? strlen(f->body) : 0;
    return 0;
}

static fake_t mk(int status, const char *body) { fake_t f; memset(&f, 0, sizeof f); f.status = status; f.body = body; f.retry_after = -1; return f; }

static nw_upload_result_t attempt(nw_upload_state_t *s, fake_t *f, nw_ring_t *r, uint32_t now, int32_t vbat, bool low)
{
    static char buf[20000];
    nw_upload_io_t io = { f, fake_post };
    nw_report_meta_t m = meta();
    return nw_upload_attempt(s, &io, r, &m, BASE, TOKEN, now, vbat, low, buf, sizeof buf);
}

static void test_url_and_auth(void)
{
    char u[NW_UPLOAD_URL_MAX], a[NW_UPLOAD_AUTH_MAX];
    CHECK_EQ(nw_upload_build_url(u, sizeof u, "https://x.supabase.co/functions/v1"), 34 + 7);
    CHECK(strcmp(u, "https://x.supabase.co/functions/v1/ingest") == 0);
    CHECK_EQ(nw_upload_build_url(u, sizeof u, "http://x.example"), -1);          /* NFR-06: TLS only */
    CHECK_EQ(nw_upload_build_url(u, sizeof u, "https://"), -1);
    CHECK_EQ(nw_upload_build_url(u, sizeof u, "https://x.example/"), -1);        /* no trailing slash */
    CHECK_EQ(nw_upload_build_url(u, sizeof u, "https://x.example/a?b=1"), -1);
    CHECK_EQ(nw_upload_build_url(u, sizeof u, "https://x.example/a#f"), -1);
    CHECK_EQ(nw_upload_build_url(u, sizeof u, "https://x .example"), -1);
    CHECK_EQ(nw_upload_build_url(u, sizeof u, "https://x.example\r\nX: y"), -1);
    CHECK_EQ(nw_upload_build_url(u, sizeof u, ""), -1);
    CHECK_EQ(nw_upload_build_url(u, sizeof u, NULL), -1);
    CHECK_EQ(nw_upload_build_url(u, 20, "https://x.example"), -1);               /* too small */
    CHECK_EQ(nw_upload_build_url(u, 25, "https://x.example"), 24);               /* exactly fits incl. NUL */
    CHECK_EQ(nw_upload_build_url(u, 24, "https://x.example"), -1);                 /* one byte short: no room for the NUL */
    char longb[300]; memcpy(longb, "https://", 8); memset(longb + 8, 'a', 250); longb[258] = 0;
    char big[400];
    CHECK_EQ(nw_upload_build_url(big, sizeof big, longb), -1);                   /* over NW_UPLOAD_URL_MAX */

    CHECK_EQ(nw_upload_build_auth(a, sizeof a, TOKEN), 71);
    CHECK(strcmp(a, "Bearer " TOKEN) == 0);
    CHECK_EQ(nw_upload_build_auth(a, sizeof a, "0123"), -1);                     /* short */
    CHECK_EQ(nw_upload_build_auth(a, sizeof a, TOKEN "0"), -1);                  /* long */
    CHECK_EQ(nw_upload_build_auth(a, sizeof a, "ABCDEF0123456789abcdef0123456789abcdef0123456789abcdef0123456789"), -1); /* upper case */
    CHECK_EQ(nw_upload_build_auth(a, sizeof a, "g123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"), -1);
    CHECK_EQ(nw_upload_build_auth(a, 71, TOKEN), -1);                            /* no room for NUL */
    CHECK_EQ(nw_upload_build_auth(a, sizeof a, NULL), -1);
}

static void test_gate(void)
{
    nw_upload_state_t s; nw_upload_state_init(&s);
    CHECK_EQ(NW_VBAT_WIFI_CUTOFF_MV, 3300);
    CHECK_EQ(nw_upload_gate(&s, NOW, 3300), NW_UP_GATE_LOW_VBAT);                /* at the cutoff: blocked, like nw_sleep */
    CHECK_EQ(nw_upload_gate(&s, NOW, 3301), NW_UP_GATE_OK);
    CHECK_EQ(nw_upload_gate(&s, NOW, 0), NW_UP_GATE_LOW_VBAT);
    CHECK_EQ(nw_upload_gate(&s, NOW, -1), NW_UP_GATE_OK);                        /* unknown reading: not blocked (as nw_sleep) */
    s.next_attempt_unix = NOW + 10;
    CHECK_EQ(nw_upload_gate(&s, NOW + 9, 3900), NW_UP_GATE_BACKOFF);
    CHECK_EQ(nw_upload_gate(&s, NOW + 10, 3900), NW_UP_GATE_OK);                 /* boundary: allowed at next_attempt */
    CHECK_EQ(nw_upload_gate(&s, NOW + 9, 3200), NW_UP_GATE_LOW_VBAT);            /* battery reported before backoff */
    nw_upload_state_init(&s);
    CHECK_EQ(NW_UPLOAD_MAX_PER_HOUR, 6);
    for (int i = 0; i < 6; i++) { s.attempts[i] = NOW + (uint32_t)i * 10; }
    CHECK_EQ(nw_upload_gate(&s, NOW + 100, 3900), NW_UP_GATE_RATE_LIMIT);        /* 6 in the last hour */
    CHECK_EQ(nw_upload_gate(&s, NOW + 3599, 3900), NW_UP_GATE_RATE_LIMIT);       /* oldest is 3599 s old: still inside */
    CHECK_EQ(nw_upload_gate(&s, NOW + 3600, 3900), NW_UP_GATE_OK);               /* oldest left the window */
    s.attempts[5] = 0;
    CHECK_EQ(nw_upload_gate(&s, NOW + 100, 3900), NW_UP_GATE_OK);                /* only 5 */
    s.attempts[5] = NOW + 50;
    CHECK_EQ(nw_upload_gate(&s, NOW - 5000, 3900), NW_UP_GATE_RATE_LIMIT);       /* clock moved back: stay conservative */
}

static void test_ack_drains_batch_only(void)
{   /* FR-D04, openapi: delete only after a 2xx for the batch containing it */
    nw_upload_state_t s; nw_upload_state_init(&s);
    nw_ring_t r; nw_ring_init(&r);
    push_n(&r, 10, NOW - 20000);
    fake_t f = mk(200, OKBODY);
    nw_upload_result_t x = attempt(&s, &f, &r, NOW, 3900, false);
    CHECK_EQ(x.outcome, NW_UP_ACK);
    CHECK_EQ(x.drained, 10); CHECK_EQ(x.n_samples, 10); CHECK_EQ(nw_ring_count(&r), 0);
    CHECK(x.server_time_valid); CHECK_EQ(x.server_time, 1800000005u);
    CHECK(!x.outage_pending); CHECK_EQ(s.fails, 0);
    /* samples pushed DURING the upload survive */
    push_n(&r, 10, NOW - 20000);
    f = mk(200, OKBODY); f.push_ring = &r; f.push_n = 3;
    x = attempt(&s, &f, &r, NOW + 5000, 3900, false);
    CHECK_EQ(x.drained, 10); CHECK_EQ(nw_ring_count(&r), 3);
    /* full ring wraps during the upload: the unsent oldest are gone (known, FR-D04), the new ones are never acked away */
    nw_ring_init(&r); push_n(&r, NW_RING_CAP, NOW - 200000);
    f = mk(200, OKBODY); f.push_ring = &r; f.push_n = 5;
    x = attempt(&s, &f, &r, NOW + 20000, 3900, false);
    CHECK_EQ(nw_ring_count(&r), 5);
    CHECK_EQ(x.drained, NW_RING_CAP - 5);                                        /* only what is still stored and <= last_seq */
}

static void test_request_content(void)
{
    nw_upload_state_t s; nw_upload_state_init(&s);
    nw_ring_t r; nw_ring_init(&r); push_n(&r, 3, NOW - 5000);
    fake_t f = mk(200, OKBODY);
    attempt(&s, &f, &r, NOW, 3900, false);
    CHECK_EQ(f.calls, 1);
    CHECK(strcmp(f.url, BASE "/ingest") == 0);
    CHECK(strcmp(f.auth, "Bearer " TOKEN) == 0);
    CHECK(strncmp(f.sent, "{\"v\":1,", 7) == 0);                                 /* nw_report_build body, schema v1 */
    CHECK(strstr(f.sent, "\"trigger\":\"scheduled\"") != NULL);
    CHECK(strstr(f.sent, TOKEN) == NULL);                                        /* the token is a header, never in the body */
}

static void test_not_sent_paths(void)
{
    nw_upload_state_t s; nw_upload_state_init(&s);
    nw_ring_t r; nw_ring_init(&r);
    fake_t f = mk(200, OKBODY);
    nw_upload_result_t x = attempt(&s, &f, &r, NOW, 3900, false);                /* empty buffer */
    CHECK_EQ(x.outcome, NW_UP_NOT_SENT); CHECK_EQ(x.why, NW_UP_WHY_NO_PAYLOAD); CHECK_EQ(f.calls, 0);
    CHECK_EQ(s.attempts[0], 0);                                                  /* no radio, no attempt counted */
    push_n(&r, 4, NOW - 5000);
    x = attempt(&s, &f, &r, NOW, 3300, false);                                   /* low battery: no radio */
    CHECK_EQ(x.outcome, NW_UP_NOT_SENT); CHECK_EQ(x.why, NW_UP_WHY_GATE); CHECK_EQ(x.gate, NW_UP_GATE_LOW_VBAT);
    CHECK_EQ(f.calls, 0); CHECK_EQ(nw_ring_count(&r), 4); CHECK(x.outage_pending); CHECK_EQ(s.attempts[0], 0); CHECK_EQ(s.fails, 0);
    nw_upload_io_t io = { &f, fake_post }; nw_report_meta_t m = meta(); static char buf[20000];
    x = nw_upload_attempt(&s, &io, &r, &m, "http://api.invalid", TOKEN, NOW, 3900, false, buf, sizeof buf);
    CHECK_EQ(x.outcome, NW_UP_NOT_SENT); CHECK_EQ(x.why, NW_UP_WHY_BAD_CONFIG); CHECK_EQ(f.calls, 0);
    x = nw_upload_attempt(&s, &io, &r, &m, BASE, "short", NOW, 3900, false, buf, sizeof buf);
    CHECK_EQ(x.why, NW_UP_WHY_BAD_CONFIG); CHECK_EQ(f.calls, 0);
    x = nw_upload_attempt(&s, &io, &r, &m, BASE, TOKEN, NOW, 3900, false, buf, 50);   /* body buffer too small */
    CHECK_EQ(x.why, NW_UP_WHY_NO_PAYLOAD); CHECK_EQ(f.calls, 0);
    m.sent_at = 5;                                                               /* RTC never synced: schema floor */
    x = nw_upload_attempt(&s, &io, &r, &m, BASE, TOKEN, NOW, 3900, false, buf, sizeof buf);
    CHECK_EQ(x.why, NW_UP_WHY_NO_PAYLOAD); CHECK_EQ(f.calls, 0);
    s.next_attempt_unix = NOW + 100;
    x = attempt(&s, &f, &r, NOW, 3900, false);
    CHECK_EQ(x.gate, NW_UP_GATE_BACKOFF); CHECK_EQ(f.calls, 0);
}

static void test_200_without_time_is_not_an_ack(void)
{
    const char *bad[] = { "", "{}", "not json", "{\"server_time\":\"x\"}", "{\"server_time\":12}", "{\"server_time\":}",
                          "{\"server_time\":99999999999}", "{\"server_time\":18446744075509551621}", "{\"server_time\":-5}", "{\"server_time\"", "{\"server_time\":17" };
    for (unsigned i = 0; i < sizeof bad / sizeof *bad; i++) {
        nw_upload_state_t s; nw_upload_state_init(&s);
        nw_ring_t r; nw_ring_init(&r); push_n(&r, 5, NOW - 5000);
        fake_t f = mk(200, bad[i]);
        nw_upload_result_t x = attempt(&s, &f, &r, NOW, 3900, false);
        CHECK_EQ(x.outcome, NW_UP_RETRY); CHECK_EQ(nw_ring_count(&r), 5); CHECK_EQ(x.drained, 0); CHECK(x.outage_pending);
        CHECK_EQ(s.fails, 1);
    }
    /* other 2xx / 3xx are not acks either */
    int codes[] = { 201, 204, 301, 302, 100 };
    for (unsigned i = 0; i < sizeof codes / sizeof *codes; i++) {
        nw_upload_state_t s; nw_upload_state_init(&s);
        nw_ring_t r; nw_ring_init(&r); push_n(&r, 5, NOW - 5000);
        fake_t f = mk(codes[i], OKBODY);
        nw_upload_result_t x = attempt(&s, &f, &r, NOW, 3900, false);
        CHECK_EQ(x.outcome, NW_UP_RETRY); CHECK_EQ(nw_ring_count(&r), 5);
    }
    /* body without NUL after len: parser must not read past body_len */
    nw_upload_state_t s; nw_upload_state_init(&s);
    nw_ring_t r; nw_ring_init(&r); push_n(&r, 2, NOW - 5000);
    nw_upload_http_resp_t resp = { 200, -1, "{\"server_time\":1800000005}garbage", 26 };
    CHECK_EQ(nw_upload_on_response(&s, &r, 2, 2, &resp, NOW, false).outcome, NW_UP_ACK);
    nw_upload_http_resp_t cut = { 200, -1, "{\"server_time\":1800000005}", 24 };   /* cut inside the number: 18000000 < NW_TS_MIN */
    nw_ring_init(&r); push_n(&r, 2, NOW - 5000);
    CHECK_EQ(nw_upload_on_response(&s, &r, 2, 2, &cut, NOW, false).outcome, NW_UP_RETRY);
}

static void test_401(void)
{
    nw_upload_state_t s; nw_upload_state_init(&s);
    nw_ring_t r; nw_ring_init(&r); push_n(&r, 8, NOW - 9000);
    fake_t f = mk(401, "{\"error\":\"token_revoked\"}");
    s.fails = 3; s.next_attempt_unix = 5; 
    nw_upload_result_t x = attempt(&s, &f, &r, NOW, 3900, false);
    CHECK_EQ(x.outcome, NW_UP_REVOKED); CHECK(x.reenter_setup); CHECK_EQ(x.drained, 8); CHECK_EQ(nw_ring_count(&r), 0);
    CHECK(!x.outage_pending); CHECK_EQ(s.fails, 0); CHECK_EQ(s.next_attempt_unix, 0);
    push_n(&r, 8, NOW - 9000);
    const char *other[] = { "{\"error\":\"token_invalid\"}", "", "{}", "{\"error\":\"token_revoked_x\"}", "{\"error\":\"unauthorized\"}", "{\"error\": \"token_invalid\", \"message\":\"token_revoked\"}" };
    for (unsigned i = 0; i < sizeof other / sizeof *other; i++) {
        nw_upload_state_init(&s);
        f = mk(401, other[i]);
        x = attempt(&s, &f, &r, NOW, 3900, false);
        CHECK_EQ(x.outcome, NW_UP_AUTH_FAILED); CHECK(!x.reenter_setup); CHECK_EQ(nw_ring_count(&r), 8); CHECK(x.outage_pending);
        CHECK(s.next_attempt_unix > NOW);
    }
    nw_upload_state_init(&s);
    f = mk(401, "{ \"error\" : \"token_revoked\" }");                             /* whitespace is valid JSON */
    CHECK_EQ(attempt(&s, &f, &r, NOW, 3900, false).outcome, NW_UP_REVOKED);
}

static void test_reject_poison_guard(void)
{
    nw_upload_state_t s; nw_upload_state_init(&s);
    nw_ring_t r; nw_ring_init(&r); push_n(&r, 6, NOW - 9000);
    CHECK_EQ(NW_UPLOAD_POISON_MAX, 3);
    fake_t f = mk(400, "{\"error\":\"bad_request\"}");
    nw_upload_result_t x = attempt(&s, &f, &r, NOW, 3900, false);
    CHECK_EQ(x.outcome, NW_UP_REJECTED); CHECK(!x.batch_dropped); CHECK_EQ(nw_ring_count(&r), 6);
    x = attempt(&s, &f, &r, NOW + 3600, 3900, false);
    CHECK(!x.batch_dropped); CHECK_EQ(nw_ring_count(&r), 6);
    x = attempt(&s, &f, &r, NOW + 7200, 3900, false);                            /* third reject of the same batch */
    CHECK(x.batch_dropped); CHECK_EQ(x.drained, 6); CHECK_EQ(nw_ring_count(&r), 0); CHECK_EQ(s.rejects, 0);
    /* a different batch resets the counter */
    nw_upload_state_init(&s); push_n(&r, 2, NOW - 9000);
    f = mk(413, "{\"error\":\"payload_too_large\"}");
    attempt(&s, &f, &r, NOW, 3900, false); attempt(&s, &f, &r, NOW + 3600, 3900, false);
    push_n(&r, 1, NOW - 100);                                                    /* new last_seq: not the same batch */
    x = attempt(&s, &f, &r, NOW + 7200, 3900, false);
    CHECK(!x.batch_dropped); CHECK_EQ(s.rejects, 1); CHECK_EQ(nw_ring_count(&r), 3);
    /* an ack in between resets too */
    f = mk(200, OKBODY); attempt(&s, &f, &r, NOW + 20000, 3900, false);
    CHECK_EQ(s.rejects, 0); CHECK_EQ(s.reject_seq, 0);
}

static void test_backoff_and_retry_after(void)
{
    nw_upload_state_t s; nw_upload_state_init(&s);
    nw_ring_t r; nw_ring_init(&r); push_n(&r, 3, NOW - 9000);
    fake_t f = mk(500, "{\"error\":\"internal\"}");
    uint32_t t = NOW, want[] = { 900, 1800, 3600, 3600, 3600 };
    for (int i = 0; i < 5; i++) {
        nw_upload_result_t x = attempt(&s, &f, &r, t, 3900, false);
        CHECK_EQ(x.outcome, NW_UP_RETRY); CHECK_EQ(s.next_attempt_unix, t + want[i]); CHECK_EQ(nw_ring_count(&r), 3);
        CHECK_EQ(attempt(&s, &f, &r, t + want[i] - 1, 3900, false).gate, NW_UP_GATE_BACKOFF);
        t += want[i];
    }
    CHECK_EQ(f.calls, 5);
    for (int i = 0; i < 300; i++) nw_upload_on_transport_error(&s, t, false);    /* saturating counter, no overflow */
    CHECK_EQ(s.fails, 255); CHECK_EQ(s.next_attempt_unix, t + 3600);
    /* 429 */
    nw_upload_state_init(&s);
    f = mk(429, "{\"error\":\"rate_limited\"}"); f.retry_after = 2000;
    attempt(&s, &f, &r, NOW, 3900, false); CHECK_EQ(s.next_attempt_unix, NOW + 2000);   /* server wait beats 900 */
    nw_upload_state_init(&s); f.retry_after = 10;
    attempt(&s, &f, &r, NOW, 3900, false); CHECK_EQ(s.next_attempt_unix, NOW + 900);    /* never shorter than the backoff */
    nw_upload_state_init(&s); f.retry_after = 86400;
    attempt(&s, &f, &r, NOW, 3900, false); CHECK_EQ(s.next_attempt_unix, NOW + 3600);   /* clamped */
    nw_upload_state_init(&s); f.retry_after = -1;
    attempt(&s, &f, &r, NOW, 3900, false); CHECK_EQ(s.next_attempt_unix, NOW + 900);
    nw_upload_state_init(&s); f = mk(500, ""); f.retry_after = 3000;                    /* Retry-After only honoured on 429 */
    attempt(&s, &f, &r, NOW, 3900, false); CHECK_EQ(s.next_attempt_unix, NOW + 900);
    nw_upload_state_init(&s); f = mk(405, "");
    CHECK_EQ(attempt(&s, &f, &r, NOW, 3900, false).outcome, NW_UP_RETRY);
    /* ack resets the ladder */
    nw_upload_state_init(&s); f = mk(500, ""); attempt(&s, &f, &r, NOW, 3900, false); attempt(&s, &f, &r, NOW + 900, 3900, false);
    CHECK_EQ(s.fails, 2);
    f = mk(200, OKBODY); attempt(&s, &f, &r, NOW + 2700, 3900, false);
    CHECK_EQ(s.fails, 0); CHECK_EQ(s.next_attempt_unix, 0);
}

static void test_low_battery_behaviour(void)
{   /* FR-D06: below 3.4 V (but above the 3.3 V cutoff) the upload still runs, but a failure waits a full hour */
    nw_upload_state_t s; nw_upload_state_init(&s);
    nw_ring_t r; nw_ring_init(&r); push_n(&r, 3, NOW - 9000);
    fake_t f = mk(500, "");
    nw_upload_result_t x = attempt(&s, &f, &r, NOW, 3350, true);
    CHECK_EQ(x.outcome, NW_UP_RETRY); CHECK_EQ(f.calls, 1); CHECK_EQ(s.next_attempt_unix, NOW + 3600);
    nw_upload_state_init(&s);
    nw_upload_on_transport_error(&s, NOW, true); CHECK_EQ(s.next_attempt_unix, NOW + 3600);
    nw_upload_state_init(&s);
    nw_upload_on_transport_error(&s, NOW, false); CHECK_EQ(s.next_attempt_unix, NOW + 900);
    /* an ack at low battery still drains */
    nw_upload_state_init(&s); f = mk(200, OKBODY);
    CHECK_EQ(attempt(&s, &f, &r, NOW, 3350, true).outcome, NW_UP_ACK); CHECK_EQ(nw_ring_count(&r), 0);
    CHECK_EQ(NW_VBAT_LOW_MV, 3400);
}

static void test_transport_error_and_rate_cap(void)
{
    nw_upload_state_t s; nw_upload_state_init(&s);
    nw_ring_t r; nw_ring_init(&r); push_n(&r, 3, NOW - 9000);
    fake_t f = mk(0, NULL); f.rc = -1;
    nw_upload_result_t x = attempt(&s, &f, &r, NOW, 3900, false);
    CHECK_EQ(x.outcome, NW_UP_RETRY); CHECK_EQ(f.calls, 1); CHECK_EQ(nw_ring_count(&r), 3); CHECK(x.outage_pending); CHECK_EQ(x.n_samples, 3);
    CHECK_EQ(s.attempts[0], NOW);                                                /* a failed call still used a slot */
    /* never more than 6 attempts in any hour, even with the backoff cleared each time */
    nw_upload_state_init(&s); f = mk(500, ""); int sent = 0;
    for (uint32_t t = NOW; t < NOW + 3600; t += 10) { s.next_attempt_unix = 0; f.calls = 0; attempt(&s, &f, &r, t, 3900, false); sent += f.calls; }
    CHECK_EQ(sent, 6);
    CHECK_EQ(nw_upload_on_response(&s, &r, 1, 1, NULL, NOW, false).outcome, NW_UP_RETRY);   /* NULL response = transport error */
}

static void test_outage_then_recovery(void)
{   /* FR-D04: 24 h offline (96 samples), then one upload drains everything */
    nw_upload_state_t s; nw_upload_state_init(&s);
    nw_ring_t r; nw_ring_init(&r); push_n(&r, NW_RING_CAP, NOW - 90000);
    fake_t f = mk(500, ""); uint32_t t = NOW;
    for (int i = 0; i < 3; i++) { attempt(&s, &f, &r, t, 3900, false); t = s.next_attempt_unix; }
    CHECK_EQ(nw_ring_count(&r), NW_RING_CAP);
    f = mk(200, OKBODY);
    nw_upload_result_t x = attempt(&s, &f, &r, t, 3900, false);
    CHECK_EQ(x.outcome, NW_UP_ACK); CHECK_EQ(x.drained, NW_RING_CAP); CHECK_EQ(x.n_samples, NW_RING_CAP); CHECK_EQ(nw_ring_count(&r), 0);
    CHECK(!x.outage_pending);
}

int main(void)
{
    test_url_and_auth();
    test_gate();
    test_ack_drains_batch_only();
    test_request_content();
    test_not_sent_paths();
    test_200_without_time_is_not_an_ack();
    test_401();
    test_reject_poison_guard();
    test_backoff_and_retry_after();
    test_low_battery_behaviour();
    test_transport_error_and_rate_cap();
    test_outage_then_recovery();
    printf("%d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}

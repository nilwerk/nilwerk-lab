/* Host tests for the offline buffer (FR-D04) and the hourly report payload (FR-D02, FR-D04). Task 4.F3. No hardware.
 * Run: built by test/host/CMakeLists.txt. With argv[1] = path, also writes the fixture-equivalent payload there;
 * check_report_contract.py uses that to compare the payload with docs/interfaces/fixtures/device-report.valid.json.
 * Review fixes covered here: C1 (seq-based ack, full wrap during the ack window), C2 (admission at push). */
#include <stdio.h>
#include <string.h>
#include "nwtest.h"
#include "nw_sample_ring.h"
#include "nw_report.h"

int nwtest_failed, nwtest_checked;

#define T0 1767222000u /* first sample of the cloud fixture device-report.valid.json */
#define NW_RING_RAM_BUDGET 4096 /* 4.F3: keep the buffer well inside the 20 KB RAM budget */
#define NW_BODY_LIMIT 64 * 1024 /* openapi /ingest 413: body > 64 KiB */

/* ---------- helpers ---------- */
static nw_sample_t full_sample(uint32_t ts)
{
    nw_sample_t s;
    memset(&s, 0, sizeof s);
    s.ts = ts;
    s.present = NW_HAS_MOISTURE | NW_HAS_MOISTURE_RAW | NW_HAS_TEMP | NW_HAS_RH | NW_HAS_LUX | NW_HAS_VBAT;
    s.moisture_x10 = 415; s.moisture_raw = 2210; s.temp_x100 = 2150; s.rh_x100 = 5500; s.lux_x10 = 12000; s.vbat_mv = 3900;
    return s;
}

/* The four samples of device-report.valid.json (15-min spacing, 4th sample has a failed soil reading). */
static void fill_fixture(nw_ring_t *r)
{
    nw_ring_init(r);
    nw_sample_t s;
    s = full_sample(1767222000u); s.moisture_x10 = 420; s.moisture_raw = 2210; s.temp_x100 = 2140; s.rh_x100 = 5500; s.lux_x10 = 12000; s.vbat_mv = 3900; nw_ring_push(r, &s, true);
    s = full_sample(1767222900u); s.moisture_x10 = 418; s.moisture_raw = 2214; s.temp_x100 = 2150; s.rh_x100 = 5500; s.lux_x10 = 11800; s.vbat_mv = 3898; nw_ring_push(r, &s, true);
    s = full_sample(1767223800u); s.moisture_x10 = 415; s.moisture_raw = 2219; s.temp_x100 = 2150; s.rh_x100 = 5400; s.lux_x10 = 11500; s.vbat_mv = 3897; nw_ring_push(r, &s, true);
    s = full_sample(1767224700u); s.present = NW_HAS_TEMP | NW_HAS_RH | NW_HAS_LUX | NW_HAS_VBAT; /* soil failed: null */
    s.temp_x100 = 2160; s.rh_x100 = 5400; s.lux_x10 = 11000; s.vbat_mv = 3896; nw_ring_push(r, &s, true);
}

static nw_event_t fixture_event = { 1767224000u, NW_EV_WETTING };

static nw_report_meta_t fixture_meta(void)
{
    nw_report_meta_t m;
    memset(&m, 0, sizeof m);
    m.sent_at = 1767225600u;
    m.trigger = NW_TRIG_SCHEDULED;
    m.fw = "0.3.1";
    m.model = "a-0.1";
    m.forecast_x10 = 415; /* 41.5 h */
    m.events = &fixture_event;
    m.n_events = 1;
    return m;
}

static size_t build(char *out, size_t cap, const nw_ring_t *r, const nw_report_meta_t *m, size_t *n)
{
    return nw_report_build(out, cap, r, m, n, NULL);
}

static bool contains(const char *hay, const char *needle) { return strstr(hay, needle) != NULL; }

/* seq of the i-th sample from the oldest, or 0 when absent: a failing check must report, not crash. */
static uint32_t seq_at(const nw_ring_t *r, size_t i) { const nw_sample_t *s = nw_ring_at(r, i); return s ? s->seq : 0; }
static uint32_t seq_newest(const nw_ring_t *r) { const nw_sample_t *s = nw_ring_newest(r); return s ? s->seq : 0; }

/* ---------- offline buffer, FR-D04 ---------- */
static void test_ring_capacity_and_wrap(void)
{
    nw_ring_t r;
    nw_ring_init(&r);
    CHECK_EQ(nw_ring_count(&r), 0);
    CHECK(nw_ring_at(&r, 0) == NULL);
    CHECK(nw_ring_newest(&r) == NULL);
    CHECK_EQ(NW_RING_CAP, 96);                              /* FR-D04: 96 x 15 min = 24 h */
    CHECK(sizeof(nw_ring_t) <= NW_RING_RAM_BUDGET);

    for (uint32_t i = 0; i < NW_RING_CAP; i++) {
        nw_sample_t s = full_sample(T0 + i * NW_SAMPLE_PERIOD_S);
        CHECK(nw_ring_push(&r, &s, true) == NW_PUSH_STORED);  /* no wrap while filling */
    }
    CHECK_EQ(nw_ring_count(&r), 96);
    CHECK_EQ(r.overwritten, 0);
    CHECK_EQ(nw_ring_at(&r, 0)->ts, T0);
    CHECK_EQ(nw_ring_at(&r, 95)->ts, T0 + 95 * 900);
    CHECK(nw_ring_at(&r, 96) == NULL);
    CHECK_EQ(nw_ring_at(&r, 0)->seq, 1);                    /* seq starts at 1 and is assigned by the ring */
    CHECK_EQ(nw_ring_newest(&r)->seq, 96);

    nw_sample_t s97 = full_sample(T0 + 96 * 900);           /* 97th: oldest goes, newest stays */
    CHECK(nw_ring_push(&r, &s97, true) == NW_PUSH_STORED_OVERWROTE);
    CHECK_EQ(nw_ring_count(&r), 96);
    CHECK_EQ(r.overwritten, 1);
    CHECK_EQ(nw_ring_at(&r, 0)->ts, T0 + 900);
    CHECK_EQ(nw_ring_newest(&r)->ts, T0 + 96 * 900);
}

/* Long run across many wraps: after every push the newest is the pushed sample, the window is contiguous and
 * the oldest is exactly 95 steps back. A 3-day run of 15-min samples. */
static void test_ring_long_run(void)
{
    nw_ring_t r;
    nw_ring_init(&r);
    int bad = 0;
    const uint32_t total = 3 * 96;
    for (uint32_t i = 0; i < total; i++) {
        nw_sample_t s = full_sample(T0 + i * 900);
        nw_ring_push(&r, &s, true);
        if (nw_ring_newest(&r)->ts != T0 + i * 900) bad++;                  /* newest never lost */
        if (nw_ring_count(&r) != (i + 1 < 96 ? i + 1 : 96)) bad++;
        size_t cnt = nw_ring_count(&r);
        if (nw_ring_at(&r, cnt - 1)->ts != T0 + i * 900) bad++;
        if (nw_ring_at(&r, 0)->ts != T0 + (i + 1 - cnt) * 900) bad++;       /* oldest correct across the wrap */
        for (size_t k = 1; k < cnt; k++)
            if (nw_ring_at(&r, k)->ts - nw_ring_at(&r, k - 1)->ts != 900) { bad++; break; }
    }
    CHECK_EQ(bad, 0);
    CHECK_EQ(r.overwritten, total - 96);
}

/* Ack by sequence (review C1): a 2xx removes exactly the samples up to the batch's last seq. */
static void test_ring_consume_upto(void)
{
    nw_ring_t r;
    nw_ring_init(&r);
    for (uint32_t i = 0; i < 10; i++) { nw_sample_t s = full_sample(T0 + i * 900); nw_ring_push(&r, &s, true); }
    CHECK_EQ(nw_ring_consume_upto(&r, 4), 4);               /* seq 1..4 */
    CHECK_EQ(nw_ring_count(&r), 6);
    CHECK_EQ(nw_ring_at(&r, 0)->ts, T0 + 4 * 900);
    CHECK_EQ(nw_ring_consume_upto(&r, 4), 0);               /* ack again: nothing <= 4 is left */
    CHECK_EQ(nw_ring_consume_upto(&r, 1000), 6);            /* never more than stored */
    CHECK_EQ(nw_ring_count(&r), 0);
    CHECK(nw_ring_newest(&r) == NULL);
    CHECK_EQ(nw_ring_consume_upto(&r, 0), 0);
    CHECK_EQ(nw_ring_consume_upto(NULL, 5), 0);

    /* refill after draining: the wrap index is still right */
    for (uint32_t i = 0; i < 150; i++) { nw_sample_t s = full_sample(T0 + (100 + i) * 900); nw_ring_push(&r, &s, true); }
    CHECK_EQ(nw_ring_count(&r), 96);
    CHECK_EQ(nw_ring_newest(&r)->ts, T0 + 249 * 900);
    CHECK_EQ(nw_ring_at(&r, 0)->ts, T0 + (249 - 95) * 900);
}

/* C1: the ring wraps FULLY during the ack window. A count-based consume(n) removed the newest unsent samples here.
 * The ack is by seq, so only the sent prefix (seq <= last) may go, and nothing of the new generation. */
static void test_ack_window_full_wrap(void)
{
    char buf[8192];
    size_t n = 0;
    uint32_t last = 0;
    nw_report_meta_t m = fixture_meta();

    /* A: batch of 4, then 96 new samples arrive during the upload: the ring wraps fully and the 4 sent samples are gone */
    nw_ring_t r;
    nw_ring_init(&r);
    for (uint32_t i = 0; i < 4; i++) { nw_sample_t s = full_sample(T0 + i * 900); nw_ring_push(&r, &s, true); }
    CHECK(nw_report_build(buf, sizeof buf, &r, &m, &n, &last) > 0);
    CHECK_EQ(n, 4);
    CHECK_EQ(last, 4);
    for (uint32_t i = 4; i < 100; i++) {
        nw_sample_t s = full_sample(T0 + i * 900);
        nw_push_t p = nw_ring_push(&r, &s, true);
        CHECK(p == NW_PUSH_STORED || p == NW_PUSH_STORED_OVERWROTE);
    }
    CHECK_EQ(r.overwritten, 4);                             /* 100 pushes into 96 slots: the 4 sent samples went */
    CHECK_EQ(nw_ring_consume_upto(&r, last), 0);            /* the 2xx: nothing of the new generation may go */
    CHECK_EQ(nw_ring_count(&r), 96);
    CHECK_EQ(seq_at(&r, 0), 5);                             /* first new sample still there */
    CHECK_EQ(seq_newest(&r), 100);
    CHECK_EQ(seq_at(&r, 95), 100);

    /* B: a full batch of 96, then 96 new samples arrive during the upload: the whole new generation must survive */
    nw_ring_t f;
    nw_ring_init(&f);
    for (uint32_t i = 0; i < NW_RING_CAP; i++) { nw_sample_t s = full_sample(T0 + i * 900); nw_ring_push(&f, &s, true); }
    static char big[NW_BODY_LIMIT];                         /* 96 samples need about 12 KB */
    CHECK(nw_report_build(big, sizeof big, &f, &m, &n, &last) > 0);
    CHECK_EQ(n, 96);
    CHECK_EQ(last, 96);
    for (uint32_t i = 96; i < 192; i++) { nw_sample_t s = full_sample(T0 + i * 900); nw_ring_push(&f, &s, true); }
    CHECK_EQ(f.overwritten, 96);
    CHECK_EQ(nw_ring_consume_upto(&f, last), 0);
    CHECK_EQ(nw_ring_count(&f), 96);
    CHECK_EQ(seq_at(&f, 0), 97);
    CHECK_EQ(seq_newest(&f), 192);

    /* C: no wrap, the sent prefix is removed and the newer sample stays (exact-prefix ack) */
    nw_ring_t p;
    nw_ring_init(&p);
    for (uint32_t i = 0; i < 4; i++) { nw_sample_t s = full_sample(T0 + i * 900); nw_ring_push(&p, &s, true); }
    CHECK(nw_report_build(buf, sizeof buf, &p, &m, &n, &last) > 0);
    for (uint32_t i = 4; i < 10; i++) { nw_sample_t s = full_sample(T0 + i * 900); nw_ring_push(&p, &s, true); }
    CHECK_EQ(nw_ring_consume_upto(&p, last), 4);
    CHECK_EQ(nw_ring_count(&p), 6);
    CHECK_EQ(seq_at(&p, 0), 5);
}

/* C2: admission at push. Refused samples are not stored and are counted. */
static void test_ring_admission(void)
{
    nw_ring_t r;
    nw_ring_init(&r);
    nw_sample_t ok = full_sample(T0);

    /* Time not synced: nothing is stored while time_synced is false (never upload before SNTP) */
    CHECK(nw_ring_push(&r, &ok, false) == NW_PUSH_REJECTED_UNSYNCED);
    CHECK_EQ(nw_ring_count(&r), 0);
    CHECK_EQ(r.rejected, 1);

    /* Schema floor: NW_TS_MIN is the schema minimum (1700000000). Exactly the floor is accepted, one below is refused. */
    CHECK_EQ(NW_TS_MIN, 1700000000u);
    nw_sample_t floor_ok = full_sample(NW_TS_MIN);
    CHECK(nw_ring_push(&r, &floor_ok, true) == NW_PUSH_STORED);
    nw_sample_t below = full_sample(NW_TS_MIN - 1);
    CHECK(nw_ring_push(&r, &below, true) == NW_PUSH_REJECTED_INVALID);
    nw_sample_t unsynced_ts = full_sample(12345u);          /* RTC never synced */
    CHECK(nw_ring_push(&r, &unsynced_ts, true) == NW_PUSH_REJECTED_INVALID);
    CHECK_EQ(nw_ring_count(&r), 1);

    /* Value ranges, only when the field is present */
    nw_sample_t x = full_sample(T0);
    x.moisture_x10 = 1001;
    CHECK(nw_ring_push(&r, &x, true) == NW_PUSH_REJECTED_INVALID);
    x = full_sample(T0); x.moisture_raw = 4096;
    CHECK(nw_ring_push(&r, &x, true) == NW_PUSH_REJECTED_INVALID);
    x = full_sample(T0); x.rh_x100 = 10001;
    CHECK(nw_ring_push(&r, &x, true) == NW_PUSH_REJECTED_INVALID);
    x = full_sample(T0); x.rh_x100 = -1;
    CHECK(nw_ring_push(&r, &x, true) == NW_PUSH_REJECTED_INVALID);
    x = full_sample(T0); x.present = 0x40;                  /* bit outside NW_PRESENT_MASK */
    CHECK(nw_ring_push(&r, &x, true) == NW_PUSH_REJECTED_INVALID);
    x = full_sample(T0); x.present &= (uint8_t)~NW_HAS_MOISTURE; x.moisture_x10 = 5000;  /* absent: value not checked */
    CHECK(nw_ring_push(&r, &x, true) == NW_PUSH_STORED);
    CHECK(nw_ring_push(NULL, &ok, true) == NW_PUSH_REJECTED_INVALID);
    CHECK(nw_ring_push(&r, NULL, true) == NW_PUSH_REJECTED_INVALID);
    CHECK_EQ(r.rejected, 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1);
    CHECK_EQ(nw_ring_count(&r), 2);
    CHECK_EQ(nw_ring_at(&r, 0)->seq, 1);                    /* refused samples take no seq */
    CHECK_EQ(nw_ring_at(&r, 1)->seq, 2);
}

/* ---------- payload, FR-D02 / schema device-report.v1 ---------- */
static void test_payload_empty_and_bounds(void)
{
    nw_ring_t r;
    fill_fixture(&r);
    nw_report_meta_t m = fixture_meta();
    char buf[8192];
    size_t n = 99;
    CHECK_EQ(build(NULL, sizeof buf, &r, &m, &n), 0);
    CHECK_EQ(build(buf, 0, &r, &m, &n), 0);
    CHECK_EQ(build(buf, sizeof buf, NULL, &m, &n), 0);
    CHECK_EQ(build(buf, sizeof buf, &r, NULL, &n), 0);

    nw_ring_t empty;
    nw_ring_init(&empty);
    CHECK_EQ(build(buf, sizeof buf, &empty, &m, &n), 0);    /* schema samples minItems 1 */
    CHECK_EQ(n, 0);

    /* exact fit: cap == length + 1 works, cap == length (no room for NUL) fails */
    size_t len = build(buf, sizeof buf, &r, &m, &n);
    CHECK(len > 0);
    CHECK_EQ(n, 4);
    static char small[8192];
    size_t len2 = build(small, len + 1, &r, &m, NULL);
    CHECK_EQ(len2, len);
    CHECK_EQ(build(small, len, &r, &m, NULL), 0);
    CHECK_EQ(strlen(buf), len);
}

static void test_payload_meta_rejects(void)
{
    nw_ring_t r;
    fill_fixture(&r);
    char buf[8192];
    size_t n = 0;
    nw_report_meta_t m;

    m = fixture_meta(); m.sent_at = 1000; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);        /* SNTP not synced */
    m = fixture_meta(); m.fw = ""; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);
    m = fixture_meta(); m.fw = "0.3\"1"; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);          /* no JSON escaping */
    m = fixture_meta(); m.fw = "0123456789012345678901234567890123"; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0); /* 34 > 32 */
    m = fixture_meta(); m.model = "m-with space"; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);
    m = fixture_meta(); m.forecast_x10 = 721; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);     /* > 72 h */
    m = fixture_meta(); m.forecast_x10 = -1; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);
    m = fixture_meta(); m.trigger = (nw_trigger_t)3; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);
    m = fixture_meta(); m.n_events = 33; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);          /* schema events maxItems 32 */
    nw_event_t ev_bad_type = { 1767224000u, (nw_event_type_t)6 };  /* local copy: fixture_event stays intact */
    m = fixture_meta(); m.events = &ev_bad_type; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);
    nw_event_t ev_bad_ts = { 5u, NW_EV_WETTING };
    m = fixture_meta(); m.events = &ev_bad_ts; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);
    nw_report_cal_t bad_cal = { 4096, 1500, 0 };
    m = fixture_meta(); m.cal = &bad_cal; CHECK_EQ(build(buf, sizeof buf, &r, &m, &n), 0);        /* cal 0..4095 */
    CHECK_EQ(n, 0);
}

static void test_payload_fixture_fields(void)
{
    nw_ring_t r;
    fill_fixture(&r);
    nw_report_meta_t m = fixture_meta();
    char buf[8192];
    size_t n = 0;
    uint32_t last = 0;
    size_t len = nw_report_build(buf, sizeof buf, &r, &m, &n, &last);
    CHECK(len > 0);
    CHECK_EQ(n, 4);
    CHECK_EQ(last, 4);
    CHECK(contains(buf, "{\"v\":1,\"sent_at\":1767225600,\"trigger\":\"scheduled\",\"fw\":\"0.3.1\",\"model\":\"a-0.1\",\"forecast_h\":41.5,"));
    CHECK(contains(buf, "\"samples\":[{\"ts\":1767222000,\"moisture_pct\":42.0,\"moisture_raw\":2210,\"temp_c\":21.40,\"rh_pct\":55.00,\"lux\":1200.0,\"vbat_mv\":3900}"));
    CHECK(contains(buf, "{\"ts\":1767224700,\"moisture_pct\":null,\"moisture_raw\":null,\"temp_c\":21.60,\"rh_pct\":54.00,\"lux\":1100.0,\"vbat_mv\":3896}]"));
    CHECK(contains(buf, ",\"events\":[{\"ts\":1767224000,\"type\":\"wetting\"}]}"));
    CHECK(!contains(buf, "\"cal\""));                         /* NULL cal: omitted */
    CHECK(!contains(buf, "\"ota\""));                         /* OTA out of scope in 4.F3 */
}

static void test_payload_optional_and_signs(void)
{
    nw_ring_t r;
    nw_ring_init(&r);
    nw_sample_t s = full_sample(T0);
    s.temp_x100 = -5;            /* -0.05 degC: sign and leading zero */
    s.rh_x100 = 1234;            /* 12.34 %RH (negative rh is refused at push, see test_ring_admission) */
    s.present &= (uint8_t)~NW_HAS_VBAT;
    CHECK(nw_ring_push(&r, &s, true) == NW_PUSH_STORED);
    nw_report_meta_t m = fixture_meta();
    m.model = NULL;
    m.forecast_x10 = NW_REPORT_FORECAST_NULL;
    nw_report_cal_t cal = { 2300, 1100, 0 };
    m.cal = &cal;
    m.n_events = 0;
    char buf[8192];
    size_t n = 0;
    CHECK(build(buf, sizeof buf, &r, &m, &n) > 0);
    CHECK(contains(buf, "\"temp_c\":-0.05"));
    CHECK(contains(buf, "\"rh_pct\":12.34"));
    CHECK(contains(buf, "\"vbat_mv\":null"));
    CHECK(!contains(buf, "\"model\""));
    CHECK(contains(buf, "\"forecast_h\":null,"));
    CHECK(contains(buf, "\"cal\":{\"dry_raw\":2300,\"wet_raw\":1100},"));
    CHECK(contains(buf, "\"events\":[]}"));
    m.cal = NULL;
    CHECK(build(buf, sizeof buf, &r, &m, &n) > 0);
    CHECK(!contains(buf, "\"cal\""));
}

/* Each sensor field has its own presence bit: a failed sensor becomes null for that field only (schema: null = sensor failed). */
static void test_payload_each_field_null_alone(void)
{
    const uint8_t all = NW_HAS_MOISTURE | NW_HAS_MOISTURE_RAW | NW_HAS_TEMP | NW_HAS_RH | NW_HAS_LUX | NW_HAS_VBAT;
    const struct { uint8_t bit; const char *key; } f[] = {
        { NW_HAS_MOISTURE, "\"moisture_pct\":null" }, { NW_HAS_MOISTURE_RAW, "\"moisture_raw\":null" },
        { NW_HAS_TEMP, "\"temp_c\":null" }, { NW_HAS_RH, "\"rh_pct\":null" },
        { NW_HAS_LUX, "\"lux\":null" }, { NW_HAS_VBAT, "\"vbat_mv\":null" },
    };
    char buf[8192];
    nw_report_meta_t m = fixture_meta();
    for (size_t k = 0; k < sizeof f / sizeof f[0]; k++) {
        nw_ring_t r;
        nw_ring_init(&r);
        nw_sample_t s = full_sample(T0);
        s.present = (uint8_t)(all & ~f[k].bit);
        nw_ring_push(&r, &s, true);
        CHECK(build(buf, sizeof buf, &r, &m, NULL) > 0);
        CHECK(contains(buf, f[k].key));
        /* the other five fields are still numbers */
        size_t nulls = 0;
        for (const char *p = buf; (p = strstr(p, ":null")) != NULL; p++) nulls++;
        CHECK_EQ(nulls, 1);
    }
}

static void test_payload_trigger_names(void)
{
    nw_ring_t r;
    fill_fixture(&r);
    char buf[8192];
    nw_report_meta_t m = fixture_meta();
    m.trigger = NW_TRIG_CRITICAL;
    CHECK(build(buf, sizeof buf, &r, &m, NULL) > 0);
    CHECK(contains(buf, "\"trigger\":\"critical\""));
    m.trigger = NW_TRIG_RECONNECT;                          /* C4: first report after an outage */
    CHECK(build(buf, sizeof buf, &r, &m, NULL) > 0);
    CHECK(contains(buf, "\"trigger\":\"reconnect\""));
    m.trigger = NW_TRIG_SCHEDULED;
    CHECK(build(buf, sizeof buf, &r, &m, NULL) > 0);
    CHECK(contains(buf, "\"trigger\":\"scheduled\""));
}

/* A full 24 h offline buffer (96 samples) must fit a single request, well under the 64 KiB body limit. */
static void test_payload_full_buffer_size(void)
{
    nw_ring_t r;
    nw_ring_init(&r);
    for (uint32_t i = 0; i < NW_RING_CAP; i++) {
        nw_sample_t s = full_sample(T0 + i * 900);
        nw_ring_push(&r, &s, true);
    }
    static char buf[NW_BODY_LIMIT];
    nw_report_meta_t m = fixture_meta();
    size_t n = 0;
    size_t len = build(buf, sizeof buf, &r, &m, &n);
    CHECK_EQ(n, 96);
    CHECK(len > 0 && len < NW_BODY_LIMIT);
    CHECK(len < 16 * 1024);                                  /* RAM: keep the JSON buffer near 16 KB, see handoff note */
}

/* The upload race: the batch of 4 is built, a new sample arrives before the 2xx, consume_upto(last) must keep it. */
static void test_upload_race_keeps_newest(void)
{
    nw_ring_t r;
    fill_fixture(&r);
    char buf[8192];
    size_t n = 0;
    uint32_t last = 0;
    nw_report_meta_t m = fixture_meta();
    CHECK(nw_report_build(buf, sizeof buf, &r, &m, &n, &last) > 0);
    nw_sample_t fresh = full_sample(T0 + 4 * 900);
    nw_ring_push(&r, &fresh, true);
    CHECK_EQ(nw_ring_consume_upto(&r, last), 4);             /* the 2xx acknowledges the 4 sent samples only */
    CHECK_EQ(nw_ring_count(&r), 1);
    CHECK_EQ(nw_ring_newest(&r)->ts, T0 + 4 * 900);
}

static int write_file(const char *path, const char *data, size_t len)
{
    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    size_t w = fwrite(data, 1, len, f);
    fclose(f);
    return w == len ? 0 : -1;
}

int main(int argc, char **argv)
{
    test_ring_capacity_and_wrap();
    test_ring_long_run();
    test_ring_consume_upto();
    test_ack_window_full_wrap();
    test_ring_admission();
    test_payload_empty_and_bounds();
    test_payload_meta_rejects();
    test_payload_fixture_fields();
    test_payload_optional_and_signs();
    test_payload_trigger_names();
    test_payload_each_field_null_alone();
    test_payload_full_buffer_size();
    test_upload_race_keeps_newest();

    if (argc > 1) {
        nw_ring_t r;
        fill_fixture(&r);
        nw_report_meta_t m = fixture_meta();
        char buf[8192];
        size_t len = build(buf, sizeof buf, &r, &m, NULL);
        CHECK(len > 0);
        CHECK(write_file(argv[1], buf, len) == 0);
    }

    printf("%d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}

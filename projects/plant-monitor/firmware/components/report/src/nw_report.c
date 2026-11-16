/* Hourly report JSON (task 4.F3, FR-D02, FR-D04). Field mapping: see nw_report.h. Pure C. */
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include "nw_report.h"

typedef struct {
    char *buf;
    size_t cap;
    size_t len;
    bool err;
} nw_w_t;

static void put(nw_w_t *w, const char *s)
{
    size_t n = strlen(s);
    if (w->err || w->len + n + 1 > w->cap) { w->err = true; return; }
    memcpy(w->buf + w->len, s, n);
    w->len += n;
    w->buf[w->len] = '\0';
}

static void putf(nw_w_t *w, const char *fmt, ...)
{
    char tmp[64];
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(tmp, sizeof tmp, fmt, ap);
    va_end(ap);
    if (n < 0 || (size_t)n >= sizeof tmp) { w->err = true; return; }
    put(w, tmp);
}

/* Fixed-point to decimal text with exactly decs digits (decs 1: x10, decs 2: x100). Sign handled for negatives. */
static void put_fix(nw_w_t *w, int64_t v, int decs)
{
    int64_t div = (decs == 1) ? 10 : 100;
    int64_t a = (v < 0) ? -v : v;
    putf(w, "%s%lld.%0*lld", (v < 0) ? "-" : "", (long long)(a / div), decs, (long long)(a % div));
}

static void put_opt_fix(nw_w_t *w, bool has, int64_t v, int decs)
{
    if (has) put_fix(w, v, decs);
    else put(w, "null");
}

static void put_opt_uint(nw_w_t *w, bool has, unsigned long v)
{
    if (has) putf(w, "%lu", v);
    else put(w, "null");
}

static bool version_ok(const char *s)
{
    size_t n = strlen(s);
    if (n == 0 || n > NW_REPORT_VERSION_MAX) return false;
    for (size_t i = 0; i < n; i++) {
        char c = s[i];
        bool ok = (c >= '0' && c <= '9') || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '.' || c == '-' || c == '_';
        if (!ok) return false; /* no JSON escaping needed: only safe characters are accepted */
    }
    return true;
}

static bool meta_ok(const nw_report_meta_t *m)
{
    if (m->sent_at < NW_REPORT_TS_MIN) return false;                 /* schema sent_at minimum; no send before SNTP */
    if ((int)m->trigger < NW_TRIG_SCHEDULED || (int)m->trigger > NW_TRIG_RECONNECT) return false;
    if (!m->fw || !version_ok(m->fw)) return false;
    if (m->model && !version_ok(m->model)) return false;
    if (m->forecast_x10 != NW_REPORT_FORECAST_NULL &&
        (m->forecast_x10 < 0 || m->forecast_x10 > NW_REPORT_FORECAST_MAX_X10)) return false;
    if (m->n_events > NW_REPORT_MAX_EVENTS || (m->n_events > 0 && !m->events)) return false;
    for (size_t i = 0; i < m->n_events; i++) {
        if (m->events[i].ts < NW_REPORT_TS_MIN) return false;
        if ((int)m->events[i].type < NW_EV_WETTING || (int)m->events[i].type > NW_EV_SENSOR_FAULT) return false;
    }
    if (m->cal && (m->cal->dry_raw > 4095 || m->cal->wet_raw > 4095)) return false; /* schema cal 0..4095 */
    return true;
}

static void put_sample(nw_w_t *w, const nw_sample_t *s)
{
    putf(w, "{\"ts\":%lu,\"moisture_pct\":", (unsigned long)s->ts);
    put_opt_fix(w, (s->present & NW_HAS_MOISTURE) != 0, s->moisture_x10, 1);
    put(w, ",\"moisture_raw\":");
    put_opt_uint(w, (s->present & NW_HAS_MOISTURE_RAW) != 0, s->moisture_raw);
    put(w, ",\"temp_c\":");
    put_opt_fix(w, (s->present & NW_HAS_TEMP) != 0, s->temp_x100, 2);
    put(w, ",\"rh_pct\":");
    put_opt_fix(w, (s->present & NW_HAS_RH) != 0, s->rh_x100, 2);
    put(w, ",\"lux\":");
    put_opt_fix(w, (s->present & NW_HAS_LUX) != 0, s->lux_x10, 1);
    put(w, ",\"vbat_mv\":");
    put_opt_uint(w, (s->present & NW_HAS_VBAT) != 0, s->vbat_mv);
    put(w, "}");
}

size_t nw_report_build(char *out, size_t cap, const nw_ring_t *r, const nw_report_meta_t *m, size_t *n_samples)
{
    if (n_samples) *n_samples = 0;
    if (!out || cap == 0 || !r || !m) return 0;
    if (!meta_ok(m)) return 0;

    size_t n = nw_ring_count(r);
    if (n == 0) return 0;                              /* schema samples minItems 1: nothing to send */
    if (n > NW_REPORT_MAX_SAMPLES) n = NW_REPORT_MAX_SAMPLES;
    for (size_t i = 0; i < n; i++) {
        if (nw_ring_at(r, i)->ts < NW_REPORT_TS_MIN) return 0; /* whole batch would get 400: refuse to build it */
    }

    nw_w_t w = { out, cap, 0, false };
    out[0] = '\0';
    putf(&w, "{\"v\":%d,\"sent_at\":%lu,", NW_REPORT_V, (unsigned long)m->sent_at);
    putf(&w, "\"trigger\":\"%s\",",
         (m->trigger == NW_TRIG_SCHEDULED) ? "scheduled" : (m->trigger == NW_TRIG_CRITICAL) ? "critical" : "reconnect");
    putf(&w, "\"fw\":\"%s\",", m->fw);
    if (m->model) putf(&w, "\"model\":\"%s\",", m->model);
    put(&w, "\"forecast_h\":");
    if (m->forecast_x10 == NW_REPORT_FORECAST_NULL) put(&w, "null");
    else put_fix(&w, m->forecast_x10, 1);
    put(&w, ",");
    if (m->cal) {
        putf(&w, "\"cal\":{\"dry_raw\":%u,\"wet_raw\":%u", (unsigned)m->cal->dry_raw, (unsigned)m->cal->wet_raw);
        if (m->cal->at) putf(&w, ",\"at\":%lu", (unsigned long)m->cal->at);
        put(&w, "},");
    }
    put(&w, "\"samples\":[");
    for (size_t i = 0; i < n; i++) {
        if (i) put(&w, ",");
        put_sample(&w, nw_ring_at(r, i));
    }
    put(&w, "],\"events\":[");
    static const char *const ev_names[] = {
        "wetting", "wetting_unexpected", "fast_drying", "waterlogged", "sensor_out_of_soil", "sensor_fault"
    };
    for (size_t i = 0; i < m->n_events; i++) {
        if (i) put(&w, ",");
        putf(&w, "{\"ts\":%lu,\"type\":\"%s\"}", (unsigned long)m->events[i].ts, ev_names[(int)m->events[i].type]);
    }
    put(&w, "]}");

    if (w.err) return 0;
    if (n_samples) *n_samples = n;
    return w.len;
}

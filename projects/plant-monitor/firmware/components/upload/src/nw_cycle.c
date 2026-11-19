/* One wake of the upload build (task 4.F3 slice 3). See nw_cycle.h. Pure C. */
#include "nw_cycle.h"
#include <string.h>

_Static_assert(sizeof(nw_cycle_state_t) <= NW_CYCLE_RTC_BUDGET_BYTES, "RTC state over budget (design proposal, motivated by NFR-12): shrink it or revisit the limit");

static bool ts_plausible_or_zero(uint32_t t) { return t == 0 || (t >= NW_TS_MIN && t <= NW_CYCLE_TS_MAX); }

static bool state_consistent(const nw_cycle_state_t *st)
{
    const unsigned char *lb = (const unsigned char *)&st->low_battery, *op = (const unsigned char *)&st->outage_pending;
    if (*lb > 1 || *op > 1) return false;                                       /* a bool byte other than 0/1 is garbage */
    if (st->last_report_unix != 0 && st->last_report_unix < NW_TS_MIN) return false;
    const nw_upload_state_t *u = &st->up;                                       /* att_head indexes attempts[]: out of range = write outside the array */
    if (u->att_head >= NW_UPLOAD_MAX_PER_HOUR || !ts_plausible_or_zero(u->next_attempt_unix)) return false;
    for (size_t i = 0; i < NW_UPLOAD_MAX_PER_HOUR; i++) if (!ts_plausible_or_zero(u->attempts[i])) return false;
    return nw_ring_valid(&st->ring);
}

bool nw_cycle_state_ensure(nw_cycle_state_t *st)
{
    if (st->magic == NW_CYCLE_MAGIC && state_consistent(st)) return false;
    memset(st, 0, sizeof *st);
    st->magic = NW_CYCLE_MAGIC;
    nw_ring_init(&st->ring);
    nw_upload_state_init(&st->up);
    return true;
}

bool nw_cycle_clock_ok(uint32_t now_unix) { return now_unix >= NW_TS_MIN; }

static size_t bounded_len(const char *s, size_t cap)   /* strnlen is POSIX, not C11 */
{
    size_t n = 0;
    while (n < cap && s[n]) n++;
    return n;
}

nw_creds_check_t nw_cycle_creds_check(const nw_prov_record_t *rec)
{
    if (!rec) return NW_CREDS_NO_SSID;
    size_t sl = bounded_len(rec->ssid, sizeof rec->ssid);
    if (sl == 0 || sl > NW_PROV_SSID_MAX_BYTES) return NW_CREDS_NO_SSID;
    size_t pl = bounded_len(rec->passphrase, sizeof rec->passphrase);
    if (pl != 0 && (pl < NW_PROV_PASS_MIN || pl > NW_PROV_PASS_MAX)) return NW_CREDS_BAD_PASSPHRASE;
    char auth[NW_UPLOAD_AUTH_MAX];
    int n = nw_upload_build_auth(auth, sizeof auth, rec->device_token);   /* validates ^[0-9a-f]{64}$ */
    memset(auth, 0, sizeof auth);
    return n < 0 ? NW_CREDS_BAD_TOKEN : NW_CREDS_OK;
}

void nw_cycle_make_sample(nw_sample_t *out, uint32_t ts, const nw_soil_t *soil, nw_err_t e_soil, const nw_aht20_t *aht, nw_err_t e_aht,
                          const nw_bh1750_t *bh, nw_err_t e_bh, uint32_t vbat_mv, nw_err_t e_bat)
{
    memset(out, 0, sizeof *out);
    out->ts = ts;
    if (e_soil == NW_OK && soil && soil->pct_x10 >= 0 && soil->pct_x10 <= 1000) {
        out->present |= NW_HAS_MOISTURE;
        out->moisture_x10 = (uint16_t)soil->pct_x10;
    }
    if (e_soil == NW_OK && soil && soil->raw >= 0 && soil->raw <= 4095) {
        out->present |= NW_HAS_MOISTURE_RAW;
        out->moisture_raw = (uint16_t)soil->raw;
    }
    if (e_aht == NW_OK && aht) {
        out->present |= NW_HAS_TEMP;
        out->temp_x100 = aht->temp_c_x100;
        if (aht->rh_x100 >= 0 && aht->rh_x100 <= 10000) {
            out->present |= NW_HAS_RH;
            out->rh_x100 = aht->rh_x100;
        }
    }
    if (e_bh == NW_OK && bh) {
        out->present |= NW_HAS_LUX;
        out->lux_x10 = bh->lux_x10;
    }
    if (e_bat == NW_OK && nw_battery_plausible(vbat_mv)) {
        out->present |= NW_HAS_VBAT;
        out->vbat_mv = (uint16_t)vbat_mv;
    }
}

nw_cycle_plan_t nw_cycle_begin(nw_cycle_state_t *st, uint32_t now_unix, const nw_sample_t *sample, int32_t vbat_mv)
{
    nw_cycle_plan_t p;
    memset(&p, 0, sizeof p);
    p.pushed = NW_PUSH_REJECTED_INVALID;
    bool synced = nw_cycle_clock_ok(now_unix);
    if (sample) {
        nw_sample_t s = *sample;
        s.ts = now_unix;
        p.pushed = nw_ring_push(&st->ring, &s, synced);
    }
    nw_sleep_in_t in = {
        .time_synced = synced, .now_unix = now_unix, .last_report_unix = st->last_report_unix,
        .buffered = (uint32_t)nw_ring_count(&st->ring), .critical_pending = false, .vbat_mv = vbat_mv,
        .low_battery_prev = st->low_battery, .outage_pending = st->outage_pending,
    };
    p.sleep = nw_sleep_decide(&in);
    st->low_battery = p.sleep.low_battery;
    st->outage_pending = p.sleep.outage_pending;
    return p;
}

static bool trigger_for(nw_report_kind_t k, nw_trigger_t *t)
{
    switch (k) {
    case NW_REPORT_SCHEDULED: *t = NW_TRIG_SCHEDULED; return true;
    case NW_REPORT_CRITICAL: *t = NW_TRIG_CRITICAL; return true;
    case NW_REPORT_RECONNECT: *t = NW_TRIG_RECONNECT; return true;
    default: return false;
    }
}

nw_upload_result_t nw_cycle_report(nw_cycle_state_t *st, const nw_upload_io_t *io, nw_report_kind_t kind, const char *fw, const char *base_url,
                                   const char *device_token, uint32_t now_unix, int32_t vbat_mv, char *buf, size_t cap)
{
    nw_report_meta_t m;
    memset(&m, 0, sizeof m);
    m.sent_at = now_unix;
    m.fw = fw;
    m.forecast_x10 = NW_REPORT_FORECAST_NULL;
    nw_upload_result_t r;
    if (!trigger_for(kind, &m.trigger)) {
        memset(&r, 0, sizeof r);
        r.outcome = NW_UP_NOT_SENT;
        r.why = NW_UP_WHY_NONE;
        r.outage_pending = st->outage_pending;
        return r;
    }
    r = nw_upload_attempt(&st->up, io, &st->ring, &m, base_url, device_token, now_unix, vbat_mv, st->low_battery, buf, cap);
    st->outage_pending = r.outage_pending;
    if (r.outcome == NW_UP_ACK) st->last_report_unix = r.server_time_valid ? r.server_time : now_unix;
    return r;
}

uint32_t nw_cycle_sleep_s(uint32_t now_unix)
{
    if (!nw_cycle_clock_ok(now_unix)) return NW_SLEEP_SAMPLE_PERIOD_S;
    return NW_SLEEP_SAMPLE_PERIOD_S - (now_unix % NW_SLEEP_SAMPLE_PERIOD_S);
}

int32_t nw_cycle_parse_retry_after(const char *value)
{
    if (!value || !*value) return -1;
    int32_t v = 0;
    size_t n = 0;
    for (; value[n]; n++) {
        if (value[n] < '0' || value[n] > '9' || n >= 9) return -1;
        v = v * 10 + (value[n] - '0');
    }
    return v;
}

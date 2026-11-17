#include "nw_upload.h"
#include <string.h>
#include "nw_sleep.h"

int nw_upload_build_url(char *out, size_t cap, const char *base)
{
    static const char scheme[] = "https://";
    if (!out || !cap || !base) return -1;
    size_t n = strlen(base), sl = sizeof scheme - 1;
    if (n <= sl || memcmp(base, scheme, sl) != 0) return -1;      /* TLS only, never http:// (NFR-06) */
    if (base[n - 1] == '/') return -1;
    for (size_t i = 0; i < n; i++) {
        unsigned char c = (unsigned char)base[i];
        if (c <= ' ' || c == 0x7f || c == '?' || c == '#') return -1;
    }
    size_t pl = sizeof NW_UPLOAD_PATH - 1;
    if (n + pl + 1 > cap || n + pl + 1 > NW_UPLOAD_URL_MAX) return -1;
    memcpy(out, base, n);
    memcpy(out + n, NW_UPLOAD_PATH, pl + 1);
    return (int)(n + pl);
}

int nw_upload_build_auth(char *out, size_t cap, const char *token)
{
    if (!out || !cap || !token || cap < NW_UPLOAD_AUTH_MAX) return -1;
    for (size_t i = 0; i < NW_UPLOAD_TOKEN_HEX; i++) {
        char c = token[i];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return -1;   /* also catches a short token (NUL) */
    }
    if (token[NW_UPLOAD_TOKEN_HEX] != 0) return -1;
    memcpy(out, "Bearer ", 7);
    memcpy(out + 7, token, NW_UPLOAD_TOKEN_HEX);
    out[7 + NW_UPLOAD_TOKEN_HEX] = 0;
    return 7 + NW_UPLOAD_TOKEN_HEX;
}

void nw_upload_state_init(nw_upload_state_t *s) { memset(s, 0, sizeof *s); }

nw_upload_gate_t nw_upload_gate(const nw_upload_state_t *s, uint32_t now, int32_t vbat_mv)
{
    if (vbat_mv >= 0 && vbat_mv <= NW_VBAT_WIFI_CUTOFF_MV) return NW_UP_GATE_LOW_VBAT;
    if (now < s->next_attempt_unix) return NW_UP_GATE_BACKOFF;
    unsigned recent = 0;
    for (unsigned i = 0; i < NW_UPLOAD_MAX_PER_HOUR; i++) {
        uint32_t t = s->attempts[i];
        if (t != 0 && (now < t || now - t < NW_UPLOAD_RATE_WINDOW_S)) recent++;  /* clock moved back: count it, stay safe */
    }
    return recent >= NW_UPLOAD_MAX_PER_HOUR ? NW_UP_GATE_RATE_LIMIT : NW_UP_GATE_OK;
}

static void record_attempt(nw_upload_state_t *s, uint32_t now)
{
    s->attempts[s->att_head] = now;
    s->att_head = (uint8_t)((s->att_head + 1) % NW_UPLOAD_MAX_PER_HOUR);
}

static uint32_t backoff_s(uint8_t fails, bool low_battery)
{
    uint32_t b = NW_UPLOAD_BACKOFF_BASE_S;
    for (uint8_t i = 1; i < fails && b < NW_UPLOAD_BACKOFF_MAX_S; i++) b *= 2;
    if (b > NW_UPLOAD_BACKOFF_MAX_S) b = NW_UPLOAD_BACKOFF_MAX_S;
    if (low_battery && b < NW_UPLOAD_LOWBAT_BACKOFF_S) b = NW_UPLOAD_LOWBAT_BACKOFF_S;
    return b;
}

/* Counts a failed attempt and sets the next allowed time. wait_s = a server hint (Retry-After) or 0. */
static void fail(nw_upload_state_t *s, uint32_t now, uint32_t wait_s, bool low_battery)
{
    if (s->fails < 255) s->fails++;
    uint32_t w = backoff_s(s->fails, low_battery);
    if (wait_s > NW_UPLOAD_RETRY_AFTER_MAX_S) wait_s = NW_UPLOAD_RETRY_AFTER_MAX_S;
    if (wait_s > w) w = wait_s;
    s->next_attempt_unix = now + w;
}

/* Finds "key":<digits> or "key":"<text>" in a body that is not NUL-terminated. Returns false when absent/malformed. */
static const char *find_value(const char *body, size_t len, const char *key, size_t *vlen)
{
    size_t kl = strlen(key);
    for (size_t i = 0; i + kl + 2 <= len; i++) {
        if (body[i] != '"' || memcmp(body + i + 1, key, kl) != 0 || body[i + 1 + kl] != '"') continue;
        size_t j = i + kl + 2;
        while (j < len && (body[j] == ' ' || body[j] == '\t' || body[j] == '\n' || body[j] == '\r')) j++;
        if (j >= len || body[j] != ':') continue;
        j++;
        while (j < len && (body[j] == ' ' || body[j] == '\t' || body[j] == '\n' || body[j] == '\r')) j++;
        if (j >= len) return NULL;
        size_t e = j;
        if (body[j] == '"') { j++; e = j; while (e < len && body[e] != '"') e++; if (e >= len) return NULL; }
        else while (e < len && body[e] >= '0' && body[e] <= '9') e++;
        *vlen = e - j;
        return body + j;
    }
    return NULL;
}

static bool parse_server_time(const char *body, size_t len, uint32_t *out)
{
    size_t vl;
    const char *v = body ? find_value(body, len, "server_time", &vl) : NULL;
    if (!v || vl == 0 || vl > 10) return false;
    uint64_t t = 0;
    for (size_t i = 0; i < vl; i++) { if (v[i] < '0' || v[i] > '9') return false; t = t * 10 + (uint64_t)(v[i] - '0'); }
    if (t < NW_TS_MIN || t > UINT32_MAX) return false;     /* a server clock before Nov 2023 is not a time */
    *out = (uint32_t)t;
    return true;
}

static bool error_is(const char *body, size_t len, const char *code)
{
    size_t vl;
    const char *v = body ? find_value(body, len, "error", &vl) : NULL;
    return v && vl == strlen(code) && memcmp(v, code, vl) == 0;
}

static nw_upload_result_t result(const nw_upload_state_t *s, nw_upload_outcome_t o)
{
    nw_upload_result_t r;
    memset(&r, 0, sizeof r);
    r.outcome = o;
    r.next_attempt_unix = s->next_attempt_unix;
    r.outage_pending = true;                 /* cleared only by an ack or a revoke */
    return r;
}

nw_upload_result_t nw_upload_on_transport_error(nw_upload_state_t *s, uint32_t now, bool low_battery)
{
    fail(s, now, 0, low_battery);
    return result(s, NW_UP_RETRY);
}

nw_upload_result_t nw_upload_on_response(nw_upload_state_t *s, nw_ring_t *rg, uint32_t last_seq, size_t n_samples,
                                         const nw_upload_http_resp_t *resp, uint32_t now, bool low_battery)
{
    nw_upload_result_t r;
    if (!resp) return nw_upload_on_transport_error(s, now, low_battery);
    int st = resp->status;
    if (st == 200) {
        uint32_t t;
        if (parse_server_time(resp->body, resp->body_len, &t)) {
            s->fails = 0; s->rejects = 0; s->reject_seq = 0; s->next_attempt_unix = 0;
            r = result(s, NW_UP_ACK);
            r.drained = nw_ring_consume_upto(rg, last_seq);    /* seq based: samples pushed meanwhile survive (review C1) */
            r.n_samples = n_samples;
            r.server_time = t; r.server_time_valid = true;
            r.outage_pending = false;
            return r;
        }
        fail(s, now, 0, low_battery);
        return result(s, NW_UP_RETRY);
    }
    if (st == 400 || st == 413) {
        if (s->rejects > 0 && s->reject_seq == last_seq) { if (s->rejects < 255) s->rejects++; }
        else { s->rejects = 1; s->reject_seq = last_seq; }
        fail(s, now, 0, low_battery);
        r = result(s, NW_UP_REJECTED);
        r.n_samples = n_samples;
        if (s->rejects >= NW_UPLOAD_POISON_MAX) {
            r.drained = nw_ring_consume_upto(rg, last_seq);
            r.batch_dropped = true;
            s->rejects = 0; s->reject_seq = 0;
        }
        return r;
    }
    if (st == 401) {
        if (error_is(resp->body, resp->body_len, "token_revoked")) {
            nw_upload_state_init(s);
            r = result(s, NW_UP_REVOKED);
            r.drained = nw_ring_consume_upto(rg, UINT32_MAX);   /* the data belongs to a released/deleted device */
            r.reenter_setup = true;
            r.outage_pending = false;
            return r;
        }
        fail(s, now, 0, low_battery);
        return result(s, NW_UP_AUTH_FAILED);
    }
    uint32_t hint = 0;
    if (st == 429 && resp->retry_after_s > 0) hint = (uint32_t)resp->retry_after_s;
    fail(s, now, hint, low_battery);
    return result(s, NW_UP_RETRY);
}

nw_upload_result_t nw_upload_attempt(nw_upload_state_t *s, const nw_upload_io_t *io, nw_ring_t *rg, const nw_report_meta_t *meta,
                                     const char *base_url, const char *device_token, uint32_t now, int32_t vbat_mv,
                                     bool low_battery, char *buf, size_t cap)
{
    char url[NW_UPLOAD_URL_MAX], auth[NW_UPLOAD_AUTH_MAX];
    nw_upload_result_t r = result(s, NW_UP_NOT_SENT);
    if (!io || !io->post || nw_upload_build_url(url, sizeof url, base_url) < 0 || nw_upload_build_auth(auth, sizeof auth, device_token) < 0) {
        r.why = NW_UP_WHY_BAD_CONFIG;
        memset(auth, 0, sizeof auth);
        return r;
    }
    nw_upload_gate_t g = nw_upload_gate(s, now, vbat_mv);
    if (g != NW_UP_GATE_OK) { r.why = NW_UP_WHY_GATE; r.gate = g; memset(auth, 0, sizeof auth); return r; }
    size_t n = 0; uint32_t last_seq = 0;
    size_t len = nw_report_build(buf, cap, rg, meta, &n, &last_seq);
    if (len == 0) { r.why = NW_UP_WHY_NO_PAYLOAD; memset(auth, 0, sizeof auth); return r; }
    record_attempt(s, now);                                  /* counted before the call: a crash or timeout still used the slot */
    nw_upload_http_resp_t resp;
    memset(&resp, 0, sizeof resp);
    int rc = io->post(io->ctx, url, auth, buf, len, &resp);
    memset(auth, 0, sizeof auth);
    if (rc < 0) { r = nw_upload_on_transport_error(s, now, low_battery); r.n_samples = n; return r; }
    r = nw_upload_on_response(s, rg, last_seq, n, &resp, now, low_battery);
    return r;
}

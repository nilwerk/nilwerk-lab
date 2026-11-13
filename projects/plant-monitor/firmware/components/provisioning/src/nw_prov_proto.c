/* Device side of the BLE provisioning wire contract (task 4.F2, FR-D03). See include/nw_prov_proto.h. */
#include "nw_prov_proto.h"

#include <stdio.h>
#include <string.h>

/* ---------- UTF-8 ---------- */
int nw_prov_utf8_chars(const char *s, size_t n)
{
    const uint8_t *p = (const uint8_t *)s;
    size_t i = 0;
    int chars = 0;
    while (i < n) {
        uint32_t cp;
        size_t extra;
        if (p[i] < 0x80) { cp = p[i]; extra = 0; }
        else if ((p[i] & 0xE0) == 0xC0) { cp = p[i] & 0x1F; extra = 1; }
        else if ((p[i] & 0xF0) == 0xE0) { cp = p[i] & 0x0F; extra = 2; }
        else if ((p[i] & 0xF8) == 0xF0) { cp = p[i] & 0x07; extra = 3; }
        else return -1;
        for (size_t k = 1; k <= extra; k++) {
            if (i + k >= n || (p[i + k] & 0xC0) != 0x80) return -1;
            cp = (cp << 6) | (p[i + k] & 0x3F);
        }
        if ((extra == 1 && cp < 0x80) || (extra == 2 && cp < 0x800) || (extra == 3 && cp < 0x10000)) return -1; /* overlong */
        if (cp > 0x10FFFF || (cp >= 0xD800 && cp <= 0xDFFF)) return -1;
        i += extra + 1;
        chars++;
    }
    return chars;
}

/* ---------- field rules ---------- */
bool nw_prov_valid_ssid(const char *ssid)
{
    if (!ssid) return false;
    size_t n = strlen(ssid);
    return n >= 1 && n <= NW_PROV_SSID_MAX_BYTES;
}

bool nw_prov_valid_passphrase(const char *pass)
{
    if (!pass) return false;
    size_t n = strlen(pass);
    return n == 0 || (n >= NW_PROV_PASS_MIN && n <= NW_PROV_PASS_MAX);
}

bool nw_prov_valid_claim_token(const char *tok)
{
    if (!tok || strlen(tok) != NW_PROV_CLAIM_TOKEN_LEN) return false;
    for (const char *c = tok; *c; c++) {
        bool ok = (*c >= 'A' && *c <= 'Z') || (*c >= 'a' && *c <= 'z') || (*c >= '0' && *c <= '9') || *c == '-' || *c == '_';
        if (!ok) return false;
    }
    return true;
}

int nw_prov_adv_name(const char *hw_id, char *out, size_t cap)
{
    if (!hw_id || !out || strlen(hw_id) != NW_PROV_HWID_LEN || strncmp(hw_id, "nw-", 3) != 0) return NW_PROV_ERR_ARG;
    for (int i = 3; i < NW_PROV_HWID_LEN; i++) {
        char c = hw_id[i];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return NW_PROV_ERR_ARG;
    }
    if (cap < NW_PROV_ADV_NAME_LEN + 1) return NW_PROV_ERR_TOO_SMALL;
    memcpy(out, "NW-", 3);
    memcpy(out + 3, hw_id + NW_PROV_HWID_LEN - 6, 6);
    out[NW_PROV_ADV_NAME_LEN] = '\0';
    return NW_PROV_ADV_NAME_LEN;
}

/* ---------- tiny strict JSON reader: one flat object of scalar values ---------- */
typedef struct { const char *p, *end; } cur_t;

static void skip_ws(cur_t *c) { while (c->p < c->end && (*c->p == ' ' || *c->p == '\t' || *c->p == '\r' || *c->p == '\n')) c->p++; }

static int hex4(cur_t *c, uint32_t *out)
{
    if (c->end - c->p < 4) return -1;
    uint32_t v = 0;
    for (int i = 0; i < 4; i++) {
        char h = *c->p++;
        v <<= 4;
        if (h >= '0' && h <= '9') v |= (uint32_t)(h - '0');
        else if (h >= 'a' && h <= 'f') v |= (uint32_t)(h - 'a' + 10);
        else if (h >= 'A' && h <= 'F') v |= (uint32_t)(h - 'A' + 10);
        else return -1;
    }
    *out = v;
    return 0;
}

static int put_cp(char *out, size_t cap, size_t *n, uint32_t cp)
{
    uint8_t b[4]; size_t k;
    if (cp < 0x80) { b[0] = (uint8_t)cp; k = 1; }
    else if (cp < 0x800) { b[0] = (uint8_t)(0xC0 | (cp >> 6)); b[1] = (uint8_t)(0x80 | (cp & 0x3F)); k = 2; }
    else if (cp < 0x10000) { b[0] = (uint8_t)(0xE0 | (cp >> 12)); b[1] = (uint8_t)(0x80 | ((cp >> 6) & 0x3F)); b[2] = (uint8_t)(0x80 | (cp & 0x3F)); k = 3; }
    else { b[0] = (uint8_t)(0xF0 | (cp >> 18)); b[1] = (uint8_t)(0x80 | ((cp >> 12) & 0x3F)); b[2] = (uint8_t)(0x80 | ((cp >> 6) & 0x3F)); b[3] = (uint8_t)(0x80 | (cp & 0x3F)); k = 4; }
    if (out) {
        if (*n + k >= cap) return -1;           /* keep room for the NUL */
        memcpy(out + *n, b, k);
    }
    *n += k;
    return 0;
}

/* Parses a JSON string at c->p (must point at the opening quote). out may be NULL (skip). Raw control characters (< 0x20) are rejected. */
static int parse_string(cur_t *c, char *out, size_t cap)
{
    size_t n = 0;
    if (c->p >= c->end || *c->p != '"') return -1;
    c->p++;
    while (c->p < c->end) {
        uint8_t ch = (uint8_t)*c->p++;
        if (ch == '"') { if (out) out[n] = '\0'; return 0; }
        if (ch < 0x20) return -1;
        if (ch == '\\') {
            if (c->p >= c->end) return -1;
            char e = *c->p++;
            uint32_t cp;
            switch (e) {
            case '"': cp = '"'; break; case '\\': cp = '\\'; break; case '/': cp = '/'; break;
            case 'b': cp = 8; break; case 'f': cp = 12; break; case 'n': cp = 10; break; case 'r': cp = 13; break; case 't': cp = 9; break;
            case 'u':
                if (hex4(c, &cp) != 0) return -1;
                if (cp >= 0xD800 && cp <= 0xDBFF) {   /* high surrogate: needs a low one */
                    uint32_t lo;
                    if (c->end - c->p < 2 || c->p[0] != '\\' || c->p[1] != 'u') return -1;
                    c->p += 2;
                    if (hex4(c, &lo) != 0 || lo < 0xDC00 || lo > 0xDFFF) return -1;
                    cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                } else if (cp >= 0xDC00 && cp <= 0xDFFF) return -1; /* lone low surrogate */
                break;
            default: return -1;
            }
            if (cp == 0) return -1;                  /* \u0000 would truncate the C string */
            if (put_cp(out, cap, &n, cp) != 0) return -1;
        } else {
            if (out) { if (n + 1 >= cap) return -1; out[n] = (char)ch; }
            n++;
        }
    }
    return -1; /* unterminated */
}

static int skip_scalar(cur_t *c)
{
    if (c->p >= c->end) return -1;
    if (*c->p == '"') return parse_string(c, NULL, 0);
    if (*c->p == '{' || *c->p == '[') return -1;      /* nested values are not accepted */
    const char *s = c->p;
    while (c->p < c->end && *c->p != ',' && *c->p != '}' && *c->p != ' ' && *c->p != '\t' && *c->p != '\r' && *c->p != '\n') c->p++;
    return c->p > s ? 0 : -1;
}

int nw_prov_parse_claim(const char *json, size_t len, nw_prov_claim_req_t *out)
{
    if (!json || !out) return NW_PROV_ERR_ARG;
    if (len == 0 || len > NW_PROV_REQ_MAX_BYTES) return NW_PROV_ERR_BAD_REQUEST;
    cur_t c = {json, json + len};
    char key[16];
    bool have_v = false, have_name = false, have_tok = false;
    char tmp_name[NW_PROV_NAME_MAX_BYTES + 1];
    char tmp_tok[NW_PROV_CLAIM_TOKEN_LEN + 1];

    skip_ws(&c);
    if (c.p >= c.end || *c.p++ != '{') return NW_PROV_ERR_BAD_REQUEST;
    skip_ws(&c);
    if (c.p < c.end && *c.p == '}') return NW_PROV_ERR_BAD_REQUEST;
    for (;;) {
        skip_ws(&c);
        /* keys longer than the buffer cannot be one of ours: skip them as unknown */
        cur_t save = c;
        bool known_key = parse_string(&c, key, sizeof key) == 0;
        if (!known_key) { c = save; if (parse_string(&c, NULL, 0) != 0) return NW_PROV_ERR_BAD_REQUEST; key[0] = '\0'; }
        skip_ws(&c);
        if (c.p >= c.end || *c.p++ != ':') return NW_PROV_ERR_BAD_REQUEST;
        skip_ws(&c);
        if (!strcmp(key, "v")) {
            if (have_v || c.end - c.p < 1 || *c.p != '1') return NW_PROV_ERR_BAD_REQUEST;
            c.p++;
            if (c.p < c.end && *c.p >= '0' && *c.p <= '9') return NW_PROV_ERR_BAD_REQUEST; /* 10, 11 ... */
            if (c.p < c.end && (*c.p == '.' || *c.p == 'e' || *c.p == 'E')) return NW_PROV_ERR_BAD_REQUEST;
            have_v = true;
        } else if (!strcmp(key, "name")) {
            if (have_name || parse_string(&c, tmp_name, sizeof tmp_name) != 0) return NW_PROV_ERR_BAD_REQUEST;
            have_name = true;
        } else if (!strcmp(key, "claim_token")) {
            if (have_tok || parse_string(&c, tmp_tok, sizeof tmp_tok) != 0) return NW_PROV_ERR_BAD_REQUEST;
            have_tok = true;
        } else if (skip_scalar(&c) != 0) {
            return NW_PROV_ERR_BAD_REQUEST;
        }
        skip_ws(&c);
        if (c.p >= c.end) return NW_PROV_ERR_BAD_REQUEST;
        if (*c.p == ',') { c.p++; continue; }
        if (*c.p == '}') { c.p++; break; }
        return NW_PROV_ERR_BAD_REQUEST;
    }
    skip_ws(&c);
    if (c.p != c.end) return NW_PROV_ERR_BAD_REQUEST;       /* trailing garbage */
    if (!have_v || !have_name || !have_tok) return NW_PROV_ERR_BAD_REQUEST;

    int chars = nw_prov_utf8_chars(tmp_name, strlen(tmp_name));
    if (chars < NW_PROV_NAME_MIN_CHARS || chars > NW_PROV_NAME_MAX_CHARS) return NW_PROV_ERR_BAD_REQUEST;
    for (const char *q = tmp_name; *q; q++)
        if ((uint8_t)*q < 0x20 || (uint8_t)*q == 0x7F) return NW_PROV_ERR_BAD_REQUEST;
    if (!nw_prov_valid_claim_token(tmp_tok)) return NW_PROV_ERR_BAD_REQUEST;

    memcpy(out->name, tmp_name, strlen(tmp_name) + 1);
    memcpy(out->claim_token, tmp_tok, sizeof out->claim_token);
    return NW_PROV_OK;
}

/* ---------- replies ---------- */
static int emit(size_t cap, int n)
{
    if (n < 0 || (size_t)n >= cap) return NW_PROV_ERR_TOO_SMALL;
    return n;
}

int nw_prov_build_claim_reply(char *buf, size_t cap, bool ok)
{
    if (!buf) return NW_PROV_ERR_ARG;
    return emit(cap, ok ? snprintf(buf, cap, "{\"v\":%d,\"ok\":true}", NW_PROV_PROTO_VERSION)
                             : snprintf(buf, cap, "{\"v\":%d,\"ok\":false,\"error\":\"bad_request\"}", NW_PROV_PROTO_VERSION));
}

const char *nw_prov_state_str(nw_prov_status_state_t st)
{
    switch (st) {
    case NW_PROV_ST_IDLE: return "idle";
    case NW_PROV_ST_WIFI_CONNECTING: return "wifi_connecting";
    case NW_PROV_ST_WIFI_FAILED: return "wifi_failed";
    case NW_PROV_ST_CLAIMING: return "claiming";
    case NW_PROV_ST_CLAIMED: return "claimed";
    case NW_PROV_ST_CLAIM_FAILED: return "claim_failed";
    }
    return "idle";
}

const char *nw_prov_reason_str(nw_prov_reason_t r)
{
    switch (r) {
    case NW_PROV_REASON_NONE: return NULL;
    case NW_PROV_REASON_AUTH: return "auth";
    case NW_PROV_REASON_NO_AP: return "no_ap";
    case NW_PROV_REASON_TIMEOUT: return "timeout";
    case NW_PROV_REASON_CLAIM_TOKEN_INVALID: return "claim_token_invalid";
    case NW_PROV_REASON_DEVICE_OWNED: return "device_owned";
    case NW_PROV_REASON_NETWORK: return "network";
    case NW_PROV_REASON_SERVER: return "server";
    }
    return NULL;
}

int nw_prov_build_status(char *buf, size_t cap, nw_prov_status_state_t st, nw_prov_reason_t reason)
{
    if (!buf) return NW_PROV_ERR_ARG;
    const char *r = nw_prov_reason_str(reason);
    if (r) return emit(cap, snprintf(buf, cap, "{\"v\":%d,\"state\":\"%s\",\"reason\":\"%s\"}", NW_PROV_PROTO_VERSION, nw_prov_state_str(st), r));
    return emit(cap, snprintf(buf, cap, "{\"v\":%d,\"state\":\"%s\",\"reason\":null}", NW_PROV_PROTO_VERSION, nw_prov_state_str(st)));
}

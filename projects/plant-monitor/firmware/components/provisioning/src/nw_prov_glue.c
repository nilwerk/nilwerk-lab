/* Glue core (task 4.F2 slice 2). See include/nw_prov_glue.h. FR-D03, FR-D09, NFR-06. */
#include "nw_prov_glue.h"

#include <stdio.h>
#include <string.h>

static void g_ble(void *c, bool on) { nw_glue_t *g = c; if (g->io.ble_set) g->io.ble_set(g->io.ctx, on); }

static void g_wifi(void *c, const char *ssid, const char *pass)
{
    nw_glue_t *g = c;
    g->wifi_armed = true;
    g->wifi_deadline_ms = g->now_ms + NW_GLUE_WIFI_JOIN_TIMEOUT_MS;
    if (g->io.wifi_start) g->io.wifi_start(g->io.ctx, ssid, pass);
}

static void g_claim(void *c, const char *tok, const char *name)
{
    nw_glue_t *g = c;
    int n = nw_glue_build_claim_body(g->body, sizeof g->body, g->hw_id, tok, name, g->fw);
    if (n < 0) {                                  /* cannot build a valid request: end the attempt as a server-side failure, never hang */
        g->claim_deadline_ms = g->now_ms;         /* unreachable with validated inputs; the next tick ends the attempt at once */
        g->claim_armed = true;
        return;
    }
    g->claim_armed = true;
    g->claim_deadline_ms = g->now_ms + NW_GLUE_HTTP_TIMEOUT_MS;
    if (g->io.http_post) g->io.http_post(g->io.ctx, g->body, (size_t)n);
}

int nw_glue_init(nw_glue_t *g, const nw_glue_io_t *io, const char *hw_id, const char *fw, nw_prov_ops_t *ops_out)
{
    if (!g || !io || !hw_id || !fw || !ops_out) return NW_PROV_ERR_ARG;
    size_t fl = strlen(fw);
    if (strlen(hw_id) != NW_PROV_HWID_LEN || strncmp(hw_id, "nw-", 3) != 0 || fl < 1 || fl > NW_GLUE_FW_MAX) return NW_PROV_ERR_ARG;
    for (int i = 3; i < NW_PROV_HWID_LEN; i++) {
        char c = hw_id[i];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return NW_PROV_ERR_ARG;
    }
    memset(g, 0, sizeof *g);
    g->io = *io;
    strcpy(g->hw_id, hw_id);
    strcpy(g->fw, fw);
    memset(ops_out, 0, sizeof *ops_out);
    ops_out->ctx = g;
    ops_out->ble_set = g_ble;
    ops_out->wifi_connect = g_wifi;
    ops_out->claim_post = g_claim;
    ops_out->store = io->store;
    ops_out->store_ctx = io->store_ctx;
    return NW_PROV_OK;
}

void nw_glue_attach(nw_glue_t *g, nw_prov_t *prov) { g->prov = prov; }

/* ---- /device-claim request ---- */
static int put(char *buf, size_t cap, size_t *pos, const char *s)
{
    size_t n = strlen(s);
    if (*pos + n + 1 > cap) return NW_PROV_ERR_TOO_SMALL;
    memcpy(buf + *pos, s, n);
    *pos += n;
    buf[*pos] = 0;
    return 0;
}

static int put_json_str(char *buf, size_t cap, size_t *pos, const char *s)
{
    char one[8];
    if (put(buf, cap, pos, "\"") < 0) return NW_PROV_ERR_TOO_SMALL;
    for (; *s; s++) {
        unsigned char c = (unsigned char)*s;
        if (c == '"') strcpy(one, "\\\"");
        else if (c == '\\') strcpy(one, "\\\\");
        else if (c < 0x20) snprintf(one, sizeof one, "\\u%04x", c);
        else { one[0] = (char)c; one[1] = 0; }
        if (put(buf, cap, pos, one) < 0) return NW_PROV_ERR_TOO_SMALL;
    }
    return put(buf, cap, pos, "\"");
}

int nw_glue_build_claim_body(char *buf, size_t cap, const char *hw_id, const char *claim_token, const char *name, const char *fw)
{
    if (!buf || !cap || !hw_id || !claim_token || !name || !fw) return NW_PROV_ERR_ARG;
    size_t pos = 0;
    buf[0] = 0;
    if (put(buf, cap, &pos, "{\"hw_id\":") < 0 || put_json_str(buf, cap, &pos, hw_id) < 0 ||
        put(buf, cap, &pos, ",\"claim_token\":") < 0 || put_json_str(buf, cap, &pos, claim_token) < 0 ||
        put(buf, cap, &pos, ",\"name\":") < 0 || put_json_str(buf, cap, &pos, name) < 0 ||
        put(buf, cap, &pos, ",\"fw\":") < 0 || put_json_str(buf, cap, &pos, fw) < 0 || put(buf, cap, &pos, "}") < 0) {
        buf[0] = 0;
        return NW_PROV_ERR_TOO_SMALL;
    }
    return (int)pos;
}

/* ---- results ---- */
nw_prov_claim_result_t nw_glue_map_http_status(int status)
{
    switch (status) {
    case 200: return NW_PROV_CLAIM_OK;
    case 401: return NW_PROV_CLAIM_TOKEN_INVALID;
    case 409: return NW_PROV_CLAIM_DEVICE_OWNED;
    default:  return NW_PROV_CLAIM_SERVER;        /* 400, 413, 429, 500 and every other status: "server" (WO glue item 3) */
    }
}

bool nw_glue_parse_device_token(const char *body, size_t len, char out[65])
{
    static const char key[] = "\"device_token\"";
    if (!body) return false;
    for (size_t i = 0; i + sizeof key - 1 <= len; i++) {
        if (memcmp(body + i, key, sizeof key - 1) != 0) continue;
        size_t j = i + sizeof key - 1;
        while (j < len && (body[j] == ' ' || body[j] == '\t' || body[j] == '\n' || body[j] == '\r')) j++;
        if (j >= len || body[j] != ':') return false;
        j++;
        while (j < len && (body[j] == ' ' || body[j] == '\t' || body[j] == '\n' || body[j] == '\r')) j++;
        if (j >= len || body[j] != '"') return false;
        j++;
        if (j + 65 > len || body[j + 64] != '"') return false;
        for (int k = 0; k < 64; k++) {
            char c = body[j + (size_t)k];
            if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
        }
        memcpy(out, body + j, 64);
        out[64] = 0;
        return true;
    }
    return false;
}

int nw_glue_on_apply(nw_glue_t *g, uint32_t now_ms)
{
    g->now_ms = now_ms;
    return nw_prov_on_apply(g->prov, now_ms);
}

int nw_glue_on_wifi_result(nw_glue_t *g, nw_prov_wifi_result_t r, uint32_t now_ms)
{
    g->now_ms = now_ms;
    g->wifi_armed = false;
    return nw_prov_on_wifi_result(g->prov, r, now_ms);   /* on OK this runs g_claim, which arms the HTTP timer */
}

int nw_glue_on_http_response(nw_glue_t *g, int status, const char *body, size_t len, uint32_t now_ms)
{
    char tok[65] = {0};
    g->now_ms = now_ms;
    g->claim_armed = false;
    nw_prov_claim_result_t r = nw_glue_map_http_status(status);
    if (r == NW_PROV_CLAIM_OK && !nw_glue_parse_device_token(body, len, tok)) r = NW_PROV_CLAIM_SERVER;  /* 200 without a usable token */
    int rc = nw_prov_on_claim_result(g->prov, r, tok, now_ms);
    memset(tok, 0, sizeof tok);
    return rc;
}

int nw_glue_on_transport_error(nw_glue_t *g, uint32_t now_ms)
{
    g->now_ms = now_ms;
    g->claim_armed = false;
    return nw_prov_on_claim_result(g->prov, NW_PROV_CLAIM_NETWORK, NULL, now_ms);
}

void nw_glue_tick(nw_glue_t *g, uint32_t now_ms)
{
    g->now_ms = now_ms;
    nw_prov_t *p = g->prov;
    if (g->wifi_armed && p->state != NW_PROV_S_WIFI_CONNECTING) g->wifi_armed = false;   /* result arrived another way (button restart) */
    if (g->claim_armed && p->state != NW_PROV_S_CLAIMING) g->claim_armed = false;
    if (g->wifi_armed && (uint32_t)(now_ms - g->wifi_deadline_ms) < 0x80000000u) {      /* wrap-safe "now >= deadline" */
        g->wifi_armed = false;
        nw_prov_on_wifi_result(p, NW_PROV_WIFI_TIMEOUT, now_ms);
    }
    if (g->claim_armed && (uint32_t)(now_ms - g->claim_deadline_ms) < 0x80000000u) {
        g->claim_armed = false;
        nw_prov_on_claim_result(p, NW_PROV_CLAIM_NETWORK, NULL, now_ms);
    }
    nw_prov_tick(p, now_ms);
}

nw_glue_next_t nw_glue_next_after_setup(const nw_prov_t *p, bool record_present)
{
    if (nw_prov_in_setup(p)) return NW_GLUE_NEXT_STAY;
    if (p->state == NW_PROV_S_CLAIMED || p->state == NW_PROV_S_NORMAL) return NW_GLUE_NEXT_NORMAL;
    /* CLOSED */
    return record_present ? NW_GLUE_NEXT_NORMAL : NW_GLUE_NEXT_SLEEP_UNTIL_RESET;
}

/* PR #172 (Theo): a failed boot decision never falls through to normal mode; the unit sleeps until reset. */
nw_glue_next_t nw_glue_next_after_boot(const nw_prov_t *p, int boot_rc, bool record_present)
{
    if (boot_rc != NW_PROV_OK) return NW_GLUE_NEXT_SLEEP_UNTIL_RESET;
    return nw_glue_next_after_setup(p, record_present);
}

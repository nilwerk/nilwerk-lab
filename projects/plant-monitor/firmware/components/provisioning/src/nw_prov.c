/* Provisioning state machine (task 4.F2, FR-D03/D07/D09, NFR-03/06). See include/nw_prov.h. */
#include "nw_prov.h"

#include <string.h>

static void wipe(void *p, size_t n) { volatile uint8_t *v = p; while (n--) *v++ = 0; }

static bool in_flight(const nw_prov_t *p) { return p->state == NW_PROV_S_WIFI_CONNECTING || p->state == NW_PROV_S_CLAIMING; }

bool nw_prov_in_setup(const nw_prov_t *p)
{
    return p->state == NW_PROV_S_ADVERTISING || p->state == NW_PROV_S_SESSION || in_flight(p);
}

static void ble(nw_prov_t *p, bool on) { if (p->ops.ble_set) p->ops.ble_set(p->ops.ctx, on); }

static void clear_secrets(nw_prov_t *p)
{
    wipe(&p->pending, sizeof p->pending);
    wipe(p->claim_token, sizeof p->claim_token);
    p->have_wifi = p->have_claim = false;
}

static void end_setup(nw_prov_t *p, nw_prov_state_t to)
{
    clear_secrets(p);
    p->state = to;
    ble(p, false);                                           /* FR-D09 */
}

static void start_setup(nw_prov_t *p, uint32_t now_ms)
{
    clear_secrets(p);
    p->failed_handshakes = 0;
    p->st = NW_PROV_ST_IDLE;
    p->reason = NW_PROV_REASON_NONE;
    p->setup_started_ms = now_ms;
    p->state = NW_PROV_S_ADVERTISING;
    ble(p, true);
}

void nw_prov_init(nw_prov_t *p, const nw_prov_ops_t *ops)
{
    memset(p, 0, sizeof *p);
    p->ops = *ops;
    p->state = NW_PROV_S_NORMAL;
}

int nw_prov_boot(nw_prov_t *p, uint32_t button_held_ms, uint32_t now_ms)
{
    if (!p || !p->ops.store.load || !p->ops.store.erase) return NW_PROV_ERR_ARG;
    if (button_held_ms >= NW_PROV_BUTTON_RESET_MS) {
        if (p->ops.store.erase(p->ops.store_ctx) != 0) return NW_PROV_ERR_STORE;   /* do not enter setup with an old record we failed to wipe */
        start_setup(p, now_ms);
        return NW_PROV_OK;
    }
    nw_prov_record_t *rec = &p->pending;                    /* scratch: only used to test presence, wiped below */
    int r = p->ops.store.load(p->ops.store_ctx, rec);
    wipe(rec, sizeof *rec);
    if (r < 0) return NW_PROV_ERR_STORE;
    if (r == 1 || button_held_ms >= NW_PROV_BUTTON_SETUP_MS) { start_setup(p, now_ms); return NW_PROV_OK; }
    p->state = NW_PROV_S_NORMAL;
    ble(p, false);
    return NW_PROV_OK;
}

void nw_prov_button(nw_prov_t *p, uint32_t held_ms, uint32_t now_ms)
{
    if (in_flight(p) || held_ms < NW_PROV_BUTTON_SETUP_MS) return;
    if (held_ms >= NW_PROV_BUTTON_RESET_MS) {
        if (p->ops.store.erase(p->ops.store_ctx) != 0) return;
    }
    start_setup(p, now_ms);                                  /* restarts the 300 s window and the guess counter ("button restarts it") */
}

int nw_prov_on_handshake(nw_prov_t *p, bool ok, uint32_t now_ms)
{
    nw_prov_tick(p, now_ms);
    if (p->state != NW_PROV_S_ADVERTISING && p->state != NW_PROV_S_SESSION) return NW_PROV_ERR_STATE;
    if (ok) { p->state = NW_PROV_S_SESSION; return NW_PROV_OK; }
    if (++p->failed_handshakes >= NW_PROV_MAX_FAILED_HANDSHAKES) end_setup(p, NW_PROV_S_CLOSED);
    else p->state = NW_PROV_S_ADVERTISING;                   /* a failed handshake drops the session */
    return NW_PROV_OK;
}

int nw_prov_on_wifi_config(nw_prov_t *p, const char *ssid, const char *passphrase, uint32_t now_ms)
{
    nw_prov_tick(p, now_ms);
    if (p->state != NW_PROV_S_SESSION) return NW_PROV_ERR_STATE;
    if (!nw_prov_valid_ssid(ssid) || !nw_prov_valid_passphrase(passphrase)) return NW_PROV_ERR_BAD_REQUEST;
    strcpy(p->pending.ssid, ssid);
    strcpy(p->pending.passphrase, passphrase);
    p->have_wifi = true;
    p->st = NW_PROV_ST_IDLE;
    p->reason = NW_PROV_REASON_NONE;
    return NW_PROV_OK;
}

int nw_prov_on_claim(nw_prov_t *p, const char *json, size_t len, char *reply, size_t reply_cap, uint32_t now_ms)
{
    nw_prov_tick(p, now_ms);
    if (p->state != NW_PROV_S_SESSION) {
        nw_prov_build_claim_reply(reply, reply_cap, false);
        return NW_PROV_ERR_STATE;
    }
    nw_prov_claim_req_t req;
    int r = nw_prov_parse_claim(json, len, &req);
    if (r == NW_PROV_OK) {
        strcpy(p->pending.name, req.name);
        strcpy(p->claim_token, req.claim_token);
        p->have_claim = true;
        p->st = NW_PROV_ST_IDLE;
        p->reason = NW_PROV_REASON_NONE;
    }
    wipe(&req, sizeof req);
    int w = nw_prov_build_claim_reply(reply, reply_cap, r == NW_PROV_OK);
    return w < 0 ? w : r;
}

int nw_prov_on_apply(nw_prov_t *p, uint32_t now_ms)
{
    nw_prov_tick(p, now_ms);
    if (p->state != NW_PROV_S_SESSION || !p->have_wifi || !p->have_claim) return NW_PROV_ERR_STATE;
    p->state = NW_PROV_S_WIFI_CONNECTING;
    p->st = NW_PROV_ST_WIFI_CONNECTING;
    p->reason = NW_PROV_REASON_NONE;
    if (p->ops.wifi_connect) p->ops.wifi_connect(p->ops.ctx, p->pending.ssid, p->pending.passphrase);
    return NW_PROV_OK;
}

int nw_prov_on_wifi_result(nw_prov_t *p, nw_prov_wifi_result_t r, uint32_t now_ms)
{
    if (p->state != NW_PROV_S_WIFI_CONNECTING) return NW_PROV_ERR_STATE;
    if (r == NW_PROV_WIFI_OK) {
        p->state = NW_PROV_S_CLAIMING;
        p->st = NW_PROV_ST_CLAIMING;
        p->reason = NW_PROV_REASON_NONE;
        if (p->ops.claim_post) p->ops.claim_post(p->ops.ctx, p->claim_token, p->pending.name);
        return NW_PROV_OK;
    }
    /* wifi_failed leaves setup mode open for a retry until the 300 s limit (section 2). The claim token and name are kept. */
    p->state = NW_PROV_S_SESSION;
    p->have_wifi = false;
    wipe(p->pending.ssid, sizeof p->pending.ssid);
    wipe(p->pending.passphrase, sizeof p->pending.passphrase);
    p->st = NW_PROV_ST_WIFI_FAILED;
    p->reason = r == NW_PROV_WIFI_AUTH ? NW_PROV_REASON_AUTH : r == NW_PROV_WIFI_NO_AP ? NW_PROV_REASON_NO_AP : NW_PROV_REASON_TIMEOUT;
    nw_prov_tick(p, now_ms);
    return NW_PROV_OK;
}

int nw_prov_on_claim_result(nw_prov_t *p, nw_prov_claim_result_t r, const char *device_token, uint32_t now_ms)
{
    if (p->state != NW_PROV_S_CLAIMING) return NW_PROV_ERR_STATE;
    if (r == NW_PROV_CLAIM_OK) {
        if (!device_token || strlen(device_token) >= sizeof p->pending.device_token) r = NW_PROV_CLAIM_SERVER;  /* unusable reply */
    }
    if (r == NW_PROV_CLAIM_OK) {
        strcpy(p->pending.device_token, device_token);
        if (!p->ops.store.save || p->ops.store.save(p->ops.store_ctx, &p->pending) != 0) {
            r = NW_PROV_CLAIM_SERVER;                          /* nothing stored: the sensor is not usable, so do not report claimed */
            wipe(p->pending.device_token, sizeof p->pending.device_token);
        } else {
            p->st = NW_PROV_ST_CLAIMED;
            p->reason = NW_PROV_REASON_NONE;
            end_setup(p, NW_PROV_S_CLAIMED);                   /* wipes RAM copies of Wi-Fi password and claim token, BLE off */
            return NW_PROV_OK;
        }
    }
    p->state = NW_PROV_S_SESSION;                              /* claim_failed: stay open for a retry (new token via nw-claim, then apply) */
    p->have_claim = false;
    wipe(p->claim_token, sizeof p->claim_token);
    p->st = NW_PROV_ST_CLAIM_FAILED;
    p->reason = r == NW_PROV_CLAIM_TOKEN_INVALID ? NW_PROV_REASON_CLAIM_TOKEN_INVALID
              : r == NW_PROV_CLAIM_DEVICE_OWNED ? NW_PROV_REASON_DEVICE_OWNED
              : r == NW_PROV_CLAIM_NETWORK ? NW_PROV_REASON_NETWORK : NW_PROV_REASON_SERVER;
    nw_prov_tick(p, now_ms);
    return NW_PROV_OK;
}

void nw_prov_tick(nw_prov_t *p, uint32_t now_ms)
{
    /* The 300 s window is not enforced while a Wi-Fi join or claim call is in flight (they have their own timeouts);
     * it is checked again as soon as that attempt fails. */
    if ((p->state == NW_PROV_S_ADVERTISING || p->state == NW_PROV_S_SESSION) &&
        (uint32_t)(now_ms - p->setup_started_ms) >= NW_PROV_SETUP_TIMEOUT_MS)
        end_setup(p, NW_PROV_S_CLOSED);
}

int nw_prov_status_json(const nw_prov_t *p, char *buf, size_t cap)
{
    return nw_prov_build_status(buf, cap, p->st, p->reason);
}

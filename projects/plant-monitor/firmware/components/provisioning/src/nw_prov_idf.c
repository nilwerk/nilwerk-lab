/* ESP-IDF glue for the setup flow (task 4.F2 slice 2). See include/nw_prov_idf.h.
 *
 * STATUS: compiled by the CI ESP-IDF build jobs (esp32c3, setup flow on); not run on hardware. The protocomm and wifi_prov
 * references are in docs/adr/ADR-011 (verification note). Remaining [verify] tags are open items for the bench run.
 * All state machine work goes through nw_glue_* (host-tested). This file only moves events in and out, under one mutex
 * (BLE endpoint handlers, the Wi-Fi/prov event loop and the http task are different FreeRTOS tasks; nw_prov has no locking). */
#include "nw_prov_idf.h"

#include <string.h>

#include "esp_event.h"
#include "esp_http_client.h"
#include "nw_ingest_ca.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "nw_prov_glue.h"
#include "nw_prov_store_nvs.h"
#include "nw_sec2.h"
#include "protocomm_security.h"   /* PROTOCOMM_SECURITY_SESSION_EVENT and its ids (SETUP_OK, CREDENTIALS_MISMATCH, INVALID_SECURITY_PARAMS in v5.4) */
#include "sdkconfig.h"
#include "wifi_provisioning/manager.h"
#include "wifi_provisioning/scheme_ble.h"

static const char *TAG = "nw_setup";

static nw_glue_t s_glue;
static nw_prov_t s_prov;
static SemaphoreHandle_t s_lock;
static esp_netif_t *s_sta;
static bool s_mgr_up;

static uint32_t now_ms(void) { return (uint32_t)(esp_timer_get_time() / 1000); }
#define LOCK() xSemaphoreTake(s_lock, portMAX_DELAY)
#define UNLOCK() xSemaphoreGive(s_lock)

/* ---- hw_id: "nw-" + 12 hex of the factory base MAC (ble-provisioning.md section 1; openapi pattern) ---- */
static void make_hw_id(char out[NW_PROV_HWID_LEN + 1])
{
    uint8_t m[6] = {0};
    esp_read_mac(m, ESP_MAC_WIFI_STA);   /* [verify] base MAC choice: must be the same value forever, also on the label */
    snprintf(out, NW_PROV_HWID_LEN + 1, "nw-%02x%02x%02x%02x%02x%02x", m[0], m[1], m[2], m[3], m[4], m[5]);
}

/* ---- io: Wi-Fi join (the manager connects when prov-config is applied; we only have to wait for its result event) ---- */
static void io_ble_set(void *ctx, bool on)
{
    (void)ctx;
    /* Advertising is owned by wifi_prov_mgr (start/stop provisioning). Setup end stops the manager from nw_setup_run(), outside the lock.
     * This is the state machine's request only: "advertising" is logged by start_ble() once the manager really starts (sim: never). */
    ESP_LOGI(TAG, "NWSETUP ble %s", on ? "requested" : "off");
}
static void io_wifi_start(void *ctx, const char *ssid, const char *pass)
{
    (void)ctx; (void)ssid; (void)pass;   /* wifi_prov_mgr stores the config and joins on apply when the SRP session is DONE (manager.c:1255-1291, v5.4 reviewer check) */
    ESP_LOGI(TAG, "NWSETUP wifi joining");
}

/* ---- io: POST /device-claim in a one-shot task (esp_http_client_perform blocks). TLS: pinned CA (NFR-06, ADR-004, F-01), not the bundle. ---- */
typedef struct { char *body; size_t len; } post_job_t;

static void post_task(void *arg)
{
    post_job_t *job = arg;
    char resp[512];
    int got = 0;
    esp_http_client_config_t cfg = {
        .url = CONFIG_PLANT_API_BASE_URL "/device-claim",
        .method = HTTP_METHOD_POST,
        .timeout_ms = NW_GLUE_HTTP_TIMEOUT_MS,
        .cert_pem = NW_INGEST_CA_PEM,                 /* the only trust anchor for the claim POST (same root as the upload) */
        .transport_type = HTTP_TRANSPORT_OVER_SSL,
    };
    int status = -1;
    int terr = (int)ESP_FAIL;              /* transport error code, logged only when no HTTP status was read (init failure keeps ESP_FAIL) */
    /* Fail closed: an empty pin sends nothing (no fallback to the bundle). */
    esp_http_client_handle_t c = NULL;
    if (NW_INGEST_CA_PEM[0] == '\0') ESP_LOGE(TAG, "NWSETUP no pinned CA: claim not sent (NFR-06)");
    else c = esp_http_client_init(&cfg);
    if (c) {
        esp_http_client_set_header(c, "Content-Type", "application/json");
        esp_err_t oe = esp_http_client_open(c, (int)job->len);
        if (oe != ESP_OK) {
            terr = (int)oe;
        } else {
            int wr = esp_http_client_write(c, job->body, (int)job->len);
            if (wr != (int)job->len) {
                terr = wr < 0 ? wr : (int)ESP_FAIL;          /* negative: error; positive: short write */
            } else {
                int fh = esp_http_client_fetch_headers(c);   /* [verify] return value semantics for chunked replies */
                if (fh < 0) {
                    terr = fh;
                } else {
                    status = esp_http_client_get_status_code(c);
                    got = esp_http_client_read_response(c, resp, sizeof resp - 1);
                    if (got < 0) got = 0;
                }
            }
        }
        esp_http_client_cleanup(c);
    }
    resp[got] = 0;
    /* Logs only the HTTP status or the transport code: never the body, the token, the Wi-Fi password or the SSID. */
    if (status >= 0) ESP_LOGI(TAG, "NWSETUP claim post: status=%d", status);
    else ESP_LOGW(TAG, "NWSETUP claim post: transport error=%d", terr);
    LOCK();
    if (status < 0) nw_glue_on_transport_error(&s_glue, now_ms());
    else nw_glue_on_http_response(&s_glue, status, resp, (size_t)got, now_ms());
    UNLOCK();
    memset(job->body, 0, job->len);
    memset(resp, 0, sizeof resp);
    vPortFree(job->body);
    vPortFree(job);
    vTaskDelete(NULL);
}

static void io_http_post(void *ctx, const char *body, size_t len)
{
    (void)ctx;
    /* Called with the lock held (inside nw_glue_on_wifi_result). Copy the body: the glue buffer may be reused. */
    post_job_t *job = pvPortMalloc(sizeof *job);
    char *copy = pvPortMalloc(len + 1);
    if (!job || !copy) { if (job) vPortFree(job); if (copy) vPortFree(copy); ESP_LOGE(TAG, "no memory for claim"); return; }  /* glue deadline ends it */
    memcpy(copy, body, len); copy[len] = 0;
    job->body = copy; job->len = len;
    if (xTaskCreate(post_task, "nw_claim", 6144, job, 5, NULL) != pdPASS) { vPortFree(copy); vPortFree(job); }
}

/* ---- protocomm custom endpoints (UTF-8 JSON, ble-provisioning.md section 2) ---- */
static esp_err_t reply(uint8_t **out, ssize_t *outlen, const char *s)
{
    size_t n = strlen(s);
    *out = malloc(n + 1);                 /* protocomm frees it */
    if (!*out) return ESP_ERR_NO_MEM;
    memcpy(*out, s, n + 1);
    *outlen = (ssize_t)n;
    return ESP_OK;
}

static const char *state_name(nw_prov_state_t s)
{
    switch (s) {
    case NW_PROV_S_NORMAL: return "NORMAL";
    case NW_PROV_S_ADVERTISING: return "ADVERTISING";
    case NW_PROV_S_SESSION: return "SESSION";
    case NW_PROV_S_WIFI_CONNECTING: return "WIFI_CONNECTING";
    case NW_PROV_S_CLAIMING: return "CLAIMING";
    case NW_PROV_S_CLAIMED: return "CLAIMED";
    case NW_PROV_S_CLOSED: return "CLOSED";
    }
    return "?";
}

/* ---- protocomm security-2 session result -> state machine (FR-D03: 5 failed handshakes end setup mode) ----
 * protocomm posts these on the default event loop (security2.c:273-274 in ESP-IDF v5.4): SETUP_OK when the SRP handshake
 * succeeds (the session becomes DONE, which is the only state in which endpoints are decrypted: protocomm.c:199-214,
 * security2.c:467); CREDENTIALS_MISMATCH when the PoP is wrong. Registered in nw_setup_run(), removed after the loop. */
static void on_session_event(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg; (void)data;
    if (base != PROTOCOMM_SECURITY_SESSION_EVENT) return;
    LOCK();
    if (id == PROTOCOMM_SECURITY_SESSION_SETUP_OK) {
        nw_prov_state_t before = s_prov.state;
        nw_prov_on_handshake(&s_prov, true, now_ms());
        ESP_LOGI(TAG, "NWSETUP session: setup ok (%s -> %s)", state_name(before), state_name(s_prov.state));
    } else if (id == PROTOCOMM_SECURITY_SESSION_CREDENTIALS_MISMATCH) {
        nw_prov_on_handshake(&s_prov, false, now_ms());
        ESP_LOGW(TAG, "NWSETUP session: wrong proof of possession (failed handshakes %u)", (unsigned)s_prov.failed_handshakes);
    } else if (id == PROTOCOMM_SECURITY_SESSION_INVALID_SECURITY_PARAMS) {
        /* Logging only (protocomm posts it for an empty username or a bad client public key). No state change. */
        ESP_LOGW(TAG, "NWSETUP session: invalid security params (no state change, state=%s)", state_name(s_prov.state));
    }
    UNLOCK();
}

/* Why setup ended, for the end line only (task 4.F2 logging). "closed" = 5 failed handshakes (guessing limit);
 * "window" = CLOSED without the guessing limit, i.e. the setup window ran out (also the no-verifier path). */
static const char *end_reason(nw_prov_state_t st, unsigned failed, int boot_rc)
{
    if (boot_rc != NW_PROV_OK) return "boot failed";
    if (st == NW_PROV_S_CLAIMED) return "claimed";
    if (st == NW_PROV_S_CLOSED) return failed >= NW_PROV_MAX_FAILED_HANDSHAKES ? "closed" : "window";
    return "not in setup";
}

static esp_err_t ep_claim(uint32_t session_id, const uint8_t *in, ssize_t inlen, uint8_t **out, ssize_t *outlen, void *priv)
{
    (void)session_id; (void)priv;
    char rep[64];
    ESP_LOGI(TAG, "NWSETUP claim in: len=%d", (int)inlen);
    if (inlen < 0 || inlen > NW_PROV_REQ_MAX_BYTES) {
        LOCK(); nw_prov_state_t st = s_prov.state; UNLOCK();
        ESP_LOGW(TAG, "NWSETUP claim rejected: state=%s reason=LEN", state_name(st));
        nw_prov_build_claim_reply(rep, sizeof rep, false); return reply(out, outlen, rep);
    }
    LOCK();
    int rc = nw_prov_on_claim(&s_prov, (const char *)in, (size_t)inlen, rep, sizeof rep, now_ms());
    nw_prov_state_t st = s_prov.state;
    UNLOCK();
    if (rc == NW_PROV_OK) ESP_LOGI(TAG, "NWSETUP claim accepted");
    else ESP_LOGW(TAG, "NWSETUP claim rejected: state=%s reason=%s", state_name(st), rc == NW_PROV_ERR_STATE ? "ERR_STATE" : "PARSE");
    return reply(out, outlen, rep);       /* rep is always a valid body, ok or bad_request */
}

static esp_err_t ep_status(uint32_t session_id, const uint8_t *in, ssize_t inlen, uint8_t **out, ssize_t *outlen, void *priv)
{
    (void)session_id; (void)in; (void)priv;
    char b[96];
    LOCK();
    int n = nw_prov_status_json(&s_prov, b, sizeof b);
    UNLOCK();
    ESP_LOGI(TAG, "NWSETUP status in: inlen=%d reply len=%d", (int)inlen, n);
    if (n < 0) return ESP_FAIL;
    return reply(out, outlen, b);
}

/* ---- wifi_provisioning events -> state machine ---- */
static void on_prov_event(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg;
    if (base != WIFI_PROV_EVENT) return;
    LOCK();
    switch (id) {
    case WIFI_PROV_CRED_RECV: {            /* prov-config received, [verify] fires on apply with the config in data */
        wifi_sta_config_t *c = data;
        ESP_LOGI(TAG, "NWSETUP wifi cred recv");   /* SSID and passphrase are never logged */
        nw_prov_on_wifi_config(&s_prov, (const char *)c->ssid, (const char *)c->password, now_ms());
        nw_glue_on_apply(&s_glue, now_ms());   /* needs nw-claim first (contract order); else ERR_STATE and nw-status stays idle */
        break;
    }
    case WIFI_PROV_CRED_FAIL: {
        wifi_prov_sta_fail_reason_t *r = data;
        ESP_LOGW(TAG, "NWSETUP wifi cred fail: reason=%d", (int)*r);
        nw_glue_on_wifi_result(&s_glue, *r == WIFI_PROV_STA_AUTH_ERROR ? NW_PROV_WIFI_AUTH : NW_PROV_WIFI_NO_AP, now_ms());
        break;
    }
    case WIFI_PROV_CRED_SUCCESS:
        ESP_LOGI(TAG, "NWSETUP wifi cred success");
        nw_glue_on_wifi_result(&s_glue, NW_PROV_WIFI_OK, now_ms());   /* starts the claim POST */
        break;
    default: break;
    }
    UNLOCK();
}

/* Security 2 verifier: per-unit salt + SRP verifier generated at factory time from the label PoP (never the PoP itself).
 * Read from NVS namespace "nw_sec2" (keys "salt", "verifier"). Missing -> refuse to advertise (fail closed, no default PoP). */
static bool load_sec2(wifi_prov_security2_params_t *p, uint8_t *salt, size_t *sl, uint8_t *ver, size_t *vl)
{
    nvs_handle_t h;
    if (nvs_open("nw_sec2", NVS_READONLY, &h) != ESP_OK) return false;
    bool ok = nvs_get_blob(h, "salt", salt, sl) == ESP_OK && nvs_get_blob(h, "verifier", ver, vl) == ESP_OK;
    nvs_close(h);
    if (!ok || !nw_sec2_valid(salt, *sl, ver, *vl)) return false;   /* exact lengths, not blank (4.F2b) */
    p->salt = (const char *)salt; p->salt_len = (uint16_t)*sl; p->verifier = (const char *)ver; p->verifier_len = (uint16_t)*vl;   /* IDF 5.4: const char * + uint16_t */
    return true;
}

static bool start_ble(void)
{
    static uint8_t salt[32], ver[384];
    size_t sl = sizeof salt, vl = sizeof ver;
    wifi_prov_security2_params_t sec2 = {0};
    if (!load_sec2(&sec2, salt, &sl, ver, &vl)) { ESP_LOGE(TAG, "NWSETUP no security-2 salt/verifier in NVS: BLE stays off"); return false; }
    wifi_prov_mgr_config_t cfg = {.scheme = wifi_prov_scheme_ble, .scheme_event_handler = WIFI_PROV_SCHEME_BLE_EVENT_HANDLER_FREE_BTDM};
    if (wifi_prov_mgr_init(cfg) != ESP_OK) { ESP_LOGE(TAG, "NWSETUP BLE: wifi_prov_mgr_init failed"); return false; }
    s_mgr_up = true;
    static uint8_t uuid[16];               /* wifi_prov_scheme_ble wants the UUID in little-endian order [verify] */
    static const uint8_t be[16] = {0xb5,0x36,0x72,0xdd,0x52,0x27,0x40,0xa0,0x8b,0x6f,0x6f,0x83,0x6f,0x8a,0x58,0x4c};  /* NW_PROV_SERVICE_UUID */
    for (int i = 0; i < 16; i++) uuid[i] = be[15 - i];
    wifi_prov_scheme_ble_set_service_uuid(uuid);
    char name[NW_PROV_ADV_NAME_LEN + 1];
    nw_prov_adv_name(s_glue.hw_id, name, sizeof name);
    wifi_prov_mgr_endpoint_create("nw-claim");
    wifi_prov_mgr_endpoint_create("nw-status");
    { esp_err_t pe = wifi_prov_mgr_start_provisioning(WIFI_PROV_SECURITY_2, &sec2, name, NULL);
      if (pe != ESP_OK) { ESP_LOGE(TAG, "NWSETUP BLE: start_provisioning failed (%d)", (int)pe); return false; } }
    wifi_prov_mgr_endpoint_register("nw-claim", ep_claim, NULL);
    wifi_prov_mgr_endpoint_register("nw-status", ep_status, NULL);
    ESP_LOGI(TAG, "NWSETUP ble advertising");   /* only here: the manager is up (the state machine's request is logged in io_ble_set) */
    return true;
}

nw_setup_result_t nw_setup_run(uint32_t button_held_ms)
{
    s_lock = xSemaphoreCreateMutex();
    /* NVS first: the Wi-Fi driver (esp_wifi_init below) opens NVS during init. Without this, Wi-Fi init fails with
     * ESP_ERR_NVS_NOT_INITIALIZED (4353), wifi_prov_mgr cannot set STA mode, BLE provisioning never starts, and the unit
     * goes to deep sleep. Found by the bench debug boot log (NWSETUP BLE: start_provisioning failed (12289)). */
    esp_err_t nvs_ret = nvs_flash_init();
    if (nvs_ret != ESP_OK && nvs_ret != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "nvs_flash_init failed (%d); not erasing, setup refused", (int)nvs_ret);
        return NW_SETUP_SLEEP_UNTIL_RESET;
    }
    esp_netif_init();
    esp_event_loop_create_default();
    s_sta = esp_netif_create_default_wifi_sta();
    wifi_init_config_t wc = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&wc);
    esp_event_handler_register(WIFI_PROV_EVENT, ESP_EVENT_ANY_ID, on_prov_event, NULL);
    /* default loop: protocomm posts with esp_event_post, no loop argument (security2.c:273-274, v5.4 reviewer check) */
    esp_event_handler_register(PROTOCOMM_SECURITY_SESSION_EVENT, PROTOCOMM_SECURITY_SESSION_SETUP_OK, on_session_event, NULL);
    esp_event_handler_register(PROTOCOMM_SECURITY_SESSION_EVENT, PROTOCOMM_SECURITY_SESSION_CREDENTIALS_MISMATCH, on_session_event, NULL);
    esp_event_handler_register(PROTOCOMM_SECURITY_SESSION_EVENT, PROTOCOMM_SECURITY_SESSION_INVALID_SECURITY_PARAMS, on_session_event, NULL);

    char hw[NW_PROV_HWID_LEN + 1];
    make_hw_id(hw);
    nw_glue_io_t io = {.ble_set = io_ble_set, .wifi_start = io_wifi_start, .http_post = io_http_post};
    nw_prov_ops_t ops;
    nw_prov_store_nvs(&io.store);
    if (nw_glue_init(&s_glue, &io, hw, CONFIG_PLANT_FW_VERSION, &ops) != NW_PROV_OK) {
        ESP_LOGE(TAG, "glue init");
        esp_event_handler_unregister(PROTOCOMM_SECURITY_SESSION_EVENT, PROTOCOMM_SECURITY_SESSION_SETUP_OK, on_session_event);
        esp_event_handler_unregister(PROTOCOMM_SECURITY_SESSION_EVENT, PROTOCOMM_SECURITY_SESSION_CREDENTIALS_MISMATCH, on_session_event);
        esp_event_handler_unregister(PROTOCOMM_SECURITY_SESSION_EVENT, PROTOCOMM_SECURITY_SESSION_INVALID_SECURITY_PARAMS, on_session_event);
        esp_event_handler_unregister(WIFI_PROV_EVENT, ESP_EVENT_ANY_ID, on_prov_event);
        return NW_SETUP_SLEEP_UNTIL_RESET;
    }
    nw_prov_init(&s_prov, &ops);
#ifdef CONFIG_PLANT_BENCH_SETUP_WINDOW_S
    s_prov.setup_window_ms = CONFIG_PLANT_BENCH_SETUP_WINDOW_S * 1000u;   /* bench CI image only (sdkconfig.defaults.bench-ci): 300 s */
#endif
    nw_glue_attach(&s_glue, &s_prov);

    LOCK();
    int rc = nw_prov_boot(&s_prov, button_held_ms, now_ms());
    bool setup = nw_prov_in_setup(&s_prov);
    UNLOCK();
    if (rc != NW_PROV_OK) ESP_LOGE(TAG, "NWSETUP boot decision failed (%d)", rc);
    ESP_LOGI(TAG, "NWSETUP boot: %s (button held %u ms)", setup ? "setup mode" : "normal mode", (unsigned)button_held_ms);

    if (setup && !start_ble()) {           /* no verifier: do not advertise; close setup so nothing waits on a radio that is off */
        LOCK(); nw_glue_tick(&s_glue, now_ms() + NW_PROV_SETUP_TIMEOUT_MS); UNLOCK();
    }
    for (;;) {
        LOCK();
        nw_glue_tick(&s_glue, now_ms());
        nw_glue_next_t next = nw_glue_next_after_setup(&s_prov, false);
        UNLOCK();
        if (next != NW_GLUE_NEXT_STAY) break;
        vTaskDelay(pdMS_TO_TICKS(500));
    }
    esp_event_handler_unregister(PROTOCOMM_SECURITY_SESSION_EVENT, PROTOCOMM_SECURITY_SESSION_SETUP_OK, on_session_event);
    esp_event_handler_unregister(PROTOCOMM_SECURITY_SESSION_EVENT, PROTOCOMM_SECURITY_SESSION_CREDENTIALS_MISMATCH, on_session_event);
    esp_event_handler_unregister(PROTOCOMM_SECURITY_SESSION_EVENT, PROTOCOMM_SECURITY_SESSION_INVALID_SECURITY_PARAMS, on_session_event);
    if (s_mgr_up) { wifi_prov_mgr_stop_provisioning(); wifi_prov_mgr_deinit(); s_mgr_up = false; }   /* BLE off (FR-D09) [verify] deinit frees BT memory */
    esp_event_handler_unregister(WIFI_PROV_EVENT, ESP_EVENT_ANY_ID, on_prov_event);   /* after the manager stops, so its end events still reach the handler */
    bool have_record = false;
    { nw_prov_record_t r; if (s_glue.io.store.load && s_glue.io.store.load(s_glue.io.store_ctx, &r) == 0) { have_record = true; memset(&r, 0, sizeof r); } }
    nw_glue_next_t next = nw_glue_next_after_boot(&s_prov, rc, have_record);   /* PR #172: failed boot decision sleeps, never normal */
    LOCK(); nw_prov_state_t end_st = s_prov.state; unsigned end_failed = s_prov.failed_handshakes; UNLOCK();
    ESP_LOGI(TAG, "NWSETUP end: reason=%s state=%s -> %s", end_reason(end_st, end_failed, rc), state_name(end_st),
             next == NW_GLUE_NEXT_NORMAL ? "normal mode" : "sleep until reset");
    return next == NW_GLUE_NEXT_NORMAL ? NW_SETUP_NORMAL : NW_SETUP_SLEEP_UNTIL_RESET;
}

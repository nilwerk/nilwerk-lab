/* ESP-IDF adapter of the hourly upload (task 4.F3 slice 3). See nw_upload_idf.h. NOT COMPILED OR RUN by its author; every "[verify]" below is an
 * ESP-IDF v5.4 API detail that was written from memory of the Espressif docs and must be confirmed by the CI compile and a bench run.
 * Secrets: the device token and the Wi-Fi passphrase live only in the local record/auth buffers, are wiped after use and are NEVER logged. */
#include "nw_upload_idf.h"

#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <time.h>

#include "esp_event.h"
#include "esp_http_client.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_netif_sntp.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "nvs_flash.h"
#include "nw_ingest_ca.h"
#include "nw_prov_store_nvs.h"

static const char *TAG = "nw_upload";

#define JSON_BUF_BYTES 16384            /* 96 samples need about 13 KB (nw_upload.h); heap, only while a report is built */
#define RESP_BUF_BYTES 256              /* the /ingest answer is a small JSON object; a longer one is cut (the ack check reads server_time at the front) */
#define WIFI_RETRIES 3
#define EV_GOT_IP BIT0
#define EV_FAILED BIT1

static RTC_DATA_ATTR nw_cycle_state_t s_st;   /* retained across deep sleep; power-on content is garbage, nw_cycle_state_ensure() handles it */
static EventGroupHandle_t s_ev;
static bool s_wifi_up;
static int s_retries;
static volatile bool s_stopping;                /* set before any intentional disconnect/stop: on_event must not reconnect then */
static esp_event_handler_instance_t s_h_wifi, s_h_ip;

static uint32_t now_unix(void)
{
    time_t t = time(NULL);
    return t < 0 ? 0 : (uint32_t)t;
}

/* ---- Wi-Fi station ---- */
static void on_event(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg; (void)data;
    if (s_stopping || !s_ev) return;                 /* teardown in progress: a disconnect we caused ourselves is not a reason to reconnect */
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retries++ < WIFI_RETRIES) esp_wifi_connect();
        else xEventGroupSetBits(s_ev, EV_FAILED);
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(s_ev, EV_GOT_IP);
    }
}

/* Frees what wifi_up() created: handlers first (so none can touch the group), then the event group. Safe to call twice. Runs on EVERY exit path. */
static void wifi_release(void)
{
    s_stopping = true;
    s_retries = WIFI_RETRIES;
    if (s_h_wifi) { esp_event_handler_instance_unregister(WIFI_EVENT, ESP_EVENT_ANY_ID, s_h_wifi); s_h_wifi = NULL; }
    if (s_h_ip) { esp_event_handler_instance_unregister(IP_EVENT, IP_EVENT_STA_GOT_IP, s_h_ip); s_h_ip = NULL; }
    if (s_ev) { vEventGroupDelete(s_ev); s_ev = NULL; }
}

static bool wifi_up(const nw_prov_record_t *rec)
{
    if (s_wifi_up) return true;
    wifi_release();                                                  /* belt and braces: nothing left over from an earlier failed try */
    s_ev = xEventGroupCreate();
    if (!s_ev) return false;
    s_retries = 0;
    s_stopping = false;
    esp_netif_init();
    esp_err_t e = esp_event_loop_create_default();
    if (e != ESP_OK && e != ESP_ERR_INVALID_STATE) { wifi_release(); return false; }     /* INVALID_STATE = the setup flow already created it */
    if (!esp_netif_get_handle_from_ifkey("WIFI_STA_DEF")) esp_netif_create_default_wifi_sta();   /* [verify] the ifkey and a clean hand-over from nw_prov_idf.c */
    wifi_init_config_t wc = WIFI_INIT_CONFIG_DEFAULT();
    e = esp_wifi_init(&wc);
    if (e != ESP_OK && e != ESP_ERR_INVALID_STATE) { wifi_release(); return false; }     /* [verify] what a second init returns */
    esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, on_event, NULL, &s_h_wifi);
    esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, on_event, NULL, &s_h_ip);
    esp_wifi_set_storage(WIFI_STORAGE_RAM);                          /* credentials stay in NVS under nw_prov only, not a second copy in the Wi-Fi NVS */
    esp_wifi_set_mode(WIFI_MODE_STA);
    wifi_config_t cfg;
    memset(&cfg, 0, sizeof cfg);
    strncpy((char *)cfg.sta.ssid, rec->ssid, sizeof cfg.sta.ssid);   /* SSID is 1-32 bytes (nw_cycle_creds_check), no NUL needed at 32 */
    strncpy((char *)cfg.sta.password, rec->passphrase, sizeof cfg.sta.password - 1);
    cfg.sta.threshold.authmode = rec->passphrase[0] ? WIFI_AUTH_WPA2_PSK : WIFI_AUTH_OPEN;   /* WPA2 threshold, no SAE settings: WPA3-only APs are unsupported, see DEV_GUIDE 7.4 */
    cfg.sta.pmf_cfg.capable = true;
    e = esp_wifi_set_config(WIFI_IF_STA, &cfg);
    memset(&cfg, 0, sizeof cfg);
    if (e != ESP_OK || esp_wifi_start() != ESP_OK) { wifi_release(); return false; }
    EventBits_t b = xEventGroupWaitBits(s_ev, EV_GOT_IP | EV_FAILED, pdFALSE, pdFALSE, pdMS_TO_TICKS(CONFIG_PLANT_UPLOAD_NET_TIMEOUT_S * 1000));
    s_wifi_up = (b & EV_GOT_IP) != 0;
    if (!s_wifi_up) {
        s_stopping = true;                                           /* before stop: a late disconnect event must not reconnect */
        s_retries = WIFI_RETRIES;
        esp_wifi_stop();
        wifi_release();
        ESP_LOGW(TAG, "wifi: no connection (%s)", (b & EV_FAILED) ? "join failed" : "timeout");
    }
    return s_wifi_up;
}

static void wifi_down(void)
{
    if (s_wifi_up) {
        s_stopping = true;                                           /* BEFORE the disconnect: on_event would otherwise see s_retries==0 after a good join and call esp_wifi_connect() */
        s_retries = WIFI_RETRIES;
        esp_wifi_disconnect();
        esp_wifi_stop();
        s_wifi_up = false;
    }
    wifi_release();
}

/* ---- SNTP ---- */
static bool sntp_sync(void)
{
    esp_sntp_config_t c = ESP_NETIF_SNTP_DEFAULT_CONFIG(CONFIG_PLANT_NTP_SERVER);
    if (esp_netif_sntp_init(&c) != ESP_OK) return false;
    esp_err_t e = esp_netif_sntp_sync_wait(pdMS_TO_TICKS(CONFIG_PLANT_UPLOAD_NET_TIMEOUT_S * 1000));
    esp_netif_sntp_deinit();
    return e == ESP_OK;
}

/* ---- HTTPS POST: nw_upload_io_t.post. TLS with the PINNED CA (ADR-004, F-01), https only (nw_upload_build_url refused anything else), no redirects. ---- */
static char s_resp[RESP_BUF_BYTES];

static int io_post(void *ctx, const char *url, const char *auth, const char *body, size_t len, nw_upload_http_resp_t *resp)
{
    (void)ctx;
    /* Fail closed: without a pinned CA nothing is sent (no fallback to the certificate bundle, no skipped verification). */
    if (NW_INGEST_CA_PEM[0] == '\0') {
        ESP_LOGE(TAG, "no pinned CA in nw_ingest_ca.h: upload refused (ADR-004)");
        return -1;
    }
    esp_http_client_config_t cfg = {
        .url = url,
        .method = HTTP_METHOD_POST,
        .timeout_ms = CONFIG_PLANT_UPLOAD_HTTP_TIMEOUT_MS,
        .cert_pem = NW_INGEST_CA_PEM,                  /* the only trust anchor for the ingest host */
        .transport_type = HTTP_TRANSPORT_OVER_SSL,
        .disable_auto_redirect = true,                 /* the contract only knows 200; a redirect must not carry the bearer token elsewhere */
    };
    esp_http_client_handle_t c = esp_http_client_init(&cfg);
    if (!c) return -1;
    int rc = -1;
    esp_http_client_set_header(c, "Content-Type", "application/json");
    esp_http_client_set_header(c, "Authorization", auth);   /* the client keeps its own heap copy of the header value */
    if (esp_http_client_open(c, (int)len) == ESP_OK && esp_http_client_write(c, body, (int)len) == (int)len) {
        esp_http_client_fetch_headers(c);              /* [verify] return value is ambiguous for chunked answers: the status code decides */
        int st = esp_http_client_get_status_code(c);
        if (st > 0) {
            int got = esp_http_client_read_response(c, s_resp, sizeof s_resp - 1);
            if (got < 0) got = 0;
            s_resp[got] = 0;
            char *ra = NULL;
            resp->retry_after_s = (esp_http_client_get_header(c, "Retry-After", &ra) == ESP_OK) ? nw_cycle_parse_retry_after(ra) : -1;   /* [verify] */
            resp->status = st;
            resp->body = s_resp;
            resp->body_len = (size_t)got;
            rc = 0;
        }
    }
    /* Token wipe, honestly: the caller's buffer (rec.device_token) is zeroed by nw_upload_idf_wake. The client's heap copy of the header is released by
     * esp_http_client_cleanup() but NOT zeroed (free() does not wipe), and the TLS/mbedTLS buffers that carried it are not wiped by us either. The public
     * API has no "set header from a buffer I own" or "wipe header" call; esp_http_client_delete_header() frees without wiping too. Not claimed wiped. */
    esp_http_client_cleanup(c);
    return rc;
}

uint32_t nw_upload_idf_wake(const nw_soil_t *soil, nw_err_t e_soil, const nw_aht20_t *aht, nw_err_t e_aht, const nw_bh1750_t *bh, nw_err_t e_bh,
                            uint32_t vbat_mv, nw_err_t e_bat)
{
    if (nw_cycle_state_ensure(&s_st)) ESP_LOGI(TAG, "RTC state initialised (power-on)");
    int32_t vbat = (e_bat == NW_OK && nw_battery_plausible(vbat_mv)) ? (int32_t)vbat_mv : -1;
    bool radio_ok = vbat < 0 || vbat > NW_VBAT_WIFI_CUTOFF_MV;     /* same cutoff as nw_sleep_decide: no Wi-Fi, not even for SNTP, on a sagging cell */

    /* Stored credentials: the NVS record written by the setup flow. Never hard-coded, never logged. */
    static nw_prov_record_t rec;
    nw_prov_store_t store;
    nw_prov_store_nvs(&store);
    bool have_creds = false;
    esp_err_t ne = nvs_flash_init();                               /* NEVER erase on failure: that would wipe the token */
    if (ne == ESP_OK || ne == ESP_ERR_INVALID_STATE) {             /* INVALID_STATE: already initialised by the setup flow this boot */
        int lr = store.load(NULL, &rec);
        nw_creds_check_t cc = lr == 0 ? nw_cycle_creds_check(&rec) : NW_CREDS_NO_SSID;
        have_creds = (lr == 0 && cc == NW_CREDS_OK);
        if (!have_creds) ESP_LOGW(TAG, "no usable stored credentials (load=%d check=%d): unit not provisioned, buffering needs a synced clock", lr, (int)cc);
    } else {
        ESP_LOGE(TAG, "nvs_flash_init failed (%d); not erasing", (int)ne);
    }

    uint32_t now = now_unix();
    if (!nw_cycle_clock_ok(now)) {                                 /* power-on: the ring refuses unsynced samples, so sync first */
        if (have_creds && radio_ok && wifi_up(&rec) && sntp_sync()) now = now_unix();
        if (!nw_cycle_clock_ok(now)) {
            ESP_LOGW(TAG, "clock not synced: this sample is dropped, retry next wake");
            wifi_down();
            memset(&rec, 0, sizeof rec);
            return nw_cycle_sleep_s(0);
        }
    }

    nw_sample_t smp;
    nw_cycle_make_sample(&smp, now, soil, e_soil, aht, e_aht, bh, e_bh, vbat_mv, e_bat);
    nw_cycle_plan_t plan = nw_cycle_begin(&s_st, now, &smp, vbat);
    ESP_LOGI(TAG, "wake: pushed=%d buffered=%u report=%d low_bat=%d blocked_low_vbat=%d", (int)plan.pushed, (unsigned)nw_ring_count(&s_st.ring),
             (int)plan.sleep.report, (int)plan.sleep.low_battery, (int)plan.sleep.wifi_blocked_low_vbat);

    if (plan.sleep.report != NW_REPORT_NONE && have_creds) {
        if (strstr(CONFIG_PLANT_API_BASE_URL, ".invalid"))
            ESP_LOGW(TAG, "PLANT_API_BASE_URL is the .invalid placeholder: the upload cannot succeed (A-082: set the real URL locally)");
        char *buf = malloc(JSON_BUF_BYTES);
        if (buf && wifi_up(&rec)) {
            nw_upload_io_t io = { NULL, io_post };
            nw_upload_result_t r = nw_cycle_report(&s_st, &io, plan.sleep.report, CONFIG_PLANT_FW_VERSION, CONFIG_PLANT_API_BASE_URL,
                                                   rec.device_token, now_unix(), vbat, buf, JSON_BUF_BYTES);
            ESP_LOGI(TAG, "upload: outcome=%d gate=%d why=%d samples=%u drained=%u next_attempt=%u outage=%d%s", (int)r.outcome, (int)r.gate, (int)r.why,
                     (unsigned)r.n_samples, (unsigned)r.drained, (unsigned)r.next_attempt_unix, (int)r.outage_pending,
                     r.payload_too_large ? " PAYLOAD_TOO_LARGE(firmware bug)" : "");
            if (r.server_time_valid) {                             /* the ack re-syncs the RTC (nw_upload.h) */
                struct timeval tv = { .tv_sec = (time_t)r.server_time, .tv_usec = 0 };
                settimeofday(&tv, NULL);
            }
            if (r.reenter_setup) {                                 /* 401 token_revoked: forget the token, back to setup (FR-D07) */
                store.erase(NULL);
                memset(&rec, 0, sizeof rec);
                free(buf);
                wifi_down();
                ESP_LOGW(TAG, "token revoked: record erased, restarting into setup");
                esp_restart();
            }
        } else {
            s_st.outage_pending = true;                            /* a due report that could not even connect: next one is a reconnect (FR-D04) */
            ESP_LOGW(TAG, "report due but no connection (or no memory): buffered, will retry");
        }
        free(buf);
    }
    wifi_down();
    memset(&rec, 0, sizeof rec);
    return nw_cycle_sleep_s(now_unix());
}

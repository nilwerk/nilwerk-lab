/* Glue core between the provisioning state machine (nw_prov.h) and the radio/network stack (task 4.F2, slice 2).
 * Pure C, no ESP-IDF headers: built and tested on the host with a fake transport (test/host/test_glue.c).
 * The ESP-IDF side (NimBLE, Wi-Fi, esp_http_client) is src/nw_prov_idf.c and only fills nw_glue_io_t and feeds results back.
 * Requirements: FR-D03, FR-D09, NFR-03, NFR-06. Contract: docs/interfaces/ble-provisioning.md, openapi.yaml /device-claim.
 * This file does NOT change the state machine or the button times (WO glue item 6). */
#ifndef NW_PROV_GLUE_H
#define NW_PROV_GLUE_H

#include "nw_prov.h"

/* In-flight bounds. nw_prov_tick() does not time out WIFI_CONNECTING or CLAIMING (nw_prov.c), so these two are the only bound
 * (Theo C2). [proposed] values, not measured: a home Wi-Fi join normally takes a few seconds, 20 s covers a slow DHCP; the claim
 * call is one TLS handshake plus one POST, 15 s covers a slow mobile-hotspot link. Bench check needed (WO, step on timing). */
#define NW_GLUE_WIFI_JOIN_TIMEOUT_MS 20000u
#define NW_GLUE_HTTP_TIMEOUT_MS 15000u
#define NW_GLUE_FW_MAX 32                      /* openapi /device-claim: fw maxLength 32 */
#define NW_GLUE_BODY_MAX 1024                  /* name <= 320 bytes UTF-8, doubled worst case if all quotes, plus fixed fields */

/* What the platform provides. All start calls are non-blocking; results come back through nw_glue_on_*. */
typedef struct {
    void *ctx;
    void (*ble_set)(void *ctx, bool advertising);
    void (*wifi_start)(void *ctx, const char *ssid, const char *passphrase);
    void (*http_post)(void *ctx, const char *body, size_t len);   /* POST <api>/device-claim, JSON, TLS (pinned CA / bundle) */
    nw_prov_store_t store;
    void *store_ctx;
} nw_glue_io_t;

typedef struct {
    nw_prov_t *prov;
    nw_glue_io_t io;
    char hw_id[NW_PROV_HWID_LEN + 1];
    char fw[NW_GLUE_FW_MAX + 1];
    uint32_t now_ms;                       /* time of the call in progress (ops callbacks have no clock argument) */
    bool wifi_armed, claim_armed;
    uint32_t wifi_deadline_ms, claim_deadline_ms;
    char body[NW_GLUE_BODY_MAX];
} nw_glue_t;

/* Builds the ops table for nw_prov_init() and wires the glue in front of the io. Returns NW_PROV_OK or NW_PROV_ERR_ARG
 * (hw_id must match ^nw-[0-9a-f]{12}$, fw 1-32 chars). Call nw_prov_init(prov, &ops) afterwards, then nw_glue_attach(). */
int nw_glue_init(nw_glue_t *g, const nw_glue_io_t *io, const char *hw_id, const char *fw, nw_prov_ops_t *ops_out);
void nw_glue_attach(nw_glue_t *g, nw_prov_t *prov);

/* Request body for POST /device-claim: {"hw_id","claim_token","name","fw"} exactly as openapi.yaml requires (Theo C3).
 * Returns length or a negative nw_prov_err_t. name is JSON-escaped. */
int nw_glue_build_claim_body(char *buf, size_t cap, const char *hw_id, const char *claim_token, const char *name, const char *fw);

/* HTTP status to app reason (Theo C3). 200 is NW_PROV_CLAIM_OK only if the body also holds a 64-hex device_token (checked in
 * nw_glue_on_http_response); this function maps the status alone and returns OK for 200. */
nw_prov_claim_result_t nw_glue_map_http_status(int status);
/* Reads "device_token":"<64 hex>" out of a 200 body. Returns true and fills out[65] if present and well-formed. */
bool nw_glue_parse_device_token(const char *body, size_t len, char out[65]);

/* Use this instead of nw_prov_on_apply(): it stamps the Wi-Fi join deadline. */
int nw_glue_on_apply(nw_glue_t *g, uint32_t now_ms);

/* Results from the platform. Safe to call late: they are ignored (NW_PROV_ERR_STATE) once the state machine moved on. */
int nw_glue_on_wifi_result(nw_glue_t *g, nw_prov_wifi_result_t r, uint32_t now_ms);
int nw_glue_on_http_response(nw_glue_t *g, int status, const char *body, size_t len, uint32_t now_ms);
int nw_glue_on_transport_error(nw_glue_t *g, uint32_t now_ms);   /* TLS error, DNS, connection reset, no route: CLAIM_NETWORK */
/* Call at least once a second in setup mode: fires the two in-flight timeouts, then nw_prov_tick(). */
void nw_glue_tick(nw_glue_t *g, uint32_t now_ms);

/* Behaviour after setup ended (Theo C4, FR-D09, NFR-01). BLE and Wi-Fi are off in all three results.
 *  NORMAL      a record is stored (claimed, or setup was started by the button on a provisioned device): continue as normal.
 *  SLEEP_UNTIL_RESET  never provisioned and setup closed: deep sleep with no timer wake source (about 5 uA datasheet-class,
 *              measured value is task 5.4). Any reset re-runs nw_prov_boot, which enters setup again because no record exists.
 *              Not button wake: IO9 is not an RTC pin on the ESP32-C3 (only IO0-IO5 can wake deep sleep). */
typedef enum { NW_GLUE_NEXT_STAY = 0, NW_GLUE_NEXT_NORMAL, NW_GLUE_NEXT_SLEEP_UNTIL_RESET } nw_glue_next_t;
nw_glue_next_t nw_glue_next_after_setup(const nw_prov_t *p, bool record_present);
/* Decision after nw_prov_boot() and the setup loop (PR #172, Theo): a failed boot decision (boot_rc != NW_PROV_OK) never
 * falls through to NORMAL; it sleeps until reset. Otherwise the same as nw_glue_next_after_setup(). */
nw_glue_next_t nw_glue_next_after_boot(const nw_prov_t *p, int boot_rc, bool record_present);

#endif

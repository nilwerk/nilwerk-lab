/* Provisioning state machine (task 4.F2). Pure C, no ESP-IDF: every side effect goes through nw_prov_ops_t, so the whole
 * flow runs on the host with fakes. Requirements: FR-D03 (setup mode on first boot or button; Wi-Fi credentials, device name,
 * claim token), FR-D07 (factory reset wipes NVS and re-enters setup), FR-D09 (BLE only in setup mode), NFR-03 (3 min setup budget),
 * NFR-06 (credentials on the device only, never sent to the cloud; A-013). Contract: docs/interfaces/ble-provisioning.md.
 *
 * Time: callers pass a monotonic millisecond counter (uint32_t, wrap-safe). Events are delivered from one task (no locking here). */
#ifndef NW_PROV_H
#define NW_PROV_H

#include "nw_prov_proto.h"

/* ---- limits (ble-provisioning.md section 1) ----
 * Traceability: FR-D03 (setup mode and its end). The 5 attempts and the 300 s cut-off come from ADR-011 (Accepted) and the
 * A-070 answer of 2026-11-10. They are not NFR-03, which is the 3-minute user-time target. */
#define NW_PROV_MAX_FAILED_HANDSHAKES 5      /* FR-D03, ADR-011 (Accepted), A-070 (2026-11-10): 5 failed handshakes end setup mode */
#define NW_PROV_SETUP_TIMEOUT_MS (5u * 60u * 1000u) /* FR-D03, ADR-011 (Accepted), A-070 (2026-11-10): 300 s device cut-off from setup-mode entry */
/* [proposed] button gestures, not in the contract: the pinhole button (C-01) held at boot or at run time. Final times need a bench check. */
#define NW_PROV_BUTTON_SETUP_MS 3000u        /* hold >= 3 s: (re)enter setup mode, credentials kept until a new claim succeeds */
#define NW_PROV_BUTTON_RESET_MS 10000u       /* hold >= 10 s: factory reset (FR-D07): wipe stored credentials, then setup mode */

/* What is kept on the device after a successful claim (A-013: here and nowhere else; plain flash for the demo, Q-H6). */
typedef struct {
    char ssid[NW_PROV_SSID_MAX_BYTES + 1];
    char passphrase[NW_PROV_PASS_MAX + 1];
    char name[NW_PROV_NAME_MAX_BYTES + 1];
    char device_token[65];                   /* 64 hex chars returned once by /device-claim (openapi), + NUL */
} nw_prov_record_t;

/* Storage abstraction: ESP-IDF NVS adapter in nw_prov_store_nvs.c, RAM fake in the host tests. Return 0 on success, negative on error.
 * load: 0 = record present and filled, 1 = nothing stored. */
typedef struct {
    int (*load)(void *ctx, nw_prov_record_t *out);
    int (*save)(void *ctx, const nw_prov_record_t *rec);
    int (*erase)(void *ctx);
} nw_prov_store_t;

typedef enum { NW_PROV_WIFI_OK = 0, NW_PROV_WIFI_AUTH, NW_PROV_WIFI_NO_AP, NW_PROV_WIFI_TIMEOUT } nw_prov_wifi_result_t;
typedef enum { NW_PROV_CLAIM_OK = 0, NW_PROV_CLAIM_TOKEN_INVALID, NW_PROV_CLAIM_DEVICE_OWNED, NW_PROV_CLAIM_NETWORK, NW_PROV_CLAIM_SERVER } nw_prov_claim_result_t;

/* Hardware / network side effects. All are non-blocking starts; the result comes back as nw_prov_on_wifi_result / nw_prov_on_claim_result. */
typedef struct {
    void *ctx;
    void (*ble_set)(void *ctx, bool advertising);                                    /* FR-D09: off whenever not in setup mode */
    void (*wifi_connect)(void *ctx, const char *ssid, const char *passphrase);       /* start joining (ESP-IDF wifi) */
    void (*claim_post)(void *ctx, const char *claim_token, const char *name);        /* POST /device-claim over TLS; hw_id and fw are the caller's */
    nw_prov_store_t store;
    void *store_ctx;
} nw_prov_ops_t;

typedef enum {
    NW_PROV_S_NORMAL = 0,        /* BLE off, normal operation (credentials stored) */
    NW_PROV_S_ADVERTISING,       /* setup mode, waiting for the handshake */
    NW_PROV_S_SESSION,           /* handshake ok (security 2), receiving prov-config / nw-claim */
    NW_PROV_S_WIFI_CONNECTING,
    NW_PROV_S_CLAIMING,
    NW_PROV_S_CLAIMED,           /* done: stored, BLE off */
    NW_PROV_S_CLOSED,            /* setup ended by the guessing limit or the 300 s limit; BLE off; nothing stored */
} nw_prov_state_t;

typedef struct {
    nw_prov_ops_t ops;
    nw_prov_state_t state;
    uint32_t setup_started_ms;
    uint32_t setup_window_ms;                /* 0 = NW_PROV_SETUP_TIMEOUT_MS (production, host tests). Bench CI image only: set in nw_prov_idf.c */
    uint8_t failed_handshakes;
    bool have_wifi, have_claim;
    nw_prov_status_state_t st;               /* what nw-status reports */
    nw_prov_reason_t reason;
    nw_prov_record_t pending;                /* credentials held in RAM until the claim succeeds */
    char claim_token[NW_PROV_CLAIM_TOKEN_LEN + 1]; /* single use, wiped when claimed (or setup ends) */
} nw_prov_t;

void nw_prov_init(nw_prov_t *p, const nw_prov_ops_t *ops);

/* Boot decision (FR-D03 / FR-D07). button_held_ms = how long the button has been held at boot (0 = not pressed).
 * No stored record -> setup mode (first boot); hold >= RESET -> erase + setup; hold >= SETUP -> setup; otherwise NORMAL. */
int nw_prov_boot(nw_prov_t *p, uint32_t button_held_ms, uint32_t now_ms);
/* Button held at run time (same thresholds). Ignored while a claim is in flight. */
void nw_prov_button(nw_prov_t *p, uint32_t held_ms, uint32_t now_ms);

/* Protocol events (call order from ble-provisioning.md section 3, step 3). */
int nw_prov_on_handshake(nw_prov_t *p, bool ok, uint32_t now_ms);
/* Any nw-claim / nw-status call from the phone: records the security-2 session if it is still ADVERTISING (IDF glue calls it first). */
int nw_prov_on_endpoint(nw_prov_t *p, uint32_t now_ms);
int nw_prov_on_wifi_config(nw_prov_t *p, const char *ssid, const char *passphrase, uint32_t now_ms);
/* nw-claim write: parses and validates; reply (always filled) is the JSON body to return. Returns NW_PROV_OK or the error (reply says bad_request). */
int nw_prov_on_claim(nw_prov_t *p, const char *json, size_t len, char *reply, size_t reply_cap, uint32_t now_ms);
int nw_prov_on_apply(nw_prov_t *p, uint32_t now_ms);                  /* prov-config apply: needs wifi_config and nw-claim first */
int nw_prov_on_wifi_result(nw_prov_t *p, nw_prov_wifi_result_t r, uint32_t now_ms);
/* device_token = the 64-hex token from /device-claim, only read on NW_PROV_CLAIM_OK. */
int nw_prov_on_claim_result(nw_prov_t *p, nw_prov_claim_result_t r, const char *device_token, uint32_t now_ms);
void nw_prov_tick(nw_prov_t *p, uint32_t now_ms);                     /* call at least once a second in setup mode */

/* nw-status body (read endpoint). */
int nw_prov_status_json(const nw_prov_t *p, char *buf, size_t cap);
bool nw_prov_in_setup(const nw_prov_t *p);                            /* BLE should be on */

#endif

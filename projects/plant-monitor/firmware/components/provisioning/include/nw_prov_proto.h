/* BLE provisioning wire contract, device side (task 4.F2). Pure C, no ESP-IDF headers: built by test/host.
 * Contract: docs/interfaces/ble-provisioning.md (sections 1-2). Requirements: FR-D03, FR-D07, FR-D09, NFR-03, NFR-06.
 * Covers the custom endpoints nw-claim and nw-status (UTF-8 JSON) and the field rules for prov-config (SSID, passphrase).
 * Not covered: nw-hub (hub is v1.1, A-023), protobuf endpoints and the SRP6a handshake (ESP-IDF protocomm). */
#ifndef NW_PROV_PROTO_H
#define NW_PROV_PROTO_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* ---- contract constants (each cites the line in ble-provisioning.md it comes from) ---- */
#define NW_PROV_PROTO_VERSION 1              /* "v":1 in every JSON body (section 2) */
#define NW_PROV_REQ_MAX_BYTES 2048           /* custom endpoints: max 2 KiB per request (section 2) */
#define NW_PROV_NAME_MIN_CHARS 1             /* nw-claim name: 1-80 characters (section 2 table) */
#define NW_PROV_NAME_MAX_CHARS 80
#define NW_PROV_NAME_MAX_BYTES (NW_PROV_NAME_MAX_CHARS * 4)  /* UTF-8, 4 bytes per char worst case */
#define NW_PROV_CLAIM_TOKEN_LEN 22           /* nw-claim claim_token: 22 chars base64url (section 2 table; 16 bytes, openapi /claim-token) */
#define NW_PROV_SSID_MAX_BYTES 32            /* IEEE 802.11 SSID */
#define NW_PROV_PASS_MIN 8                   /* WPA2-PSK passphrase 8-63 chars, or empty for an open network (4.A3 review C2, app README) */
#define NW_PROV_PASS_MAX 63
#define NW_PROV_HWID_LEN 15                  /* "nw-" + 12 hex, openapi /device-claim pattern ^nw-[0-9a-f]{12}$ */
#define NW_PROV_ADV_NAME_LEN 9               /* "NW-" + last 6 hex of hw_id (section 1) */
#define NW_PROV_SERVICE_UUID "b53672dd-5227-40a0-8b6f-6f836f8a584c" /* section 1: generated in 4.F2 (python uuid4), written into the contract */

typedef enum {
    NW_PROV_OK = 0,
    NW_PROV_ERR_BAD_REQUEST = -1,  /* malformed JSON, wrong v, missing/invalid field -> reply {"ok":false,"error":"bad_request"} */
    NW_PROV_ERR_ARG = -2,
    NW_PROV_ERR_STATE = -3,        /* event not allowed in the current state */
    NW_PROV_ERR_TOO_SMALL = -4,    /* output buffer too small */
    NW_PROV_ERR_STORE = -5,
} nw_prov_err_t;

typedef struct {
    char name[NW_PROV_NAME_MAX_BYTES + 1];
    char claim_token[NW_PROV_CLAIM_TOKEN_LEN + 1];
} nw_prov_claim_req_t;

/* nw-claim request: {"v":1,"name":"...","claim_token":"..."}. Unknown keys with scalar values are ignored (forward compatible);
 * nested values, duplicate keys, bad UTF-8, control characters in name, or the wrong lengths are bad_request. */
int nw_prov_parse_claim(const char *json, size_t len, nw_prov_claim_req_t *out);

/* Field rules for prov-config. passphrase may be "" (open network). */
bool nw_prov_valid_ssid(const char *ssid);
bool nw_prov_valid_passphrase(const char *pass);
bool nw_prov_valid_claim_token(const char *tok);
/* Number of UTF-8 code points, or -1 if the string is not valid UTF-8 (overlongs, surrogates, > U+10FFFF rejected). */
int nw_prov_utf8_chars(const char *s, size_t n);

/* "NW-" + last 6 hex of hw_id, e.g. nw-a1b2c3d4e5f6 -> NW-d4e5f6. out >= NW_PROV_ADV_NAME_LEN + 1 bytes. */
int nw_prov_adv_name(const char *hw_id, char *out, size_t cap);

/* Reply bodies. Return length written (excluding NUL) or a negative nw_prov_err_t. */
int nw_prov_build_claim_reply(char *buf, size_t cap, bool ok);             /* {"v":1,"ok":true} / {"v":1,"ok":false,"error":"bad_request"} */

typedef enum {
    NW_PROV_ST_IDLE = 0,         /* not in the contract list: before apply (see ble-provisioning.md note added in 4.F2) */
    NW_PROV_ST_WIFI_CONNECTING,
    NW_PROV_ST_WIFI_FAILED,
    NW_PROV_ST_CLAIMING,
    NW_PROV_ST_CLAIMED,
    NW_PROV_ST_CLAIM_FAILED,
} nw_prov_status_state_t;

typedef enum {
    NW_PROV_REASON_NONE = 0,
    NW_PROV_REASON_AUTH, NW_PROV_REASON_NO_AP, NW_PROV_REASON_TIMEOUT,                       /* wifi_failed */
    NW_PROV_REASON_CLAIM_TOKEN_INVALID, NW_PROV_REASON_DEVICE_OWNED, NW_PROV_REASON_NETWORK, NW_PROV_REASON_SERVER, /* claim_failed */
} nw_prov_reason_t;

/* nw-status body: {"v":1,"state":"wifi_failed","reason":"auth"} (reason null when none). */
int nw_prov_build_status(char *buf, size_t cap, nw_prov_status_state_t st, nw_prov_reason_t reason);
const char *nw_prov_state_str(nw_prov_status_state_t st);
const char *nw_prov_reason_str(nw_prov_reason_t r);

#endif

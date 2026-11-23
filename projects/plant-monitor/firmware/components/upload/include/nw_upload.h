/* Hourly upload logic (task 4.F3 slice 2, FR-D02, FR-D04, FR-D06, NFR-04, NFR-06). Pure C, no ESP-IDF, no network.
 * Contract: docs/interfaces/openapi.yaml /ingest (the deployed 4.B2 function, cloud/supabase/functions/_shared/handlers.ts).
 * NOT WORKING ON HARDWARE: the TLS client, Wi-Fi bring-up, SNTP and the RTC-retained storage of nw_upload_state_t are not
 * written yet. This file decides; a thin ESP-IDF adapter only has to implement nw_upload_io_t.
 *
 * One attempt = nw_upload_attempt(): config check -> gate (battery, backoff, rate limit) -> nw_report_build -> POST ->
 * classify the answer -> drain the ring on an ack. Response table (openapi /ingest):
 *   200 + integer server_time   ACK            ring drained up to the batch's last_seq (nw_ring_consume_upto), failures reset
 *   200 without server_time     RETRY          NOT an ack (a proxy or a broken answer must not delete data); /ingest is
 *                                              idempotent on (device, ts), so the repeat costs nothing
 *   other 2xx, 1xx, 3xx         RETRY          redirects are never followed; the contract only knows 200
 *   400, 413                    REJECTED       our payload is wrong; not retried blindly: after NW_UPLOAD_POISON_MAX rejects of
 *                                              the SAME batch (same first seq) the batch is dropped so one bad batch cannot block the buffer for good
 *   401 token_revoked           REVOKED        device was released/deleted: stop uploading, discard the buffer, re-enter setup
 *                                              (openapi: "[proposed, Mira to confirm]"; confirmed here, and ONLY for this code)
 *   401 token_invalid / other   AUTH_FAILED    buffer kept, backoff; a damaged token must not wipe 24 h of data
 *   429                         RETRY          honours Retry-After (clamped), never shorter than the backoff
 *   405, 5xx, transport error   RETRY          exponential backoff
 * Single source for the thresholds: nw_sleep.h (NW_VBAT_*); this file only uses them. */
#ifndef NW_UPLOAD_H
#define NW_UPLOAD_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "nw_report.h"
#include "nw_sample_ring.h"

#define NW_UPLOAD_PATH "/ingest"                 /* openapi path; base URL is a build setting, never committed (A-082) */
#define NW_UPLOAD_TOKEN_HEX 64                   /* device token: 32 bytes hex (openapi /device-claim, ADR-004) */
#define NW_UPLOAD_URL_MAX 256
#define NW_UPLOAD_AUTH_MAX (7 + NW_UPLOAD_TOKEN_HEX + 1) /* "Bearer " + token + NUL */
#define NW_UPLOAD_MAX_PER_HOUR 6                 /* openapi /ingest: max 6 requests per device per hour [proposed, not in 4.B2] */
#define NW_UPLOAD_RATE_WINDOW_S 3600
#define NW_UPLOAD_BACKOFF_BASE_S 900             /* ASSUMED: one sample wake. Failures: 900, 1800, 3600, 3600 ... s */
#define NW_UPLOAD_BACKOFF_MAX_S 3600             /* ASSUMED: never later than the next hourly report */
#ifdef CONFIG_PLANT_BENCH_UPLOAD_MINUTE
/* BENCH CI IMAGE ONLY: one request per minute needs more than the production limit of 6 per hour. 70 leaves room for the window edge.
 * The cloud does not enforce a limit yet (openapi /ingest, [not in 4.B2]); if it starts to, bench uploads get 429 with Retry-After.
 * Back-off 60 s: a failed minute retries the next minute. Production values above are unchanged. */
#undef NW_UPLOAD_MAX_PER_HOUR
#define NW_UPLOAD_MAX_PER_HOUR 70
#undef NW_UPLOAD_BACKOFF_BASE_S
#define NW_UPLOAD_BACKOFF_BASE_S 60
#undef NW_UPLOAD_BACKOFF_MAX_S
#define NW_UPLOAD_BACKOFF_MAX_S 60
#endif
#define NW_UPLOAD_LOWBAT_BACKOFF_S 3600          /* ASSUMED: below NW_VBAT_LOW_MV a failed upload waits a full hour (radio energy) */
#define NW_UPLOAD_RETRY_AFTER_MAX_S 3600         /* a server value above this is clamped: never silent for more than an hour */
#define NW_UPLOAD_POISON_MAX 3                   /* rejects (400/413) of the same batch before it is dropped */

typedef enum {
    NW_UP_ACK = 0,
    NW_UP_RETRY,
    NW_UP_REJECTED,
    NW_UP_AUTH_FAILED,
    NW_UP_REVOKED,
    NW_UP_NOT_SENT                               /* nothing went on the air: see gate / reason */
} nw_upload_outcome_t;

typedef enum {
    NW_UP_GATE_OK = 0,
    NW_UP_GATE_LOW_VBAT,                         /* cell at or below NW_VBAT_WIFI_CUTOFF_MV (same rule as nw_sleep_decide) */
    NW_UP_GATE_BACKOFF,                          /* now < next_attempt_unix */
    NW_UP_GATE_RATE_LIMIT                        /* NW_UPLOAD_MAX_PER_HOUR attempts in the last hour */
} nw_upload_gate_t;

typedef enum {
    NW_UP_WHY_NONE = 0,
    NW_UP_WHY_GATE,
    NW_UP_WHY_BAD_CONFIG,                        /* base URL or token malformed: not an outage, no retry helps */
    NW_UP_WHY_NO_PAYLOAD                         /* empty buffer, or nw_report_build refused (schema range, unsynced ts) */
} nw_upload_why_t;

/* Retained across deep sleep (RTC/NVS): the caller stores it. All zero = fresh. */
typedef struct {
    uint32_t next_attempt_unix;                  /* no attempt before this RTC time; 0 = none */
    uint8_t fails;                               /* consecutive failed attempts, saturates at 255 */
    uint8_t rejects;                             /* consecutive rejects of reject_seq */
    uint32_t reject_seq;                         /* FIRST seq of the batch that was rejected (stable while undrained) */
    uint32_t attempts[NW_UPLOAD_MAX_PER_HOUR];   /* start time of the last attempts (ring), 0 = empty */
    uint8_t att_head;
} nw_upload_state_t;

typedef struct {
    int status;                                  /* HTTP status */
    int32_t retry_after_s;                       /* Retry-After header in seconds, -1 = absent */
    const char *body;                            /* not necessarily NUL-terminated */
    size_t body_len;
} nw_upload_http_resp_t;

typedef struct {
    void *ctx;
    /* POST url, headers Authorization: <auth> and Content-Type: application/json, body. Over TLS with the pinned CA / bundle.
     * Returns 0 when an HTTP answer was received (filled into resp, valid until the next call), negative on any transport
     * failure (DNS, TLS, connect, timeout). */
    int (*post)(void *ctx, const char *url, const char *auth, const char *body, size_t len, nw_upload_http_resp_t *resp);
} nw_upload_io_t;

typedef struct {
    nw_upload_outcome_t outcome;
    nw_upload_gate_t gate;                       /* meaningful when outcome == NW_UP_NOT_SENT and why == GATE */
    nw_upload_why_t why;
    size_t drained;                              /* samples removed from the ring (ack, revoke, poison drop) */
    size_t n_samples;                            /* samples in the batch that was sent */
    bool server_time_valid;
    uint32_t server_time;                        /* unix s from the ack: the caller re-syncs the RTC and stores last_report_unix */
    uint32_t next_attempt_unix;                  /* copy of the state, for logging */
    bool outage_pending;                         /* value to retain for nw_sleep_in_t.outage_pending (cleared by an ack) */
    bool reenter_setup;                          /* REVOKED: caller wipes the token record and starts setup (FR-D07) */
    bool batch_dropped;                          /* poison guard fired */
    bool payload_too_large;                      /* answer was 413: a FIRMWARE BUG (we send max 96 samples, server limit is 192); log distinctly */
} nw_upload_result_t;

/* https://host[:port][/path], no trailing slash, no query/fragment/space/control chars. Writes base + "/ingest".
 * Returns the length or -1. */
int nw_upload_build_url(char *out, size_t cap, const char *base_url);
/* "Bearer <64 lowercase hex>". Returns the length or -1 (token must match ^[0-9a-f]{64}$, openapi /device-claim). */
int nw_upload_build_auth(char *out, size_t cap, const char *token);

void nw_upload_state_init(nw_upload_state_t *s);
/* Gate for the next attempt. Low battery first (no radio at all), then backoff, then the 6-per-hour limit.
 * vbat_mv < 0 = unknown: not blocked (same as nw_sleep_decide). */
nw_upload_gate_t nw_upload_gate(const nw_upload_state_t *s, uint32_t now_unix, int32_t vbat_mv);

/* Classifies one HTTP answer and updates state and ring (drain on ack). first_seq/last_seq = seq of the batch's first/last sample (last_seq from nw_report_build's *last_seq)
 * that was sent. low_battery = the retained FR-D06 state (nw_sleep_out_t.low_battery). */
nw_upload_result_t nw_upload_on_response(nw_upload_state_t *s, nw_ring_t *r, uint32_t first_seq, uint32_t last_seq, size_t n_samples,
                                         const nw_upload_http_resp_t *resp, uint32_t now_unix, bool low_battery);
/* Transport error (no HTTP answer): same backoff as a 5xx, nothing drained. */
nw_upload_result_t nw_upload_on_transport_error(nw_upload_state_t *s, uint32_t now_unix, bool low_battery);

/* The whole attempt. buf/cap = scratch for the JSON body (96 samples need about 13 KB; nw_report_build returns 0 when too
 * small). The auth header copy is wiped before returning. */
nw_upload_result_t nw_upload_attempt(nw_upload_state_t *s, const nw_upload_io_t *io, nw_ring_t *r, const nw_report_meta_t *meta,
                                     const char *base_url, const char *device_token, uint32_t now_unix, int32_t vbat_mv,
                                     bool low_battery, char *buf, size_t cap);

#endif

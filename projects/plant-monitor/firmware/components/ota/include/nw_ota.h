/* OTA image check and rollback decision (task 4.F4). Pure C: no ESP-IDF, no network, no flash.
 *
 * Requirements: FR-D05 (firmware update with automatic rollback), ADR-009 (SHA-256 of the image from the ingest manifest,
 * download into the inactive slot, confirm only after a successful ingest, otherwise bootloader rollback), NFR-06 (TLS).
 * Integrity is SHA-256 over TLS (A-009). Image signing is a documented follow-up (ADR-009 risk O-3), NOT in this file.
 *
 * NOT RUN ON HARDWARE: the esp_https_ota download, esp_ota_mark_app_valid_cancel_rollback() and the RTC-retained counter
 * behind nw_ota_boot_t are not written yet. This file decides; the ESP-IDF adapter only has to feed it the state and act
 * on the answer.
 */
#ifndef NW_OTA_H
#define NW_OTA_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define NW_OTA_SHA256_LEN 32
#define NW_OTA_SHA256_HEX_LEN 64

/* Rollback window, counted in BOOTS and not in seconds: the device has no trusted clock before SNTP, and the
 * confirmation point (a successful /ingest) comes once per hourly report = every 4th wake of 15 min (FR-D01, FR-D02).
 * [decided, A-116, Arsany 21 Nov: accept 8 boots] 8 boots = two hourly upload chances before rollback. Derived here, not from an NFR. */
#define NW_OTA_MAX_UNCONFIRMED_BOOTS 8

/* Streaming SHA-256 (FIPS 180-4) for the chunked download. */
typedef struct {
    uint32_t h[8];
    uint64_t bytes;   /* total bytes hashed so far */
    uint8_t buf[64];
    uint8_t buf_len;
} nw_sha256_t;

void nw_sha256_init(nw_sha256_t *c);
void nw_sha256_update(nw_sha256_t *c, const void *data, size_t len);
void nw_sha256_final(nw_sha256_t *c, uint8_t out[NW_OTA_SHA256_LEN]);

/* Parses the manifest's 64-character hex SHA-256 (either case). Returns false and leaves `out` untouched when the
 * length is not exactly 64 or a character is not hex. */
bool nw_ota_parse_sha256_hex(const char *hex, size_t len, uint8_t out[NW_OTA_SHA256_LEN]);

/* Constant-time comparison of two 32-byte digests. */
bool nw_ota_digest_equal(const uint8_t a[NW_OTA_SHA256_LEN], const uint8_t b[NW_OTA_SHA256_LEN]);

/* The pure check (FR-D05, ADR-009): true only when the SHA-256 of the whole image equals `expected`.
 * A NULL expected digest always fails: an image with no expected hash is never installed. */
bool nw_ota_image_ok(const void *img, size_t len, const uint8_t expected[NW_OTA_SHA256_LEN]);

/* Result of the hash check on the downloaded image. NOT_CHECKED is 0, so an unset value refuses install. */
typedef enum {
    NW_OTA_HASH_NOT_CHECKED = 0,
    NW_OTA_HASH_MISMATCH,
    NW_OTA_HASH_MATCH
} nw_ota_hash_result_t;

/* Maps nw_ota_image_ok() onto the hash result: MATCH only when the image digest equals `expected`. */
nw_ota_hash_result_t nw_ota_hash_check(const void *img, size_t len, const uint8_t expected[NW_OTA_SHA256_LEN]);

/* Install gate (architect condition C1, PR #153): the image may be written to the inactive slot only on a MATCH.
 * The hash result is a required parameter; NOT_CHECKED and MISMATCH both refuse. The ESP-IDF adapter must call this
 * gate before it writes any byte to the inactive slot. */
bool nw_ota_may_install(nw_ota_hash_result_t hash);

/* Boot state the firmware keeps (the RTC-retained fields are written by the ESP-IDF adapter, not here). */
typedef struct {
    bool pending_verify;           /* the running image came from OTA and is not confirmed yet */
    uint8_t unconfirmed_boots;     /* boots of that image so far, INCLUDING the current one (caller increments it) */
    bool ingest_ok;                /* a successful /ingest happened since this boot (the confirmation point, ADR-009) */
    uint8_t max_unconfirmed_boots; /* window in boots, normally NW_OTA_MAX_UNCONFIRMED_BOOTS */
} nw_ota_boot_t;

typedef enum {
    NW_OTA_KEEP = 0,   /* not a pending image: nothing to do */
    NW_OTA_CONFIRM,    /* ingest succeeded: mark the image valid and cancel the rollback */
    NW_OTA_WAIT,       /* pending and inside the window: keep running; the next boot counts */
    NW_OTA_ROLLBACK    /* pending and the window is used up: roll back to the previous slot, then reboot */
} nw_ota_decision_t;

/* Order matters: not pending -> KEEP; a successful ingest -> CONFIRM (also at the window boundary); window used up
 * -> ROLLBACK; otherwise WAIT. */
nw_ota_decision_t nw_ota_boot_decide(const nw_ota_boot_t *b);

#endif

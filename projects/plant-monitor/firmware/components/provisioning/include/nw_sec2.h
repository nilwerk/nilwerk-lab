/* Per-unit security-2 data check (task 4.F2b, A-081 a). Pure C, no ESP-IDF: host-tested (test/host/test_sec2.c).
 * The factory tool tools/nw_sec2_gen.py writes NVS namespace "nw_sec2", blobs "salt" (16 B) and "verifier" (384 B). */
#ifndef NW_SEC2_H
#define NW_SEC2_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define NW_SEC2_NVS_NAMESPACE "nw_sec2"   /* contract: docs/interfaces/ble-provisioning.md (PR #129) */
#define NW_SEC2_KEY_SALT "salt"
#define NW_SEC2_KEY_VERIFIER "verifier"
#define NW_SEC2_SALT_LEN 16u              /* same as tools/nw_sec2_gen.py SALT_LEN */
#define NW_SEC2_VERIFIER_LEN 384u         /* 3072-bit SRP group, fixed width */

/* true only when both blobs have the exact length and neither is all zero or all 0xFF (erased flash, blank factory step).
 * Anything else: BLE must stay off (fail closed, no default PoP). */
bool nw_sec2_valid(const uint8_t *salt, size_t salt_len, const uint8_t *verifier, size_t verifier_len);
#endif

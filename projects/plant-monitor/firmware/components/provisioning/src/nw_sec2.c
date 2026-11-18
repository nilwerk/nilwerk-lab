#include "nw_sec2.h"

static bool uniform(const uint8_t *p, size_t n)    /* all bytes equal (0x00 or 0xFF blank), n >= 1 */
{
    for (size_t i = 1; i < n; i++) if (p[i] != p[0]) return false;
    return true;
}

bool nw_sec2_valid(const uint8_t *salt, size_t salt_len, const uint8_t *verifier, size_t verifier_len)
{
    if (!salt || !verifier) return false;
    if (salt_len != NW_SEC2_SALT_LEN || verifier_len != NW_SEC2_VERIFIER_LEN) return false;
    if (uniform(salt, salt_len) || uniform(verifier, verifier_len)) return false;
    return true;
}

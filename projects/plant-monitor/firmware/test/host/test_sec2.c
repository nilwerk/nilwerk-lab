/* Host tests for the per-unit security-2 data check (task 4.F2b, A-081 a). No hardware. */
#include <stdio.h>
#include <string.h>
#include "nwtest.h"
#include "nw_sec2.h"

int nwtest_failed, nwtest_checked;

static void fill(uint8_t *p, size_t n, uint8_t seed) { for (size_t i = 0; i < n; i++) p[i] = (uint8_t)(seed + i * 7u + 1u); }

int main(void)
{
    uint8_t s[NW_SEC2_SALT_LEN], v[NW_SEC2_VERIFIER_LEN];
    fill(s, sizeof s, 3); fill(v, sizeof v, 9);
    CHECK_EQ(NW_SEC2_SALT_LEN, 16); CHECK_EQ(NW_SEC2_VERIFIER_LEN, 384);                       /* sizes of tools/nw_sec2_gen.py */
    CHECK(strcmp(NW_SEC2_NVS_NAMESPACE, "nw_sec2") == 0 && strcmp(NW_SEC2_KEY_SALT, "salt") == 0 && strcmp(NW_SEC2_KEY_VERIFIER, "verifier") == 0);
    CHECK(nw_sec2_valid(s, sizeof s, v, sizeof v));
    /* length must be exact (a truncated or padded blob is not a verifier) */
    CHECK(!nw_sec2_valid(s, sizeof s - 1, v, sizeof v));
    CHECK(!nw_sec2_valid(s, sizeof s + 1, v, sizeof v));
    CHECK(!nw_sec2_valid(s, sizeof s, v, sizeof v - 1));
    CHECK(!nw_sec2_valid(s, 0, v, sizeof v)); CHECK(!nw_sec2_valid(s, sizeof s, v, 0));
    /* blank data: erased flash (0xFF) or zero-filled must not enable BLE */
    uint8_t blank[NW_SEC2_VERIFIER_LEN];
    memset(blank, 0xFF, sizeof blank); CHECK(!nw_sec2_valid(blank, 16, v, sizeof v)); CHECK(!nw_sec2_valid(s, sizeof s, blank, sizeof blank));
    memset(blank, 0x00, sizeof blank); CHECK(!nw_sec2_valid(blank, 16, v, sizeof v)); CHECK(!nw_sec2_valid(s, sizeof s, blank, sizeof blank));
    /* one differing byte at the very end is enough to be valid (loop must reach the last byte) */
    memset(blank, 0x00, sizeof blank); blank[sizeof blank - 1] = 1; CHECK(nw_sec2_valid(s, sizeof s, blank, sizeof blank));
    memset(blank, 0x00, sizeof blank); blank[1] = 1; CHECK(nw_sec2_valid(s, sizeof s, blank, sizeof blank));
    CHECK(!nw_sec2_valid(NULL, 16, v, sizeof v)); CHECK(!nw_sec2_valid(s, sizeof s, NULL, sizeof v));
    printf("sec2 host tests: %d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}

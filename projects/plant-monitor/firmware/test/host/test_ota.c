/* Host tests for the OTA image check and the rollback decision (task 4.F4). FR-D05 (update with automatic rollback),
 * ADR-009 (SHA-256 of the image, confirm only after a successful ingest, otherwise rollback). No network, no flash.
 * The MOCK image below is a test string, not firmware. Its digests were computed with Python hashlib, not with nw_ota.c. */
#include <stdio.h>
#include <string.h>
#include "nwtest.h"
#include "nw_ota.h"

int nwtest_failed, nwtest_checked;

/* Reference digests (Python hashlib). The NIST vectors are the FIPS 180-2 examples. */
static const char *HEX_EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
static const char *HEX_ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
static const char *HEX_448 = "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1";
static const char *HEX_1M_A = "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0";
static const char *HEX_55 = "9f4390f8d30c2dd92ec9f095b65e2b9ae9b0a925a5258e241c9f1e910f734318";
static const char *HEX_56 = "b35439a4ac6f0948b6d6f9e3c6af0f5f590ce20f1bde7090ef7970686ec6738a";
static const char *HEX_64 = "ffe054fe7ae0cb6dc65c3af9b61d5209f439851db43d0ba5997337df154668eb";

#define MOCK_IMG "MOCK OTA image, not firmware"
static const char *HEX_MOCK = "c4f99efa0243dcabd7452864638f6c75ac6706dd80e565eebc2a4d38bd443294";

static void sha_hex_of(const void *data, size_t len, char out[65])
{
    nw_sha256_t c;
    uint8_t d[NW_OTA_SHA256_LEN];
    static const char hx[] = "0123456789abcdef";
    nw_sha256_init(&c);
    nw_sha256_update(&c, data, len);
    nw_sha256_final(&c, d);
    for (int i = 0; i < 32; i++) {
        out[2 * i] = hx[d[i] >> 4];
        out[2 * i + 1] = hx[d[i] & 15];
    }
    out[64] = 0;
}

static void test_sha256_vectors(void)
{
    char got[65];
    sha_hex_of("", 0, got);
    CHECK(strcmp(got, HEX_EMPTY) == 0);
    sha_hex_of("abc", 3, got);
    CHECK(strcmp(got, HEX_ABC) == 0);
    sha_hex_of("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq", 56, got);
    CHECK(strcmp(got, HEX_448) == 0);
    /* padding edges: 55 bytes (fits one block), 56 (needs a second block), 64 (exactly one block) */
    char a55[56], a56[57], a64[65];
    memset(a55, 'a', 55); a55[55] = 0;
    memset(a56, 'a', 56); a56[56] = 0;
    memset(a64, 'a', 64); a64[64] = 0;
    sha_hex_of(a55, 55, got); CHECK(strcmp(got, HEX_55) == 0);
    sha_hex_of(a56, 56, got); CHECK(strcmp(got, HEX_56) == 0);
    sha_hex_of(a64, 64, got); CHECK(strcmp(got, HEX_64) == 0);
    /* one million 'a': one-shot and streamed in 1000-byte chunks must both equal the reference */
    static char one_m[1000000];
    memset(one_m, 'a', sizeof one_m);
    sha_hex_of(one_m, sizeof one_m, got);
    CHECK(strcmp(got, HEX_1M_A) == 0);
    nw_sha256_t c;
    uint8_t d[NW_OTA_SHA256_LEN];
    nw_sha256_init(&c);
    for (size_t off = 0; off < sizeof one_m; off += 1000) nw_sha256_update(&c, one_m + off, 1000);
    nw_sha256_final(&c, d);
    CHECK(c.bytes == 1000000u);
    char hx[65];
    for (int i = 0; i < 32; i++) sprintf(hx + 2 * i, "%02x", d[i]);
    CHECK(strcmp(hx, HEX_1M_A) == 0);
    /* split "abc" as "a" + "bc" */
    nw_sha256_init(&c);
    nw_sha256_update(&c, "a", 1);
    nw_sha256_update(&c, "bc", 2);
    nw_sha256_final(&c, d);
    for (int i = 0; i < 32; i++) sprintf(hx + 2 * i, "%02x", d[i]);
    CHECK(strcmp(hx, HEX_ABC) == 0);
}

static void test_hex_parse(void)
{
    uint8_t out[NW_OTA_SHA256_LEN];
    uint8_t want[NW_OTA_SHA256_LEN];
    CHECK(nw_ota_parse_sha256_hex(HEX_ABC, 64, out));
    for (int i = 0; i < 32; i++) {
        unsigned v;
        (void)sscanf(HEX_ABC + 2 * i, "%2x", &v);
        want[i] = (uint8_t)v;
    }
    CHECK(memcmp(out, want, 32) == 0);
    /* upper case is accepted and gives the same bytes */
    char up[65];
    for (int i = 0; i < 64; i++) up[i] = (char)((HEX_ABC[i] >= 'a' && HEX_ABC[i] <= 'f') ? HEX_ABC[i] - 32 : HEX_ABC[i]);
    up[64] = 0;
    uint8_t out_up[NW_OTA_SHA256_LEN];
    CHECK(nw_ota_parse_sha256_hex(up, 64, out_up));
    CHECK(memcmp(out_up, want, 32) == 0);
    /* wrong length, non-hex character, NULL: rejected, and out is not written */
    uint8_t keep[NW_OTA_SHA256_LEN];
    memset(keep, 0x5a, sizeof keep);
    CHECK(!nw_ota_parse_sha256_hex(HEX_ABC, 63, keep));
    CHECK(!nw_ota_parse_sha256_hex(HEX_ABC, 65, keep));
    CHECK(!nw_ota_parse_sha256_hex(HEX_ABC, 0, keep));
    char bad[65];
    memcpy(bad, HEX_ABC, 65);
    bad[63] = 'g';
    CHECK(!nw_ota_parse_sha256_hex(bad, 64, keep));
    CHECK(!nw_ota_parse_sha256_hex(NULL, 64, keep));
    uint8_t all5a[NW_OTA_SHA256_LEN];
    memset(all5a, 0x5a, sizeof all5a);
    CHECK(memcmp(keep, all5a, sizeof keep) == 0);
}

/* AC 1: the image check accepts the exact image and rejects a mismatch (wrong content, one flipped bit,
 * truncated, extended, and a digest that differs in its first or last byte only). */
static void test_image_check(void)
{
    uint8_t exp[NW_OTA_SHA256_LEN];
    CHECK(nw_ota_parse_sha256_hex(HEX_MOCK, 64, exp));
    CHECK(nw_ota_image_ok(MOCK_IMG, strlen(MOCK_IMG), exp));                 /* match */
    CHECK(!nw_ota_image_ok(MOCK_IMG, strlen(MOCK_IMG) - 1, exp));           /* truncated */

    char img[sizeof MOCK_IMG];
    memcpy(img, MOCK_IMG, sizeof MOCK_IMG);
    img[0] ^= 0x01;                                                         /* one bit flipped in byte 0 */
    CHECK(!nw_ota_image_ok(img, strlen(img), exp));
    memcpy(img, MOCK_IMG, sizeof MOCK_IMG);
    img[strlen(img) - 1] ^= 0x01;                                           /* one bit flipped in the last byte */
    CHECK(!nw_ota_image_ok(img, strlen(img), exp));

    char longer[sizeof MOCK_IMG + 1];
    memcpy(longer, MOCK_IMG, strlen(MOCK_IMG));
    longer[strlen(MOCK_IMG)] = '!';
    CHECK(!nw_ota_image_ok(longer, strlen(MOCK_IMG) + 1, exp));             /* appended byte */

    /* digest that differs only in its last byte, and only in its first byte: a partial compare fails one of these */
    uint8_t last_bad[NW_OTA_SHA256_LEN], first_bad[NW_OTA_SHA256_LEN];
    memcpy(last_bad, exp, sizeof exp);
    memcpy(first_bad, exp, sizeof exp);
    last_bad[NW_OTA_SHA256_LEN - 1] ^= 0x80;
    first_bad[0] ^= 0x80;
    CHECK(!nw_ota_image_ok(MOCK_IMG, strlen(MOCK_IMG), last_bad));
    CHECK(!nw_ota_image_ok(MOCK_IMG, strlen(MOCK_IMG), first_bad));

    /* no expected digest: never installs */
    CHECK(!nw_ota_image_ok(MOCK_IMG, strlen(MOCK_IMG), NULL));
    /* the empty image has its own digest */
    uint8_t empty[NW_OTA_SHA256_LEN];
    CHECK(nw_ota_parse_sha256_hex(HEX_EMPTY, 64, empty));
    CHECK(nw_ota_image_ok("", 0, empty));
    CHECK(!nw_ota_image_ok(MOCK_IMG, strlen(MOCK_IMG), empty));
}

static nw_ota_boot_t boot(bool pending, unsigned boots, bool ingest)
{
    nw_ota_boot_t b;
    b.pending_verify = pending;
    b.unconfirmed_boots = (uint8_t)boots;
    b.ingest_ok = ingest;
    b.max_unconfirmed_boots = NW_OTA_MAX_UNCONFIRMED_BOOTS;
    return b;
}

static nw_ota_decision_t decide(bool pending, unsigned boots, bool ingest)
{
    nw_ota_boot_t b = boot(pending, boots, ingest);
    return nw_ota_boot_decide(&b);
}

/* AC 2 (FR-D05, ADR-009): a pending image that is not confirmed within the window rolls back; a successful ingest
 * confirms it, also at the window boundary. */
static void test_rollback_decision(void)
{
    CHECK_EQ(NW_OTA_MAX_UNCONFIRMED_BOOTS, 8);
    /* not a pending image: nothing to do, whatever the counter says */
    nw_ota_boot_t idle0 = boot(false, 0, false);
    nw_ota_boot_t idle9 = boot(false, 9, false);
    CHECK_EQ(nw_ota_boot_decide(&idle0), NW_OTA_KEEP);
    CHECK_EQ(nw_ota_boot_decide(&idle9), NW_OTA_KEEP);
    CHECK_EQ(nw_ota_boot_decide(&(nw_ota_boot_t){ .pending_verify = false, .unconfirmed_boots = 0, .ingest_ok = true,
                                                  .max_unconfirmed_boots = 8 }), NW_OTA_KEEP);
    /* pending, inside the window, no ingest yet: wait for the next boot */
    CHECK_EQ(decide(true, 1, false), NW_OTA_WAIT);
    CHECK_EQ(decide(true, 7, false), NW_OTA_WAIT);
    /* window used up (8th boot) without an ingest: roll back; later boots stay rolled back */
    CHECK_EQ(decide(true, 8, false), NW_OTA_ROLLBACK);
    CHECK_EQ(decide(true, 20, false), NW_OTA_ROLLBACK);
    /* a successful ingest confirms the image, in the window and at the boundary */
    CHECK_EQ(decide(true, 1, true), NW_OTA_CONFIRM);
    CHECK_EQ(decide(true, 3, true), NW_OTA_CONFIRM);
    CHECK_EQ(decide(true, 8, true), NW_OTA_CONFIRM);
    /* a window of one boot: the first unconfirmed boot already rolls back */
    nw_ota_boot_t one = { true, 1, false, 1 };
    CHECK_EQ(nw_ota_boot_decide(&one), NW_OTA_ROLLBACK);
    /* FR-D05 says "rolls back to the previous slot": the slot switch itself is in the ESP-IDF adapter (not built here) */
}

/* C1 (architect review of PR #153): the install gate takes the hash result as a required input and refuses install on
 * anything but a MATCH. The mismatch case is called through the real hash check, not with a hand-set enum value. */
static void test_install_gate(void)
{
    uint8_t exp[NW_OTA_SHA256_LEN];
    CHECK(nw_ota_parse_sha256_hex(HEX_MOCK, 64, exp));
    /* the unset value (0) refuses */
    CHECK(!nw_ota_may_install(NW_OTA_HASH_NOT_CHECKED));
    /* a mismatch from the decision inputs: wrong content, and a NULL expected digest */
    char flipped[sizeof MOCK_IMG];
    memcpy(flipped, MOCK_IMG, sizeof MOCK_IMG);
    flipped[0] ^= 0x01;
    nw_ota_hash_result_t bad = nw_ota_hash_check(flipped, strlen(flipped), exp);
    CHECK_EQ(bad, NW_OTA_HASH_MISMATCH);
    CHECK(!nw_ota_may_install(bad));
    CHECK(!nw_ota_may_install(nw_ota_hash_check(MOCK_IMG, strlen(MOCK_IMG), NULL)));
    /* the exact image is the only path to install */
    nw_ota_hash_result_t good = nw_ota_hash_check(MOCK_IMG, strlen(MOCK_IMG), exp);
    CHECK_EQ(good, NW_OTA_HASH_MATCH);
    CHECK(nw_ota_may_install(good));
    /* the gate and the image check agree on a truncated image */
    CHECK(!nw_ota_may_install(nw_ota_hash_check(MOCK_IMG, strlen(MOCK_IMG) - 1, exp)));
}

int main(void)
{
    test_sha256_vectors();
    test_hex_parse();
    test_image_check();
    test_install_gate();
    test_rollback_decision();
    printf("test_ota: %d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}

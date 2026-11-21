/* OTA image check and rollback decision (task 4.F4, FR-D05, ADR-009). Pure C. See nw_ota.h. */
#include "nw_ota.h"
#include <string.h>

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
};

static uint32_t rotr(uint32_t x, unsigned n)
{
    return (x >> n) | (x << (32u - n));
}

static void compress(uint32_t h[8], const uint8_t blk[64])
{
    uint32_t w[64];
    for (unsigned i = 0; i < 16; i++) {
        w[i] = ((uint32_t)blk[4 * i] << 24) | ((uint32_t)blk[4 * i + 1] << 16) |
               ((uint32_t)blk[4 * i + 2] << 8) | (uint32_t)blk[4 * i + 3];
    }
    for (unsigned i = 16; i < 64; i++) {
        uint32_t s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
    for (unsigned i = 0; i < 64; i++) {
        uint32_t S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        uint32_t ch = (e & f) ^ (~e & g);
        uint32_t t1 = hh + S1 + ch + K[i] + w[i];
        uint32_t S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t t2 = S0 + maj;
        hh = g; g = f; f = e; e = d + t1;
        d = c; c = b; b = a; a = t1 + t2;
    }
    h[0] += a; h[1] += b; h[2] += c; h[3] += d;
    h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
}

void nw_sha256_init(nw_sha256_t *c)
{
    static const uint32_t iv[8] = {
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
    };
    memcpy(c->h, iv, sizeof iv);
    c->bytes = 0;
    c->buf_len = 0;
}

void nw_sha256_update(nw_sha256_t *c, const void *data, size_t len)
{
    const uint8_t *p = data;
    c->bytes += len;
    while (len > 0) {
        size_t take = 64u - c->buf_len;
        if (take > len) take = len;
        memcpy(c->buf + c->buf_len, p, take);
        c->buf_len = (uint8_t)(c->buf_len + take);
        p += take;
        len -= take;
        if (c->buf_len == 64) {
            compress(c->h, c->buf);
            c->buf_len = 0;
        }
    }
}

void nw_sha256_final(nw_sha256_t *c, uint8_t out[NW_OTA_SHA256_LEN])
{
    uint8_t blk[128];
    uint64_t bits = c->bytes * 8u;
    size_t n = c->buf_len;
    size_t total = (n < 56) ? 64 : 128;
    memcpy(blk, c->buf, n);
    blk[n] = 0x80;
    memset(blk + n + 1, 0, total - n - 1 - 8);
    for (unsigned i = 0; i < 8; i++) {
        blk[total - 8 + i] = (uint8_t)(bits >> (56 - 8 * i));
    }
    compress(c->h, blk);
    if (total == 128) compress(c->h, blk + 64);
    for (unsigned i = 0; i < 8; i++) {
        out[4 * i] = (uint8_t)(c->h[i] >> 24);
        out[4 * i + 1] = (uint8_t)(c->h[i] >> 16);
        out[4 * i + 2] = (uint8_t)(c->h[i] >> 8);
        out[4 * i + 3] = (uint8_t)c->h[i];
    }
}

static int hexval(char ch)
{
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
    if (ch >= 'A' && ch <= 'F') return ch - 'A' + 10;
    return -1;
}

bool nw_ota_parse_sha256_hex(const char *hex, size_t len, uint8_t out[NW_OTA_SHA256_LEN])
{
    uint8_t tmp[NW_OTA_SHA256_LEN];
    if (!hex || len != NW_OTA_SHA256_HEX_LEN) return false;
    for (size_t i = 0; i < NW_OTA_SHA256_LEN; i++) {
        int hi = hexval(hex[2 * i]);
        int lo = hexval(hex[2 * i + 1]);
        if (hi < 0 || lo < 0) return false;
        tmp[i] = (uint8_t)((hi << 4) | lo);
    }
    memcpy(out, tmp, NW_OTA_SHA256_LEN);
    return true;
}

bool nw_ota_digest_equal(const uint8_t a[NW_OTA_SHA256_LEN], const uint8_t b[NW_OTA_SHA256_LEN])
{
    uint8_t diff = 0;
    for (size_t i = 0; i < NW_OTA_SHA256_LEN; i++) {
        diff |= (uint8_t)(a[i] ^ b[i]);
    }
    return diff == 0;
}

bool nw_ota_image_ok(const void *img, size_t len, const uint8_t expected[NW_OTA_SHA256_LEN])
{
    nw_sha256_t c;
    uint8_t digest[NW_OTA_SHA256_LEN];
    if (!expected || (!img && len > 0)) return false;
    nw_sha256_init(&c);
    nw_sha256_update(&c, img, len);
    nw_sha256_final(&c, digest);
    return nw_ota_digest_equal(digest, expected);
}

nw_ota_hash_result_t nw_ota_hash_check(const void *img, size_t len, const uint8_t expected[NW_OTA_SHA256_LEN])
{
    return nw_ota_image_ok(img, len, expected) ? NW_OTA_HASH_MATCH : NW_OTA_HASH_MISMATCH;
}

bool nw_ota_may_install(nw_ota_hash_result_t hash)
{
    return hash == NW_OTA_HASH_MATCH;
}

nw_ota_decision_t nw_ota_boot_decide(const nw_ota_boot_t *b)
{
    if (!b->pending_verify) return NW_OTA_KEEP;
    if (b->ingest_ok) return NW_OTA_CONFIRM;
    if (b->unconfirmed_boots >= b->max_unconfirmed_boots) return NW_OTA_ROLLBACK;
    return NW_OTA_WAIT;
}

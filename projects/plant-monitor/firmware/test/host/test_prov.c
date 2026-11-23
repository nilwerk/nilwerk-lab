/* Host tests for the provisioning protocol and state machine (task 4.F2). FR-D03, FR-D07, FR-D09, NFR-03, NFR-06, A-013. No hardware. */
#include <stdio.h>
#include <string.h>
#include "nwtest.h"
#include "nw_prov.h"

int nwtest_failed, nwtest_checked;

#define TOKEN "k3J9aB2cD4eF6gH8iJ0kLm"   /* 22 chars base64url */
#define CLAIM_JSON "{\"v\":1,\"name\":\"Basil on the sill\",\"claim_token\":\"" TOKEN "\"}"
#define HWID "nw-a1b2c3d4e5f6"

/* ---------- fakes ---------- */
typedef struct {
    bool ble_on; int ble_calls;
    int wifi_calls; char wifi_ssid[40], wifi_pass[70];
    int claim_calls; char claim_tok[30], claim_name[330];
    bool stored; nw_prov_record_t rec; int save_calls, erase_calls; int fail_save, fail_erase, fail_load;
} fake_t;

static void f_ble(void *c, bool on) { fake_t *f = c; f->ble_on = on; f->ble_calls++; }
static void f_wifi(void *c, const char *s, const char *p) { fake_t *f = c; f->wifi_calls++; snprintf(f->wifi_ssid, sizeof f->wifi_ssid, "%s", s); snprintf(f->wifi_pass, sizeof f->wifi_pass, "%s", p); }
static void f_claim(void *c, const char *t, const char *n) { fake_t *f = c; f->claim_calls++; snprintf(f->claim_tok, sizeof f->claim_tok, "%s", t); snprintf(f->claim_name, sizeof f->claim_name, "%s", n); }
static int f_load(void *c, nw_prov_record_t *o) { fake_t *f = c; if (f->fail_load) return -1; if (!f->stored) return 1; *o = f->rec; return 0; }
static int f_save(void *c, const nw_prov_record_t *r) { fake_t *f = c; f->save_calls++; if (f->fail_save) return -1; f->rec = *r; f->stored = true; return 0; }
static int f_erase(void *c) { fake_t *f = c; f->erase_calls++; if (f->fail_erase) return -1; f->stored = false; memset(&f->rec, 0, sizeof f->rec); return 0; }

static void mk(nw_prov_t *p, fake_t *f)
{
    memset(f, 0, sizeof *f);
    nw_prov_ops_t ops = {.ctx = f, .ble_set = f_ble, .wifi_connect = f_wifi, .claim_post = f_claim,
                         .store = {f_load, f_save, f_erase}, .store_ctx = f};
    nw_prov_init(p, &ops);
}
static void status(nw_prov_t *p, char *b, size_t n) { CHECK(nw_prov_status_json(p, b, n) > 0); }

/* drive to SESSION via first boot + good handshake */
static void to_session(nw_prov_t *p, fake_t *f, uint32_t t)
{
    mk(p, f);
    CHECK_EQ(nw_prov_boot(p, 0, t), NW_PROV_OK);
    CHECK_EQ(nw_prov_on_handshake(p, true, t), NW_PROV_OK);
    CHECK_EQ(p->state, NW_PROV_S_SESSION);
}
static void send_config_and_claim(nw_prov_t *p, uint32_t t)
{
    char rep[64];
    CHECK_EQ(nw_prov_on_wifi_config(p, "HomeNet-2G", "correct-horse", t), NW_PROV_OK);
    CHECK_EQ(nw_prov_on_claim(p, CLAIM_JSON, strlen(CLAIM_JSON), rep, sizeof rep, t), NW_PROV_OK);
    CHECK_EQ(nw_prov_on_apply(p, t), NW_PROV_OK);
}

/* ---------- proto ---------- */
static int claim(const char *j, nw_prov_claim_req_t *o) { return nw_prov_parse_claim(j, strlen(j), o); }

static void test_claim_parse_ok(void)
{
    nw_prov_claim_req_t r;
    CHECK_EQ(claim(CLAIM_JSON, &r), NW_PROV_OK);               /* the example of ble-provisioning.md section 2 */
    CHECK(!strcmp(r.name, "Basil on the sill")); CHECK(!strcmp(r.claim_token, TOKEN));
    CHECK_EQ(claim(" {\n \"claim_token\" : \"" TOKEN "\" ,\"name\":\"x\",\"v\":1 } ", &r), NW_PROV_OK); /* key order, whitespace */
    CHECK_EQ(claim("{\"v\":1,\"name\":\"x\",\"claim_token\":\"" TOKEN "\",\"future\":true,\"n\":-1.5e3,\"s\":\"y\"}", &r), NW_PROV_OK); /* unknown scalars ignored */
    CHECK_EQ(claim("{\"v\":1,\"a_very_long_unknown_key_name\":0,\"name\":\"x\",\"claim_token\":\"" TOKEN "\"}", &r), NW_PROV_OK);
}
static void test_claim_name_rules(void)
{
    nw_prov_claim_req_t r; char j[1200];
    const char *pre = "{\"v\":1,\"claim_token\":\"" TOKEN "\",\"name\":\"";
    snprintf(j, sizeof j, "%s\"}", pre);                       CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* empty: min 1 */
    char n80[81]; memset(n80, 'a', 80); n80[80] = 0;
    snprintf(j, sizeof j, "%s%s\"}", pre, n80);                CHECK_EQ(claim(j, &r), NW_PROV_OK);              /* 80: max */
    char n81[82]; memset(n81, 'a', 81); n81[81] = 0;
    snprintf(j, sizeof j, "%s%s\"}", pre, n81);                CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* 81: too long */
    /* 80 characters that are 3 bytes each (240 bytes) are fine: the limit counts characters, not bytes */
    char e80[400] = ""; for (int i = 0; i < 80; i++) strcat(e80, "\xE2\x82\xAC");   /* euro sign */
    snprintf(j, sizeof j, "%s%s\"}", pre, e80);                CHECK_EQ(claim(j, &r), NW_PROV_OK); CHECK_EQ(strlen(r.name), 240);
    char e81[400]; strcpy(e81, e80); strcat(e81, "\xE2\x82\xAC");
    snprintf(j, sizeof j, "%s%s\"}", pre, e81);                CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST);
    snprintf(j, sizeof j, "%sFarn \xC3\xBC" "ber\xF0\x9F\x8C\xB1\"}", pre); CHECK_EQ(claim(j, &r), NW_PROV_OK);       /* umlaut + 4-byte emoji */
    snprintf(j, sizeof j, "%sbad\xC0\xAF\"}", pre);            CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* overlong UTF-8 */
    snprintf(j, sizeof j, "%sbad\xED\xA0\x80\"}", pre);        CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* encoded surrogate */
    snprintf(j, sizeof j, "%sbad\xED\xBF\xBF\"}", pre);        CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* U+DFFF, last surrogate */
    snprintf(j, sizeof j, "%sbad\xE2\x82\"}", pre);            CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* truncated sequence */
    snprintf(j, sizeof j, "%sa\\u00fcb\"}", pre);              CHECK_EQ(claim(j, &r), NW_PROV_OK); CHECK(!strcmp(r.name, "a\xC3\xBC" "b")); /* \u escape */
    snprintf(j, sizeof j, "%s\\ud83c\\udf31\"}", pre);         CHECK_EQ(claim(j, &r), NW_PROV_OK); CHECK(!strcmp(r.name, "\xF0\x9F\x8C\xB1")); /* surrogate pair */
    snprintf(j, sizeof j, "%s\\ud83c x\"}", pre);              CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* lone high surrogate */
    snprintf(j, sizeof j, "%s\\udf31\"}", pre);                CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* lone low surrogate */
    snprintf(j, sizeof j, "%sa\\u0000b\"}", pre);              CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* NUL via escape */
    snprintf(j, sizeof j, "%sa\\nb\"}", pre);                  CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* control char via escape */
    snprintf(j, sizeof j, "%sa\tb\"}", pre);                   CHECK_EQ(claim(j, &r), NW_PROV_ERR_BAD_REQUEST); /* raw control char */
    snprintf(j, sizeof j, "%sa\\\"b\\\\\"}", pre);             CHECK_EQ(claim(j, &r), NW_PROV_OK); CHECK(!strcmp(r.name, "a\"b\\"));
}
static void test_claim_token_rules(void)
{
    nw_prov_claim_req_t r;
    CHECK(nw_prov_valid_claim_token(TOKEN)); CHECK(nw_prov_valid_claim_token("AAAAAAAAAAAAAAAAAAAA-_"));
    CHECK(!nw_prov_valid_claim_token("k3J9aB2cD4eF6gH8iJ0kL"));      /* 21 */
    CHECK(!nw_prov_valid_claim_token("k3J9aB2cD4eF6gH8iJ0kLmN"));    /* 23 */
    CHECK(!nw_prov_valid_claim_token("k3J9aB2cD4eF6gH8iJ0k+m"));     /* '+' is base64, not base64url */
    CHECK(!nw_prov_valid_claim_token("k3J9aB2cD4eF6gH8iJ0kL="));     /* padding */
    CHECK(!nw_prov_valid_claim_token(NULL));
    CHECK_EQ(claim("{\"v\":1,\"name\":\"x\",\"claim_token\":\"short\"}", &r), NW_PROV_ERR_BAD_REQUEST);
    CHECK_EQ(claim("{\"v\":1,\"name\":\"x\"}", &r), NW_PROV_ERR_BAD_REQUEST);                    /* missing token */
    CHECK_EQ(claim("{\"v\":1,\"claim_token\":\"" TOKEN "\"}", &r), NW_PROV_ERR_BAD_REQUEST);    /* missing name */
}
static void test_claim_malformed(void)
{
    nw_prov_claim_req_t r;
    const char *bad[] = {
        "", "{}", "[]", "null", "{", "{\"v\":1,\"name\":\"x\",\"claim_token\":\"" TOKEN "\"",              /* unterminated */
        "{\"v\":2,\"name\":\"x\",\"claim_token\":\"" TOKEN "\"}",                                           /* wrong version */
        "{\"v\":\"1\",\"name\":\"x\",\"claim_token\":\"" TOKEN "\"}", "{\"v\":10,\"name\":\"x\",\"claim_token\":\"" TOKEN "\"}",
        "{\"v\":1.0,\"name\":\"x\",\"claim_token\":\"" TOKEN "\"}",
        "{\"name\":\"x\",\"claim_token\":\"" TOKEN "\"}",                                                   /* no v */
        "{\"v\":1,\"v\":1,\"name\":\"x\",\"claim_token\":\"" TOKEN "\"}",                                   /* duplicate key */
        "{\"v\":1,\"name\":\"x\",\"name\":\"y\",\"claim_token\":\"" TOKEN "\"}",
        "{\"v\":1,\"name\":\"x\",\"claim_token\":\"" TOKEN "\"} x",                                        /* trailing garbage */
        "{\"v\":1,\"name\":\"x\",\"claim_token\":\"" TOKEN "\",}",                                         /* trailing comma */
        "{\"v\":1,\"name\":\"x\",\"claim_token\":\"" TOKEN "\",\"o\":{\"a\":1}}",                          /* nested */
        "{\"v\":1,\"name\":\"x\",\"claim_token\":\"" TOKEN "\",\"o\":[1]}",
        "{\"v\":1,\"name\":5,\"claim_token\":\"" TOKEN "\"}",                                               /* wrong type */
        "{\"v\":1 \"name\":\"x\",\"claim_token\":\"" TOKEN "\"}",                                           /* missing comma */
        "{v:1,\"name\":\"x\",\"claim_token\":\"" TOKEN "\"}",                                               /* unquoted key */
    };
    for (size_t i = 0; i < sizeof bad / sizeof *bad; i++) { int e = claim(bad[i], &r); if (e != NW_PROV_ERR_BAD_REQUEST) printf("  case %zu\n", i); CHECK_EQ(e, NW_PROV_ERR_BAD_REQUEST); }
    CHECK_EQ(nw_prov_parse_claim(NULL, 0, &r), NW_PROV_ERR_ARG);
    char big[2050]; memset(big, ' ', sizeof big);                                  /* literal 2 KiB: contract number, not the macro */ memcpy(big, CLAIM_JSON, strlen(CLAIM_JSON));
    CHECK_EQ(nw_prov_parse_claim(big, 2048, &r), NW_PROV_OK);          /* exactly 2 KiB incl. padding: ok */
    CHECK_EQ(nw_prov_parse_claim(big, 2049, &r), NW_PROV_ERR_BAD_REQUEST); /* 2 KiB + 1 */
    /* no NUL terminator needed and no over-read: pass an exact-length buffer */
    char exact[sizeof CLAIM_JSON - 1]; memcpy(exact, CLAIM_JSON, sizeof exact);
    CHECK_EQ(nw_prov_parse_claim(exact, sizeof exact, &r), NW_PROV_OK);
    for (size_t cut = 0; cut < sizeof exact; cut++) CHECK(nw_prov_parse_claim(exact, cut, &r) != NW_PROV_OK); /* every truncation is rejected */
}
static void test_wifi_rules(void)
{
    CHECK(nw_prov_valid_ssid("a")); CHECK(nw_prov_valid_ssid("12345678901234567890123456789012")); /* 32 */
    CHECK(!nw_prov_valid_ssid("")); CHECK(!nw_prov_valid_ssid("123456789012345678901234567890123")); CHECK(!nw_prov_valid_ssid(NULL));
    CHECK(nw_prov_valid_passphrase("")); CHECK(nw_prov_valid_passphrase("12345678"));              /* open network or WPA2 8-63 */
    CHECK(!nw_prov_valid_passphrase("1234567"));
    char p63[64]; memset(p63, 'x', 63); p63[63] = 0; CHECK(nw_prov_valid_passphrase(p63));
    char p64[65]; memset(p64, 'x', 64); p64[64] = 0; CHECK(!nw_prov_valid_passphrase(p64)); CHECK(!nw_prov_valid_passphrase(NULL));
}
static void test_adv_name_and_uuid(void)
{
    char n[16];
    CHECK_EQ(nw_prov_adv_name("nw-a1b2c3d4e5f6", n, sizeof n), 9); CHECK(!strcmp(n, "NW-d4e5f6"));   /* contract example: nw-... -> NW-d4e5f6 */
    CHECK_EQ(nw_prov_adv_name("nw-a1b2c3d4e5f6", n, 9), NW_PROV_ERR_TOO_SMALL);
    CHECK_EQ(nw_prov_adv_name("nw-A1B2C3D4E5F6", n, sizeof n), NW_PROV_ERR_ARG);                      /* upper case is not a valid hw_id */
    CHECK_EQ(nw_prov_adv_name("nw-a1b2c3d4e5f", n, sizeof n), NW_PROV_ERR_ARG);
    CHECK_EQ(nw_prov_adv_name("xx-a1b2c3d4e5f6", n, sizeof n), NW_PROV_ERR_ARG);
    CHECK_EQ(strlen(NW_PROV_SERVICE_UUID), 36);
}
static void test_replies_golden(void)
{
    char b[96];
    CHECK(nw_prov_build_claim_reply(b, sizeof b, true) > 0);  CHECK(!strcmp(b, "{\"v\":1,\"ok\":true}"));
    CHECK(nw_prov_build_claim_reply(b, sizeof b, false) > 0); CHECK(!strcmp(b, "{\"v\":1,\"ok\":false,\"error\":\"bad_request\"}"));
    CHECK(nw_prov_build_status(b, sizeof b, NW_PROV_ST_WIFI_CONNECTING, NW_PROV_REASON_NONE) > 0); CHECK(!strcmp(b, "{\"v\":1,\"state\":\"wifi_connecting\",\"reason\":null}"));
    CHECK(nw_prov_build_status(b, sizeof b, NW_PROV_ST_WIFI_FAILED, NW_PROV_REASON_NO_AP) > 0);    CHECK(!strcmp(b, "{\"v\":1,\"state\":\"wifi_failed\",\"reason\":\"no_ap\"}"));
    CHECK_EQ(nw_prov_build_claim_reply(b, 8, true), NW_PROV_ERR_TOO_SMALL);
    CHECK_EQ(nw_prov_build_status(b, 10, NW_PROV_ST_CLAIMED, NW_PROV_REASON_NONE), NW_PROV_ERR_TOO_SMALL);
    /* every state/reason string is the one in the contract list, and each reason fits its state */
    CHECK(!strcmp(nw_prov_state_str(NW_PROV_ST_CLAIMING), "claiming")); CHECK(!strcmp(nw_prov_state_str(NW_PROV_ST_CLAIMED), "claimed"));
    CHECK(!strcmp(nw_prov_state_str(NW_PROV_ST_CLAIM_FAILED), "claim_failed"));
    CHECK(!strcmp(nw_prov_reason_str(NW_PROV_REASON_AUTH), "auth")); CHECK(!strcmp(nw_prov_reason_str(NW_PROV_REASON_TIMEOUT), "timeout"));
    CHECK(!strcmp(nw_prov_reason_str(NW_PROV_REASON_CLAIM_TOKEN_INVALID), "claim_token_invalid"));
    CHECK(!strcmp(nw_prov_reason_str(NW_PROV_REASON_DEVICE_OWNED), "device_owned"));
    CHECK(!strcmp(nw_prov_reason_str(NW_PROV_REASON_NETWORK), "network")); CHECK(!strcmp(nw_prov_reason_str(NW_PROV_REASON_SERVER), "server"));
}

/* ---------- state machine ---------- */
static void test_first_boot_enters_setup(void)               /* FR-D03 */
{
    nw_prov_t p; fake_t f; mk(&p, &f); char s[96];
    CHECK_EQ(nw_prov_boot(&p, 0, 1000), NW_PROV_OK);
    CHECK_EQ(p.state, NW_PROV_S_ADVERTISING); CHECK(f.ble_on); CHECK(nw_prov_in_setup(&p)); CHECK_EQ(f.erase_calls, 0);
    status(&p, s, sizeof s); CHECK(!strcmp(s, "{\"v\":1,\"state\":\"idle\",\"reason\":null}"));
}
static void test_normal_boot_keeps_ble_off(void)             /* FR-D09 */
{
    nw_prov_t p; fake_t f; mk(&p, &f); f.stored = true;
    CHECK_EQ(nw_prov_boot(&p, 0, 0), NW_PROV_OK);
    CHECK_EQ(p.state, NW_PROV_S_NORMAL); CHECK(!f.ble_on); CHECK(!nw_prov_in_setup(&p));
    CHECK_EQ(nw_prov_boot(&p, NW_PROV_BUTTON_SETUP_MS - 1, 0), NW_PROV_OK); CHECK_EQ(p.state, NW_PROV_S_NORMAL); /* short press: nothing */
    CHECK(f.stored);
    /* every setup event is refused outside setup mode */
    char rep[64];
    CHECK_EQ(nw_prov_on_handshake(&p, true, 0), NW_PROV_ERR_STATE);
    CHECK_EQ(nw_prov_on_wifi_config(&p, "a", "", 0), NW_PROV_ERR_STATE);
    CHECK_EQ(nw_prov_on_claim(&p, CLAIM_JSON, strlen(CLAIM_JSON), rep, sizeof rep, 0), NW_PROV_ERR_STATE);
    CHECK(strstr(rep, "\"ok\":false"));
    CHECK_EQ(nw_prov_on_apply(&p, 0), NW_PROV_ERR_STATE);
}
static void test_button_hold_enters_setup_keeps_record(void) /* FR-D03 button */
{
    nw_prov_t p; fake_t f; mk(&p, &f); f.stored = true; strcpy(f.rec.ssid, "Old");
    CHECK_EQ(nw_prov_boot(&p, NW_PROV_BUTTON_SETUP_MS, 0), NW_PROV_OK);
    CHECK_EQ(p.state, NW_PROV_S_ADVERTISING); CHECK(f.ble_on); CHECK(f.stored); CHECK_EQ(f.erase_calls, 0);  /* old credentials stay until a claim succeeds */
}
static void test_factory_reset_wipes_then_setup(void)        /* FR-D07 */
{
    nw_prov_t p; fake_t f; mk(&p, &f); f.stored = true; strcpy(f.rec.ssid, "Old");
    CHECK_EQ(nw_prov_boot(&p, NW_PROV_BUTTON_RESET_MS, 0), NW_PROV_OK);
    CHECK(!f.stored); CHECK_EQ(f.erase_calls, 1); CHECK_EQ(p.state, NW_PROV_S_ADVERTISING); CHECK(f.ble_on);
    /* erase failure: do not enter setup pretending the wipe happened */
    mk(&p, &f); f.stored = true; f.fail_erase = 1;
    CHECK_EQ(nw_prov_boot(&p, NW_PROV_BUTTON_RESET_MS, 0), NW_PROV_ERR_STORE); CHECK_EQ(p.state, NW_PROV_S_NORMAL); CHECK(!f.ble_on);
    /* run-time gestures */
    mk(&p, &f); f.stored = true; p.state = NW_PROV_S_NORMAL;
    nw_prov_button(&p, NW_PROV_BUTTON_SETUP_MS - 1, 5); CHECK_EQ(p.state, NW_PROV_S_NORMAL);
    nw_prov_button(&p, NW_PROV_BUTTON_SETUP_MS, 5); CHECK_EQ(p.state, NW_PROV_S_ADVERTISING); CHECK(f.stored);
    mk(&p, &f); f.stored = true; nw_prov_button(&p, NW_PROV_BUTTON_RESET_MS, 5); CHECK(!f.stored); CHECK_EQ(p.state, NW_PROV_S_ADVERTISING);
    mk(&p, &f); f.stored = true; f.fail_erase = 1; nw_prov_button(&p, NW_PROV_BUTTON_RESET_MS, 5); CHECK(f.stored); CHECK_EQ(p.state, NW_PROV_S_NORMAL);
}
static void test_storage_read_error_is_not_first_boot(void)
{
    nw_prov_t p; fake_t f; mk(&p, &f); f.stored = true; f.fail_load = 1;
    CHECK_EQ(nw_prov_boot(&p, 0, 0), NW_PROV_ERR_STORE);    /* never silently open BLE because flash could not be read */
    CHECK(!f.ble_on);
}
static void test_happy_path_and_credentials_stored_on_device_only(void)  /* A-013, NFR-06 */
{
    nw_prov_t p; fake_t f; char s[96]; to_session(&p, &f, 1000);
    send_config_and_claim(&p, 2000);
    CHECK_EQ(p.state, NW_PROV_S_WIFI_CONNECTING); CHECK_EQ(f.wifi_calls, 1);
    CHECK(!strcmp(f.wifi_ssid, "HomeNet-2G")); CHECK(!strcmp(f.wifi_pass, "correct-horse"));
    status(&p, s, sizeof s); CHECK(!strcmp(s, "{\"v\":1,\"state\":\"wifi_connecting\",\"reason\":null}"));
    CHECK_EQ(nw_prov_on_wifi_result(&p, NW_PROV_WIFI_OK, 3000), NW_PROV_OK);
    CHECK_EQ(p.state, NW_PROV_S_CLAIMING); CHECK_EQ(f.claim_calls, 1);
    CHECK(!strcmp(f.claim_tok, TOKEN)); CHECK(!strcmp(f.claim_name, "Basil on the sill"));
    status(&p, s, sizeof s); CHECK(!strcmp(s, "{\"v\":1,\"state\":\"claiming\",\"reason\":null}"));
    CHECK_EQ(f.save_calls, 0);                                              /* nothing persisted before the cloud accepted the claim */
    const char *tok = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
    CHECK_EQ(nw_prov_on_claim_result(&p, NW_PROV_CLAIM_OK, tok, 4000), NW_PROV_OK);
    CHECK_EQ(p.state, NW_PROV_S_CLAIMED); CHECK(!f.ble_on); CHECK(!nw_prov_in_setup(&p));      /* FR-D09: BLE off after claim */
    status(&p, s, sizeof s); CHECK(!strcmp(s, "{\"v\":1,\"state\":\"claimed\",\"reason\":null}"));
    CHECK_EQ(f.save_calls, 1); CHECK(f.stored);
    CHECK(!strcmp(f.rec.ssid, "HomeNet-2G")); CHECK(!strcmp(f.rec.passphrase, "correct-horse"));
    CHECK(!strcmp(f.rec.name, "Basil on the sill")); CHECK(!strcmp(f.rec.device_token, tok));
    /* RAM copies of the Wi-Fi password and the single-use claim token are gone */
    CHECK_EQ(p.pending.passphrase[0], 0); CHECK_EQ(p.pending.ssid[0], 0); CHECK_EQ(p.claim_token[0], 0); CHECK_EQ(p.pending.device_token[0], 0);
    /* next boot: record present -> normal operation, BLE off */
    nw_prov_t q; fake_t *same = &f; nw_prov_ops_t ops = p.ops; (void)same; nw_prov_init(&q, &ops);
    CHECK_EQ(nw_prov_boot(&q, 0, 0), NW_PROV_OK); CHECK_EQ(q.state, NW_PROV_S_NORMAL);
}
static void test_no_credentials_in_status_or_reply(void)    /* NFR-06: nothing secret leaves through the readable endpoints */
{
    nw_prov_t p; fake_t f; char s[96], rep[64]; to_session(&p, &f, 0);
    CHECK_EQ(nw_prov_on_wifi_config(&p, "HomeNet-2G", "correct-horse", 0), NW_PROV_OK);
    CHECK_EQ(nw_prov_on_claim(&p, CLAIM_JSON, strlen(CLAIM_JSON), rep, sizeof rep, 0), NW_PROV_OK);
    CHECK(!strstr(rep, "correct-horse") && !strstr(rep, TOKEN) && !strstr(rep, "HomeNet"));
    nw_prov_on_apply(&p, 0);
    status(&p, s, sizeof s); CHECK(!strstr(s, "correct-horse") && !strstr(s, TOKEN) && !strstr(s, "HomeNet"));
}
static void test_event_order_enforced(void)
{
    nw_prov_t p; fake_t f; char rep[64];
    mk(&p, &f); nw_prov_boot(&p, 0, 0);
    CHECK_EQ(nw_prov_on_wifi_config(&p, "HomeNet-2G", "correct-horse", 0), NW_PROV_ERR_STATE);   /* no handshake yet */
    CHECK_EQ(nw_prov_on_claim(&p, CLAIM_JSON, strlen(CLAIM_JSON), rep, sizeof rep, 0), NW_PROV_ERR_STATE);
    CHECK_EQ(nw_prov_on_apply(&p, 0), NW_PROV_ERR_STATE);
    nw_prov_on_handshake(&p, true, 0);
    CHECK_EQ(nw_prov_on_apply(&p, 0), NW_PROV_ERR_STATE);                                         /* nothing received */
    nw_prov_on_wifi_config(&p, "HomeNet-2G", "correct-horse", 0);
    CHECK_EQ(nw_prov_on_apply(&p, 0), NW_PROV_ERR_STATE);                                         /* claim missing */
    nw_prov_on_claim(&p, CLAIM_JSON, strlen(CLAIM_JSON), rep, sizeof rep, 0);
    CHECK_EQ(nw_prov_on_wifi_result(&p, NW_PROV_WIFI_OK, 0), NW_PROV_ERR_STATE);                  /* not connecting yet */
    CHECK_EQ(nw_prov_on_claim_result(&p, NW_PROV_CLAIM_OK, "x", 0), NW_PROV_ERR_STATE);
    CHECK_EQ(nw_prov_on_apply(&p, 0), NW_PROV_OK); CHECK_EQ(f.wifi_calls, 1);
    CHECK_EQ(nw_prov_on_apply(&p, 0), NW_PROV_ERR_STATE); CHECK_EQ(f.wifi_calls, 1);              /* second apply does not start a second join */
    CHECK_EQ(nw_prov_on_wifi_config(&p, "Other", "", 0), NW_PROV_ERR_STATE);                      /* no config changes while connecting */
}
static void test_bad_inputs_do_not_change_state(void)
{
    nw_prov_t p; fake_t f; char rep[64]; to_session(&p, &f, 0);
    CHECK_EQ(nw_prov_on_wifi_config(&p, "", "correct-horse", 0), NW_PROV_ERR_BAD_REQUEST);
    CHECK_EQ(nw_prov_on_wifi_config(&p, "HomeNet-2G", "short", 0), NW_PROV_ERR_BAD_REQUEST);
    CHECK(!p.have_wifi);
    CHECK_EQ(nw_prov_on_claim(&p, "{\"v\":1}", 7, rep, sizeof rep, 0), NW_PROV_ERR_BAD_REQUEST);
    CHECK(!strcmp(rep, "{\"v\":1,\"ok\":false,\"error\":\"bad_request\"}")); CHECK(!p.have_claim);
    CHECK_EQ(p.state, NW_PROV_S_SESSION);
    CHECK_EQ(nw_prov_on_wifi_config(&p, "OpenCafe", "", 0), NW_PROV_OK);                          /* open network is allowed */
    CHECK_EQ(nw_prov_on_claim(&p, CLAIM_JSON, strlen(CLAIM_JSON), rep, 8, 0), NW_PROV_ERR_TOO_SMALL); /* reply buffer too small is reported */
}
static void test_wifi_failures_retry_in_same_setup(void)    /* ble-provisioning.md section 2: wifi_failed keeps setup open */
{
    nw_prov_wifi_result_t rs[] = {NW_PROV_WIFI_AUTH, NW_PROV_WIFI_NO_AP, NW_PROV_WIFI_TIMEOUT};
    const char *want[] = {"auth", "no_ap", "timeout"};
    for (int i = 0; i < 3; i++) {
        nw_prov_t p; fake_t f; char s[96], rep[64]; to_session(&p, &f, 0); send_config_and_claim(&p, 100);
        CHECK_EQ(nw_prov_on_wifi_result(&p, rs[i], 200), NW_PROV_OK);
        status(&p, s, sizeof s); CHECK(strstr(s, "\"state\":\"wifi_failed\"") && strstr(s, want[i]));
        CHECK(f.ble_on); CHECK(nw_prov_in_setup(&p)); CHECK_EQ(p.state, NW_PROV_S_SESSION); CHECK_EQ(f.save_calls, 0);
        CHECK_EQ(p.pending.passphrase[0], 0);                                                      /* failed password not kept in RAM */
        CHECK(p.have_claim);                                                                       /* claim token still valid for the retry */
        CHECK_EQ(nw_prov_on_apply(&p, 250), NW_PROV_ERR_STATE);                                    /* the failed SSID/password is not reused silently */
        CHECK_EQ(nw_prov_on_wifi_config(&p, "HomeNet-2G", "correct-horse", 300), NW_PROV_OK);
        CHECK_EQ(nw_prov_on_apply(&p, 300), NW_PROV_OK); CHECK_EQ(f.wifi_calls, 2);
        CHECK_EQ(nw_prov_on_wifi_result(&p, NW_PROV_WIFI_OK, 400), NW_PROV_OK);
        CHECK_EQ(nw_prov_on_claim_result(&p, NW_PROV_CLAIM_OK, "t", 500), NW_PROV_OK); CHECK_EQ(p.state, NW_PROV_S_CLAIMED);
        (void)rep;
    }
}
static void test_claim_failures_map_to_reasons_and_retry(void)
{
    nw_prov_claim_result_t rs[] = {NW_PROV_CLAIM_TOKEN_INVALID, NW_PROV_CLAIM_DEVICE_OWNED, NW_PROV_CLAIM_NETWORK, NW_PROV_CLAIM_SERVER};
    const char *want[] = {"claim_token_invalid", "device_owned", "network", "server"};
    for (int i = 0; i < 4; i++) {
        nw_prov_t p; fake_t f; char s[96], rep[64]; to_session(&p, &f, 0); send_config_and_claim(&p, 1);
        nw_prov_on_wifi_result(&p, NW_PROV_WIFI_OK, 2);
        CHECK_EQ(nw_prov_on_claim_result(&p, rs[i], NULL, 3), NW_PROV_OK);
        status(&p, s, sizeof s); CHECK(strstr(s, "\"state\":\"claim_failed\"") && strstr(s, want[i]));
        CHECK(f.ble_on); CHECK_EQ(f.save_calls, 0); CHECK(!f.stored); CHECK_EQ(p.claim_token[0], 0);   /* a used/refused token is not kept */
        CHECK_EQ(nw_prov_on_apply(&p, 4), NW_PROV_ERR_STATE);                                      /* needs a fresh token first */
        CHECK_EQ(nw_prov_on_claim(&p, CLAIM_JSON, strlen(CLAIM_JSON), rep, sizeof rep, 5), NW_PROV_OK);
        CHECK_EQ(nw_prov_on_wifi_config(&p, "HomeNet-2G", "correct-horse", 5), NW_PROV_OK);
        CHECK_EQ(nw_prov_on_apply(&p, 6), NW_PROV_OK);
    }
}
static void test_claim_ok_but_flash_write_fails(void)        /* never report claimed when nothing was stored */
{
    nw_prov_t p; fake_t f; char s[96]; to_session(&p, &f, 0); send_config_and_claim(&p, 1); nw_prov_on_wifi_result(&p, NW_PROV_WIFI_OK, 2);
    f.fail_save = 1;
    CHECK_EQ(nw_prov_on_claim_result(&p, NW_PROV_CLAIM_OK, "0123", 3), NW_PROV_OK);
    status(&p, s, sizeof s); CHECK(strstr(s, "claim_failed")); CHECK(!f.stored); CHECK(f.ble_on); CHECK_EQ(p.pending.device_token[0], 0);
    /* a missing or oversized device token from the server is a server error, not a stored record */
    to_session(&p, &f, 0); send_config_and_claim(&p, 1); nw_prov_on_wifi_result(&p, NW_PROV_WIFI_OK, 2);
    CHECK_EQ(nw_prov_on_claim_result(&p, NW_PROV_CLAIM_OK, NULL, 3), NW_PROV_OK); CHECK_EQ(f.save_calls, 0);
    status(&p, s, sizeof s); CHECK(strstr(s, "\"reason\":\"server\""));
    char big[80]; memset(big, 'a', 79); big[79] = 0;
    to_session(&p, &f, 0); send_config_and_claim(&p, 1); nw_prov_on_wifi_result(&p, NW_PROV_WIFI_OK, 2);
    CHECK_EQ(nw_prov_on_claim_result(&p, NW_PROV_CLAIM_OK, big, 3), NW_PROV_OK); CHECK_EQ(f.save_calls, 0);
}
static void test_five_failed_handshakes_close_setup(void)    /* ADR-011 / ble-provisioning.md section 1 */
{
    nw_prov_t p; fake_t f; mk(&p, &f); nw_prov_boot(&p, 0, 0);
    for (int i = 1; i <= 4; i++) { CHECK_EQ(nw_prov_on_handshake(&p, false, (uint32_t)i), NW_PROV_OK); CHECK_EQ(p.state, NW_PROV_S_ADVERTISING); CHECK(f.ble_on); }
    CHECK_EQ(nw_prov_on_handshake(&p, false, 5), NW_PROV_OK);
    CHECK_EQ(p.state, NW_PROV_S_CLOSED); CHECK(!f.ble_on); CHECK(!nw_prov_in_setup(&p));
    CHECK_EQ(nw_prov_on_handshake(&p, true, 6), NW_PROV_ERR_STATE);                              /* even the right code is refused now */
    nw_prov_button(&p, NW_PROV_BUTTON_SETUP_MS, 7);                                              /* button restarts it, counter reset */
    CHECK_EQ(p.state, NW_PROV_S_ADVERTISING); CHECK(f.ble_on); CHECK_EQ(p.failed_handshakes, 0);
}
static void test_good_handshake_does_not_reset_failure_count(void)
{
    nw_prov_t p; fake_t f; mk(&p, &f); nw_prov_boot(&p, 0, 0);
    for (int i = 0; i < 4; i++) nw_prov_on_handshake(&p, false, 1);
    CHECK_EQ(nw_prov_on_handshake(&p, true, 2), NW_PROV_OK); CHECK_EQ(p.state, NW_PROV_S_SESSION);
    CHECK_EQ(nw_prov_on_handshake(&p, false, 3), NW_PROV_OK);                                    /* 5th failure overall closes setup */
    CHECK_EQ(p.state, NW_PROV_S_CLOSED);
}
static void test_failed_handshake_drops_session_secrets(void)
{
    nw_prov_t p; fake_t f; char rep[64]; to_session(&p, &f, 0);
    nw_prov_on_wifi_config(&p, "HomeNet-2G", "correct-horse", 1); nw_prov_on_claim(&p, CLAIM_JSON, strlen(CLAIM_JSON), rep, sizeof rep, 1);
    nw_prov_on_handshake(&p, false, 2);                                                           /* a new, failed handshake attempt */
    CHECK_EQ(p.state, NW_PROV_S_ADVERTISING);
    CHECK_EQ(nw_prov_on_apply(&p, 3), NW_PROV_ERR_STATE);                                         /* cannot apply on a dropped session */
}
static void test_five_minute_limit(void)                     /* ADR-011, NFR-03 context */
{
    nw_prov_t p; fake_t f; mk(&p, &f); nw_prov_boot(&p, 0, 1000);
    nw_prov_tick(&p, 1000 + NW_PROV_SETUP_TIMEOUT_MS - 1); CHECK_EQ(p.state, NW_PROV_S_ADVERTISING); CHECK(f.ble_on);
    nw_prov_tick(&p, 1000 + NW_PROV_SETUP_TIMEOUT_MS); CHECK_EQ(p.state, NW_PROV_S_CLOSED); CHECK(!f.ble_on);
    CHECK_EQ(NW_PROV_SETUP_TIMEOUT_MS, 300000u);
    /* an event arriving after the deadline is refused even without a tick */
    mk(&p, &f); nw_prov_boot(&p, 0, 0);
    CHECK_EQ(nw_prov_on_handshake(&p, true, NW_PROV_SETUP_TIMEOUT_MS + 5), NW_PROV_ERR_STATE); CHECK_EQ(p.state, NW_PROV_S_CLOSED);
    /* session with received credentials: closing wipes them */
    to_session(&p, &f, 0); nw_prov_on_wifi_config(&p, "HomeNet-2G", "correct-horse", 10);
    nw_prov_tick(&p, NW_PROV_SETUP_TIMEOUT_MS); CHECK_EQ(p.state, NW_PROV_S_CLOSED); CHECK_EQ(p.pending.passphrase[0], 0); CHECK(!p.have_wifi);
}
static void test_bench_window_only_when_set(void)            /* bench CI image: window 60 s; production default stays 300 s */
{
    nw_prov_t p; fake_t f; mk(&p, &f); nw_prov_boot(&p, 0, 1000);
    CHECK_EQ(p.setup_window_ms, 0u);                           /* production: field unset, NW_PROV_SETUP_TIMEOUT_MS applies */
    nw_prov_tick(&p, 1000 + 60000u); CHECK_EQ(p.state, NW_PROV_S_ADVERTISING); CHECK(f.ble_on);
    mk(&p, &f); p.setup_window_ms = 60000u; nw_prov_boot(&p, 0, 1000);   /* what nw_prov_idf.c does on the bench image */
    nw_prov_tick(&p, 1000 + 60000u - 1); CHECK_EQ(p.state, NW_PROV_S_ADVERTISING); CHECK(f.ble_on);
    nw_prov_tick(&p, 1000 + 60000u); CHECK_EQ(p.state, NW_PROV_S_CLOSED); CHECK(!f.ble_on);
}
static void test_millis_wraparound(void)
{
    nw_prov_t p; fake_t f; mk(&p, &f); uint32_t start = 0xFFFFFFFFu - 1000u;
    nw_prov_boot(&p, 0, start);
    nw_prov_tick(&p, start + 299000u); CHECK_EQ(p.state, NW_PROV_S_ADVERTISING);                 /* counter wrapped meanwhile */
    nw_prov_tick(&p, start + 300000u); CHECK_EQ(p.state, NW_PROV_S_CLOSED);
}
static void test_deadline_not_enforced_in_flight_but_after_failure(void)
{
    nw_prov_t p; fake_t f; to_session(&p, &f, 0); send_config_and_claim(&p, 100);
    nw_prov_tick(&p, NW_PROV_SETUP_TIMEOUT_MS + 1); CHECK_EQ(p.state, NW_PROV_S_WIFI_CONNECTING); CHECK(f.ble_on);     /* join in flight */
    nw_prov_on_wifi_result(&p, NW_PROV_WIFI_OK, NW_PROV_SETUP_TIMEOUT_MS + 2);
    CHECK_EQ(p.state, NW_PROV_S_CLAIMING);
    nw_prov_on_claim_result(&p, NW_PROV_CLAIM_OK, "t", NW_PROV_SETUP_TIMEOUT_MS + 3);                                  /* success after the window still counts */
    CHECK_EQ(p.state, NW_PROV_S_CLAIMED);
    /* but a failure after the deadline ends setup */
    to_session(&p, &f, 0); send_config_and_claim(&p, 100);
    nw_prov_on_wifi_result(&p, NW_PROV_WIFI_AUTH, NW_PROV_SETUP_TIMEOUT_MS + 2);
    CHECK_EQ(p.state, NW_PROV_S_CLOSED); CHECK(!f.ble_on);
}
static void test_button_ignored_while_claim_in_flight(void)
{
    nw_prov_t p; fake_t f; to_session(&p, &f, 0); send_config_and_claim(&p, 1);
    nw_prov_button(&p, NW_PROV_BUTTON_RESET_MS, 2); CHECK_EQ(p.state, NW_PROV_S_WIFI_CONNECTING); CHECK_EQ(f.erase_calls, 0);
}
static void test_restart_during_setup_resets_window(void)
{
    nw_prov_t p; fake_t f; to_session(&p, &f, 0); nw_prov_on_wifi_config(&p, "HomeNet-2G", "correct-horse", 1);
    nw_prov_button(&p, NW_PROV_BUTTON_SETUP_MS, 200000u);
    CHECK_EQ(p.state, NW_PROV_S_ADVERTISING); CHECK(!p.have_wifi); CHECK_EQ(p.pending.passphrase[0], 0);
    nw_prov_tick(&p, 200000u + 299999u); CHECK_EQ(p.state, NW_PROV_S_ADVERTISING);
}
static void test_null_and_arg_guards(void)
{
    nw_prov_t p; fake_t f; mk(&p, &f); char b[8];
    CHECK_EQ(nw_prov_boot(NULL, 0, 0), NW_PROV_ERR_ARG);
    CHECK_EQ(nw_prov_build_claim_reply(NULL, 8, true), NW_PROV_ERR_ARG);
    CHECK_EQ(nw_prov_build_status(NULL, 8, NW_PROV_ST_IDLE, NW_PROV_REASON_NONE), NW_PROV_ERR_ARG);
    CHECK_EQ(nw_prov_build_status(b, 0, NW_PROV_ST_IDLE, NW_PROV_REASON_NONE), NW_PROV_ERR_TOO_SMALL);
    CHECK_EQ(nw_prov_utf8_chars("a\xC3\xBC", 3), 2); CHECK_EQ(nw_prov_utf8_chars("", 0), 0);
}

int main(void)
{
    test_claim_parse_ok(); test_claim_name_rules(); test_claim_token_rules(); test_claim_malformed(); test_wifi_rules();
    test_adv_name_and_uuid(); test_replies_golden();
    test_first_boot_enters_setup(); test_normal_boot_keeps_ble_off(); test_button_hold_enters_setup_keeps_record();
    test_factory_reset_wipes_then_setup(); test_storage_read_error_is_not_first_boot();
    test_happy_path_and_credentials_stored_on_device_only(); test_no_credentials_in_status_or_reply(); test_event_order_enforced();
    test_bad_inputs_do_not_change_state(); test_wifi_failures_retry_in_same_setup(); test_claim_failures_map_to_reasons_and_retry();
    test_claim_ok_but_flash_write_fails(); test_five_failed_handshakes_close_setup(); test_good_handshake_does_not_reset_failure_count();
    test_failed_handshake_drops_session_secrets(); test_five_minute_limit(); test_millis_wraparound(); test_bench_window_only_when_set();
    test_deadline_not_enforced_in_flight_but_after_failure(); test_button_ignored_while_claim_in_flight();
    test_restart_during_setup_resets_window(); test_null_and_arg_guards();
    printf("provisioning host tests: %d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}

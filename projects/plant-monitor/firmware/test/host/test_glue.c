/* Host tests for the glue core (task 4.F2 slice 2). Fake transport, no hardware, no ESP-IDF.
 * Each test name cites the WO glue acceptance item (Theo C2-C4 in PR #66) it proves. */
#include <stdio.h>
#include <string.h>
#include "nwtest.h"
#include "nw_prov_glue.h"

int nwtest_failed, nwtest_checked;

#define TOKEN "k3J9aB2cD4eF6gH8iJ0kLm"
#define CLAIM_JSON "{\"v\":1,\"name\":\"Basil on the sill\",\"claim_token\":\"" TOKEN "\"}"
#define HWID "nw-a1b2c3d4e5f6"
#define DEVTOK "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
#define OK200 "{\"device_id\":\"x\",\"device_token\":\"" DEVTOK "\",\"server_time\":1,\"config\":{}}"

typedef struct {
    bool ble_on; int wifi_calls, post_calls; char post_body[NW_GLUE_BODY_MAX];
    bool stored; nw_prov_record_t rec; int save_calls;
} fk_t;
static void k_ble(void *c, bool on) { ((fk_t *)c)->ble_on = on; }
static void k_wifi(void *c, const char *s, const char *p) { (void)s; (void)p; ((fk_t *)c)->wifi_calls++; }   /* never answers */
static void k_post(void *c, const char *b, size_t n) { fk_t *f = c; f->post_calls++; snprintf(f->post_body, sizeof f->post_body, "%.*s", (int)n, b); }
static int k_load(void *c, nw_prov_record_t *o) { fk_t *f = c; if (!f->stored) return 1; *o = f->rec; return 0; }
static int k_save(void *c, const nw_prov_record_t *r) { fk_t *f = c; f->save_calls++; f->rec = *r; f->stored = true; return 0; }
static int k_erase(void *c) { fk_t *f = c; f->stored = false; return 0; }

typedef struct { nw_glue_t g; nw_prov_t p; fk_t f; } rig_t;

static void rig_no_handshake(rig_t *r)
{
    memset(r, 0, sizeof *r);
    nw_glue_io_t io = {.ctx = &r->f, .ble_set = k_ble, .wifi_start = k_wifi, .http_post = k_post,
                       .store = {k_load, k_save, k_erase}, .store_ctx = &r->f};
    nw_prov_ops_t ops;
    CHECK_EQ(nw_glue_init(&r->g, &io, HWID, "0.4.2-dev", &ops), NW_PROV_OK);
    nw_prov_init(&r->p, &ops);
    nw_glue_attach(&r->g, &r->p);
    CHECK_EQ(nw_prov_boot(&r->p, 0, 0), NW_PROV_OK);
}
static void rig(rig_t *r)
{
    rig_no_handshake(r);
    CHECK_EQ(nw_prov_on_handshake(&r->p, true, 0), NW_PROV_OK);
}
static void to_wifi(rig_t *r, uint32_t t)
{
    char rep[64];
    rig(r);
    if (t > 1000000u) {                                   /* start the 5 min window at t (wrap test) */
        nw_prov_button(&r->p, NW_PROV_BUTTON_SETUP_MS, t);
        CHECK_EQ(nw_prov_on_handshake(&r->p, true, t), NW_PROV_OK);
    }
    CHECK_EQ(nw_prov_on_wifi_config(&r->p, "HomeNet-2G", "correct-horse", t), NW_PROV_OK);
    CHECK_EQ(nw_prov_on_claim(&r->p, CLAIM_JSON, strlen(CLAIM_JSON), rep, sizeof rep, t), NW_PROV_OK);
    CHECK_EQ(nw_glue_on_apply(&r->g, t), NW_PROV_OK);
}
static void to_claiming(rig_t *r, uint32_t t)
{
    to_wifi(r, t);
    CHECK_EQ(nw_glue_on_wifi_result(&r->g, NW_PROV_WIFI_OK, t + 100), NW_PROV_OK);
    CHECK_EQ(r->p.state, NW_PROV_S_CLAIMING);
}
static const char *reason(rig_t *r) { static char b[96]; nw_prov_status_json(&r->p, b, sizeof b); return b; }

/* WO glue item 1 (Theo C2): a fake that never answers must end in wifi_failed/timeout, never hang. */
static void test_item1_wifi_never_answers_ends_in_timeout(void)
{
    rig_t r; to_wifi(&r, 1000);
    CHECK_EQ(r.f.wifi_calls, 1);
    nw_glue_tick(&r.g, 1000 + NW_GLUE_WIFI_JOIN_TIMEOUT_MS - 1); CHECK_EQ(r.p.state, NW_PROV_S_WIFI_CONNECTING);   /* not early */
    nw_glue_tick(&r.g, 1000 + NW_GLUE_WIFI_JOIN_TIMEOUT_MS);
    CHECK_EQ(r.p.state, NW_PROV_S_SESSION); CHECK(strstr(reason(&r), "\"wifi_failed\"") && strstr(reason(&r), "\"timeout\""));
    nw_glue_tick(&r.g, 1000 + 5 * NW_GLUE_WIFI_JOIN_TIMEOUT_MS); CHECK_EQ(r.p.state, NW_PROV_S_SESSION);          /* fires once */
}
/* WO glue item 1: same for the claim POST: claim_failed/network. */
static void test_item1_http_never_answers_ends_in_network(void)
{
    rig_t r; to_claiming(&r, 2000);
    CHECK_EQ(r.f.post_calls, 1);
    uint32_t t0 = 2100;
    nw_glue_tick(&r.g, t0 + NW_GLUE_HTTP_TIMEOUT_MS - 1); CHECK_EQ(r.p.state, NW_PROV_S_CLAIMING);
    nw_glue_tick(&r.g, t0 + NW_GLUE_HTTP_TIMEOUT_MS);
    CHECK_EQ(r.p.state, NW_PROV_S_SESSION); CHECK(strstr(reason(&r), "\"claim_failed\"") && strstr(reason(&r), "\"network\""));
}
static void test_item1_timeout_is_wrap_safe_and_retry_rearms(void)
{
    rig_t r; uint32_t t = 0xFFFFFFF0u; to_wifi(&r, t);
    nw_glue_tick(&r.g, t + 100); CHECK_EQ(r.p.state, NW_PROV_S_WIFI_CONNECTING);
    nw_glue_tick(&r.g, t + NW_GLUE_WIFI_JOIN_TIMEOUT_MS);                      /* wraps past 0 */
    CHECK_EQ(r.p.state, NW_PROV_S_SESSION);
    /* retry: new wifi config + apply must arm a fresh timer (state goes SESSION -> WIFI_CONNECTING again) */
    uint32_t t2 = t + NW_GLUE_WIFI_JOIN_TIMEOUT_MS + 10;
    CHECK_EQ(nw_prov_on_wifi_config(&r.p, "HomeNet-2G", "correct-horse", t2), NW_PROV_OK);
    CHECK_EQ(nw_glue_on_apply(&r.g, t2), NW_PROV_OK); CHECK_EQ(r.f.wifi_calls, 2);
    nw_glue_tick(&r.g, t2 + NW_GLUE_WIFI_JOIN_TIMEOUT_MS - 1); CHECK_EQ(r.p.state, NW_PROV_S_WIFI_CONNECTING);
    nw_glue_tick(&r.g, t2 + NW_GLUE_WIFI_JOIN_TIMEOUT_MS); CHECK_EQ(r.p.state, NW_PROV_S_SESSION);
}
static void test_item1_late_result_after_timeout_is_ignored(void)
{
    rig_t r; to_wifi(&r, 0);
    nw_glue_tick(&r.g, NW_GLUE_WIFI_JOIN_TIMEOUT_MS);
    CHECK_EQ(nw_glue_on_wifi_result(&r.g, NW_PROV_WIFI_OK, NW_GLUE_WIFI_JOIN_TIMEOUT_MS + 5), NW_PROV_ERR_STATE);
    CHECK_EQ(r.f.post_calls, 0);                                               /* a late join must not start a claim */
}

/* WO glue item 2 (Theo C3): body carries hw_id, claim_token, name, fw as openapi.yaml requires. */
static void test_item2_claim_body_fields(void)
{
    rig_t r; to_claiming(&r, 0);
    const char *b = r.f.post_body;
    CHECK(strstr(b, "\"hw_id\":\"" HWID "\"")); CHECK(strstr(b, "\"claim_token\":\"" TOKEN "\""));
    CHECK(strstr(b, "\"name\":\"Basil on the sill\"")); CHECK(strstr(b, "\"fw\":\"0.4.2-dev\""));
    CHECK_EQ(b[0], '{'); CHECK_EQ(b[strlen(b) - 1], '}');
    CHECK(!strstr(b, "ssid") && !strstr(b, "passphrase") && !strstr(b, "correct-horse") && !strstr(b, "HomeNet"));   /* NFR-06 */
    /* additionalProperties:false -> exactly four keys */
    int colons = 0; for (const char *c = b; *c; c++) if (*c == ':') colons++;
    CHECK_EQ(colons, 4);
}
static void test_item2_escaping_and_limits(void)
{
    char b[NW_GLUE_BODY_MAX];
    int n = nw_glue_build_claim_body(b, sizeof b, HWID, TOKEN, "a\"b\\c\n", "1");
    CHECK(n > 0); CHECK(strstr(b, "\"name\":\"a\\\"b\\\\c\\u000a\""));
    CHECK_EQ(nw_glue_build_claim_body(b, 20, HWID, TOKEN, "x", "1"), NW_PROV_ERR_TOO_SMALL); CHECK_EQ(b[0], 0);
    char big[NW_PROV_NAME_MAX_BYTES + 1]; memset(big, '"', NW_PROV_NAME_MAX_BYTES); big[NW_PROV_NAME_MAX_BYTES] = 0;
    CHECK(nw_glue_build_claim_body(b, sizeof b, HWID, TOKEN, big, "1") > 0);       /* worst case (all quotes, 320 bytes) fits the glue buffer */
    nw_glue_t g; nw_prov_ops_t ops; nw_glue_io_t io = {0};
    CHECK_EQ(nw_glue_init(&g, &io, "nw-A1B2C3D4E5F6", "1", &ops), NW_PROV_ERR_ARG);   /* upper case */
    CHECK_EQ(nw_glue_init(&g, &io, "nw-a1b2c3d4e5f", "1", &ops), NW_PROV_ERR_ARG);    /* short */
    CHECK_EQ(nw_glue_init(&g, &io, HWID, "", &ops), NW_PROV_ERR_ARG);
    CHECK_EQ(nw_glue_init(&g, &io, HWID, "123456789012345678901234567890123", &ops), NW_PROV_ERR_ARG);   /* fw 33 chars */
    CHECK_EQ(nw_glue_init(&g, &io, HWID, "12345678901234567890123456789012", &ops), NW_PROV_OK);          /* fw 32 chars */
}

/* WO glue item 3 (Theo C3): every HTTP outcome maps to an app reason; every case end to end. */
static void run_status(int status, const char *body, nw_prov_status_state_t st, const char *want_reason)
{
    rig_t r; to_claiming(&r, 0);
    CHECK_EQ(nw_glue_on_http_response(&r.g, status, body, body ? strlen(body) : 0, 500), NW_PROV_OK);
    CHECK_EQ(r.p.st, st);
    CHECK(strstr(reason(&r), want_reason) != NULL);
    if (st == NW_PROV_ST_CLAIM_FAILED) CHECK_EQ(r.p.state, NW_PROV_S_SESSION);   /* stays open for a retry */
}
static void test_item3_http_mapping(void)
{
    rig_t r; to_claiming(&r, 0);
    CHECK_EQ(nw_glue_on_http_response(&r.g, 200, OK200, strlen(OK200), 500), NW_PROV_OK);
    CHECK_EQ(r.p.state, NW_PROV_S_CLAIMED); CHECK(r.f.stored); CHECK(!strcmp(r.f.rec.device_token, DEVTOK));
    CHECK(!strcmp(r.f.rec.ssid, "HomeNet-2G")); CHECK(!r.f.ble_on);
    run_status(401, "{}", NW_PROV_ST_CLAIM_FAILED, "claim_token_invalid");
    run_status(409, "{}", NW_PROV_ST_CLAIM_FAILED, "device_owned");
    const int server[] = {400, 413, 429, 500, 502, 503, 404, 301, 204, 0, -1, 999};
    for (unsigned i = 0; i < sizeof server / sizeof *server; i++) run_status(server[i], "{}", NW_PROV_ST_CLAIM_FAILED, "\"server\"");
    run_status(200, "{\"device_id\":\"x\"}", NW_PROV_ST_CLAIM_FAILED, "\"server\"");                                  /* 200 without a token */
    run_status(200, "{\"device_token\":\"ABCDEF0123456789abcdef0123456789abcdef0123456789abcdef0123456789\"}", NW_PROV_ST_CLAIM_FAILED, "\"server\""); /* upper case hex */
    run_status(200, "{\"device_token\":\"0123\"}", NW_PROV_ST_CLAIM_FAILED, "\"server\"");                          /* short */
    run_status(200, NULL, NW_PROV_ST_CLAIM_FAILED, "\"server\"");
    rig(&r); to_claiming(&r, 0);
    CHECK_EQ(nw_glue_on_transport_error(&r.g, 500), NW_PROV_OK);                                                   /* TLS error / DNS / reset */
    CHECK(strstr(reason(&r), "\"claim_failed\"") && strstr(reason(&r), "\"network\""));
    CHECK(!r.f.stored);                                                                                            /* nothing stored on any failure */
}
static void test_item3_token_parser(void)
{
    char t[65];
    CHECK(nw_glue_parse_device_token("{ \"device_token\" :\n \"" DEVTOK "\" }", 0 + strlen("{ \"device_token\" :\n \"" DEVTOK "\" }"), t)); CHECK(!strcmp(t, DEVTOK));
    CHECK(!nw_glue_parse_device_token("{\"device_token\":\"" DEVTOK, strlen("{\"device_token\":\"" DEVTOK), t));   /* no closing quote */
    CHECK(!nw_glue_parse_device_token("{\"device_token\":" DEVTOK "}", strlen("{\"device_token\":" DEVTOK "}"), t)); /* not a string */
}

/* WO glue item 4 (Theo C4, FR-D09): what happens after CLOSED. */
static void test_item4_behaviour_after_closed(void)
{
    rig_t r; rig(&r);
    CHECK_EQ(nw_glue_next_after_setup(&r.p, false), NW_GLUE_NEXT_STAY);                 /* still in setup */
    for (int i = 0; i < NW_PROV_MAX_FAILED_HANDSHAKES; i++) nw_prov_on_handshake(&r.p, false, 10 + i);
    CHECK_EQ(r.p.state, NW_PROV_S_CLOSED); CHECK(!r.f.ble_on);
    CHECK_EQ(nw_glue_next_after_setup(&r.p, false), NW_GLUE_NEXT_SLEEP_UNTIL_RESET);    /* never provisioned: sleep, radios off */
    CHECK_EQ(nw_glue_next_after_setup(&r.p, true), NW_GLUE_NEXT_NORMAL);                /* button setup on a provisioned unit: back to normal */
    rig_t c; to_claiming(&c, 0); nw_glue_on_http_response(&c.g, 200, OK200, strlen(OK200), 5);
    CHECK_EQ(nw_glue_next_after_setup(&c.p, true), NW_GLUE_NEXT_NORMAL);
    /* 5 minute close through the glue tick */
    rig_t t; rig(&t); nw_glue_tick(&t.g, NW_PROV_SETUP_TIMEOUT_MS);
    CHECK_EQ(t.p.state, NW_PROV_S_CLOSED); CHECK(!t.f.ble_on);
    CHECK_EQ(nw_glue_next_after_setup(&t.p, false), NW_GLUE_NEXT_SLEEP_UNTIL_RESET);
    /* a reset after CLOSED on a never-provisioned unit enters setup again (no record): the only exit, as the PR states */
    nw_prov_t p2; nw_prov_ops_t ops = {.ctx = &t.f, .ble_set = k_ble, .store = {k_load, k_save, k_erase}, .store_ctx = &t.f};
    nw_prov_init(&p2, &ops); CHECK_EQ(nw_prov_boot(&p2, 0, 0), NW_PROV_OK); CHECK_EQ(p2.state, NW_PROV_S_ADVERTISING);
}

/* PR #172 (Theo): a failed boot decision must not fall through to normal mode. Sleep until reset instead. */
static int k_load_err(void *c, nw_prov_record_t *o) { (void)c; (void)o; return -1; }
static int k_erase_err(void *c) { (void)c; return -1; }
static void test_pr172_failed_boot_decision_sleeps_until_reset(void)
{
    fk_t f = {0};
    nw_prov_ops_t ops = {.ctx = &f, .ble_set = k_ble, .store = {k_load_err, k_save, k_erase}, .store_ctx = &f};
    nw_prov_t p; nw_prov_init(&p, &ops);
    int rc = nw_prov_boot(&p, 0, 0);                                                  /* NVS read error */
    CHECK_EQ(rc, NW_PROV_ERR_STORE); CHECK_EQ(p.state, NW_PROV_S_NORMAL);
    CHECK_EQ(nw_glue_next_after_boot(&p, rc, false), NW_GLUE_NEXT_SLEEP_UNTIL_RESET);  /* no fall-through to normal */

    nw_prov_ops_t ops2 = {.ctx = &f, .ble_set = k_ble, .store = {k_load, k_save, k_erase_err}, .store_ctx = &f};
    nw_prov_t p2; nw_prov_init(&p2, &ops2);
    rc = nw_prov_boot(&p2, NW_PROV_BUTTON_RESET_MS, 0);                               /* factory reset, erase fails */
    CHECK_EQ(rc, NW_PROV_ERR_STORE);
    CHECK_EQ(nw_glue_next_after_boot(&p2, rc, true), NW_GLUE_NEXT_SLEEP_UNTIL_RESET); /* old record not wiped: do not run it */

    nw_prov_t p3; nw_prov_init(&p3, &ops2);
    f.stored = true;                                                                  /* healthy provisioned boot: unchanged */
    rc = nw_prov_boot(&p3, 0, 0);
    CHECK_EQ(rc, NW_PROV_OK); CHECK_EQ(nw_glue_next_after_boot(&p3, rc, true), NW_GLUE_NEXT_NORMAL);
}

/* Bench finding (4.F2): the ESP-IDF glue never called nw_prov_on_handshake, so nw-claim was refused with ERR_STATE on every real
 * run. This drives the endpoint path the way ep_claim does (nw_prov_on_endpoint first, no manual handshake call). */
static void test_endpoint_call_records_session_without_manual_handshake(void)
{
    rig_t r; char rep[64];
    rig_no_handshake(&r);
    CHECK_EQ(r.p.state, NW_PROV_S_ADVERTISING);
    CHECK_EQ(nw_prov_on_claim(&r.p, CLAIM_JSON, strlen(CLAIM_JSON), rep, sizeof rep, 0), NW_PROV_ERR_STATE);   /* gap without the endpoint hook */
    CHECK_EQ(nw_prov_on_endpoint(&r.p, 1), NW_PROV_OK);
    CHECK_EQ(r.p.state, NW_PROV_S_SESSION);
    CHECK_EQ(nw_prov_on_claim(&r.p, CLAIM_JSON, strlen(CLAIM_JSON), rep, sizeof rep, 2), NW_PROV_OK);
    CHECK(strstr(rep, "\"ok\":true") != NULL);
    CHECK_EQ(nw_prov_on_wifi_config(&r.p, "HomeNet-2G", "correct-horse", 3), NW_PROV_OK);
    CHECK_EQ(nw_glue_on_apply(&r.g, 3), NW_PROV_OK);
    CHECK_EQ(r.f.wifi_calls, 1);
}

/* WO glue item 6: the glue must not touch the state machine constants. Items 5 (traceability) is checked by test_prov / contract check. */
static void test_item6_constants_unchanged(void)
{
    CHECK_EQ(NW_PROV_SETUP_TIMEOUT_MS, 300000u); CHECK_EQ(NW_PROV_MAX_FAILED_HANDSHAKES, 5);
    CHECK_EQ(NW_PROV_BUTTON_SETUP_MS, 3000u); CHECK_EQ(NW_PROV_BUTTON_RESET_MS, 10000u);
}

int main(void)
{
    test_item1_wifi_never_answers_ends_in_timeout(); test_item1_http_never_answers_ends_in_network();
    test_item1_timeout_is_wrap_safe_and_retry_rearms(); test_item1_late_result_after_timeout_is_ignored();
    test_item2_claim_body_fields(); test_item2_escaping_and_limits();
    test_item3_http_mapping(); test_item3_token_parser();
    test_item4_behaviour_after_closed(); test_pr172_failed_boot_decision_sleeps_until_reset();
    test_item6_constants_unchanged(); test_endpoint_call_records_session_without_manual_handshake();
    printf("glue host tests: %d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}

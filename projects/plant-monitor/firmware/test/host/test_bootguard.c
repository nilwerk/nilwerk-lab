/* Host tests for the boot-loop guard and safe fallback. FR-D05 (a new image that fails to confirm rolls back), NFR-01 (a looping unit must not
 * burn the cell on radio retries), NFR-12 (fallback = plain deep sleep, radios off). No flash, no radio, no ESP-IDF. Every rule has a mutant in
 * mutate_bootguard.py. The limit and the long sleep are [proposed] values: the tests pin the macros, so a change is a visible test edit. */
#include <stdio.h>
#include <string.h>
#include "nwtest.h"
#include "nw_bootguard.h"
#include "nw_cycle.h"

int nwtest_failed, nwtest_checked;

#define N NW_BOOTGUARD_MAX_FAILED_BOOTS

static nw_bootguard_t fresh(void) { nw_bootguard_t s; nw_bootguard_init(&s); return s; }

/* One boot that dies before it is confirmed (panic, watchdog, reset button). */
static nw_bootguard_out_t failed_boot(nw_bootguard_t *s, const nw_ota_boot_t *ota) { return nw_bootguard_boot(s, ota, NW_BG_RESET_OTHER); }
/* One boot that reaches the normal end of the cycle. */
static nw_bootguard_out_t good_boot(nw_bootguard_t *s, const nw_ota_boot_t *ota)
{
    nw_bootguard_out_t o = nw_bootguard_boot(s, ota, NW_BG_RESET_OTHER);
    if (o.action == NW_BG_RUN) nw_bootguard_confirm_good(s);
    return o;
}
static nw_ota_boot_t pend(uint8_t boots) { nw_ota_boot_t b = { true, boots, false, NW_OTA_MAX_UNCONFIRMED_BOOTS }; return b; }
/* Independent copy of the check formula, so a state can be built with a MATCHING check and one field out of range: the range rules must hold on
 * their own, the check is not allowed to be the only guard. Also pins the formula: a change to it must be a visible test edit. */
static void reseal(nw_bootguard_t *s)
{
    uint32_t v = ((uint32_t)s->failed_boots) | ((uint32_t)s->in_fallback << 8) | ((uint32_t)s->reserved << 16);
    s->check = (s->magic ^ 0x9E3779B9u) + v * 0x01000193u;
}
/* Corrupt one byte of a valid state through its raw bytes (what a bit flip in RTC memory does). */
static void flip(nw_bootguard_t *s, size_t byte) { ((unsigned char *)s)[byte] ^= 0x5A; }

static void test_constants_and_budget(void)
{
    CHECK_EQ(N, 5);                                        /* [proposed] */
    CHECK_EQ(NW_BOOTGUARD_FALLBACK_SLEEP_S, 21600);        /* [proposed] 6 h */
    CHECK(N < NW_OTA_MAX_UNCONFIRMED_BOOTS);               /* the guard trips before the 8-boot OTA window (A-116) ends */
    CHECK_EQ(sizeof(nw_bootguard_t), NW_BOOTGUARD_RTC_BYTES);
    CHECK_EQ(NW_BOOTGUARD_RTC_BYTES, 12);
    /* RTC budget: guard + cycle state inside the proposed 4096 bytes (NFR-12 motivates the cap, defines no number) */
    CHECK(sizeof(nw_cycle_state_t) + sizeof(nw_bootguard_t) <= NW_CYCLE_RTC_BUDGET_BYTES);
    CHECK(sizeof(nw_bootguard_t) <= 16);
}

static void test_counter_increment_and_clear(void)
{
    nw_bootguard_t s = fresh();
    CHECK(nw_bootguard_valid(&s));
    CHECK_EQ(s.failed_boots, 0);
    for (unsigned i = 1; i <= N; i++) {                      /* failed boots in a row: counter rises by one each */
        nw_bootguard_out_t o = failed_boot(&s, NULL);
        CHECK_EQ(o.action, NW_BG_RUN);
        CHECK_EQ(s.failed_boots, i);
        CHECK(nw_bootguard_valid(&s));
    }
    /* a confirmed good boot clears the counter */
    nw_bootguard_t t = fresh();
    failed_boot(&t, NULL); failed_boot(&t, NULL); failed_boot(&t, NULL);
    CHECK_EQ(t.failed_boots, 3);
    nw_bootguard_boot(&t, NULL, NW_BG_RESET_OTHER);
    CHECK_EQ(t.failed_boots, 4);
    nw_bootguard_confirm_good(&t);
    CHECK_EQ(t.failed_boots, 0);
    CHECK_EQ(t.in_fallback, 0);
    CHECK(nw_bootguard_valid(&t));
    /* after the clear the next failure series starts from zero again: N more failures are allowed before the fallback */
    for (unsigned i = 0; i < N; i++) CHECK_EQ(failed_boot(&t, NULL).action, NW_BG_RUN);
    CHECK_EQ(failed_boot(&t, NULL).action, NW_BG_FALLBACK);
    /* a healthy unit that wakes every 15 min never accumulates */
    nw_bootguard_t h = fresh();
    for (int i = 0; i < 100; i++) { CHECK_EQ(good_boot(&h, NULL).action, NW_BG_RUN); CHECK_EQ(h.failed_boots, 0); }
    /* power-on garbage: not a failure, counts as the first boot */
    nw_bootguard_t g; memset(&g, 0xA5, sizeof g);
    nw_bootguard_out_t og = nw_bootguard_boot(&g, NULL, NW_BG_RESET_POWERON);
    CHECK_EQ(og.action, NW_BG_RUN);
    CHECK_EQ(g.failed_boots, 1);
    CHECK(nw_bootguard_valid(&g));
    nw_bootguard_t z; memset(&z, 0, sizeof z);              /* all-zero RTC is also power-on */
    CHECK_EQ(nw_bootguard_boot(&z, NULL, NW_BG_RESET_POWERON).action, NW_BG_RUN);
    CHECK_EQ(z.failed_boots, 1);
}

static void test_threshold_reached_fallback(void)
{
    nw_bootguard_t s = fresh();
    for (unsigned i = 0; i < N; i++) CHECK_EQ(failed_boot(&s, NULL).action, NW_BG_RUN);   /* N failed boots */
    CHECK_EQ(s.failed_boots, N);
    nw_bootguard_out_t o = nw_bootguard_boot(&s, NULL, NW_BG_RESET_OTHER);                                   /* boot N+1 */
    CHECK_EQ(o.action, NW_BG_FALLBACK);
    CHECK_EQ(o.why, NW_BG_WHY_COUNT);
    CHECK_EQ(o.sleep_s, NW_BOOTGUARD_FALLBACK_SLEEP_S);
    CHECK_EQ(s.in_fallback, 1);
    CHECK_EQ(s.failed_boots, N);                            /* the counter is not cleared by the fallback itself */
    CHECK(nw_bootguard_valid(&s));
    /* one below the limit still runs: boundary is exact */
    nw_bootguard_t b = fresh();
    for (unsigned i = 0; i < N - 1; i++) failed_boot(&b, NULL);
    CHECK_EQ(nw_bootguard_boot(&b, NULL, NW_BG_RESET_OTHER).action, NW_BG_RUN);
    /* after the long sleep: exactly one probation boot, then straight back to fallback if it fails too */
    nw_bootguard_out_t p = nw_bootguard_boot(&s, NULL, NW_BG_RESET_OTHER);
    CHECK_EQ(p.action, NW_BG_RUN);
    CHECK_EQ(s.in_fallback, 0);
    CHECK_EQ(s.failed_boots, N);
    nw_bootguard_out_t p2 = nw_bootguard_boot(&s, NULL, NW_BG_RESET_OTHER);
    CHECK_EQ(p2.action, NW_BG_FALLBACK);
    CHECK_EQ(p2.why, NW_BG_WHY_COUNT);
    /* a probation boot that is confirmed returns the unit to normal service */
    nw_bootguard_t r = fresh();
    for (unsigned i = 0; i < N; i++) failed_boot(&r, NULL);
    CHECK_EQ(nw_bootguard_boot(&r, NULL, NW_BG_RESET_OTHER).action, NW_BG_FALLBACK);
    CHECK_EQ(good_boot(&r, NULL).action, NW_BG_RUN);
    CHECK_EQ(r.failed_boots, 0);
    CHECK_EQ(r.in_fallback, 0);
    CHECK_EQ(good_boot(&r, NULL).action, NW_BG_RUN);
}

static void test_fallback_does_not_retry_radios(void)
{
    nw_bootguard_t s = fresh();
    nw_bootguard_out_t run = nw_bootguard_boot(&s, NULL, NW_BG_RESET_OTHER);
    CHECK(run.allow_ble);                                    /* a normal boot may use the radios */
    CHECK(run.allow_wifi);
    CHECK_EQ(run.sleep_s, 0);
    for (unsigned i = 1; i < N; i++) failed_boot(&s, NULL);
    nw_bootguard_out_t o = nw_bootguard_boot(&s, NULL, NW_BG_RESET_OTHER);
    CHECK_EQ(o.action, NW_BG_FALLBACK);
    CHECK(!o.allow_ble);                                     /* no BLE setup, no advertising */
    CHECK(!o.allow_wifi);                                    /* no association, no SNTP, no upload */
    CHECK(o.sleep_s >= 3600);                                /* a long sleep, not the 15 min sample period */
    /* corrupt-state fallback also keeps the radios off */
    nw_bootguard_t c = fresh(); flip(&c, 4);
    nw_bootguard_out_t oc = nw_bootguard_boot(&c, NULL, NW_BG_RESET_OTHER);
    CHECK_EQ(oc.action, NW_BG_FALLBACK);
    CHECK(!oc.allow_ble);
    CHECK(!oc.allow_wifi);
    CHECK_EQ(oc.sleep_s, NW_BOOTGUARD_FALLBACK_SLEEP_S);
    /* a rollback answer does not start the radios either: it reboots into the previous image */
    nw_bootguard_t rb = fresh();
    nw_ota_boot_t ota = pend(NW_OTA_MAX_UNCONFIRMED_BOOTS);
    nw_bootguard_out_t orb = nw_bootguard_boot(&rb, &ota, NW_BG_RESET_OTHER);
    CHECK_EQ(orb.action, NW_BG_ROLLBACK);
    CHECK(!orb.allow_ble);
    CHECK(!orb.allow_wifi);
    /* the log line: exactly one line, says fallback, radios off */
    char line[160];
    size_t n = nw_bootguard_log_line(line, sizeof line, &o);
    CHECK(n > 0);
    CHECK_EQ(n, strlen(line));
    CHECK(strchr(line, '\n') == NULL);
    CHECK(strstr(line, "NWBOOTGUARD fallback") == line);
    CHECK(strstr(line, "why=count") != NULL);
    CHECK(strstr(line, "failed=5") != NULL);
    CHECK(strstr(line, "limit=5") != NULL);
    CHECK(strstr(line, "sleep_s=21600") != NULL);
    CHECK(strstr(line, "ble=off wifi=off") != NULL);
    CHECK(strstr(line, "why=corrupt") == NULL);
    char tiny[16];
    size_t nt = nw_bootguard_log_line(tiny, sizeof tiny, &o);
    CHECK_EQ(nt, sizeof tiny - 1);                           /* truncated, still NUL-terminated */
    CHECK_EQ(tiny[sizeof tiny - 1], 0);
    char none[32] = "x";
    CHECK_EQ(nw_bootguard_log_line(none, sizeof none, &run), 0);   /* a normal boot logs nothing */
    CHECK_EQ(none[0], 0);
    CHECK_EQ(nw_bootguard_log_line(none, 0, &o), 0);
    char oc_line[160];
    nw_bootguard_log_line(oc_line, sizeof oc_line, &oc);
    CHECK(strstr(oc_line, "why=corrupt") != NULL);
}

static void test_rollback_when_not_confirmed(void)
{
    /* the 4.F4 window: pending image, 8th unconfirmed boot, no ingest: rollback (decided by nw_ota_boot_decide) */
    nw_bootguard_t s = fresh();
    nw_ota_boot_t w = pend(NW_OTA_MAX_UNCONFIRMED_BOOTS);
    nw_bootguard_out_t o = nw_bootguard_boot(&s, &w, NW_BG_RESET_OTHER);
    CHECK_EQ(o.action, NW_BG_ROLLBACK);
    CHECK_EQ(o.why, NW_BG_WHY_OTA_WINDOW);
    CHECK_EQ(o.sleep_s, 0);
    CHECK_EQ(s.failed_boots, 0);                             /* the previous image starts with a full budget */
    CHECK(nw_bootguard_valid(&s));
    /* inside the window and not looping: keep running, the next boot counts */
    nw_bootguard_t s2 = fresh();
    nw_ota_boot_t in = pend(NW_OTA_MAX_UNCONFIRMED_BOOTS - 1);
    CHECK_EQ(nw_bootguard_boot(&s2, &in, NW_BG_RESET_OTHER).action, NW_BG_RUN);
    /* a pending image that has already been confirmed by an ingest is never rolled back by the window */
    nw_bootguard_t s3 = fresh();
    nw_ota_boot_t ok = pend(NW_OTA_MAX_UNCONFIRMED_BOOTS); ok.ingest_ok = true;
    CHECK_EQ(nw_bootguard_boot(&s3, &ok, NW_BG_RESET_OTHER).action, NW_BG_RUN);
    /* not an OTA image: the window never applies, whatever the counter says */
    nw_ota_boot_t idle = pend(NW_OTA_MAX_UNCONFIRMED_BOOTS); idle.pending_verify = false;
    nw_bootguard_t s4 = fresh();
    CHECK_EQ(nw_bootguard_boot(&s4, &idle, NW_BG_RESET_OTHER).action, NW_BG_RUN);
    /* a looping unconfirmed OTA image: the guard trips at N and rolls back instead of sleeping (earlier than the 8-boot window) */
    nw_bootguard_t s5 = fresh();
    nw_ota_boot_t lp = pend(1);
    for (unsigned i = 0; i < N; i++) CHECK_EQ(failed_boot(&s5, &lp).action, NW_BG_RUN);
    nw_bootguard_out_t ol = nw_bootguard_boot(&s5, &lp, NW_BG_RESET_OTHER);
    CHECK_EQ(ol.action, NW_BG_ROLLBACK);
    CHECK_EQ(ol.why, NW_BG_WHY_OTA_LOOP);
    CHECK_EQ(ol.sleep_s, 0);
    CHECK_EQ(s5.failed_boots, 0);
    CHECK_EQ(s5.in_fallback, 0);
    /* after the rollback the previous image is not pending: if it loops too, the guard falls back, no second rollback */
    for (unsigned i = 0; i < N; i++) failed_boot(&s5, NULL);
    CHECK_EQ(nw_bootguard_boot(&s5, NULL, NW_BG_RESET_OTHER).action, NW_BG_FALLBACK);
    /* the same loop without a pending image falls back, it does not roll back */
    nw_bootguard_t s6 = fresh();
    for (unsigned i = 0; i < N; i++) failed_boot(&s6, NULL);
    CHECK_EQ(nw_bootguard_boot(&s6, NULL, NW_BG_RESET_OTHER).action, NW_BG_FALLBACK);
    /* an OTA state that is NOT pending verify (an image that was confirmed long ago) looping at the limit: fallback, not rollback */
    nw_bootguard_t s8 = fresh();
    nw_ota_boot_t np = pend(3); np.pending_verify = false;
    for (unsigned i = 0; i < N; i++) failed_boot(&s8, &np);
    CHECK_EQ(nw_bootguard_boot(&s8, &np, NW_BG_RESET_OTHER).action, NW_BG_FALLBACK);
    /* the window rollback also clears a raised counter */
    nw_bootguard_t s9 = fresh();
    failed_boot(&s9, NULL); failed_boot(&s9, NULL);
    CHECK_EQ(s9.failed_boots, 2);
    nw_ota_boot_t w9 = pend(NW_OTA_MAX_UNCONFIRMED_BOOTS);
    CHECK_EQ(nw_bootguard_boot(&s9, &w9, NW_BG_RESET_OTHER).action, NW_BG_ROLLBACK);
    CHECK_EQ(s9.failed_boots, 0);
    CHECK_EQ(s9.in_fallback, 0);
    /* a looping pending image whose ingest was confirmed is not the suspect-by-window, but a loop at the limit still rolls back */
    nw_bootguard_t s7 = fresh();
    nw_ota_boot_t cf = pend(2); cf.ingest_ok = true;
    for (unsigned i = 0; i < N; i++) failed_boot(&s7, &cf);
    CHECK_EQ(nw_bootguard_boot(&s7, &cf, NW_BG_RESET_OTHER).action, NW_BG_ROLLBACK);
}

static void test_magic_mismatch_needs_poweron_reset(void)
{
    /* F4: a wiped or damaged magic is power-on ONLY when the reset reason says power-on. Otherwise a loop could hide behind it. */
    nw_bootguard_t g; memset(&g, 0xA5, sizeof g);
    nw_bootguard_out_t o = nw_bootguard_boot(&g, NULL, NW_BG_RESET_OTHER);
    CHECK_EQ(o.action, NW_BG_FALLBACK);
    CHECK_EQ(o.why, NW_BG_WHY_CORRUPT);
    CHECK(!o.allow_ble && !o.allow_wifi);
    CHECK_EQ(o.sleep_s, NW_BOOTGUARD_FALLBACK_SLEEP_S);
    CHECK(nw_bootguard_valid(&g));
    CHECK_EQ(g.in_fallback, 1);
    nw_bootguard_t z; memset(&z, 0, sizeof z);
    CHECK_EQ(nw_bootguard_boot(&z, NULL, NW_BG_RESET_OTHER).action, NW_BG_FALLBACK);
    /* the unknown / unset reason is the fail-safe one */
    nw_bootguard_t u; memset(&u, 0, sizeof u);
    CHECK_EQ(nw_bootguard_boot(&u, NULL, (nw_bg_reset_t)0).action, NW_BG_FALLBACK);
    nw_bootguard_t v; memset(&v, 0, sizeof v);
    CHECK_EQ(nw_bootguard_boot(&v, NULL, (nw_bg_reset_t)77).action, NW_BG_FALLBACK);
    /* wrong magic with a matching check: still only power-on may accept it */
    nw_bootguard_t m = fresh(); m.magic ^= 1u; reseal(&m);
    nw_bootguard_t m2 = m;
    CHECK_EQ(nw_bootguard_boot(&m, NULL, NW_BG_RESET_OTHER).why, NW_BG_WHY_CORRUPT);
    CHECK_EQ(nw_bootguard_boot(&m2, NULL, NW_BG_RESET_POWERON).action, NW_BG_RUN);
    /* a power-on reset with a VALID counter keeps counting (RTC survived, e.g. a button reset reported as power-on by mistake): no special case */
    nw_bootguard_t k = fresh();
    failed_boot(&k, NULL);
    CHECK_EQ(nw_bootguard_boot(&k, NULL, NW_BG_RESET_POWERON).action, NW_BG_RUN);
    CHECK_EQ(k.failed_boots, 2);
    /* a looping unit whose magic is wiped every time now reaches fallback on its first bad boot, and the radios stay off */
    nw_bootguard_t w; memset(&w, 0, sizeof w);
    nw_bootguard_out_t ow = nw_bootguard_boot(&w, NULL, NW_BG_RESET_OTHER);
    CHECK(ow.action == NW_BG_FALLBACK && !ow.allow_wifi && !ow.allow_ble);
}

/* C6: the log line shows the count that caused the decision, also for a rollback (the state is cleared before the line is built). */
static void test_log_shows_causing_count(void)
{
    nw_bootguard_t s = fresh();
    nw_ota_boot_t lp = pend(1);
    for (unsigned i = 0; i < N; i++) failed_boot(&s, &lp);
    nw_bootguard_out_t o = nw_bootguard_boot(&s, &lp, NW_BG_RESET_OTHER);
    CHECK_EQ(o.action, NW_BG_ROLLBACK);
    CHECK_EQ(s.failed_boots, 0);
    CHECK_EQ(o.failed, N);
    char line[160];
    nw_bootguard_log_line(line, sizeof line, &o);
    CHECK(strstr(line, "NWBOOTGUARD rollback why=ota_loop failed=5") == line);
    CHECK(strchr(line, '\n') == NULL);
    nw_bootguard_t w = fresh();
    failed_boot(&w, NULL); failed_boot(&w, NULL);
    nw_ota_boot_t win = pend(NW_OTA_MAX_UNCONFIRMED_BOOTS);
    nw_bootguard_out_t ow = nw_bootguard_boot(&w, &win, NW_BG_RESET_OTHER);
    CHECK_EQ(ow.action, NW_BG_ROLLBACK);
    CHECK_EQ(ow.failed, 2);
    nw_bootguard_log_line(line, sizeof line, &ow);
    CHECK(strstr(line, "why=ota_window failed=2") != NULL);
}

static void test_corrupted_counter_fails_safe(void)
{
    /* every byte of the retained struct flipped on its own: valid magic with wrong content -> fallback, never a run, never an out-of-range count.
     * Magic bytes (0..3) flipped = power-on case, covered separately. */
    for (size_t i = 4; i < sizeof(nw_bootguard_t); i++) {
        nw_bootguard_t s = fresh();
        failed_boot(&s, NULL);
        CHECK(nw_bootguard_valid(&s));
        flip(&s, i);
        CHECK(!nw_bootguard_valid(&s));
        nw_bootguard_out_t o = nw_bootguard_boot(&s, NULL, NW_BG_RESET_OTHER);
        CHECK_EQ(o.action, NW_BG_FALLBACK);
        CHECK_EQ(o.why, NW_BG_WHY_CORRUPT);
        CHECK(!o.allow_ble && !o.allow_wifi);
        CHECK(nw_bootguard_valid(&s));                       /* re-sealed: the next boot is not corrupt again */
        CHECK_EQ(s.in_fallback, 1);                          /* and marked so the next boot is the probation boot */
        CHECK_EQ(s.failed_boots, N);
        CHECK(s.failed_boots <= N);
    }
    /* each field out of range WITH a matching check (the check alone must not be the only guard) */
    nw_bootguard_t k = fresh(); reseal(&k);
    CHECK(nw_bootguard_valid(&k));                           /* the test copy of the formula agrees with the code */
    nw_bootguard_t a = fresh(); a.failed_boots = 200; reseal(&a);
    CHECK(!nw_bootguard_valid(&a));
    nw_bootguard_t b = fresh(); b.in_fallback = 2; reseal(&b);
    CHECK(!nw_bootguard_valid(&b));
    nw_bootguard_t c = fresh(); c.reserved = 1; reseal(&c);
    CHECK(!nw_bootguard_valid(&c));
    nw_bootguard_t d = fresh(); d.failed_boots = N + 1; reseal(&d);
    CHECK(!nw_bootguard_valid(&d));
    nw_bootguard_t d2 = fresh(); d2.failed_boots = N; reseal(&d2);
    CHECK(nw_bootguard_valid(&d2));                          /* N itself is a legal count (N failed boots so far) */
    CHECK_EQ(nw_bootguard_boot(&a, NULL, NW_BG_RESET_OTHER).why, NW_BG_WHY_CORRUPT);
    CHECK_EQ(nw_bootguard_boot(&b, NULL, NW_BG_RESET_OTHER).why, NW_BG_WHY_CORRUPT);
    CHECK_EQ(nw_bootguard_boot(&c, NULL, NW_BG_RESET_OTHER).why, NW_BG_WHY_CORRUPT);
    /* the check covers each field: change one, keep the old check */
    nw_bootguard_t m = fresh(); m.failed_boots = 2; reseal(&m); m.failed_boots = 3;
    CHECK(!nw_bootguard_valid(&m));
    nw_bootguard_t m2 = fresh(); m2.in_fallback = 1; reseal(&m2); m2.in_fallback = 0;
    CHECK(!nw_bootguard_valid(&m2));
    nw_bootguard_t m3 = fresh(); m3.in_fallback = 1;         /* flag changed, check not */
    CHECK(!nw_bootguard_valid(&m3));
    nw_bootguard_t m4 = fresh(); m4.magic ^= 1u; reseal(&m4);   /* wrong magic, matching check: still not valid */
    CHECK(!nw_bootguard_valid(&m4));
    /* wrong check only */
    nw_bootguard_t e = fresh(); e.check ^= 1u;
    CHECK(!nw_bootguard_valid(&e));
    CHECK_EQ(nw_bootguard_boot(&e, NULL, NW_BG_RESET_OTHER).action, NW_BG_FALLBACK);
    /* out-of-range count with a stale check */
    nw_bootguard_t f = fresh(); f.failed_boots = 255;
    CHECK_EQ(nw_bootguard_boot(&f, NULL, NW_BG_RESET_OTHER).action, NW_BG_FALLBACK);
    CHECK(f.failed_boots <= N);
    /* corrupt state + pending OTA: still fallback, not a rollback (a corrupt counter says nothing about the image) */
    nw_bootguard_t g = fresh(); flip(&g, 5);
    nw_ota_boot_t p = pend(1);
    CHECK_EQ(nw_bootguard_boot(&g, &p, NW_BG_RESET_OTHER).action, NW_BG_FALLBACK);
    /* after a corrupt fallback the unit gets the probation boot like any other fallback */
    CHECK_EQ(nw_bootguard_boot(&g, NULL, NW_BG_RESET_OTHER).action, NW_BG_RUN);
    /* in_fallback set at the limit is a valid pair; in_fallback with a low count is still valid (probation sets the count itself) */
    nw_bootguard_t h = fresh(); h.in_fallback = 1; h.check = 0;
    CHECK(!nw_bootguard_valid(&h));
}

/* Adapter rule (b), header: a ROLLBACK that cannot be carried out must end in the fallback sleep, with the probation boot after it. */
static void test_rollback_failed_falls_to_fallback(void)
{
    nw_bootguard_t s = fresh();
    nw_ota_boot_t p = pend(1);
    for (unsigned i = 0; i < N; i++) CHECK_EQ(failed_boot(&s, &p).action, NW_BG_RUN);
    nw_bootguard_out_t r = failed_boot(&s, &p);
    CHECK_EQ(r.action, NW_BG_ROLLBACK);
    CHECK_EQ(s.failed_boots, 0);                           /* the guard cleared its counter on ROLLBACK: the adapter must repair this */
    nw_bootguard_out_t f = nw_bootguard_rollback_failed(&s);
    CHECK_EQ(f.action, NW_BG_FALLBACK);
    CHECK_EQ(f.why, NW_BG_WHY_ROLLBACK_FAILED);
    CHECK_EQ(f.sleep_s, NW_BOOTGUARD_FALLBACK_SLEEP_S);
    CHECK(!f.allow_ble);
    CHECK(!f.allow_wifi);
    CHECK_EQ(f.failed, N);
    CHECK(nw_bootguard_valid(&s));
    CHECK_EQ(s.in_fallback, 1);
    char line[128];
    CHECK(nw_bootguard_log_line(line, sizeof line, &f) > 0);
    CHECK(strstr(line, "NWBOOTGUARD fallback why=rollback_failed failed=5 limit=5 sleep_s=21600 ble=off wifi=off") == line);
    /* the next boot is the probation boot: one normal attempt, then straight back to the rollback attempt (the image is still pending) */
    CHECK_EQ(failed_boot(&s, &p).action, NW_BG_RUN);
    CHECK_EQ(failed_boot(&s, &p).action, NW_BG_ROLLBACK);
    /* from a corrupt or stale state it still lands in a valid fallback state */
    nw_bootguard_t g = fresh(); flip(&g, 6);
    CHECK_EQ(nw_bootguard_rollback_failed(&g).action, NW_BG_FALLBACK);
    CHECK(nw_bootguard_valid(&g));
}

int main(void)
{
    test_constants_and_budget();
    test_counter_increment_and_clear();
    test_threshold_reached_fallback();
    test_fallback_does_not_retry_radios();
    test_rollback_when_not_confirmed();
    test_magic_mismatch_needs_poweron_reset();
    test_log_shows_causing_count();
    test_corrupted_counter_fails_safe();
    test_rollback_failed_falls_to_fallback();
    printf("test_bootguard: %d checks, %d failed\n", nwtest_checked, nwtest_failed);
    return nwtest_failed ? 1 : 0;
}

/* Boot-loop guard and safe fallback (FR-D05, NFR-01, NFR-12). Pure C. See nw_bootguard.h. */
#include "nw_bootguard.h"
#include <stdio.h>
#include <string.h>

_Static_assert(sizeof(nw_bootguard_t) == NW_BOOTGUARD_RTC_BYTES, "retained guard state changed size: update NW_BOOTGUARD_RTC_BYTES and the budget text");
_Static_assert(NW_BOOTGUARD_MAX_FAILED_BOOTS >= 1u && NW_BOOTGUARD_MAX_FAILED_BOOTS < NW_OTA_MAX_UNCONFIRMED_BOOTS,
               "limit must be at least 1 and below the OTA window so a looping new image is rolled back before the window ends");

static uint32_t bg_check(const nw_bootguard_t *st)
{
    uint32_t v = ((uint32_t)st->failed_boots) | ((uint32_t)st->in_fallback << 8) | ((uint32_t)st->reserved << 16);
    return (st->magic ^ 0x9E3779B9u) + v * 0x01000193u;
}

static void seal(nw_bootguard_t *st) { st->check = bg_check(st); }

void nw_bootguard_init(nw_bootguard_t *st)
{
    memset(st, 0, sizeof *st);
    st->magic = NW_BOOTGUARD_MAGIC;
    seal(st);
}

bool nw_bootguard_valid(const nw_bootguard_t *st)
{
    if (st->magic != NW_BOOTGUARD_MAGIC) return false;
    if (st->failed_boots > NW_BOOTGUARD_MAX_FAILED_BOOTS) return false;
    if (st->in_fallback > 1) return false;
    if (st->reserved != 0) return false;
    return st->check == bg_check(st);
}

static nw_bootguard_out_t out_of(nw_bg_action_t a, nw_bg_why_t why, uint8_t failed)
{
    nw_bootguard_out_t o;
    o.action = a;
    o.allow_ble = (a == NW_BG_RUN);
    o.allow_wifi = (a == NW_BG_RUN);
    o.sleep_s = (a == NW_BG_FALLBACK) ? NW_BOOTGUARD_FALLBACK_SLEEP_S : 0;
    o.why = why;
    o.failed = failed;
    return o;
}

nw_bootguard_out_t nw_bootguard_boot(nw_bootguard_t *st, const nw_ota_boot_t *ota, nw_bg_reset_t reset)
{
    bool pending = ota && ota->pending_verify;

    if (st->magic != NW_BOOTGUARD_MAGIC && reset == NW_BG_RESET_POWERON) {   /* power-on: RTC memory is garbage, not a failure */
        nw_bootguard_init(st);
    } else if (!nw_bootguard_valid(st)) {             /* wrong magic without a power-on reset, or content wrong now: stop retrying */
        nw_bootguard_init(st);
        st->failed_boots = NW_BOOTGUARD_MAX_FAILED_BOOTS;
        st->in_fallback = 1;
        seal(st);
        return out_of(NW_BG_FALLBACK, NW_BG_WHY_CORRUPT, st->failed_boots);
    }

    if (st->in_fallback) {                            /* probation: the long sleep is over, one more normal attempt */
        st->in_fallback = 0;
        st->failed_boots = (uint8_t)(NW_BOOTGUARD_MAX_FAILED_BOOTS - 1u);
    }

    if (st->failed_boots >= NW_BOOTGUARD_MAX_FAILED_BOOTS) {
        if (pending) {                                 /* the new image is the suspect: back to the previous slot (FR-D05) */
            uint8_t seen = st->failed_boots;
            nw_bootguard_init(st);
            return out_of(NW_BG_ROLLBACK, NW_BG_WHY_OTA_LOOP, seen);
        }
        st->in_fallback = 1;
        seal(st);
        return out_of(NW_BG_FALLBACK, NW_BG_WHY_COUNT, st->failed_boots);
    }

    if (pending && nw_ota_boot_decide(ota) == NW_OTA_ROLLBACK) {   /* the 4.F4 window rule, not repeated here */
        uint8_t seen = st->failed_boots;
        nw_bootguard_init(st);
        return out_of(NW_BG_ROLLBACK, NW_BG_WHY_OTA_WINDOW, seen);
    }

    st->failed_boots++;
    seal(st);
    return out_of(NW_BG_RUN, NW_BG_WHY_NONE, st->failed_boots);
}

void nw_bootguard_confirm_good(nw_bootguard_t *st)
{
    nw_bootguard_init(st);
}

size_t nw_bootguard_log_line(char *buf, size_t cap, const nw_bootguard_out_t *out)
{
    static const char *const why_s[] = { "none", "count", "corrupt", "ota_loop", "ota_window" };
    if (!buf || cap == 0) return 0;
    buf[0] = 0;
    if (out->action == NW_BG_RUN) return 0;
    int n = snprintf(buf, cap, "NWBOOTGUARD %s why=%s failed=%u limit=%u sleep_s=%u ble=off wifi=off",
                     out->action == NW_BG_FALLBACK ? "fallback" : "rollback", why_s[out->why], (unsigned)out->failed,
                     (unsigned)NW_BOOTGUARD_MAX_FAILED_BOOTS, (unsigned)out->sleep_s);
    if (n < 0) { buf[0] = 0; return 0; }
    return (size_t)n < cap ? (size_t)n : cap - 1;
}

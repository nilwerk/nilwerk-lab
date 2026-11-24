/* Boot-loop guard and safe fallback. Pure C: no ESP-IDF, no flash, no radio. The ESP-IDF adapter only feeds it the retained state and acts on the answer.
 *
 * Requirements: FR-D05 covers ONLY the rollback branch (a new image that fails to confirm rolls back to the previous one; built on nw_ota_boot_decide,
 * not repeated here). The fallback state and its long sleep have no requirement of their own: they are a design proposal constrained by NFR-01
 * (a unit that resets in a loop must not burn its cell on endless Wi-Fi/BLE attempts) and NFR-12 (fallback is plain deep sleep, radios off, 50 uA
 * limit unchanged). FR-D04: offline samples stay in the RTC ring, which this guard never touches.
 *
 * NOT RUN ON HARDWARE. Every number marked [proposed] is a design proposal, not a decision (open point for Arsany).
 *
 * How it works (per boot, adapter order):
 *   1. nw_bootguard_boot(&rtc_guard, ota_or_null): counts this boot as "unconfirmed" and answers RUN, FALLBACK or ROLLBACK.
 *   2. RUN: normal cycle. When the cycle reaches its normal end (sample taken, about to deep-sleep) call nw_bootguard_confirm_good(): counter back to 0.
 *      A boot that dies before that point (panic, watchdog, brownout, reset button) leaves the count raised, so the next boot sees the failure.
 *   3. FALLBACK: no BLE, no Wi-Fi, no sensors. Log the one line from nw_bootguard_log_line(), deep sleep for out.sleep_s, nothing else.
 *   4. ROLLBACK: the running image is an unconfirmed OTA image and it is looping (or its window is used up): switch to the previous slot and reboot.
 *      A looping image rolls back at the START of boot N+1 (boot 6 with N = 5), after N failed boots. This is earlier than the decided 8-boot OTA
 *      window (A-116) and is NEW behaviour, accepted by the owner. It stays off until the bench proves it (Kconfig PLANT_BOOTGUARD).
 *
 * ADAPTER (task 4.F7b): components/bootguard/src/nw_bootguard_idf.c implements the rules below. It is compiled only with CONFIG_PLANT_BOOTGUARD (default n);
 * no CI build line sets that option, so it is NOT compiled by CI and NOT run on hardware. The CI build compiles THIS pure file for the ESP32-C3 (nw_bootguard.c.obj,
 * libbootguard.a), linked into no image. Reset-reason mapping and the sleep-path table are in nw_bootguard_map.h and tested on the host.
 * ADAPTER RULES (the contract the adapter follows, not verified on a board):
 *   (a) EVERY deliberate sleep path calls nw_bootguard_confirm_good() first: the normal end of a cycle, the low-battery skip (FR-D06), the BLE setup
 *       timeout on a never-provisioned unit (FR-D03), and just before an OTA reboot (otherwise the new image starts with the old image's raised count).
 *       A sleep path that forgets it counts a failed boot per wake and trips the fallback after N+1 wakes.
 *   (b) If ROLLBACK cannot be carried out (no valid previous slot, the call fails), the adapter must enter the FALLBACK sleep itself. The guard clears
 *       the counter on ROLLBACK, so without this the same image would loop forever with radios on.
 *   (c) Pass the real reset reason: NW_BG_RESET_POWERON only for a genuine power-on reset. Anything else (software, watchdog, brownout, deep-sleep wake,
 *       unknown) with a bad magic is treated as corruption and falls back.
 *   After a fallback sleep the next boot is a PROBATION boot: exactly one normal attempt. If it fails again, the guard goes straight back to fallback.
 */
#ifndef NW_BOOTGUARD_H
#define NW_BOOTGUARD_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "nw_ota.h"

/* Unconfirmed boots in a row that stop the retries: after this many failed boots the NEXT boot falls back instead of running.
 * [proposed] 5. Not an NFR value. Reasoning: 5 quick resets cost about 5 x 25 mA x ~1 s = ~35 uAh, small next to one hourly report; it is above one
 * stray reset or two (button, brownout on a weak USB port) and below the OTA window of 8 boots (NW_OTA_MAX_UNCONFIRMED_BOOTS, A-116 decided 8), so a
 * looping new image is rolled back by this guard before the slow 8-boot window ends. Open point for Arsany. */
#define NW_BOOTGUARD_MAX_FAILED_BOOTS 5u

/* Long sleep in fallback. [proposed] 21600 s = 6 h. Reasoning: 4 probation tries per day (up to 0.17 mAh each)
 * (estimate, 0.52 to 1.2 mAh/day in total vs 5.9 mAh/day in normal duty, power budget section 12) while a unit that recovers is back within 6 h; 24 h would save about 0.5 mAh/day more but delays alerts (FR-E03)
 * and a recovered unit by a day. Open point for Arsany. */
#define NW_BOOTGUARD_FALLBACK_SLEEP_S 21600u

/* Retained across deep sleep and software resets (RTC_NOINIT_ATTR in the adapter, see nw_bootguard_idf.c), 12 bytes. RTC memory, not NVS, as nw_cycle_state_t does: a counter
 * written on EVERY boot would wear flash (NVS is wear-levelled but a loop writes it thousands of times a day), RTC memory costs no write cycles.
 * Budget [proposed]: NW_BOOTGUARD_RTC_BYTES = 12 on top of nw_cycle_state_t, both together inside NW_CYCLE_RTC_BUDGET_BYTES (4096, also a proposal,
 * checked in test_bootguard.c). Limit: RTC memory is lost on a full power loss, so a loop that cuts the supply (brownout that drops the RTC domain)
 * is NOT counted. Whether a C3 brownout keeps RTC memory is UNVERIFIED (bench item). */
#define NW_BOOTGUARD_MAGIC 0x4E574247u   /* "NWBG": a mismatch means power-on garbage and re-initialises the counter (first boot) */
#define NW_BOOTGUARD_RTC_BYTES 12u

typedef struct {
    uint32_t magic;
    uint8_t failed_boots;    /* boots started and not confirmed, including the current one once nw_bootguard_boot returned RUN */
    uint8_t in_fallback;     /* 1 = the last answer was FALLBACK: the next boot is the probation boot */
    uint16_t reserved;       /* always 0 */
    uint32_t check;          /* over all fields above: a valid magic with a wrong check is corruption, not power-on */
} nw_bootguard_t;

typedef enum {
    NW_BG_RUN = 0,       /* normal cycle */
    NW_BG_FALLBACK,      /* stop retrying: no BLE, no Wi-Fi, sleep out.sleep_s, log one line */
    NW_BG_ROLLBACK       /* unconfirmed OTA image is failing: roll back to the previous slot and reboot (FR-D05, nw_ota) */
} nw_bg_action_t;

typedef enum {
    NW_BG_WHY_NONE = 0,
    NW_BG_WHY_COUNT,         /* failed boot count reached NW_BOOTGUARD_MAX_FAILED_BOOTS */
    NW_BG_WHY_CORRUPT,       /* retained counter had a valid magic but inconsistent content: fail safe */
    NW_BG_WHY_OTA_LOOP,      /* guard tripped while an unconfirmed OTA image was running */
    NW_BG_WHY_OTA_WINDOW,    /* OTA window used up without confirmation (nw_ota_boot_decide said ROLLBACK) */
    NW_BG_WHY_ROLLBACK_FAILED /* the adapter could not carry out a ROLLBACK answer (adapter rule b): fallback instead */
} nw_bg_why_t;

/* Why the retained magic may be wrong. Only NW_BG_RESET_POWERON explains a magic mismatch; 0 (OTHER) is the fail-safe default. */
typedef enum {
    NW_BG_RESET_OTHER = 0,   /* software, watchdog, brownout, deep-sleep wake, button, unknown */
    NW_BG_RESET_POWERON      /* genuine power-on reset: RTC memory legitimately holds garbage */
} nw_bg_reset_t;

typedef struct {
    nw_bg_action_t action;
    bool allow_ble;          /* false in FALLBACK and ROLLBACK: no BLE setup, no advertising */
    bool allow_wifi;         /* false in FALLBACK and ROLLBACK: no association, no SNTP, no upload */
    uint32_t sleep_s;        /* deep sleep for FALLBACK, else 0 */
    nw_bg_why_t why;
    uint8_t failed;          /* failed boots counted when the decision was made (what the log line shows) */
} nw_bootguard_out_t;

/* Re-initialise to a clean valid state (failed_boots 0, not in fallback). */
void nw_bootguard_init(nw_bootguard_t *st);

/* True when magic, fields and check are consistent. Out of range fields (failed_boots > MAX, in_fallback > 1, reserved != 0) are inconsistent. */
bool nw_bootguard_valid(const nw_bootguard_t *st);

/* Call once at the start of every boot, before any radio. `ota` is the OTA boot state (nw_ota_boot_t, unconfirmed_boots already incremented by the
 * caller as in nw_ota.h) or NULL when the running image is not an OTA image pending verify.
 *   - magic mismatch AND reset == NW_BG_RESET_POWERON: re-init, count this boot, RUN.
 *   - magic mismatch with any other reset reason: corruption, same as the next line (fail safe; a looping unit cannot hide behind a wiped magic).
 *   - valid magic, inconsistent content: re-init, answer FALLBACK (why CORRUPT), fail safe.
 *   - previous answer was FALLBACK: probation, exactly one more attempt.
 *   - failed_boots already at the limit: FALLBACK (why COUNT), or ROLLBACK when an unconfirmed OTA image is pending (why OTA_LOOP).
 *   - pending OTA image whose window is used up: ROLLBACK (why OTA_WINDOW), decided by nw_ota_boot_decide.
 *   - otherwise count this boot and RUN.
 * On ROLLBACK the counter is cleared so the previous image starts with a full budget. */
nw_bootguard_out_t nw_bootguard_boot(nw_bootguard_t *st, const nw_ota_boot_t *ota, nw_bg_reset_t reset);

/* Call when the cycle reaches its normal end (the deep sleep after a finished wake). Clears the counter and the probation flag. */
void nw_bootguard_confirm_good(nw_bootguard_t *st);

/* Adapter rule (b): call when a ROLLBACK answer could not be carried out. The guard cleared its counter on ROLLBACK, so this puts it back into the fallback
 * state (count at the limit, in_fallback 1: the next boot is the probation boot) and returns the FALLBACK answer (why ROLLBACK_FAILED, sleep_s as for any fallback). */
nw_bootguard_out_t nw_bootguard_rollback_failed(nw_bootguard_t *st);

/* One log line, no newline inside, NUL-terminated, truncated to cap: "NWBOOTGUARD <action> why=<w> failed=<n> limit=<N> sleep_s=<s> ble=off wifi=off".
 * Returns the length written, 0 for RUN (nothing to log) or cap == 0. */
size_t nw_bootguard_log_line(char *buf, size_t cap, const nw_bootguard_out_t *out);

#endif

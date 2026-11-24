/* ESP-IDF adapter for the boot-loop guard (task 4.F7b, FR-D05, NFR-01, NFR-12). See nw_bootguard.h for the contract and nw_bootguard_idf.h for the API.
 * Compiled only with CONFIG_PLANT_BOOTGUARD. NOT COMPILED BY CI (no build line sets the option), NOT RUN ON HARDWARE.
 *
 * Deliberate sleep paths and whether they call confirm_good (header rules a and c; the table is nw_bg_path_confirms, pinned by test_bootguard_map):
 *   normal end of the cycle (upload path and bench loop)      main.c, NW_BG_PATH_NORMAL_END            confirms
 *   low-battery skip (FR-D06)                                 same exit as the normal end in main.c    confirms
 *   BLE setup timeout, never-provisioned unit (FR-D03)        main.c, NW_BG_PATH_BLE_SETUP_TIMEOUT     confirms
 *   just before an OTA reboot                                 NO caller yet (no OTA adapter)           would confirm
 *   reset button, also during pairing                         hardware reset, no code runs             does NOT confirm, counted as a failed boot
 *   restart after a revoked token (FR-D07, nw_upload_idf.c)   esp_restart() there, not changed         does NOT confirm, one count, next boot confirms
 *   HAL init failure in main.c (`return;` from app_main)    never sleeps, never confirms             counted as a failed boot, ends in fallback after N+1 tries
 *   the guard's fallback sleep                                this file                                does NOT confirm (probation must survive)
 *   sleep after a failed rollback                             this file                                does NOT confirm
 */
#include "sdkconfig.h"
#include "nw_bootguard_idf.h"

#ifdef CONFIG_PLANT_BOOTGUARD
#include <stdint.h>
#include <stdio.h>
#include "esp_attr.h"
#include "esp_log.h"
#include "esp_ota_ops.h"
#include "esp_sleep.h"
#include "esp_system.h"
#include "nw_bootguard.h"

_Static_assert(NW_BG_IDF_RST_POWERON == (int)ESP_RST_POWERON, "nw_bootguard_map.h: ESP_RST_POWERON value drifted");

static const char *TAG = "bootguard";

/* RTC_NOINIT, not RTC_DATA_ATTR: RTC_DATA_ATTR is re-initialised from the image on any reset that is not a deep-sleep wake (as I read the IDF docs;
 * bench item), which would wipe the counter exactly in the panic/watchdog/reset loop the guard exists for. RTC_NOINIT keeps its bytes across
 * software resets and deep sleep; after a power-on it is garbage, which the magic and check in nw_bootguard_t exist to detect. 12 bytes. */
static RTC_NOINIT_ATTR nw_bootguard_t s_guard;

/* The OTA "pending verify" flag. The OTA component (nw_ota) decides the rollback window in nw_ota_boot_decide(); this adapter only fills its input
 * struct from the bootloader's image state and does NOT repeat the window rule. The window counter (unconfirmed_boots) belongs to the OTA adapter,
 * which is not written: it is passed as 0, so the guard's OTA_WINDOW branch cannot fire yet and only the loop branch (OTA_LOOP) can. */
static bool read_ota_state(nw_ota_boot_t *o)
{
    const esp_partition_t *running = esp_ota_get_running_partition();
    esp_ota_img_states_t state;
    if (running == NULL || esp_ota_get_state_partition(running, &state) != ESP_OK) return false;   /* factory app or no OTA data: not pending */
    if (state != ESP_OTA_IMG_PENDING_VERIFY) return false;
    o->pending_verify = true;
    o->unconfirmed_boots = 0;
    o->ingest_ok = false;
    o->max_unconfirmed_boots = NW_OTA_MAX_UNCONFIRMED_BOOTS;
    return true;
}

static void log_answer(const nw_bootguard_out_t *out)
{
    char line[128];
    if (nw_bootguard_log_line(line, sizeof line, out) > 0) ESP_LOGW(TAG, "%s", line);
}

/* Radios were never started (the guard runs first), so this is plain deep sleep. UNVERIFIED (bench): the soil supply pin (IO3) is not configured on
 * this path, so its level in sleep depends on the board pull-down (NFR-12), same open point as the setup-flow sleep in main.c. */
static void fallback_sleep(uint32_t sleep_s)
{
    fflush(stdout);
    esp_sleep_enable_timer_wakeup((uint64_t)sleep_s * 1000000ULL);
    esp_deep_sleep_start();
    for (;;) { }   /* not reached */
}

void nw_bootguard_idf_start(void)
{
    nw_ota_boot_t ota;
    bool pending = read_ota_state(&ota);
    nw_bootguard_out_t out = nw_bootguard_boot(&s_guard, pending ? &ota : NULL, nw_bg_map_reset_reason((int)esp_reset_reason()));
    if (out.action == NW_BG_RUN) return;
    log_answer(&out);
    if (out.action == NW_BG_ROLLBACK) {
        esp_ota_mark_app_invalid_rollback_and_reboot();   /* returns only on failure (no valid previous slot, no OTA data) */
        out = nw_bootguard_rollback_failed(&s_guard);     /* rule (b): a failed rollback falls to the fallback sleep */
        log_answer(&out);
    }
    fallback_sleep(out.sleep_s);
}

void nw_bootguard_idf_confirm(nw_bg_path_t path)
{
    if (nw_bg_path_confirms(path)) nw_bootguard_confirm_good(&s_guard);
}
#endif /* CONFIG_PLANT_BOOTGUARD */

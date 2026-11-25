/* Pure helpers for the boot-loop guard's ESP-IDF adapter (task 4.F7b). No ESP-IDF include: built by test/host and always compiled by the component.
 * Two things live here so the host tests can pin them: the reset-reason mapping and the sleep-path table. NOT RUN ON HARDWARE. */
#ifndef NW_BOOTGUARD_MAP_H
#define NW_BOOTGUARD_MAP_H

#include <stdbool.h>
#include "nw_bootguard.h"

/* Value of ESP_RST_POWERON in esp_reset_reason_t. The adapter has a _Static_assert against the real enum, so a drift breaks the ESP-IDF build. */
#define NW_BG_IDF_RST_POWERON 1

/* esp_reset_reason() as an int in, guard reset reason out. POWERON only for a genuine power-on reset; software, panic, watchdog, brownout, external
 * pin, deep-sleep wake, UNKNOWN (0) and any value this code has never seen map to NW_BG_RESET_OTHER, the fail-safe value 0 (header rule c). */
nw_bg_reset_t nw_bg_map_reset_reason(int idf_reason);

/* Every way a boot can end (or be cut short) on purpose or by the user, with whether it calls nw_bootguard_confirm_good() first (header rules a and c). */
typedef enum {
    NW_BG_PATH_NORMAL_END = 0,      /* sample taken (and report tried), about to deep-sleep: CONFIRMS */
    NW_BG_PATH_LOW_BATTERY_SKIP,    /* FR-D06 low-battery cycle: shares the normal exit in main.c (nw_upload_idf_wake returns the sleep time): CONFIRMS */
    NW_BG_PATH_BLE_SETUP_TIMEOUT,   /* never-provisioned unit, setup window closed, deep sleep until reset (FR-D03): CONFIRMS */
    NW_BG_PATH_BEFORE_OTA_REBOOT,   /* deliberate reboot into a fresh OTA image: CONFIRMS (no caller yet: the OTA adapter does not exist) */
    NW_BG_PATH_RESET_BUTTON,        /* reset button (EN) pressed, also during pairing: a hardware reset, no code runs, does NOT confirm and is counted */
    NW_BG_PATH_TOKEN_REVOKED_RESTART, /* esp_restart() after a revoked token (FR-D07): does NOT confirm, costs one count, the next boot's setup path confirms */
    NW_BG_PATH_FALLBACK_SLEEP,      /* the guard's own long sleep: must NOT confirm, or the probation boot is lost */
    NW_BG_PATH_ROLLBACK_FAILED_SLEEP, /* rollback call returned (failed) and the unit sleeps: must NOT confirm */
    NW_BG_PATH_COUNT
} nw_bg_path_t;

/* True when the path calls nw_bootguard_confirm_good(). Out of range: false (fail safe: the count keeps rising, the unit ends in fallback). */
bool nw_bg_path_confirms(nw_bg_path_t path);

#endif

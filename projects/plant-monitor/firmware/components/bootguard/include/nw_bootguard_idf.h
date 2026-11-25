/* ESP-IDF adapter for the boot-loop guard (task 4.F7b, FR-D05, NFR-01, NFR-12). Compiled only with CONFIG_PLANT_BOOTGUARD (default n).
 * NOT COMPILED FOR ESP-IDF YET (no CI build line sets the option, no local build), NOT RUN ON HARDWARE. */
#ifndef NW_BOOTGUARD_IDF_H
#define NW_BOOTGUARD_IDF_H

#include "nw_bootguard_map.h"

/* Call FIRST in app_main, before any radio, sensor or storage work. Returns only when the answer is RUN.
 * FALLBACK: logs the guard's one line and deep-sleeps for the guard's fallback time (no BLE, no Wi-Fi); does not return.
 * ROLLBACK: logs one line, calls esp_ota_mark_app_invalid_rollback_and_reboot() (does not return when it works); when it fails, puts the guard into the
 * fallback state (nw_bootguard_rollback_failed), logs the fallback line and deep-sleeps; does not return. */
void nw_bootguard_idf_start(void);

/* Call on every deliberate end of a boot. Confirms (counter back to 0) only when the sleep-path table says so (nw_bg_path_confirms). */
void nw_bootguard_idf_confirm(nw_bg_path_t path);

#endif

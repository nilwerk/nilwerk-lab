/* ESP-IDF adapter of the hourly upload (task 4.F3 slice 3): Wi-Fi station with the stored credentials, SNTP, HTTPS POST on esp_http_client with
 * the ESP-IDF certificate bundle, RTC-retained nw_cycle_state_t. Compiled only with CONFIG_PLANT_UPLOAD.
 * NOT COMPILED OR RUN BY ITS AUTHOR (no ESP-IDF in the sandbox): the first compile is CI's "ESP-IDF build (esp32c3, upload)" step; it has never
 * run on a board. All decisions are in nw_cycle.c / nw_upload.c / nw_sleep.c (host-tested); this file only does I/O. */
#ifndef NW_UPLOAD_IDF_H
#define NW_UPLOAD_IDF_H

#include <stdint.h>
#include "nw_cycle.h"

/* One wake, called by main.c after the sensors were read (readings + their error codes). Blocks while the radio is on (Wi-Fi join and SNTP are each
 * bounded by CONFIG_PLANT_UPLOAD_NET_TIMEOUT_S, the POST by CONFIG_PLANT_UPLOAD_HTTP_TIMEOUT_MS). Returns the deep-sleep time in seconds; the
 * caller sleeps. A revoked token (401 token_revoked) erases the stored record and restarts into setup, so in that case it does not return. */
uint32_t nw_upload_idf_wake(const nw_soil_t *soil, nw_err_t e_soil, const nw_aht20_t *aht, nw_err_t e_aht, const nw_bh1750_t *bh, nw_err_t e_bh,
                            uint32_t vbat_mv, nw_err_t e_bat);

#endif

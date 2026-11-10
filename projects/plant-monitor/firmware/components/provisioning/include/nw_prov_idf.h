/* ESP-IDF side of the setup flow (task 4.F2 slice 2): NimBLE + wifi_provisioning (protocomm security 2), Wi-Fi station,
 * esp_http_client for POST /device-claim. NOT COMPILED AND NOT RUN by the author (no ESP-IDF in the authoring sandbox);
 * first compile is the CI job "ESP-IDF build (esp32c3)". FR-D03, FR-D07, FR-D09, NFR-06. */
#ifndef NW_PROV_IDF_H
#define NW_PROV_IDF_H

#include <stdbool.h>
#include <stdint.h>

typedef enum { NW_SETUP_NORMAL = 0, NW_SETUP_SLEEP_UNTIL_RESET } nw_setup_result_t;

/* Runs the whole boot decision and, if needed, setup mode, blocking until setup ends (claimed, or closed by the 5 attempt /
 * 5 minute limit). button_held_ms: how long the setup button was held at power-up (main.c measures it).
 * Returns what the caller must do next: continue with normal operation, or deep sleep with no timer (never provisioned,
 * setup closed). BLE and Wi-Fi are off on return (FR-D09). */
nw_setup_result_t nw_setup_run(uint32_t button_held_ms);

#endif

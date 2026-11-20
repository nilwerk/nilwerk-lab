# OTA image check and rollback decision (task 4.F4, FR-D05, ADR-009). Pure C in this slice: nw_ota.c has no ESP-IDF
# dependency and is built by test/host without ESP-IDF. The ESP-IDF adapter (esp_https_ota download into the inactive slot,
# esp_ota_mark_app_valid_cancel_rollback, RTC-retained boot counter) is NOT written yet; main does not require this
# component in this slice, so the ESP-IDF build does not compile it. NOT COMPILED for ESP-IDF, NOT ON HARDWARE.
idf_component_register(
    SRCS "src/nw_ota.c"
    INCLUDE_DIRS "include"
)

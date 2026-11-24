# Boot-loop guard and safe fallback (FR-D05, NFR-01, NFR-12). Pure C in this slice: nw_bootguard.c has no ESP-IDF dependency and is built by
# test/host without ESP-IDF. The ESP-IDF adapter (RTC_DATA_ATTR instance, reading the OTA pending flag, esp_ota_mark_app_invalid_rollback_and_reboot,
# esp_deep_sleep) is NOT written yet; main does not require this component in this slice, so the ESP-IDF build and the QEMU boot check do not
# compile or run it. NOT COMPILED for ESP-IDF, NOT ON HARDWARE.
idf_component_register(
    SRCS "src/nw_bootguard.c"
    INCLUDE_DIRS "include"
    REQUIRES ota
)

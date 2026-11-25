# Boot-loop guard and safe fallback (FR-D05, NFR-01, NFR-12).
# nw_bootguard.c and nw_bootguard_map.c are pure C (no ESP-IDF) and built by test/host. CI compiles them for the ESP32-C3 (log lines nw_bootguard.c.obj,
# libbootguard.a) as a component that no image links, because the default build does not use the guard.
# nw_bootguard_idf.c (task 4.F7b: RTC_NOINIT state, OTA pending flag, rollback, fallback deep sleep) is added ONLY with CONFIG_PLANT_BOOTGUARD (default n).
# No CI build line sets that option, so the adapter is NOT compiled for ESP-IDF yet and NOT run on hardware: its first compile is a manual build with
# sdkconfig.defaults.bootguard (see that file). The PRIV_REQUIRES are unconditional on purpose (CONFIG_* is not known when requirements expand).
set(srcs "src/nw_bootguard.c" "src/nw_bootguard_map.c")
if(CONFIG_PLANT_BOOTGUARD)
    list(APPEND srcs "src/nw_bootguard_idf.c")
endif()
idf_component_register(
    SRCS ${srcs}
    INCLUDE_DIRS "include"
    REQUIRES ota
    PRIV_REQUIRES app_update esp_system esp_hw_support log
)

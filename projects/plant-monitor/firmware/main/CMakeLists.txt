# upload is required unconditionally: CONFIG_* values are NOT available while ESP-IDF evaluates component requirements (early expansion), so a
# conditional `list(APPEND req upload)` silently dropped it and main.c could not find nw_upload_idf.h (CI run 392, upload build step). With the option
# off the component only compiles its pure-C files and nothing in main.c references it.
idf_component_register(SRCS "main.c" "sim_mock_hal.c" INCLUDE_DIRS "." REQUIRES sensors provisioning upload PRIV_REQUIRES driver esp_system)
# SIMULATOR ONLY. Linking esp_wifi (setup image) pulls the ADC2 calibration constructor (adc2_init_cal.c, run before app_main), which
# busy-waits for an ADC self-calibration conversion that QEMU's ESP32-C3 model never completes. Wrap that one call; sim_mock_hal.c answers
# it. Option off: no link change, so every board build is unchanged.
if(CONFIG_PLANT_SIM_MOCK_SENSORS)
    target_link_options(${COMPONENT_LIB} INTERFACE "-Wl,--wrap=adc_hal_self_calibration")
endif()

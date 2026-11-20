# upload is required unconditionally: CONFIG_* values are NOT available while ESP-IDF evaluates component requirements (early expansion), so a
# conditional `list(APPEND req upload)` silently dropped it and main.c could not find nw_upload_idf.h (CI run 392, upload build step). With the option
# off the component only compiles its pure-C files and nothing in main.c references it.
idf_component_register(SRCS "main.c" "sim_mock_hal.c" INCLUDE_DIRS "." REQUIRES sensors provisioning upload PRIV_REQUIRES driver esp_system)

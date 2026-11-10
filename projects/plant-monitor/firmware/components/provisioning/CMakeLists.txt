# Provisioning logic (task 4.F2). nw_prov*.c (state machine, protocol, glue core) are pure C and also built by test/host without ESP-IDF;
# the NVS adapter and nw_prov_idf.c (NimBLE + wifi_provisioning + Wi-Fi + HTTP) are IDF-only.
# nw_prov_idf.c is NOT COMPILED by its author (slice 2); the first compile is the CI "ESP-IDF build (esp32c3)" job.
set(srcs "src/nw_prov_proto.c" "src/nw_prov.c" "src/nw_prov_glue.c" "src/nw_prov_store_nvs.c")
if(CONFIG_PLANT_SETUP_FLOW)
    list(APPEND srcs "src/nw_prov_idf.c")
endif()
idf_component_register(
    SRCS ${srcs}
    INCLUDE_DIRS "include"
    REQUIRES nvs_flash
    PRIV_REQUIRES esp_wifi esp_event esp_netif esp_http_client esp_timer mbedtls wifi_provisioning protocomm bt esp-tls
)

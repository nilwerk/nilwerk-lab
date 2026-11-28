# Hourly upload (task 4.F3). nw_upload.c (response table, backoff) and nw_cycle.c (one wake: credentials check, sample mapping, cadence, report/outage
# state) are pure C and also built by test/host without ESP-IDF. nw_upload_idf.c (Wi-Fi, SNTP, esp_http_client with the pinned CA, nw_ingest_ca.h) is
# IDF-only and compiled only with CONFIG_PLANT_UPLOAD (default off). NOT COMPILED by its author (slice 3): the first compile is CI's upload build step.
set(srcs "src/nw_upload.c" "src/nw_cycle.c")
if(CONFIG_PLANT_UPLOAD)
    list(APPEND srcs "src/nw_upload_idf.c")
endif()
idf_component_register(
    SRCS ${srcs}
    INCLUDE_DIRS "include"
    REQUIRES storage report power sensors provisioning
    PRIV_REQUIRES nvs_flash esp_wifi esp_event esp_netif esp_http_client esp-tls mbedtls
)

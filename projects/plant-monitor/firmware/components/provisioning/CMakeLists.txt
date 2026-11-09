# Provisioning logic (task 4.F2). nw_prov*.c are pure C and also built by test/host without ESP-IDF; the NVS adapter is IDF-only.
# No BLE stack yet (separate slice: wifi_provisioning + NimBLE glue), so nothing here pulls bluetooth into the image.
idf_component_register(
    SRCS "src/nw_prov_proto.c" "src/nw_prov.c" "src/nw_prov_store_nvs.c"
    INCLUDE_DIRS "include"
    REQUIRES nvs_flash
)

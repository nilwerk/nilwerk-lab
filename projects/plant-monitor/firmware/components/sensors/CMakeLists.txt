# Sensor drivers (task 4.F1). The nw_*.c files are pure C and are also built by test/host without ESP-IDF.
idf_component_register(
    SRCS "src/nw_aht20.c" "src/nw_bh1750.c" "src/nw_soil.c" "src/nw_battery.c" "src/hal_esp32.c"
    INCLUDE_DIRS "include"
    REQUIRES driver esp_adc esp_driver_gpio esp_driver_i2c
)

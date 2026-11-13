# Embedded skills — ESP32-C3, ESP-IDF, edge AI

| Name | What | URL | Status | Used by |
|---|---|---|---|---|
| ESP-IDF programming guide (ESP32-C3) | Build, drivers, sleep modes, NVS. **The page shows v6.1, not v5.x: the version pin is open (see Note).** | https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/ | verified 13 Nov (Lead fetch) (official, version pin open) | Mira |
| esp-tflite-micro | TFLite Micro port for ESP32 (ESP-NN kernels); ESP-NN table covers ESP32-C3 | https://github.com/espressif/esp-tflite-micro | verified 13 Nov (Lead fetch) | Mira |
| TensorFlow Lite for Microcontrollers | int8 export, op coverage | https://www.tensorflow.org/lite/microcontrollers | to verify | Mira |
| NimBLE in ESP-IDF | BLE stack for setup | https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/bluetooth/nimble/index.html | to verify | Mira |
| ESP-IDF Wi-Fi provisioning | Provisioning component | https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/provisioning/provisioning.html | to verify | Mira |
| ESP-IDF unit tests | Host and target tests | https://docs.espressif.com/projects/esp-idf/en/latest/esp32c3/api-guides/unit-tests.html | to verify | Mira, Ines |

Rule: check every API name against the library source before coding (Mira, meeting 13 Nov).

Note (Lead, 13 Nov): the ESP-IDF page we link shows v6.1. Our guidelines and TEAM say ESP-IDF v5.x. Theo and Mira decide the version pin before the firmware build; until then do not claim a version.

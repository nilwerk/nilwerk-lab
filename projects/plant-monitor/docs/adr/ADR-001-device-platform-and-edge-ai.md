# ADR-001: ESP32-C3-MINI-1, ESP-IDF, on-device TFLite Micro

Status: Accepted for G2 review (follows Q-02, Q-16) · Date: 2026-11-03 · Deciders: Arsany (Q-02/Q-16), Theo

## Context
Need BLE setup, Wi-Fi, deep sleep, OTA and two small models (thirst forecast, event/fault detection) on a battery device with a pre-certified module (NFR-08). Requirements: FR-D01..D07, FR-E01..E04, NFR-01.

## Decision
ESP32-C3-MINI-1 module, ESP-IDF 5.x in C, esp-tflite-micro with ESP-NN, int8 models under 30 KB flash, 20 KB RAM, 50 ms. Sampling every 15 min with Wi-Fi off; hourly Wi-Fi report; features use relative moisture (0-100 % between each device's dry/wet points) and slopes.

## Alternatives
- Keep ESP8266: no BLE, no TFLite Micro support; rejected in Q-02.
- ESP32-S3: more power and cost; reserved for the out-of-scope camera option.

## Consequences
+ BLE + Wi-Fi on one pre-certified module; one OTA mechanism. - Single core RISC-V, tight RAM: model and TLS buffers must be budgeted together (risk O-1, O-2). Models are built and validated under `ml/` (Python 3.11).

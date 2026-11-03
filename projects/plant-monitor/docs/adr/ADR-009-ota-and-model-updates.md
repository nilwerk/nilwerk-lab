# ADR-009: OTA via ingest manifest, dual slot, rollback; models in own partition

Status: Accepted for G2 review · Date: 2026-11-03 · Deciders: Theo, Mira

## Context
FR-D05 (update with automatic rollback), Req §5 (new models via OTA), NFR-06.

## Decision
The `/ingest` response includes `fw_target` and `model_target` with signed Storage URLs and SHA-256. Device downloads into the inactive OTA slot (ESP-IDF `esp_https_ota`), verifies hash, reboots, and confirms the image only after the next successful ingest; otherwise bootloader rollback. Models sit in a separate data partition. Update only when battery is above a threshold. Secure boot / signed images are deferred (risk O-3).

## Alternatives
Separate OTA server or MQTT: extra moving part. Always-on polling: costs battery.

## Consequences
Updates take effect within one reporting cycle; staged rollout is by per-device `fw_target`, which is enough for 3 units.

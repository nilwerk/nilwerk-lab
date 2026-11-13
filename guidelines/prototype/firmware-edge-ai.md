# Firmware and edge AI
- Contract constants live in code with FR/NFR ID comments; tests and PRs cite the same IDs.
- Golden-file drift test: report payload checked against `docs/interfaces/device-report.schema.json` and a checked-in example.
- Every reviewer condition becomes a named host test that cites the review comment.
- Every timing or power PR states the estimated µA per state and the deep-sleep budget.
- Persistent device state (RTC/NVS) is listed in the feature spec before training.
- N-of-M debounce: worst-case alert latency stated in the PR.
- Windows are segment-aware. Synthetic data is flagged, reported separately and has provenance (source, licence, version).
- Edge AI budgets: int8, < 30 KB flash, < 20 KB RAM, < 50 ms, always compared to the watering-interval baseline.
- Security: TLS, per-device token, signed OTA with rollback.
- Flash or OpenOCD errors: check the board profile, port, cable and bootloader mode before touching code.
- Slice tasks to about 5 agent minutes; one PR concern each.

- Reference conventions from Arsany's other project (C99, CMocka, layered `hardware_layer`/`sensor_layer`) live in `skills/vendor/agents-reference/firmware.instructions.md`. Ideas worth keeping: only the hardware layer touches registers; one module per component with its own test; no magic numbers. Our toolchain is ESP-IDF, so do not copy its build rules.
- Verify board pinouts, voltage limits and library support in official vendor documentation. Never guess from a similar board.
- State exactly what was and was not tested on hardware. Never claim a flash, sensor reading or physical test that did not happen.

- Before copying open-source code (IDF or esp-tflite-micro examples), check its licence and keep the notices.
- In troubleshooting, separate observed facts from likely causes. First bring-up on a current-limited supply with no LiPo straight on a rail (see `safety.md`).
- Host test baseline: `test/host` builds with gcc and runs 7 of 7 ctest tests incl. two mutation suites (about 31 s). The IDF-only files (`hal_esp32.c`, `nw_prov_idf.c`) are compiled only in CI. Re-check the C standard and warning defaults after the ESP-IDF version pin.

# Soil sensor calibration: dry reads low, wet reads high, and the upload accepts only a pinned certificate authority

**What it shows.** The soil-moisture calibration of the plant monitor now follows the probe's real direction. In dry air the raw reading is low (about 15 to 25 counts), and in water it is high (about 360 counts). The top picture is the output of the host tests for the firmware, run on a PC. The bottom picture is the mapping curve from the same code: 0 % at the dry point, 100 % at the wet point, and an error if someone enters the two points the wrong way round. The hourly upload now trusts only one pinned certificate authority and sends nothing until that authority is set.

**Agent minutes:** 8.4 (measured from launch to this caption; the Agent Log holds the final figure)
**Human estimate:** 4 h for an experienced embedded engineer without AI (own judgement: calibration logic with direction guard, host tests and mutants, a certificate pin with a fail-closed path, two contract checks with self-tests, and updates to the bench documents).

**Images.**
1. Host test output: all 38 host test suites pass on a PC, including 44 of 44 mutants of the sensor driver logic killed, and the new checks for the calibration direction and the certificate pin.
2. Soil mapping curve, drawn from the compiled calibration function with the device defaults (dry 20, wet 360).

**Verified.** The host test suite passes (38 of 38 suites, run on the committed code). The sensor driver tests pass (468 checks, 0 failed). The calibration direction is covered by tests that fail when the direction is inverted or the two points are swapped.

**Not verified.**
- The ESP-IDF firmware build has not been run, so the upload code has not been compiled for the device.
- Nothing has run on a board. The probe readings (20 dry, 360 wet) are two spot readings from the bench, not a calibration per soil type, and the accuracy target is not measured yet.
- The upload stays off until the certificate authority for the ingest server is supplied, so no data is sent from this build.

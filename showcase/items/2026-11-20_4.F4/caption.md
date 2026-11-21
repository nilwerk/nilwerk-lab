# Firmware OTA: image hash check and rollback decision (host tests, not on hardware)

**What it shows.** The pure-C logic for firmware over-the-air updates runs on a PC, with no device and no network. The image check computes SHA-256 and rejects any image whose hash does not match the expected value (a changed byte, a truncated or extended image, a digest that differs in one byte). The rollback decision keeps a new image only after a successful cloud report; if no report confirms it within the window, the decision is to roll back to the previous slot. A mutation check shows the tests fail when the hash comparison is weakened or the window boundary moves, and pass again once restored.

**Task.** 4.F4, Firmware: OTA updates (FR-D05, ADR-009). Scope: logic and host tests only.

**Persona.** Firmware + Edge AI role.

**Time.** Agent minutes: about 5 (measured from the first to the last clock reading of this run, 19:36 to the caption write, 19:41 Berlin time; the run's final time block is in the PR). Own human estimate for an experienced engineer: about 4 h.

**Images.** None. The owner asked for no images in the repository for this item.

**Verified on a PC.** 44 host checks pass with address and undefined-behaviour sanitizers; 12 of 12 mutants are caught by the tests; the full host suite (26 test runs) passes.

**Unverified.** The ESP-IDF build of the new component, real flash partitions and the rollback on a device, the download over TLS from the cloud (no live endpoint), signed images (a documented follow-up), the 8-boot rollback window (a proposed value, open question to the team), and the simulator: the rollback path is not yet part of the firmware image, so the boot simulator was not extended.

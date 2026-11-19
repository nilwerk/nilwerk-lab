# 4.F3 slice 4: the saved sample buffer is checked after every deep sleep

**What it shows:** the host-test log (`host-tests-output.txt`) for the new integrity check of the 96-sample buffer that lives in RTC memory. After each wake the retained copy is checked (ring indices, sample order, schema ranges, flags), not only a magic number; a damaged copy is reset instead of writing outside the buffer. The retained state is 3140 bytes, held under a 4096-byte budget by a compile-time check. 47 of 47 hand-made mutants killed, 21 of 21 ctest entries pass.

- Task: 4.F3 (slice 4), persona: Mira (Firmware + Edge AI), branch `agent/firmware/4.F3-s4`, PR: see the PR list for this branch.
- Agent minutes and human-hour estimate: in the PR description.
- Unverified: nothing ran on a board; no ESP-IDF build was run (no toolchain in the session); whether RTC memory really keeps the buffer across deep sleep, and the 4096-byte budget, are still to be checked with `idf.py size` and on the bench.

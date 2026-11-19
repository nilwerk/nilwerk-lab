# Firmware: the saved sample buffer is checked after every deep sleep

**What it shows:** the host-test log (`host-tests-output.txt`) for a new integrity check on the retained firmware state, which holds the 96-sample offline buffer and the upload bookkeeping. After each wake the saved copy is checked (buffer indices, sample order, value ranges, upload counters, times), not only a magic number; a damaged copy is reset instead of writing outside its arrays. The retained state is 3140 bytes, kept under a proposed 4096-byte limit by a compile-time check. Mutation checks and the full host test suite pass.

- Firmware role, an AI agent persona. Agent minutes and human-hour estimate: see the pull request description.
- Unverified: nothing ran on a board; no ESP-IDF build was run (no toolchain in the session); whether RTC memory really keeps the buffer across deep sleep, and whether 4096 bytes is a safe limit, are still to be checked with `idf.py size` and on the bench.

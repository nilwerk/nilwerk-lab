# 4.F3 slice 2: hourly upload logic, tested without a network

**What it shows:** the host-test log (`host-tests-output.txt`) for the new `upload` component: request URL and bearer-token header, response handling against the deployed `/ingest` contract (ack, 401 revoked vs invalid, 400/413, 429 Retry-After, 5xx), exponential backoff, the 6-requests-per-hour cap, low-battery behaviour, and draining the 24 h buffer only on a real ack. 596 checks in `test_upload`, 45 of 45 mutants killed, 19 of 19 ctest entries pass.

- Task: 4.F3 (slice 2), persona: Mira (Firmware + Edge AI), branch `agent/firmware/4.F3-slice2`, PR: see the PR list for this branch.
- Agent minutes and human-hour estimate: in the PR description.
- Unverified: no real HTTP, TLS or Wi-Fi code exists yet (only a fake transport), no ESP-IDF build was run (no toolchain in the session), nothing ran on hardware, the base URL is not set anywhere (A-082), backoff and low-battery timings are ASSUMED.

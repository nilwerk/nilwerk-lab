# CI: v1 firmware build and care-tips Deno checks

**What it shows:** `ci.yml` now (1) builds the firmware a second time with the v1 perfboard defaults (`PLANT_BOARD_V1_SUPERMINI`, separate build dir `build-v1` and `sdkconfig.v1`, then greps that the option really is on), and the `detect` gate also runs the firmware job on `v1/` changes (WIRING.md pin table is checked by a host test); (2) the cloud job runs `deno lint tips/*.ts` and `deno check` for the tips sources and `tips/test/tips.test.ts`. Evidence: `deno-local-output.txt` (local Deno 2.1.4, same as CI) and the PR's own CI run.

- Task: ci-v1-and-tips (extra round), persona: Kai (Pipeline / DevOps), branch `agent/devops/ci-v1-and-tips`.
- Finding, not hidden: `deno lint` fails on `tips/test/tips.test.ts` (5x require-await, async stubs at lines 15, 21, 154, 175, 194). Lint in CI therefore covers `tips/*.ts` only; no rule was weakened, the test file is still type-checked. Owner (cloud-ai) fixes the stubs, then lint can include the test file.
- Unverified locally: the ESP-IDF builds (no toolchain in the sandbox); the CI run is the evidence.

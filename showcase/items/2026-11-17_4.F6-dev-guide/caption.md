# 4.F6 firmware dev guide for new joiners

**What it shows:** the evidence file `evidence-output.txt` holds the real run of the 19 firmware host tests (19 of 19 pass, with the new guide in the tree) and the link check of the new `firmware/DEV_GUIDE.md`: all relative links resolve. The guide takes a person who has never used ESP-IDF from install to a first flash and a bench check on either board.

- Task: 4.F6 (WO-005 / issue #68 enabler), persona: Mira (Firmware + Edge AI), branch `agent/firmware/4.F6-dev-guide`, PR: see the PR list for this branch.
- Agent minutes: not yet logged in the Agent Log. Human-hour estimate by the agent: about 6 h.
- Unverified: no ESP-IDF install, build, flash or serial output was run (no toolchain, no hardware); install steps and OS-specific port/driver details are marked UNVERIFIED in the guide; host tests were run on Linux only.

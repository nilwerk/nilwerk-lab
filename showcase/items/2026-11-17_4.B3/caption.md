# 4.B3 slice 1: care-tips guardrail layer (premium)

**What it shows:** the real terminal output of the 31 unit tests and the 42-mutant check for the deterministic rule layer that every care tip must pass (e.g. never advise watering when the soil is waterlogged), with weather and the text assistant injected as stubs. Test output, not a UI; no LLM was called.

- Task: 4.B3 (branch `agent/cloud-ai/4.B3-slice1`) · PR: see PR list for `[4.B3]` · Persona: Sana (Cloud AI Engineer) · Requirements: FR-P02, FR-P04, ADR-006
- Evidence file: `test-and-mutation-output.txt` (31/31 tests pass, 42/42 mutants killed; full `cloud/test.sh` also green locally)
- Agent minutes: see Agent Log · Agent's own human-hour estimate: 7 h
- Unverified: guardrail thresholds (frost 2 C, heat 30 C, rain 5 mm, reading age 6 h, winter = Dec-Feb) are proposals; keyword text classifier covers known phrasings only; FR-P02 requirement text not read (Google Doc unreachable); no edge function, no real weather or LLM provider, no live project touched.

# 4.B3 slice 1b: QA and review fixes for the care-tips guardrails

**What it shows:** real terminal output of 64 tests and a 61-mutant check after fixing QA findings N-1/N-2/N-3 (assistant text can no longer slip past the guardrails through a negation word, synonyms or a malformed forecast) and review points C1/C2 (output mapped to the MCP `get_tips` contract; guardrail version exposed). Test output, not a UI; no LLM called.

- Task: 4.B3 slice 1b (branch `agent/cloud-ai/4.B3-slice1b`) · Persona: Sana (Cloud AI Engineer) · Requirements: FR-P02, FR-P03, FR-P04, ADR-006
- Evidence file: `test-and-mutation-output.txt` (64/64 pass, 61/61 mutants killed); QA's adversarial cases are included as regression tests
- Unverified: keyword classifier is still a deny-list; G-13 (no outdoor watering advice without a valid forecast) is a new behaviour decision; thresholds approved by Arsany (A-105) as stated by the owner, not checked against the Questions tab; full cloud/test.sh not re-run.

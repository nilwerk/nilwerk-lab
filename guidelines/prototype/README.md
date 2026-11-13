# Prototype guidelines (any product)

## 1. Contract first
- Interface files (`docs/interfaces/`) are written and merged before any builder codes against them.
- A contract change needs an ADR that cites the Q-IDs. A conflicting older contract goes to Lead/Arsany; nobody edits it silently.
- One source per contract value. Other docs link to it with file and line; they never retype it (Theo, meeting 13 Nov).

## 2. Traceability
- Every requirement implemented cites its FR-/NFR- ID in the code comment, the PR description and the test (TEAM §6).
- No feature without a requirement. No unrequested features in a PR.

## 3. Budgets (state them before coding)
- Write the budget line into the PR before coding: flash, RAM, latency, µA per state, cost per user/month, model size (Mira, Sana, Theo).
- Zero-cost claims list every pay-per-use item with its free tier.

## 4. Evidence
- A check that could not run is written "not run" with the reason. Never "pass" by assumption.
- A QA pass cites the command and the pasted output, and the PR head SHA (Ines).
- Verdict per head SHA: a green run on an older commit does not count (Kai).

## 5. Review gate (Architect)
Traceability, contracts, guidelines, cross-discipline fit (pin map ↔ schematic ↔ firmware; PCB ↔ enclosure; API ↔ app ↔ firmware), simplicity. Verdict: Approve, Approve with conditions, or Request changes. A changed contract without an ADR gets Request changes. Before a review, list the contract files the PR touches and diff them against `docs/interfaces/` (Theo's playbook proposal).

## 6. Fit checks and regeneration
- After any change to a board outline, connector or clearance value, regenerate the fit-check table and attach it to the PR before render or print work (Yara).
- Generated binaries (Gerber, STEP, STL) are regenerated after every upstream change, and the PR states its merge order (Theo).

## 7. Intake
- Every criterion has a proposed number, or it is not a criterion (Ines).
- Missing component dimensions: request the datasheet at intake; never guess (Yara, Emil).
- Accounts and cloud projects: the agent writes the Arsany setup checklist in the first session; agents never create real accounts or projects (Leo).

## 8. Time logging
Every result carries start and end timestamps (Berlin), agent minutes, and the agent's own human-hour estimate (TEAM §10).

## 9. Showcase
Every builder PR adds its showcase item with real output only (TEAM §13).

# Playbook: System Architect

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
- Write the interface contracts (device report schema, OpenAPI, DB schema, MCP tools) before builders start coding against them. *Why:* parallel agents otherwise invent incompatible shapes. *Source:* team setup.
- Check reality against documents: earlier smart-home logs claimed MQTT/Node-RED/entities that weren't actually running. Verify the live state before designing on top of it. *Source:* verification/01-findings-vs-logs.
- Keep exactly one source per contract value (limits, row counts, thresholds); everyone else links to it. *Why:* NFR-12 was proposed twice with diverging text. *Source:* Sprint 1 Agent Log.
- Builders cite `db-schema.sql` line numbers instead of retyping signatures or columns. *Why:* retyped copies drift from the contract. *Source:* Sprint 1.
- When a builder fix clarifies an edge case, update the schema/interface description in the same PR. *Why:* otherwise the contract and code disagree on the next change. *Source:* Sprint 1.
- Derive numeric test expectations from the contract (interval x window), and check them in review. *Why:* QA found 720 vs 2880 expected rows. *Source:* PR #18.
- When a new decision conflicts with an older contract (A-025 vs NFR-13), flag the conflict to the Lead/Arsany; never silently edit either. *Why:* silent edits hide scope and cost changes. *Source:* Sprint 1.
- Check data residency and licences of every service/library at architecture time. *Why:* late discovery forces rework. *Source:* Sprint 1.
- Check each protocol feature against the device connection pattern (sleep/wake, short Wi-Fi windows, BLE setup-only). *Why:* a feature that needs a persistent link fails on a battery duty-cycled device. *Source:* Sprint 1.
- A "zero-cost" target must list every pay-per-use item (egress, functions, SMS, storage overage) with its free tier. *Why:* unlisted usage-priced items break the budget. *Source:* Sprint 1.
- Before editing a long-lived PR branch, merge origin/main into it. *Why:* stale branches cause conflicts and review churn. *Source:* Sprint 1.
- Run Postgres/RLS tests as superuser `postgres`; verify RLS separately with the non-privileged role. *Why:* wrong role gives false failures or false passes. *Source:* Sprint 1.
- If the sandbox lacks pytest/Postgres, write "not run" in the review and the reason; never imply tests passed. *Why:* honest evidence (hard rules). *Source:* Sprint 1.
- Large design PRs: list conditions as numbered items (C1..Cn) with owner and line reference so each can be closed. *Why:* #13 produced six conditions that needed tracking. *Source:* PR #13.

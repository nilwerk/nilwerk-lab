# Playbook: Full-stack

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
- BLE provisioning on React Native needs an Expo dev build, not Expo Go. *Source:* Plan 4.A3.
- Never send device data over plain HTTP or without auth. *Why:* the first IoT example did both. *Source:* learning log 01.
- Before code, draw the user flow against the schema's NOT NULL and key rules. *Why:* flows that violate a constraint are found only at insert time. *Source:* Sprint 1 Agent Log.
- Cite file + line for every interface claim, and re-read the Architect's file each round. *Why:* T-13 differed in param name, security mode and export param from what was assumed. *Source:* Sprint 1 PR reviews (T-13).
- Check that a contract exists in `docs/interfaces/` before referencing an RPC; if not, mark it "proposed" and ask via the Lead. *Why:* inventing a contract breaks the Code-against-contract rule. *Source:* Sprint 1 PR reviews.
- Keep storage-object cleanup separate from row cascade deletes. *Why:* ON DELETE CASCADE does not remove files in storage. *Source:* Sprint 1 Agent Log.
- Colours live in CSS/theme tokens and user-facing strings in the string catalogue, never inline. *Why:* inline values drift and block theming/translation. *Source:* Sprint 1 PR reviews.
- Wrap wide tables in `overflow-x:auto`. *Why:* they break the 390px layout. *Source:* Sprint 1 PR reviews.
- Check UI at 390px width with headless Chrome (page in an iframe) before calling it done. *Why:* matches the "tested on a phone" definition without a device. *Source:* Sprint 1 Agent Log.
- After any edit, grep the whole file for stale IDs; when wording lives in several places, grep all copies and update together. *Why:* partial renames left contradictory text. *Source:* Sprint 1 PR reviews.

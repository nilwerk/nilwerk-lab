# Device claim + ingest API: tested against a real PostgreSQL, token logic mutation-checked

**What it shows:** the 13 edge-function tests passing against a local PostgreSQL (claim, hash-only token storage, a 96-sample offline batch, replay idempotency, device A's token unable to write device B), and the mutation check where all 17 deliberate bugs in the token-hash, auth, claim and idempotency code are caught (`api-tests.png`, `mutation-check.png`, real command output).

- Task: 4.B2 Cloud: device claim + ingest API · Branch `agent/cloud-ai/4.B2` · PR: link added by the Lead · Persona: Sana (Cloud AI)
- Agent minutes: from the Agent Log once logged (about 14 min wall clock, measured by the agent). Own human-hour estimate: about 14 h.

**Still unverified:** nothing ran against a real Supabase project (no secrets, no Docker): the Deno entry points (`functions/*/index.ts`, `_shared/supabase.ts`), supabase-js calls and the new key names in the hosted runtime are untested. Rate limits, OTA manifest and push dispatch are not built (marked in the OpenAPI).

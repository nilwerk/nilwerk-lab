# 4.B2b: DELETE /account edge function (GDPR erasure) with tests

**What it shows:** the last lines of the real test run for the new `delete-account` function: missing/invalid token gives 401, success erases readings, photo rows, plants, profile and auth user while releasing the devices, a second call is idempotent, and another user's data is never touched.

- Task: 4.B2b · PR: see PR list (branch `agent/cloud-ai/4.B2b`) · Persona: Sana (Cloud AI Engineer)
- Requirements: FR-A01, FR-A08, NFR-07, NFR-06. Tests: 6 new (22 total) plus 13 new mutants, all killed.
- Agent minutes: see PR description · Agent's own human-hour estimate: 6 h
- Unverified: Supabase Storage and Auth admin calls (`supabase.ts`) and Deno were never run; the tests use local Postgres with stubbed Storage/Auth.

# 4.B1 Cloud backend scaffold: tests pass on a local PostgreSQL 16

**What it shows:** the real output of `projects/plant-monitor/cloud/test.sh`: the Supabase migrations from the 2.4 schema apply cleanly, row-level security is on all 14 tables, user A cannot read, change or forge any row of user B, and the 3-month raw / 12-month roll-up retention works (`test-output.txt`).

- Task: 4.B1 · PR: [4.B1] Cloud backend scaffold (link added by Lead) · Persona: Sana (Cloud AI Engineer)
- Agent minutes: about 4 (wall clock 07:44 to 07:48, see Agent Log once logged) · Agent's own human-hour estimate: 5 h
- Unverified: not run on a real Supabase project (Docker/`supabase start` not available; `auth.uid()`, Storage and pg_cron are stubbed or skipped locally).

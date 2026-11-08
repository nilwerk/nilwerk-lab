# 4.B2 Device claim + ingest API: SQL and handler tests pass, 4 mutants caught

**What it shows:** real output of `cloud/test.sh`: a sensor claims itself with a one-time token and gets a hash-only device token; hourly reports (incl. a 96-sample offline buffer) are stored idempotently, out-of-range values are flagged, alerts open and resolve; `mutation-check.txt` shows four deliberately broken versions (wrong token checks, missing idempotency) all failing the tests.

- Task: 4.B2 · PR: link added by Lead · Persona: Sana (Cloud AI Engineer)
- Agent minutes: see Agent Log (run interrupted by an API rate limit; active time about 10) · Agent's own human-hour estimate: 8 h
- Unverified: Deno entry points and supabase-js wiring not run (no Deno/Docker/Supabase CLI); nothing on a real Supabase project.

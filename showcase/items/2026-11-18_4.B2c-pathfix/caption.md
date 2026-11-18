# Export photo paths: path traversal blocked

**What it shows:** the export function now signs a photo link only for a path of exactly the form `<own user id>/<folder>/<file>`. Paths with `..`, a leading `/`, backslashes, `%`, control characters, the wrong segment count or another user's prefix get `url: null` and are never signed (Ines's QA note N1 on PR #130). `test-output.txt` is the real output of `cloud/test.sh` plus the guard mutants that were killed.

- Task: 4.B2c-fix, stacked on PR #130 (branch `agent/cloud-ai/4.B2c-export`), branch `agent/cloud-ai/4.B2c-pathfix`. Persona: Sana (Cloud AI Engineer). Requirements: NFR-06, NFR-07.
- Agent minutes: about 32 (start 07:45, end ~08:19 Berlin). My own human estimate: 2.5 h.
- Unverified: the full `mutation.sh` was stopped part-way (EX-1 to EX-16 incl. the new guard mutants killed; EX-17, EX-18 and the SQL mutants not re-run by me). Nothing deployed; Supabase Storage behaviour on `..` and a DB CHECK on `plant_images.storage_path` are not done or verified live.

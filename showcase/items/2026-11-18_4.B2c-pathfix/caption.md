# Export photo paths: path traversal blocked

What it shows: the account export now creates a download link for a photo only when its stored path has exactly the form user id, plant folder, file name, with the user id being the caller's own. Paths containing "..", a leading slash, backslashes, percent signs or control characters, paths with the wrong number of segments and paths under another user's id get no link and are never signed. The test output file is the real output of the cloud test script, plus the guard mutants that were killed.

- Persona: Sana (Cloud AI Engineer). Requirements: NFR-06, NFR-07.
- Agent minutes: about 32. Own human estimate: 2.5 hours.
- Unverified: the full mutation run was stopped part-way, so the later export mutants and the SQL mutants were not re-run. Nothing is deployed. How Supabase Storage treats ".." paths, and a database CHECK on the stored path, are not done or verified on a live project.

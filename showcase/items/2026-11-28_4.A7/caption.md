# Care tips screen: stored tips per plant, locked for free accounts

**What it shows:** The care tips screen lists the tips the server stored for one plant, exactly as stored, and shows an upgrade notice instead to free accounts, with loading, "no tips yet" and error states, checked with mocked data only.

- Outputs: the test run log (25 tests passing) and the run with the premium gate removed, where the free-account test fails.
- Persona: full-stack developer (role name, no personal name).
- Own human-hour estimate: about 7 h (estimated, experienced engineer, screen + read client + strings + tests).
- Not verified: not run on a phone or in a browser; not run against a live backend or a real database project; the screen is not yet reachable from the app's navigation; the plan check uses a mocked profile; no caveat text is shown because the tips contract returns none.

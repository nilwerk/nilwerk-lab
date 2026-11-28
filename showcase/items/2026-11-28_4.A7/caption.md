# Care tips screen: entry from the plant detail, stored tips per plant, locked for free accounts

**What it shows:** The plant detail screen has a "Care tips" button that opens the care tips screen. The screen lists the tips the server stored for that one plant, exactly as stored. Free accounts see an upgrade notice instead, and no tips are read for them. Loading, "no tips yet" and error states are covered, checked with mocked data only.

- Outputs: the test run log (29 tests passing across three files, including the entry tests from the plant detail) and the run with the premium gate removed, where the free-account test fails.
- Persona: full-stack developer (role name, no personal name).
- Own human-hour estimate: about 7 h (estimated, experienced engineer, screen + read client + entry + strings + tests).
- Not verified: not run on a phone or in a browser; not run against a live backend or a real database project; the entry and the tips read are tested with the mocked backend only; no caveat text is shown because the tips contract returns none.

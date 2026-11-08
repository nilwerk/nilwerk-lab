# A-052 One privacy / Impressum line: contact and Google as mail processor

**What it shows:** a single muted line on Welcome, Profile and the Premium sheet: "Contact and privacy: nilwerk.team@gmail.com. E-mail is processed by Google (Gmail)." DRAFT, needs Arsany/legal review (marked in `LegalLine.tsx` and the app README). It names only the contact and the processor fact, no other legal claim. `test-output.txt` has the test run (64 passing).

- Task: A-052 (approved by Arsany) · Persona: Leo (Full-stack Developer) · Requirements: none new (supports A-048 contact)
- Stacked on `agent/fullstack/a048-contact` (PR #52): touches the same files (config.ts, PremiumScreen, en.json), so #52 must merge first.
- Agent minutes: about 3 (16:09 to 16:13 wall clock, see PR) · Agent's own human-hour estimate: 1 h
- Unverified: wording not legally reviewed; not checked on a phone; whether a full privacy notice/Impressum is required for release is open.

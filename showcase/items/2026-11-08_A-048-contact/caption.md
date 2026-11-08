# A-048 Premium "Contact us" works with Nilwerk's shared mailbox

**What it shows:** the Premium sheet's "Contact us" now opens a mail to nilwerk.team@gmail.com (Arsany's answer to A-048) with the subject "Plant Monitor – Premium activation". The address is only the default: `CONTACT_EMAIL` overrides it, an explicitly empty value still hides the link. Also closes Ines' open QA note from #42 (reducer signedOut from every state, startup when getSession rejects). `test-output.txt` has typecheck and the 60 passing tests.

- Task: A-048 follow-up to 4.A2 · Persona: Leo (Full-stack Developer)
- Requirements: FR-P04 (contact link), FR-A01 (auth state)
- Mutants checked (each fails a test): signedOut no-op (2 tests), no getSession-rejection handler (1), wrong default address (2), old subject (1)
- Agent minutes: 2.8 (15:38:02 to 15:40:44, wall clock) · Agent's own human-hour estimate: 1.5 h
- Unverified: mail client hand-off not tried on a phone or in a browser; Linking.openURL is mocked in tests. Whether a business mailbox in a consumer app needs an Impressum/privacy line is open (flagged to Arsany, no legal text added).

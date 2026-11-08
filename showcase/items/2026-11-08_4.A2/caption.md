# 4.A2 App account and profile: sign up, sign in, profile, sign out, delete account, running on web against a mock backend

**What it shows:** the Plant Monitor app (Expo + TypeScript) in the aligned brand set from A-040: welcome with the brand mark, sign-up form with plain error messages, profile with plan and display name, the Premium sheet ("activated by Nilwerk" + contact link), and delete account with a type-DELETE confirmation. Screenshots are a web build at 390 px width against an in-memory mock of Supabase (light and dark). `test-output.txt` has the typecheck and the 54 passing tests (validation, auth state, string catalogue, AA contrast of every colour pair, screen flows).

- Task: 4.A2 · PR: [4.A2] App account and profile (link added by Lead) · Persona: Leo (Full-stack Developer)
- Requirements: FR-A01, FR-P04, NFR-06, NFR-07 (each screen cites its IDs in its source header, checked by a test)
- Agent minutes: see Agent Log (wall clock in the Lead's report) · Agent's own human-hour estimate: 14 h
- Unverified: not run against a real Supabase project or on a phone/simulator. `DELETE /account` has no edge function on main yet. "Contact us" address (`CONTACT_EMAIL`) is not decided, so the link is hidden in these screenshots' build config. Expo SDK 58 config keys were exercised only by `expo export --platform web`, not by a native build.

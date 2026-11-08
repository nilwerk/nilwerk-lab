# Plant Monitor app (task 4.A2: account and profile)

Expo (SDK 58) + TypeScript (strict). Screens: Welcome S01, Sign up / Sign in S02, Profile S03, Delete account S04, Premium sheet S40
(wireframes: `wireframes/index.html`). Requirements: FR-A01 (account), FR-P04 (plan mirrors `profiles.is_premium`), NFR-06 (own rows only, RLS), NFR-07 (delete removes all data).
Brand: the aligned set approved in A-040 (`theme.ts`, `tokens.json`, `assets/` copied from `showcase/brand/app/`; regenerate there, not here). English only, strings in `strings/en.json` (A-024).

## Run
```bash
npm ci
npm run typecheck && npm test                      # typecheck + 60 unit/screen tests (no backend needed)
EXPO_PUBLIC_MOCK_AUTH=1 npx expo start --web       # whole app against an in-memory mock of Supabase (no account, no network)
```
Real backend (needs a Supabase project, Arsany's step, see `../cloud/README.md`): set these environment variables before `expo start` / EAS build. Names only, values are never committed:

| Name | What |
|---|---|
| `SUPABASE_URL` | project URL (https) |
| `SUPABASE_PUBLISHABLE_KEY` | the NEW publishable key (`sb_publishable_...`), public by design; never a secret / service-role key |
| `CONTACT_EMAIL` | address behind "Contact us" on the Premium sheet. Default `nilwerk.team@gmail.com` (A-048, the one shared mailbox for now); set another value to override, set it to an empty string to hide the link. Opens `mailto:` with subject "Plant Monitor – Premium activation" |

`app.config.ts` copies them into `extra`; `src/config.ts` reads them. Without them the app shows a "not connected to a server" message instead of crashing.

## Layout
`App.tsx` shell and routes · `src/auth/` (`types.ts` contract, `supabaseAuth.ts` real, `fakeAuth.ts` mock, `authState.ts` reducer, `storage.ts` chunked SecureStore) · `src/screens/` · `src/ui/` (primitives, FR map) · `src/validation.ts` · `src/i18n.ts` · tests in `src/__tests__/`.

## Legal line (A-052, DRAFT: needs Arsany/legal review)
One line (`src/ui/LegalLine.tsx`, string `legal.line`) on Welcome, Profile and the Premium sheet names the contact address (CONTACT_EMAIL, default `nilwerk.team@gmail.com`; falls back to the default if the Premium link is hidden) and says e-mail is processed by Google. It cites NFR-07 (privacy) and states nothing else legally. **Open point for the legal review (PR #55 C2):** the line says nothing about Expo push notifications or any other non-EU service; this must be decided before a store release. A real privacy notice / Impressum is still to be written and reviewed before any store release.

## Not done / known gaps (4.A2)
- Never run against a real Supabase project or on a phone. Web build + jsdom-free render tests only.
- `DELETE /account` is in the OpenAPI contract but no edge function exists on `main` yet; delete will fail against a real backend until it is built (the app then shows "Nothing was removed").
- No forgot-password, no data export, no plants, no BLE setup (4.A3). Export warning for plant removal is A-022 (separate).
- `handle_new_user()` stores only the id, so the sign-up display name is kept in auth user metadata and copied into `profiles.display_name` on the first profile load.
- Apple/Google sign-in, store assets and the Expo dev build for BLE are later tasks.

# Plant Monitor app (tasks 4.A2 account and profile, 4.A3 device setup UI, 4.A4 slice 1 plants)

Expo (SDK 58) + TypeScript (strict). Screens: Welcome S01, Sign up / Sign in S02, Profile S03, Delete account S04, Premium sheet S40, plus (4.A4 slice 1) Plant list S20, Plant detail S21, Remove plant S24b/S24c with a Plants/Profile tab bar
(wireframes: `wireframes/index.html`). Requirements: FR-A01 (account), FR-P04 (plan mirrors `profiles.is_premium`), NFR-06 (own rows only, RLS), NFR-07 (delete removes all data).
Brand: the aligned set approved in A-040 (`theme.ts`, `tokens.json`, `assets/` copied from `showcase/brand/app/`; regenerate there, not here). English only, strings in `strings/en.json` (A-024).

## Run
```bash
npm ci
npm run typecheck && npm test                      # typecheck + 98 unit/screen tests (no backend needed)
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

## Device setup flow (4.A3 UI skeleton, no hardware)
Profile -> "Add a sensor" -> S10 find sensor, S11 connect (type the label code), S12 Wi-Fi, S13 name and link (+ S13e error states), S14 photo, S15 plant details, S16 done with the setup timer (target 3 min, NFR-03). Requirements: FR-A03, FR-D03, FR-A04, FR-A05, FR-A02 (add another). **No hub pairing step: the Raspberry Pi hub and screen S17 are v1.1, not v1 (A-023).** Plant removal / release (A-022) is separate.
- The screens only talk to `src/provisioning/types.ts` (`ProvisioningService`, `PlantSetupService`, `PhotoSource`), mirroring `docs/interfaces/ble-provisioning.md` and `openapi.yaml` (`/claim-token`, `/device-claim`). `fakeProvisioning.ts` implements it in memory (5 wrong codes close setup mode, wifi_failed / device_owned / claim failures) and runs the whole flow in tests and in the mock web build (`EXPO_PUBLIC_MOCK_AUTH=1`). Pure state machine: `src/screens/setup/setupState.ts`.
- **Not done, separate later slice:** the real BLE implementation of `ProvisioningService` on `@orbital-systems/react-native-esp-idf-provisioning` (needs an Expo dev build, not Expo Go), QR scanning and camera/library (`expo-image-picker`), the real `PlantSetupService` (supabase-js: plants, devices.plant_id, plant_images + storage). Until then a non-mock build shows "needs the full app build" on the first step. The BLE service UUID is still TBD in the contract.
- The in-app timer and the 3-minute target are shown, but setup time on a real sensor is measured in 5.5, not here.

## Not done / known gaps (4.A2)
- Never run against a real Supabase project or on a phone. Web build + jsdom-free render tests only.
- `DELETE /account` is in the OpenAPI contract but no edge function exists on `main` yet; delete will fail against a real backend until it is built (the app then shows "Nothing was removed").
- No forgot-password, no data export, no plant list (the setup flow exists in 4.A3 but only against a fake). Export warning for plant removal is A-022 (separate).
- `handle_new_user()` stores only the id, so the sign-up display name is kept in auth user metadata and copied into `profiles.display_name` on the first profile load.
- Apple/Google sign-in, store assets and the Expo dev build for BLE are later tasks.

## 4.A4 slice 1: plants (list, detail, remove)
### Before wiring a real client (gates, from Theo's review of PR #65)
The real `PlantsService` must not replace `unconfiguredPlants` until all three hold:
1. **Export before delete (C1).** openapi.yaml says the app MUST offer the JSON/CSV export before removal. `RemovePlantScreen` has no "Export first" step yet. TODO test: `remove plant offers export first before the typed confirmation`.
2. **Photo objects (C2).** `delete_plant` returns `photo_paths`; the caller must delete them from bucket `plant-photos` (NFR-07). The screen currently discards them. TODO test: `deletePlant removes every returned photo path from storage`.
3. **Gaps in the hourly series (C3).** `readings_hourly` has no row for an offline hour; the client must fill the 168-hour grid with nulls. TODO test: `real hourly series with missing hours yields 168 points with null gaps`.
Requirements: FR-A06 (list with status chips dry / wet / low battery / offline, detail with latest values and 7-day hourly chart), FR-A02 (no device cap), FR-A08 + A-022 (remove plant with warning and typed confirmation, then keep or release the sensor), NFR-06.
`src/plants/types.ts` is the contract (mirrors `plant_status`, `readings_hourly`, `delete_plant`, `POST /device-release` in `docs/interfaces/`). `fakePlants.ts` is the in-memory mock (5 fixture plants as in wireframe S20, synthetic readings); with `EXPO_PUBLIC_MOCK_AUTH=1` the app uses it, otherwise `unconfiguredPlants.ts` answers "not connected". Status chips: `src/plants/status.ts` maps open alert kinds to the aligned colours in `theme.ts` (shape glyph + text label + colour). Chart: `src/ui/MoistureChart.tsx` (plain Views, one bar per hour, no SVG dependency).
Not done in slice 1 (slice 2 and later): photo gallery S23 / photo hero (FR-A05, unlimited images), hourly data table S22, edit plant S24 (FR-A04), "Export first" before removal (needs GET /export + share sheet, A-022 asks to offer it), "+ Add" to S10 (4.A3), alerts tab (4.A5), 30/90-day Premium ranges (FR-P01), "dry in" forecast (FR-E01), pull-to-refresh (a Refresh button instead), a real Supabase `PlantsService` (never run against a backend or on a phone; web build + render tests only). Removing a plant in the mock does not touch a device table; real behaviour is `delete_plant` (sensor stays claimed, plant_id cleared). The mock's "latest" value is a fixture number, not derived from the synthetic chart series.

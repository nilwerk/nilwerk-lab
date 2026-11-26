# Review of the alternative design (PR #238) against the app flow

Scope: `showcase/brand/app/alt/ALT-SPEC.md` and `final-mockups.html` on PR #238 (stacked on the v3 branch), checked against `projects/plant-monitor/app` on `origin/main` (7227f82). Each of the 16 mock screens and each decision in the spec's decision table is checked. Mock frames are 360 x 760 CSS px; the app is checked at 390 x 844.

Verdict in five lines:
1. The five-step setup, the Alerts tab with badge, the day-grouped three-column gallery and one-screen details are compatible with the app. Setup and details need no code change.
2. The mock contains a plan price on the Profile screen. That is a Needs owner decision decision, and prices must not appear in `showcase/`. The mock also cannot be published as is.
3. The photo picker, the photo viewer and the "needs water" card need requirement checks or a dependency review before any code. The viewer needs signed image URLs, which the app does not fetch yet.
4. The mock's plant data (Basil 18 %, Monstera, Fern 27 %) does not match the app's fixtures (Basil 38 %, Cactus 12 %). Compare on the app's fixture before judging the numbers.
5. The navigation changes (route stack, system back, double back to exit, sheets) need a bench check and a new test set. They are not in the decision table, so they are not built here.

## Screen by screen

| # | Mock screen | Fits the app flow? | Notes |
|---|---|---|---|
| 1 | Welcome | Yes | Same three benefits idea as the app's welcome. Copy only from `strings/en.json`. |
| 2 | Sign up | Yes | Same fields and inline errors as the app's `AuthFormScreen`. |
| 3 | Setup: find sensor (1 of 5) | Yes | Matches `setup.step` "Step 1 of 5". The bench does not read the progress label. |
| 4 | Setup: connect code (2 of 5) | Yes | Matches the code field `setup.connect.codeLabel`. Bench step 2 types into it: keep the label. |
| 5 | Setup: Wi-Fi (3 of 5) | Yes | Matches `WifiStep`. |
| 6 | Setup: name and link (4 of 5) | Yes | Matches `NameStep` and `LinkingStep`. |
| 7 | Setup: photo and details (5 of 5) | Partly | The mock puts the photo and the plant details on one screen. The app has a separate photo step and a separate details step, so the mock has six screens under a "5 of 5" label. Decide which is meant. Details on one screen (the spec's decision) already holds in the app's `DetailsStep`. |
| 8 | Setup: done | Yes | The mock's "Go to my plants" label is a value change to `setup.done.seePlant`. Bench step 2 taps that label. Needs the bench owner's check first (the spec says so). |
| 9 | My plants (home) | Partly | Three tabs and the Alerts badge: built (see below). The "NEEDS WATER" card with a "Check Basil first" button is in the mock but not in the decision table. It is a new feature: the card's copy is new, and the button needs a target screen. Needs owner decision. The "+" header button is not in the decisions either: the app adds sensors from Profile only. Needs owner decision. |
| 10 | Plant detail | Partly | The mock shows a large reading and a next step. The app has the hero reading (v4 on another branch; not on main). "Next step" text is a new rule (the design review D-C, deterministic, not AI). Needs a requirement check. |
| 11 | Alerts (tab) | Yes | Built as the Alerts tab. The list already exists (`AlertsScreen`). The mock's filter by type is not in the app. Not built. |
| 12 | Profile | Yes, except price | Grouped sections are a change from the app's flat list (not built). The plan price is a Needs owner decision decision. The mock shows a price; prices must not appear in `showcase/`. The alt Profile render is therefore not published (see the renders list). |
| 13 | Premium sheet | Not in decisions | The app has a premium screen, not a sheet. The sheet shows a price. Not built. |
| 14 | Gallery (day headers, three per row) | Yes | Built in the alternative build. Tiles have no photo bytes in the mock data, as in the app. |
| 15 | Photo viewer (Previous, Next, swipe, pinch) | No | The app has no viewer. Needs a requirement check (FR-A05), and full-size images need signed Storage URLs. Not built. |
| 16 | Delete account | Yes | Same screen as the app's `DeleteAccountScreen`. Not changed. |

## Decisions

| Decision | Status in the app | Code, test and bench for the change |
|---|---|---|
| Five setup steps, as on main | Already true | None. |
| Three tabs (Plants, Alerts with badge, Profile) | Built in the alternative build | `TabBar.tsx` (new tab and badge), `App.tsx` (alerts route maps to the tab; open-alert count from `listPlants`), `strings/en.json` (`nav.alerts`, `nav.alertsBadge`). Tests: the existing tab tests pass; `altBuild.test.ts` covers the label. Bench: step 2 taps `nav.profile` and step 3 taps `nav.plants`: labels unchanged. Needs bench owner check that the bench's tap on the tab bar still matches. **Resolved (owner answer):** the badge count is cached. It is written when the plant list or the alerts screen loads, and not re-read on every navigation. Code: `App.tsx` (one cached value), `PlantsScreen.tsx` and `AlertsScreen.tsx` (`onCount`), `status.ts` (`countOpenAlertPlants`). Test: `altBuild.test.ts` (hand-computed: three of five plants). Bench: step 3 reads the list; not affected by the badge. |
| Gallery: grid of three per row, day headers, date on each photo | Built in the alternative build | `PlantGalleryScreen.tsx` (`dayGroups`, three per row). Tests: `altBuild.test.ts` (hand-written groups). Bench: not in the bench. The "date on each photo" is kept as the tile caption. |
| Photo picker (`expo-image-picker`) | Approved in the spec, not built (open question below) | Needs a dependency review and a requirement check (the spec says the build PR does that). Upload would go to Storage; it must be checked against the contract, not assumed. Not built here. Bench: not in the bench. |
| Setup details on one screen this round | Already true in the app. **Waiting on Leo** (the app developer) to decide whether the photo and the details are one screen or two, as the mock shows. The build is left as it is. | None until Leo decides. Bench step 2 (`setup.details.*`) depends on the answer. |
| Plan price on Profile | Built in the app only (owner answer). Both plan prices are shown on Profile, values from `strings/en.json`. | Code: `ProfileScreen.tsx` (two lines under the plan row), `strings/en.json` (`profile.price.*`). Test: `altBuild.test.ts` (strings). Bench: not in the bench. Prices are not written in `showcase/`. Open: the currency and the billing period are not stated in the answer (see open questions). |
| Designer role approved | Recorded in the spec | Not a code item. |

## Things in the mock that need a decision (not decided here)

- "NEEDS WATER" card and its button (screen 9).
- The "+" header button on My plants (screen 9).
- The "next step" line on plant detail (screen 10).
- The filter by type on Alerts (screen 11).
- The photo viewer (screen 15).
- Grouped sections on Profile (screen 12).
- Route stack, system back, double back to exit, bottom sheets and pull to refresh (spec, navigation section). These change every screen's back behaviour and need the bench owner's check: the bench does not yet check whether any step uses system back.

## Data mismatch

The mock uses Basil at 18 %, Monstera at 62 % and Fern at 27 %. The app's fixtures are Basil at 38 %, Cactus at 12 %, Fern at 52 % and Orchid offline. Numbers in the mock cannot be compared with the app's numbers until the mock uses the app's fixture.

## Renders

- `alt-*.png`: the mock's phone frames, 360 x 760 CSS px at 2x. Not published: the profile frame, because it shows a price.
- `altbuild-*.png`: the alternative build, 390 x 844 at 2x, mock data.
- `side-by-side-v1-alt-*.png`: v1 (origin/main, from the earlier v1 renders) beside the mock frames.

## Not done in this review

- No device run, no bench run.
- No endpoint was added. The open-alert count uses the existing `listPlants`.
- No change to backend, Supabase or contracts.

## Open questions (not built; for the team to recommend)

Arsany asked the team to recommend on these. They are not built in this branch. Routing: Theo (architecture, requirements) and Leo (app).

1. **"NEEDS WATER" card and its button** (mock, My plants). Needs a rule for which plant is named first, and a target screen for the button. Requirement check first (the design review item D-C is a related rule). Recommend: Theo and Leo.
2. **"+" button on My plants.** The app adds sensors from Profile only. A header button needs a decision on where setup starts. Recommend: Theo and Leo.
3. **Photo picker.** `expo-image-picker` is approved in principle. The dependency, the camera and library permissions, and the upload path in the contract need a review before code. Recommend: Theo (contract) and Leo (dependency).
4. **Photo viewer** (previous, next, swipe, pinch). Needs signed Storage URLs and a requirement check (FR-A05). Recommend: Theo and Leo.
5. **Setup details: one screen or two.** Waiting on Leo.
6. **Plan price: currency and billing period.** The owner gave the two values for Free and Premium. The currency symbol and the billing period (per month or per year) are not in the answer. Needs the owner to confirm before release.
7. **Route stack, system back and sheets.** The bench check is in `ROUTE-SHEETS-BENCH-CHECK.md`. The check needs a device run before any code.

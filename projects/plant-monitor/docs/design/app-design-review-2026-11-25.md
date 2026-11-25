# Plant Monitor app: design review (modern look, bench and UI-test impact)

Date: 2026-11-25 · Scope: `projects/plant-monitor/app` (screens, shared UI, tokens, strings) · Type: review only, no app code changed.

Sources read: `src/screens/**`, `src/ui/**`, `theme.ts` (generated from `tokens.json`), `tokens.json`, `strings/en.json`, `bench/app/run_appium.sh` (labels are read from `strings/en.json` at run time), `e2e/web-flow.test.js`, and the Jest tests under `src/__tests__` (selected by text search, see section 4).

The owner's brief: the app is simple but not modern. Use a consumer habit-forming app as inspiration for how it should feel: clear progress, friendly rewards, bold colour, big tap targets, playful but calm, a clear next step. Nothing is copied from that app (no layout, icons, names, mascot, colours or wording). Only general UX principles are used, listed in section 1.

---

## 1. Principles used

Each recommendation below names the principle it uses.

| Code | Principle (general UX, not specific to any app) |
|---|---|
| **P1** | One clear next step per screen: one primary action, placed first. |
| **P2** | Visible progress with real numbers: the user always knows where they are and how far is left. |
| **P3** | Immediate feedback and a clear finish: a completed milestone is acknowledged, using facts only. |
| **P4** | Large, forgiving tap targets with clear pressed feedback. |
| **P5** | Empty states are first-run guidance, not dead ends. |
| **P6** | Chunk long input: fewer fields per screen, optional fields marked. |
| **P7** | Status is shown by shape, text and colour together (already in the app; keep it). |
| **P8** | Calm personality: rewards come from real milestones, never from streaks or pressure; motion respects reduced-motion settings. |
| **P9** | Platform-native patterns: icons in navigation, pull-to-refresh, grouped settings lists. |

Effort: **S** = under half a day, **M** = 1 to 2 days, **L** = more than 2 days (developer estimate, not measured).

---

## 2. Screens reviewed and what they look like today

All values come from the style code. No screenshots were taken or used.

| Screen (file) | Current look and behaviour |
|---|---|
| Welcome (`WelcomeScreen.tsx`) | 96 px app icon, 28 px Space Grotesk title "Plant Monitor", one-line tagline, two stacked full-width buttons (filled green primary, bordered secondary), privacy caption, legal line. |
| Setup, step 1 "Add a sensor" (`SetupSteps.tsx` ReadyStep) | Title, a progress row ("Step n of 5" plus an elapsed clock in 12 px mono), four body paragraphs, a permission note, then the primary "Find my sensor" button. Found devices appear as secondary buttons. |
| Setup, step 2 "Connect" (ConnectStep) | Device name, two paragraphs, a text field for the sensor code from the label (typed, not scanned; the copy says scanning comes with the Bluetooth build), primary "Connect". |
| Setup, Wi-Fi (WifiStep) | Radio-style list of networks (checkmark glyph on selection), "Other network" option, password field, primary "Continue". |
| Setup, name (NameStep) | One text field, primary "Connect sensor". |
| Setup, linking (LinkingStep) | Spinner and two text lines with a tick glyph. No checklist, no bar. |
| Setup, link error (LinkErrorStep) | Error notice plus one to three buttons, depending on the error. |
| Setup, photo (PhotoStep) | Two buttons (take, pick), a ghost "Skip for now". |
| Setup, details (DetailsStep) | One long scroll: name, a location radio group, area, soil radio group, species, city, then "Save plant". Five text fields and two radio groups on one screen. |
| Setup, move choice (MoveChoiceStep) | Two buttons with a hint under each. |
| Setup, done (DoneStep) | "All set!" title, body with the plant name, setup time, primary "Done", secondary "Add another sensor". Text only. |
| My plants (`PlantsScreen.tsx`) | Title; "View alerts" secondary button above the list (only when plants exist); row cards (16 px padding, 14 px radius, 1 px border, plant name 18 px, area caption, moisture value bold at right, status chips below); ghost "Refresh" at the bottom. Empty state: heading and body, **no button**. |
| Plant detail (`PlantDetailScreen.tsx`) | Name title; three meta tiles (location, room, soil); status chips; age caption; five metric tiles in a two-column grid (22 px values); a 120 px bar chart with dashed threshold lines; an hourly table; "Photos" secondary; "Remove plant" as a **filled red** full-width button. |
| Profile (`ProfileScreen.tsx`) | Stacked label and value pairs (e-mail, plan, with Premium or Connect buttons), display name field and "Save name", primary "Add a sensor", a placeholder line "Your plant list is added in a later version.", "Sign out", "Delete account", legal line. All buttons are full width and there are no section headings. |
| Alerts (`AlertsScreen.tsx`) | Muted intro (7-day window; push not built), one card per alert (plant name, status chip, one sentence), ghost "Refresh". Empty state: heading and body. |
| Shared UI (`src/ui/primitives.tsx`, `TabBar.tsx`, `StatusChip.tsx`) | Buttons: 44 px minimum height, 10 px radius, 16 px semibold label, no pressed state. Tab bar: two text-only tabs with a 3 px top indicator, no icons. Status chip: glyph, text and colour. |

Cross-cutting facts from the code (these drive most recommendations):

- **No pressed state anywhere.** `Button`, the plant row and `Choice` use static style objects. Tapping gives no visual feedback beyond the default.
- **No icons.** The only glyphs are text characters (●▲◆■○✕ and ✓). Tabs are text only.
- **No motion.** No animation code is used in the app.
- **Two type tokens are unused:** `type.display` (34 px) and `type.number` (40 px). Only `type.label` is used (setup clock). So there is no hero number anywhere.
- **Loading** is plain muted text ("Loading…") on the list, detail and alerts screens.
- **The main job sits behind a tab.** The primary action "Add a sensor" lives on Profile. My plants has no add button, not even in its empty state.
- **Theme is generated.** `theme.ts` says it is generated from `tokens.json` by `showcase/brand/app/make_app_assets.py`. Colour and type changes must be made in the source, then regenerated. Do not hand-edit `theme.ts`.
- **Contrast is tested.** `src/__tests__/theme.test.ts` asserts 4.5:1 for text pairs and for every status colour on bg, surface and its soft background.

---

## 3. Recommendations by screen

Format: what to change; why (principle); effort; and what else it touches (bench step and UI tests). Bench references are to `bench/app/run_appium.sh`. Test references are to files in `projects/plant-monitor/app/src/__tests__` unless stated.

### 3.1 Welcome

**W1. Make the setup time a target, not a promise.** Change the second sentence of `welcome.tagline` from "Set up a sensor in under 3 minutes." to "Target: set up a sensor in under 3 minutes." The same wording is already used as a target on the done screen ("target: 3 minutes or less") and in NFR-03. Nothing measured on the bench supports a flat promise yet.
- Principle: honest copy (trust, P7-style clarity). Effort: **S**.
- Touches: `strings/en.json` `welcome.tagline`. `screens.test.tsx` asserts the literal "under 3 minutes" (update the expected string in the same change). Bench: none (bench reads `app.name` and `app.mockBanner` only). E2E: keep "Know when your plants are thirsty" unchanged, because `e2e/web-flow.test.js` waits for it.

**W2. Replace the bare icon-and-tagline with three short benefit lines.** Each line is a real product fact already in the copy: a sensor reads soil every 15 minutes; alerts for too dry, too wet and low battery; no limit on plants. Use a simple glyph or numbered marker per line.
- Principle: P1 (the first screen shows what the user gets before asking for an account), P5. Effort: **S**.
- Touches: new `welcome.benefit.*` keys in `strings/en.json` (keep the tagline key). `strings.test.ts` checks keys exist, so add any new keys there. Bench: none. Tests: none assert the layout.

### 3.2 Setup flow (device setup)

**S1. Progress as five segments with one number per step.** The current progress row shows "Step n of 5" with numbers out of order: ready 1, connect 1, Wi-Fi 2, name 3, linking 3, photo 4, details 5. Replace the text with five segments, one per step (fill the segments done so far), and keep the elapsed clock on the right. The clock must stay: NFR-03 (3-minute target, timer shown) is a requirement.
- Principle: P2 (clear progress). Effort: **S**.
- Touches: `SetupSteps.tsx` `Progress` only. Tests: `setupFlow.test.tsx` lines 91 and 94 assert the accessibility label "Step 1 of 5. Time so far 0:00." and a regex for step 2. Update both in the same change, or keep the label text. Bench: not affected (the bench does not read `a11y.setupProgress`, checked).

**S2. Step 1: lead with the button, shorten the instruction.** Replace the four paragraphs with one headline ("Put the sensor in the soil") and three numbered steps (press the pinhole button, keep the phone close, tap Find). Move the permission note and the "not found" help under the primary button. Add a simple illustration later if the team wants one (M).
- Principle: P1 (one primary action in view), P6 (chunked instructions). Effort: **S** for copy and order; **M** with an illustration.
- Touches: `setup.ready.*` keys. Bench step 2 waits for `setup.ready.device` as a content description, so keep that key's text format (`{name}`, `{bars}`) and the device button's `a11yLabel`. Tests: `setupFlow.test.tsx` taps "Find my sensor" and the e2e test uses the same literal; keep that text.

**S3. Scan the sensor's code with the camera, keep typing as the fallback.** Today the user types the code from the label. The copy already says QR scanning comes with the Bluetooth build, so this is planned work. Keep the text field and its label for the fallback.
- Principle: P6 (less effort, fewer typing errors), P4 (no fiddly text entry). Effort: **L** (camera permission, a new dependency, Architect and pipeline review). Needs a requirement check first.
- Touches: `ConnectStep` and the setup code parser (`provisioning/label.ts`). Bench: types into `setup.connect.codeLabel` (keep that field and its label). Tests: keep the typed path covered.

**S4. Linking as a three-row checklist.** Show three rows: Wi-Fi joined, sensor linked, plant saved. Tick each row as it completes and highlight the current one. The spinner stays, but the checklist carries the progress.
- Principle: P2 (visible progress), P3 (each step acknowledged). Effort: **S**.
- Touches: `LinkingStep` and `setup.link.*` keys. Bench: the bench header lists `setup.link.title` as a screen in the order, so keep that title text. Tests: no test was found that asserts the "Connecting" or tick texts.

**S5. Done: a clear finish and a primary label that says what happens.** Change the primary label from "Done" to what the button does ("Go to my plants"). Show a small success block: a check glyph, the plant name, and the setup time. Keep the title "All set!".
- Principle: P3 (a clear finish using facts only), P1 (the primary label names the outcome). Effort: **S**.
- Touches: `setup.done.seePlant` (value only; the bench reads this key from `strings/en.json` at run time, so the value change is picked up). Bench: taps this label and then `nav.plants`; keep `setup.done.title` ("All set!") because the bench waits for it. Tests: keep the body text "Setup time … (target: 3 minutes or less)" (`setupFlow.test.tsx` line 64). "Done" is not asserted as a literal in the tests. Note: "Go to my plants" is already the label of `setup.linked.leave` (a different screen, asserted in `setupFlow.test.tsx` line 282), so the copy is in use elsewhere in the app.

**S6. Details: split the long form into two steps.** Step A: plant name and where it is (location, area). Step B: soil, species, city (species and city marked optional). Each step has a short heading. The five fields and two radio groups stop competing on one scroll.
- Principle: P6 (chunking), P2 (progress through two short steps). Effort: **M**.
- Touches: `DetailsStep`, `setupState.ts` (step count: `STEP_COUNT` is 5 today, so the progress change in S1 must follow this). Bench: **bench change required**. Step 5 types `setup.details.name`, `area` and `city` in one screen and taps `setup.details.save`; the split changes that order. Tests: `setupRealSave.test.tsx`, `setupFlow.test.tsx`.

**S7. Move-choice and linked screens (no change now).** These are rare paths and mostly text. Only the button order might change. Not in this review's priorities.

### 3.3 My plants

**P-A. Empty-state button.** A new account lands on "No plants yet" with no action. Add a primary "Add a sensor" button under the empty text. The same button stays on Profile.
- Principle: P5 (empty state as guidance), P1 (one primary action). Effort: **S**.
- Touches: `PlantsScreen.tsx` empty branch only. Tests: `plants.test.tsx` line 129 asserts the header "No plants yet" (unchanged). Add an assertion for the button. The tab bar is shown for the active route (`App.tsx` line 113), so the empty-state button and the Profile button should not be on screen together (not checked at runtime). Bench: a new account lands here after sign-up and then taps `nav.profile`, so it is unaffected.

**P-B. Moisture meter on each row.** Add a thin horizontal meter under the plant name: 0 to 100 %, with the dry and wet thresholds marked (`dryThresholdPct` and `wetThresholdPct` already exist on the plant record, `plants/types.ts` lines 32 and 33). The fill uses the existing status colours. Keep the chip; the meter is decoration that repeats the status.
- Principle: P2 (at-a-glance progress toward a healthy band), P7 (shape and text stay). Effort: **M**.
- Touches: `PlantRow` only. The meter must be hidden from accessibility. The row's accessible label (`plants.row.a11y`) must stay exactly as it is. Bench: the bench finds the row with a regular expression built from `plants.row.a11y` (`descMatches`), so that string and the row's accessible label must not change. E2E: `web-flow.test.js` line 108 looks for the value text "38 %", which stays. Tests: `plants.test.tsx` finds rows by name; keep that.

**P-C. Refresh and alerts placement.** Add pull-to-refresh (P9). Keep the "Refresh" button for now. Move "View alerts" out of the list's top area into a header row, or into an Alerts tab once that exists (the tab bar's comment says so).
- Principle: P9 (native patterns), P1 (the list is the first thing seen). Effort: **M**.
- Touches: `PlantsScreen.tsx`. **Bench:** step 3 taps `plants.refresh` in a loop until the row appears (`run_appium.sh` line 470), so removing that button breaks the bench. Tests: `alertsScreen.test.tsx` lines 63 to 66 tap "View alerts"; update when the button moves.

### 3.4 Plant detail

**D-A. One hero number.** Show soil moisture as the hero: the `type.number` token (40 px, unused today) with the status chip under it. The other four readings (temperature, humidity, light, battery) form a smaller row of tiles below.
- Principle: P2 (one number to read first), hierarchy (P1). Effort: **S** to **M**.
- Touches: `PlantDetailScreen.tsx` `cell()` layout. Tests: grep `src/__tests__` for the value strings used by `plant.latest.*` before changing; the e2e test does not read this screen. Bench: none.

**D-B. Quieter "Remove plant".** The filled red button is the loudest thing on the screen, although the remove screen already asks the user to type the plant name to confirm. Change it to a text-style danger link at the bottom of the screen.
- Principle: P8 (calm), P1 (the primary action stays clear). Effort: **S**.
- Touches: `PlantDetailScreen.tsx` only (the `danger` button variant is also used on delete-account; do not change the variant itself). Tests: `removeLeftover.test.tsx`, `plants.test.tsx` and `plantsSlice2.test.tsx` press "Remove plant" by text, which stays. Bench: none.

**D-C. One next-step line from the status.** Under the chips, show one sentence from the current status, for example "Soil is below the dry limit: water it." This is a fixed rule (no AI), with the copy in `strings/en.json`. The code already reserves the care-tips slot ("Care tips rows … are a later slice"), so check the requirement before building.
- Principle: P1 (a clear next step). Effort: **M**.
- Touches: a pure helper next to `plants/status.ts` (unit tested), `PlantDetailScreen.tsx`, new keys. Bench: none. Ownership: the care-tip rules belong to the cloud-AI work, so the rule must stay deterministic and reviewed.

### 3.5 Profile

**F-A. Group the page into sections.** Use section headings: Account (e-mail, display name), Plan (plan line and its buttons), Sensors ("Add a sensor"), Session (sign out) and a separate Danger area (delete account) with a divider.
- Principle: P9 (grouped settings), P6 (chunking). Effort: **M**.
- Touches: `ProfileScreen.tsx`. **Keep the labels** "Add a sensor", "Save name", "Sign out" and "Delete account": the bench taps `nav.profile` then `setup.addSensor` (`run_appium.sh` line 399 and 400), and tests tap "Save name" (`screens.test.tsx` line 94), "Sign out" and "Delete account" (`deleteAccount*.test.tsx`), and the dashboard and Connect-AI entries (`profileDashboardEntry.test.tsx`, `profileConnectAiEntry.test.tsx`).

**F-B. Remove the roadmap line.** "Your plant list is added in a later version." reads as unfinished. Remove it, or replace it with the real sensor count.
- Principle: P5 (no dead ends), honest copy. Effort: **S**.
- Touches: `profile.plantsSoon` in `strings/en.json`. No test asserts it (text search found none). Bench: none.

### 3.6 Alerts

**A-A. Group by plant, with a next step.** Group the cards by plant name and end each card with the next step (the same rule as D-C). The cards already sort by alert kind (offline first) in `plants/alerts.ts`; keep that order inside each plant.
- Principle: P1 (next step), P2 (one place to see each plant's state). Effort: **S** to **M**.
- Touches: `AlertsScreen.tsx`. Tests: `alerts.test.ts` tests the pure rules and is not affected by layout. `alertsScreen.test.tsx` checks the card texts; update that file together. Bench: none.

**A-B. Move the "push not built" note to a caption.** The intro explains that push notifications are not built and that alerts show on this screen only. Keep the honesty, but move it under the title as a caption and shorten it.
- Principle: P8 (calm), honest status. Effort: **S**.
- Touches: `alerts.intro` in `strings/en.json`. `alertsScreen.test.tsx` asserts the text "Push notifications are not built yet" (update the expected string). Bench: none.

### 3.7 Shared UI and design system (all screens)

**G-A. Pressed feedback on every tappable element.** `Button`, the plant row, `Choice` and the tab bar have no pressed style. Add a visible pressed state (a background shift or a short opacity change) and keep the 44 px minimum height.
- Principle: P4 (feedback on big targets), P8 (no bouncing). Effort: **S**.
- Touches: `src/ui/primitives.tsx`, `TabBar.tsx`, the plant row. No label changes. Bench: none. Tests: none assert the style.

**G-B. Icons in the tab bar.** Add one icon for Plants and one for Profile, next to the visible text labels. Keep the text (the bench and tests find tabs by their text and role). Choose an icon set with a licence that allows use in the app, and record the licence in the repo.
- Principle: P9 (platform-native navigation). Effort: **M** (including the dependency review).
- Touches: `TabBar.tsx`; `package.json` for the new dependency (Architect review and pipeline check). Bench: taps `nav.profile` and `nav.plants` by visible text, so keep the labels; check the bench's `tap()` matching before merging (not verified in this review). Tests: `findByRole('tab')` queries (7 uses) are unaffected if the role and label stay.

**G-C. Use the accent with more intent.** Today the green accent appears only on primary buttons and the tab indicator. Use the existing accent-soft tint behind one key moment per screen (the done block, the hero number, the meter fill). Make these changes in `tokens.json` (source) and `showcase/brand/brand.css`, then regenerate `theme.ts`.
- Principle: P3 (a clear finish), bold but calm colour (P8). Effort: **S** to **M**.
- Touches: `tokens.json`, `theme.ts` (generated, do not hand-edit), `showcase/brand/app/make_app_assets.py`. Tests: `theme.test.ts` requires 4.5:1 for every text pair and every status colour on bg, surface and its soft background. Run it. Bench: none.

**G-D. Short, calm motion, reduced-motion aware.** Animate the step change (a short slide or fade), the meter fill and the checklist ticks. Turn all of it off when the system asks for reduced motion.
- Principle: P8 (calm), P2 (continuity). Effort: **M**.
- Touches: `Progress`, the meter, `LinkingStep`. Tests: needs a reduced-motion mock. Bench: the bench waits for elements with timeouts, so a 200 ms animation does not change the outcome, but this was not run on a device.

**G-E. Skeletons instead of "Loading…".** Replace the muted "Loading…" text on plants, detail and alerts with placeholder blocks in the card shape.
- Principle: P3 (perceived progress). Effort: **M**.
- Touches: `PlantsScreen.tsx`, `PlantDetailScreen.tsx`, `AlertsScreen.tsx`. Tests: grep for the loading text before changing. Bench: the bench does not wait for the loading text (not checked in detail).

---

## 4. Bench and UI-test impact register

What a change would break, by label or file. "Safe" means the change keeps the listed label or key.

| Item | Bench (`bench/app/run_appium.sh`) | UI tests (`src/__tests__`, `e2e/`) |
|---|---|---|
| `nav.profile` (tab text "Profile") | Step 2 taps it (line 399). Keep the text. | `findByRole('tab')` queries. |
| `nav.plants` (tab text "Plants") | Step 3 taps it (line 451). Keep the text. | `getByRole('tab', { name: 'Plants' })` in `e2e`. |
| `setup.addSensor` "Add a sensor" (Profile) | Step 2 taps it (line 400). Keep on Profile, or change the bench. | `setupFlow.test.tsx` headers; `profileDashboardEntry`, `profileConnectAiEntry`. |
| `setup.findSensor` "Find my sensor" | Step 2 taps it (line 401). | `setupFlow.test.tsx` line 22; `e2e` line 97. Keep the literal. |
| `setup.ready.device` "Sensor {name}, {bars}" (button content description) | Step 2 matches it with `descStarts` (line 403 to 405). Keep the format. | `setupFlow.test.tsx`. |
| `setup.connect.codeLabel` (field label) | Step 2 types the setup code into this field (line 408). Keep the label. | Grep before changing; the connect tests use the field. |
| `setup.connect.submit` "Connect" | Step 2 taps it (line 409). | Not found as a literal. The tests tap "Connect sensor" (`setup.name.submit`, the name step): `setupFlow.test.tsx` lines 38, 165, 174, 183. |
| `setup.done.seePlant` (current "Done") | Step 2 taps it (line 446). Value may change; the key must stay. | None found as a literal. |
| `setup.done.title` "All set!" | The bench waits for it (lines 436 to 437). Keep. | `setupFlow.test.tsx`. |
| `setup.details.name` / `area` / `city` / `save` | Step 5 types into them and taps save (sequence in the bench). Changing order (S6) needs a bench change. | `setupRealSave.test.tsx`, `setupFlow.test.tsx`. |
| `plants.title` "My plants" | Step 1 probes it (line 353); step 3 waits for it (line 452). Keep. | Many `findByRole('header', { name: 'My plants' })` queries. |
| `plants.refresh` "Refresh" | Step 3 taps it in a loop (line 470). Removing it (P-C) needs a bench change. | None found as a literal. |
| `plants.row.a11y` (row accessible label template) | Step 3 builds a regular expression from it (line 453). Must not change. | `plants.test.tsx` finds rows by name. |
| Setup progress label (`a11y.setupProgress`) | Not used by the bench. | `setupFlow.test.tsx` lines 91 and 94 (literal). |
| `welcome.tagline` (second sentence "under 3 minutes") | Not used by the bench. | `screens.test.tsx` (literal). `e2e` waits for the first sentence. |
| `alerts.intro` ("Push notifications are not built yet") | Not used by the bench. | `alertsScreen.test.tsx` (literal). |
| "View alerts" button | Not used by the bench. | `alertsScreen.test.tsx` lines 63 to 66. |
| "Remove plant" button | Not used by the bench. | `removeLeftover`, `plants`, `plantsSlice2` tests press it by text. Keep the text. |
| "Save name", "Sign out", "Delete account" | Not used by the bench. | `screens.test.tsx` line 94; `deleteAccount*.test.tsx`. |
| Theme tokens (`theme.ts`) | Not used by the bench. | `theme.test.ts` (4.5:1, status pairs). |

Two more rules for anyone changing the app:

- The bench reads labels from `strings/en.json` at run time. Changing a value is safe for the bench, but **renaming or removing a key breaks it immediately** (the script fails with "a string key is missing").
- Test files use literal English strings, not keys. Changing a value breaks the matching test unless both change together.

---

## 5. Top 5 changes for the next sprint

Chosen for the highest visible gain at the lowest bench and test risk. Ordered by value.

| # | Change (ID) | Principles | Effort | Bench impact | UI-test impact |
|---|---|---|---|---|---|
| 1 | **Empty-state "Add a sensor" button on My plants** (P-A) | P5, P1 | S | None. The bench still taps Profile after sign-up. | Add one assertion in `plants.test.tsx`. |
| 2 | **Five-segment setup progress, one number per step** (S1) | P2 | S | None. The bench does not read the progress label. | Update `setupFlow.test.tsx` lines 91 and 94 in the same change. |
| 3 | **Done step: outcome-named primary button and a success block** (S5) | P3, P1 | S | Value of `setup.done.seePlant` changes; the key and `setup.done.title` stay. | None literal. Keep the "Setup time …" text. |
| 4 | **Moisture meter on each plant row** (P-B) | P2, P7 | M | None, provided `plants.row.a11y` and the row's accessible label do not change. | Add a render test in `plants.test.tsx`. |
| 5 | **Pressed feedback on buttons, rows, choices and tabs** (G-A) | P4 | S | None. | None asserts style. |

**Also do now (copy, not design, effort S):** W1, the "under 3 minutes" wording on the welcome screen, since NFR-03 is a target and the bench does not measure it yet. It changes one test literal in `screens.test.tsx`.

**Next sprint or later, because they change the bench:** S6 (split details, bench step 5), P-C (removing or moving Refresh, bench step 3), F-A (sections on Profile, keep the labels). Also S3 (camera scan), which needs a requirement check.

---

## 6. What could not be checked

- **No running app, no screenshots, no device.** Every statement about the look comes from the style code. Real spacing, wrapping, font rendering and German text lengths were not seen.
- **No tests were run** (Jest, e2e) and **no bench step was run**. The bench and test references come from reading and text search. The matching rules of the bench's `tap()` were not checked in detail (G-B depends on this).
- **Not reviewed in depth:** the plant gallery, the remove-plant screen, the premium dashboard, Connect-AI, the delete-account screen and the hourly table. They were not part of the requested screens.
- **Test references** were found by text search over `src/__tests__` and `e2e/`. A test that builds its selectors some other way could still break and would only show up in a test run.
- **Contrast** was not computed for new colours. The existing contrast test must run after any token change.
- **Icon licences** were not checked (G-B needs this before a dependency is added).
- **Requirements** (FR/NFR text) were not read in full. S3 (camera scan) and D-C (next-step line) need a requirement check before they are scheduled.
- **Market or user research** was not done. The principles are general UX practice, not measured on this app's users.

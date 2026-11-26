# App v3 proposal: structure changes on My plants, device setup and plant detail

Follows `V2-PROPOSAL.md` (tokens only) and the review in `../REVIEW-lena-2026-11-26.md`. v3 changes structure: what a screen shows first, how many steps setup has, and where the main action sits.
Screenshots: `screens/2026-11-26/v3-<screen>.png` (390 x 844 at 2x, mock data). Side by side: `side-by-side-plants.png` and `side-by-side-plant-detail.png` (v1 | v2 | v3).
Principles P1 to P9 are those of `projects/plant-monitor/docs/design/app-design-review-2026-11-25.md`.
Research: `ux-research-2026-11-26.md` (team research brief). Its verification key applies: [F] fetched and checked, [S] search snippet only, [X] not verified.

## Changes, by screen

| # | Screen | Change | Principle | Research source | Status |
|---|---|---|---|---|---|
| 1 | My plants | "Needs attention" strip above the list: counts of too dry, too wet, low battery. Computed on the client from the list the screen already loads (`attentionCounts`, `src/plants/status.ts`). Shown only when a count is above zero. No endpoint. | P1 (most urgent state first), P2 | Summary-first home: Oura Today [S3, fetched page describes "key scores and a daily highlight"]; Apple "summary, then detail" [S1, S8] | Done. Counts are from the open alerts in the list, so they are only as fresh as that list. Offline and no-sensor plants are not counted (see unverified). |
| 2 | My plants, empty | Primary "Add your first plant" (goes to device setup), and a text link "How the sensor works" that shows three facts from existing copy. | P5 (empty state as guidance), P1 | NN/g empty states [F, S5]: a direct next step, and never a blank state. Apple onboarding: contextual tips, not a tour [F, S7] | Done. Not rendered: the mock always has fixture plants, so no empty account can be shown. |
| 3 | Device setup | Progress is "Step n of 4" (was 5). Stages: 1 find and connect, 2 Wi-Fi, 3 name and link, 4 photo and plant details (the finish). One screen per stage, as before. | P2 (clear progress), P6 (fewer steps) | Apple onboarding: brief and optional [F, S7]. Setup sequence: Google Home add flow, one action per step [F, S9] | Done. Setup code entry stays the only input. |
| 4 | Plant detail | Hero: soil moisture as the large number (`type.number`), above the chart. The four other readings (temperature, humidity, light, battery) form a smaller grid below. The soil value is no longer repeated in the grid. | P2 (one number to read first), P1 | Oura Vitals: summary metric, then drill-in [F, S3] | Done. |
| 5 | Plant detail | One primary action: "Photos" (filled). "Remove plant" becomes a text-style danger button (`dangerQuiet`), no fill. | P1, P8 (calm) | Material 3: one highest-importance action; secondary actions in a bar or menu [F, S2] | Done. Delete account keeps its filled danger button (profile). |
| 6 | My plants, long lists | Title and back button stay at the top while a list of five or more plants scrolls (sticky, not collapsing). | P9 (platform pattern) | Apple large title that becomes a standard title on scroll [S11, page did not load, not verified] | Done as a sticky title only. The collapse animation is not built, because its source is not verified. |
| 7 | Navigation | No change. Still four screens reached from two tabs (Plants, Profile). | — | Apple: tabs for navigation, not actions; 3 to 5 destinations [F, S1, S2] | Not done. Moving Alerts or Premium into tabs, or moving "Add" into a header, is listed for a later decision (see below). |

## Not done, and why

- **QR scan first (setup).** The research shows QR first with a code fallback [F, S9]. Our sensor label is read by typing the code. A camera scan needs a new dependency and a requirement check (review item S3, effort L). Not built, so setup code entry is still the only input. The screen says nothing about QR.
- **Splitting the details form into two steps.** The bench step d types the name, area and city on one screen. Splitting it changes the bench order. Needs the bench owner.
- **Tab bar changes.** Not made. The research suggests four tabs (Plants, Alerts, Premium, Profile) and "Add" in a header. Not done: it changes navigation for every test, and the bench taps the tabs by label. Needs a decision first.
- **Large-title collapse.** The Apple source for it was not opened [S11]. Only the sticky title was built.
- **Pull to refresh.** Not verified [S17, 404]. Not added.
- **Dark mode and the rest of the research list.** Not changed in this round.

## Hard rules kept

- 48 px targets: every button in the new screens uses `minTouchTarget` (48), including the text-style remove action.
- 3:1 control contrast: unchanged from v2 (`control` token). The quiet danger text is danger on bg, 5.95:1 light, 6.01:1 dark (the existing contrast test covers danger on bg).
- No backend, Supabase or contract change. Only `src/` screens, `strings/en.json` (new keys only, no existing value changed), and the setup step count.
- Brand tokens: no change beyond v2.
- Copy: every new string is in `strings/en.json`. Setup step copy is unchanged apart from the number.

## Bench impact (`bench/app/run_appium.sh`)

| Bench step | Touched? | Why |
|---|---|---|
| 1 (sign-in, probe `plants.title`) | No | Header text unchanged. Sticky title does not change text. |
| 2 (profile, setup, `setup.addSensor`, `setup.findSensor`, `setup.ready.device`, `setup.connect.codeLabel`, `setup.connect.submit`, `setup.wifi.*`, `setup.name.*`, `setup.link.title`, `setup.photo.*`, `setup.done.*`) | No label change | Step count is not read by the bench (`setup.step` and `a11y.setupProgress` are not in the bench key list). The details screen is unchanged. |
| 3 (`nav.plants`, `plants.title`, `plants.row.a11y`, `plants.refresh`) | Checked, not changed | The attention strip is not a button and does not match the row pattern. Refresh stays. |
| Empty-state button "Add your first plant" | Not used by the bench | A new account in the real build lands on an empty list; the bench moves on to Profile. |
| Plant detail | Not in the bench | The bench does not open plant detail. |

Not run on a device. The bench has not been run.

## UI tests

- New: `src/__tests__/v3Structure.test.tsx` (9 tests): attention counts (unit and on screen), strip hidden when there are no counts, empty-state button and how-link, long-list threshold, title still a header on long lists, soil value shown once in the hero, dash for no reading.
- Changed literals: `setupFlow.test.tsx` ("Step 1 of 4", "Step 2 of 4"), `provisioning.test.ts` (max step 4), `alertsScreen.test.tsx` (new required prop).
- Unchanged and passing: `plants.test.tsx` (the 38 % check still finds one value), `screens.test.tsx`, the contrast tests.

## Unverified

- The attention counts are only as good as the open alerts in the list. If the list is stale, the strip is stale too.
- Offline and no-sensor plants are not counted in the strip. Users may read a short strip as "all fine". The strip is hidden when all counts are zero, but offline plants still exist. Needs a decision.
- Sticky title: the static screenshots cannot show scrolling. Behaviour on a phone is not checked.
- "Remove plant" as text-style: not checked for discoverability with users.
- The research sources are one vendor's blog ([F, S3] Oura), NN/g and Apple/Google help pages. They support the direction, not the exact numbers.
- Empty state and setup progress on a real account: not rendered (the mock has fixture plants).

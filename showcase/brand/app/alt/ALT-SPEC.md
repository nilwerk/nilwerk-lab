# Alternative app design: spec

Status: design only, no app code changed. Visual source: `final-mockups.html` (all screens, user journeys, mock data). Principles P1 to P9 come from `projects/plant-monitor/docs/design/app-design-review-2026-11-25.md`.

## Decisions (answered by Arsany, 26 Nov)

| Topic | Decision |
|---|---|
| Setup steps | Five, as on main |
| Tabs | Three: Plants, Alerts (with badge), Profile |
| Gallery | Grid, three per row, day headers, date on each photo |
| Photo picker | `expo-image-picker` approved. Added in the build PR after a requirement check. |
| Setup details | One screen this round |
| Plan price | Shown on Profile before Premium is opened |
| Lena's role | Approved |

## Navigation, back and scroll

- **Route stack.** Each push records the screen and its scroll position. System back and the on-screen back both pop the stack. Alerts → plant → back returns to Alerts.
- **Sheets.** Premium, link error and move choice are bottom sheets. System back closes a sheet before it pops a screen.
- **Plants root.** First back press shows "press back again to leave". A second press within 2 s exits.
- **Header.** One fixed header with a 48 × 48 dp back control, outside the scroll area.
- **Scroll.** Virtualised lists. The last row clears the tab bar and any footer button. Position is kept on return. Pull to refresh is added, and the Refresh button stays for the bench.

## Bench and test impact

| Change | Bench | Labels or keys | Tests |
|---|---|---|---|
| Route stack and system back | Not yet checked whether any step uses system back | None | New navigation tests |
| Header back | Not yet checked whether the bench taps back by label (`a11y.back`) | Unchanged | Existing screen tests |
| Three tabs | Tabs are tapped by label (`nav.plants`, `nav.profile`); the Alerts tab is new | New `nav.alerts` key | Alerts routing tests |
| Five setup segments | Step 2 does not read `a11y.setupProgress` | Progress text | `setupFlow.test.tsx` "Step n of 5" |
| "Go to my plants" | Step 2 taps the done screen's button | Value of `setup.done.seePlant` changes | Keep "All set!" and the time text |
| Needs-water card and row meter | Step 3 taps `plants.refresh` and matches `plants.row.a11y` | Row label unchanged | Row tests |
| Next-step line and chart gap | Not in bench | New `plant.next.*` and `plant.chart.noReading` | New unit tests |
| Photo grid, viewer, add photo | Not in bench | New `gallery.*` keys | Gallery and viewer tests |

**Bench rule:** any label or key change needs Peter's bench check and Ines's review first. Nothing here has been run on a device.

## Not in this design

- Code, dependencies, strings, tokens and `theme.ts` (each follows in its own PR).
- Device screenshots and bench runs.
- Real photo upload; the real build keeps "photos not available yet" until the picker lands.

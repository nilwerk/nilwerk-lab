# App v2 proposal: what changes on each screen

Based on the review in `../REVIEW-lena-2026-11-26.md` and the design review in `projects/plant-monitor/docs/design/app-design-review-2026-11-25.md` (principles P1 to P9).
Screenshots: `screens/2026-11-26/`. Each screen has `v1-<screen>.png` (origin/main) and `v2-<screen>.png` (this branch), 390 x 844 at 2x, from the mock web build with mock data.

## What the v2 branch changes (rendered in the v2 screenshots)

Token and style only, no string, key or layout change:

| Token or style | v1 | v2 | Principle |
|---|---|---|---|
| Control border (text fields, radio choices, secondary buttons) | `line`, 1.22:1 on bg | `control`, 3.48:1 on bg, 3.82:1 on surface | P4, P6 (controls easy to find). WCAG 1.4.11 |
| Minimum touch height | 44 | 48 | P4 (large, forgiving targets). Android 48 dp |
| Label style (elapsed clock, mono) | 12 / 16 | 13 / 18 | P2 (readable progress clock) |

Visible in the screenshots: the "View alerts" button and the secondary buttons have a visible grey outline; buttons, rows and tabs are about 4 px taller. Colours of the text, status chips and the screen layout are unchanged.

Per screen:

| Screen | v2 change visible | Next step (one per screen, not rendered) |
|---|---|---|
| Welcome (`v2-welcome.png`) | Primary and secondary buttons are 48 px tall. The secondary button has a clear outline. | Show three short benefit lines above the buttons (P1). Copy-only change; keys are new, so it needs a check on the bench labels first. |
| Sign-up (`v2-auth-signup.png`) | Input fields have a visible 3:1 border. | Keep the field errors next to the field they belong to (P6). Already done in the app. |
| Setup, step 1 (`v2-setup-step1.png`) | Button 48 px, clock label 13 px. | Five segments for progress, one number per step (P2). Changes `SetupSteps.tsx` Progress; `setupFlow.test.tsx` asserts the label text. |
| My plants (`v2-plants.png`) | "View alerts" outline is visible; rows about 4 px taller. | Empty state gets a primary "Add a sensor" button (P5, P1). Code change in `PlantsScreen.tsx`. The bench is not affected. |
| Plant detail (`v2-plant-detail.png`) | Tiles and chart unchanged apart from target heights. | Soil moisture as the hero number, using the `number` type token that is not used today (P2). Remove plant becomes a quiet text button (P8). |
| Alerts (`v2-alerts.png`) | Card layout unchanged; the Refresh and View alerts buttons are taller. | Group cards by plant and end each with the next step (P1). |
| Profile (`v2-profile.png`) | Buttons and the name field have the visible border. | Group the page into sections: Account, Plan, Sensors, Session, and a separate Danger area (P9). Keep the button labels; the bench taps them. |
| Premium (`v2-premium-sheet.png`) | Buttons are taller. | No change proposed in this round. The premium dashboard screen could not be captured (see below). |

## Not rendered in this round, and why

- **Premium dashboard.** The dashboard entry only appears for a premium account (`ProfileScreen.tsx` line 61). The mock sign-up always creates a free account, and the mock has no switch for premium. The screenshot in the folder is the premium sheet instead, under the name `premium-sheet`. Needs a mock switch, or a fixture, to capture it.
- **All next-step changes above.** They change code or copy, so they are a separate PR after review. Each one names its bench and test impact in the review's section 4.
- **Dark mode.** Not captured. The dark tokens pass the checks (see the review); the screenshots are light only.
- **Real device.** Nothing was run on a phone. Font rendering on Android, text wrap in German, and the Bluetooth setup flow are not seen here.

## Bench and UI test impact of v2

- Bench (`bench/app/run_appium.sh`): none of the v2 changes alter a label, a key or a screen order. The bench taps by label, and the only coordinate tap is a fallback at the top of the screen. Taller buttons do not change the taps. Not run on a device; the bench owner's check is still needed before merge.
- UI tests: `theme.test.ts` (new: control 3:1; touch 48). Jest 36 suites, 505 tests, all pass. `npx tsc --noEmit` exit 0.

## Decisions for the owner

1. Approve the v2 direction (token-level changes now, screen steps later).
2. Choose the order of the screen steps. Recommended: P-A (empty state button) first, then S1 (progress segments), then D-A (hero number). The review's section 5 gives the same order.

# Alternative design: the rest of the screens, navigation, scroll, back and photos

Status: **draft, design only.** Extends `ALT-DESIGN.md` (My plants, plant detail, setup, done). Same principles P1 to P9 from `projects/plant-monitor/docs/design/app-design-review-2026-11-25.md`, plus the navigation rules below. Mock data only: `alt-mockup-screens.html`.

## 0. What the code does today (checked, `projects/plant-monitor/app`)

| Area | Today | Problem for the design |
|---|---|---|
| Android back | No `BackHandler` anywhere in `src` or `App.tsx`. | System back leaves the app from any screen, even plant detail or the gallery. |
| Route history | `App.tsx` holds one `route` value. Each screen gets an explicit `onBack` that sets a fixed parent (for example gallery goes back to plant detail). | No stack. Going back from an alert to a plant lands on Plants, not on Alerts. |
| Header back | `Screen` renders a ghost "Back" button in the scroll content, so it scrolls away. | The way back is lost on long screens. |
| Scroll | Every screen is a `ScrollView`. Sticky title only on long lists (v3). | Tab bar sits outside the scroll area, so the last item can hide under it. |
| Photos, real build | `noPhotoSource`: no camera or library picker. The gallery only lists photos that already exist. | "Add photo" cannot work yet. The design must show that honestly. |
| Photos, gallery | Sort buttons (Newest, Oldest), grid with a date per photo. No full-size viewer found in `PlantGalleryScreen.tsx`. | Users cannot open a photo bigger, swipe between photos, or delete one. |

## 1. Navigation model

**Route stack.** Replace the single route value with a stack. Each push records the screen and its scroll position. Each screen names its parent for the on-screen back button, and the stack decides what system back does.

| From | Forward | On-screen back | System back (Android) and edge swipe (iOS) |
|---|---|---|---|
| Plants | Plant detail | Plants | Pop to Plants |
| Alerts | Plant detail | Alerts | Pop to Alerts (not Plants) |
| Plant detail | Gallery | Plant detail | Pop to Plant detail |
| Gallery | Photo viewer | Gallery | Pop to Gallery, or close the viewer first |
| Any sheet (Premium, Remove, Sort, Move choice) | — | Close (X) | Closes the sheet first, then pops the screen below |
| Plants (root) | — | none | First press shows "Press back again to leave"; second press within 2 s exits. |

**Header.** One fixed header on every screen, outside the scroll area: back chevron (48 × 48 dp, with the existing `a11y.back` label), title, optional right action. On long lists the title shrinks into the header on scroll (v3's sticky title, now carrying the back button too).

**Sheets vs full screens.** Short, optional, or one-off tasks use a bottom sheet with a drag handle and an X. Anything the user must finish uses a full screen. Premium is a sheet (decision below). Delete account stays a full screen, because it is irreversible.

**Tabs.** Open decision. Options:
- **A. Two tabs** (today): Plants, Profile. Alerts stay reachable from the Plants header.
- **B. Three tabs** (recommended): Plants, Alerts (with a count badge for open alerts), Profile. Alerts is then one tap away, and the badge gives the "needs attention" state a permanent place. Adds one bench tab step.

Tabs show on Plants, Alerts and Profile and their sub-screens. They hide on setup, gallery, viewer and sheets, so the bottom of the screen is free for the primary action.

## 2. Scroll

- **Padding under the content:** tab bar height plus the bottom safe area, so the last row is never hidden.
- **Lists** (Plants, Alerts, gallery): virtualised lists, not a mapped array in a `ScrollView`. Photos can reach hundreds per plant.
- **Pull to refresh** on Plants and Alerts, using the platform's native control. The **Refresh** button stays, because bench step 3 taps `plants.refresh`. Pull to refresh is an addition, not a replacement.
- **Scroll position** is kept when the user goes back: the Plants list returns to the same row after a plant detail.
- **Keyboard:** on forms, the focused field scrolls above the keyboard, and the primary button sits in a footer above the keyboard, so it does not need scrolling to.
- **Sticky header** only where the title would scroll away: long lists (5+ plants, alerts), gallery, plant detail.

## 3. The rest of the screens

### Welcome
- App mark, not a stock photo. Three benefit lines (review item W2): a sensor reads every 15 minutes; alerts for too dry, too wet and low battery; no limit on plants.
- Primary "Get started". Secondary "I have an account". No Skip on the first screen, because sign-up is the next step.
- Legal line at the bottom, not in the scroll area.

### Sign up and sign in
- One field per row. Labels stay above the field, not inside it (they stay visible while typing).
- Password has a show and hide toggle with a clear label, and a rule line under the field that turns from grey to green when met.
- Errors appear under the field that caused them, with text and an icon, not only colour (P7).
- Footer button: "Create account" or "Sign in", above the keyboard.

### Profile (grouped, review item F-A)
- **Account:** email, display name, "Save name" (only active when the name changes).
- **Plan:** Free or Premium. The plan price shows here before Premium is opened (your decision). Free users see "See Premium". If no price is available: "Price available at checkout".
- **Sensors:** "Add a sensor" (primary).
- **Data:** "Export my data" and "AI connection" (rows that open their own screens).
- **Session:** "Sign out".
- **Danger zone** (separated by a divider, red text): "Delete account".

### Alerts
- Filter chips: All, Too dry, Too wet, Low battery. Each chip shows its count.
- Grouped by day ("Today", "Yesterday", then dates), newest first.
- Each alert card: plant name, status chip (text, colour and icon), time, one sentence. Tap opens the plant detail, and back returns here.
- Intro line: "Last 7 days". Push notifications are not built, so no line says otherwise.
- Empty state (P5): "No alerts this week" with a primary "Check my plants" that opens Plants.

### Plant detail
- Header with back, plant name, and a "⋯" for Remove.
- Under the header: the latest photo as a small thumbnail. Tapping it opens the gallery. With no photo: a dashed box "Add a photo" (disabled in the real build until the picker exists, with the text "Photos arrive in a later version").
- Hero moisture number, status chip, one next-step sentence, chart with dry and wet lines, metric grid. As in `ALT-DESIGN.md`.
- Bottom action row, sticky above the tab bar area: "Photos (n)" filled; "Remove plant" as text-style danger.

### Remove plant
- Full screen, as today. Type the plant name to confirm (keeps the current pattern). Says what goes: the plant history and its photos. Says that a photo removal can fail and offers a retry on the result screen.

### Gallery (FR-A05: unlimited photos, each with its date, newest or oldest first)
- Header: back, "Photos · Basil", count.
- Sort as a two-option segmented control (Newest, Oldest), not two text buttons.
- **Grid** of 3 square thumbnails per row, grouped under day headers ("Mon 24 Nov"). Each thumbnail shows its date in small text, so the grid is not only pictures.
- **Add photo** as the sticky footer button. In the real build it shows "Photos are not available yet" until a picker exists (decision needed for the picker library).
- Empty state: "No photos yet" with "Add the first photo" (same footer, same availability rule).
- Upload states per photo: uploading (a thin progress ring), done, failed (red border, "Retry"). Offline: queued, with a text status "Waiting for connection".

### Photo viewer (new)
- Full screen on a dark background. Opens from a grid tap. Back closes it and returns to the same grid position.
- Swipe left and right to move between photos. Also **Previous** and **Next** buttons, so the move does not depend on a drag (WCAG 2.2 SC 2.5.7, from the playbook).
- Pinch to zoom. A double tap also zooms, as a second option.
- Caption at the bottom: date and time. A "⋯" opens Delete, which asks for confirmation in a sheet.
- Photos are loaded at screen size. Thumbnails stay small in the grid.

### Premium (sheet, not full screen)
- Shows the price (decision). Feature list grouped in three: identify and diagnose, care, sharing. Primary "Continue" hands off to the store. "Restore purchases" as a text link. Close X.
- Premium dashboard: date range (7 or 30 days) as a segmented control. Gaps are shown as "No reading", the same rule as plant detail.

### Connect AI
- Keys are masked after saving (`••••abcd`). A copy button copies once and then shows "Copied". The screen does not claim where keys are stored, until that is verified.

### Delete account (full screen, irreversible)
- Step 1: what goes (plants, photos, history). Offers "Export my data first" as the first option (angle 3 of Poppy's note, so this links to a real export only once it exists on the phone).
- Step 2: type the account e-mail to confirm. The delete button stays disabled until it matches.

### Setup, the remaining steps (five steps, as on main)
- **1 Find sensor:** three numbered steps, primary "Find my sensor", found devices as a list.
- **2 Connect code:** one field, label-based. "Scan code" is not shown until the camera is built (review item S3).
- **3 Wi-Fi:** network list, password field, primary "Continue".
- **4 Name and link:** the three-row checklist (Wi-Fi joined, sensor linked, plant saved) from review item S4, with the clock.
- **5 Photo and details:** one screen, sections "Plant" (name, location, area), "Care" (soil, species, city, marked optional). Photo is optional ("Skip for now" as a text button). Splitting into two steps needs a bench change, so it stays one screen this round.
- **Link error** and **Move choice:** bottom sheets over the current step, not new screens.

## 4. Photos: decisions and alternatives

- **Picker (needed before any photo UI works in the real build):** `expo-image-picker` (camera and library). New dependency, so it needs a requirement check and Architect review.
- **Upload:** a queue on the phone, so a photo taken offline is kept and sent later. Shows the status above.
- **Gallery layout:** A. Grid with day headers (recommended, fits many photos). B. Timeline of large cards (fewer per screen, more emotional, more scrolling).
- **Viewer gestures:** swipe plus buttons (recommended, meets 2.5.7) or buttons only (simpler, slower for many photos).

## 5. Bench and test impact

| Change | Bench | Labels or keys | Tests |
|---|---|---|---|
| Route stack and system back | Not checked yet whether any bench step uses system back. Verify before change. | None | New `navigation.test.tsx` for stack, sheet-first back, root double press |
| Header back | Not checked yet whether the bench taps back by label. Check `a11y.back` in `run_appium.sh` before change. | `a11y.back` unchanged | Existing `screens.test.tsx` |
| Three tabs | Tabs are tapped by label (`nav.plants`, `nav.profile`). Adding Alerts changes the tab row. | New `nav.alerts` key uses the existing label | `alertsScreen.test.tsx` routing |
| Pull to refresh | None (bench taps the button) | None | New test for the refresh call |
| Photo viewer and sort control | None | New `gallery.viewer.*` keys | Gallery tests; new viewer test |
| Sheets for Premium and link error | Check whether bench taps these by label | Keys unchanged | Premium tests update to sheet |

**Bench rule:** any label or key change needs Peter's bench check and Ines's review first. Nothing here has been run on a device.

## 6. Decisions (answered by Arsany, 26 Nov)

1. **Tabs:** three (Plants, Alerts with badge, Profile). Done.
2. **Gallery layout:** grid with day headers. Done.
3. **Photo picker:** `expo-image-picker` approved. The dependency is added in the build PR after a requirement check, not in this design PR.
4. **Setup details:** one screen this round. Done.

Final mockup with all screens and user journeys: `final-mockups.html`.

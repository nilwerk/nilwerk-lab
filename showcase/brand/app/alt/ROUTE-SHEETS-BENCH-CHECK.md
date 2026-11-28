# Route stack, system back and sheets: bench check (procedure)

Purpose: check the navigation behaviour in PR #238 (route stack, system back, sheets, double back to leave, header back, scroll position, pull to refresh) on a real phone, and check the one place where the existing bench already presses Back.

Status: this is a procedure. It has NOT been run on a device. The "Current build" column is read from the code on `agent/ux/alt-build` (origin/main plus the alternative build commits). Nothing in `bench/` was changed.

## Setup (for whoever runs it)

- A dev build of the app on an Android phone (the bench target, see `bench/app/run_appium.sh`), signed in to a test account. The bench's own inputs (BENCH_* variables) are not needed for checks R1 to R7.
- Appium 2 with UiAutomator2 (the bench's stack). System back is sent with `adb -s <serial> shell input keyevent 4` (KEYCODE_BACK).
- Screen title probe: the header text, for example `plants.title` "My plants", `alerts.title` "Alerts", the plant name for detail. Read the labels from `projects/plant-monitor/app/strings/en.json` at run time; do not hard-code them.
- Record for each check: the screen title after each step, the scroll position (top or not), and whether the app stayed open.

## Checks

Each check lists its steps, the expected output, and the PASS and FAIL rules. "Current build" is what the code does now.

### R1. System back returns to the previous screen from Alerts

1. Sign in. On My plants, tap the Alerts tab.
2. Press system back once.
- Expected: the screen is My plants. The app stays open.
- PASS: title "My plants" after the press, app open.
- FAIL: any other title, or the app closes.
- Current build: NOT IMPLEMENTED. No `BackHandler` in `src/` or `App.tsx`. Expect the app to close or to do nothing at root. Predicted FAIL.

### R2. System back from a plant detail returns to the list it came from

1. On My plants, tap a plant row (for example the plant named in the list).
2. Press system back once.
- Expected: My plants, scroll position kept.
- PASS: title "My plants", the row the user tapped is still on screen.
- FAIL: app closes, or the list is reloaded at the top.
- Current build: NOT IMPLEMENTED for system back. The on-screen Back button returns to My plants (`setRoute('plants')`), so the on-screen path works. Predicted FAIL for the system back.

### R3. Alerts, then plant, then back returns to Alerts (stack, not a fixed route)

1. Open Alerts (tab). Tap a plant from an alert row.
2. Tap the on-screen Back control.
- Expected: Alerts, not My plants.
- PASS: title "Alerts".
- FAIL: title "My plants".
- Current build: FAIL predicted. The plant detail's Back is `setRoute('plants')` (App.tsx), and the alert row does not open a plant in the build (alerts are read-only), so this path does not exist yet. Mark "not reachable" if no alert row opens a plant.

### R4. A sheet closes before the screen behind it

1. Open a bottom sheet (Premium sheet in #238, the link error or the move choice).
2. Press system back once.
- Expected: the sheet closes; the screen behind it stays.
- PASS: sheet gone, screen title unchanged.
- FAIL: the screen behind closes too, or the app closes.
- Current build: the Premium screen is a full screen, not a sheet (`PremiumScreen`). No sheet exists in `src/`. Predicted: not applicable until sheets are built. Mark "not applicable" and do not count it as PASS.

### R5. Double back to leave on the root

1. On My plants (root), press system back once.
- Expected: a short message "press back again to leave" (a new string in `strings/en.json`), the app stays open.
2. Press system back again within 2 seconds.
- Expected: the app closes.
- PASS: message after the first press; app closes after the second within 2 s.
- FAIL: app closes on the first press, or no message.
- Current build: NOT IMPLEMENTED. Predicted FAIL.

### R6. One fixed header with a 48 x 48 dp back control outside the scroll area

1. On plant detail, scroll to the bottom.
2. Check the back control's position and size (Appium element rect).
- Expected: the back control is at the top at every scroll position, and its rect is at least 48 x 48 dp.
- PASS: rect at least 48 x 48 at the same y after scrolling.
- FAIL: the control scrolls away, or its rect is smaller.
- Current build: the back control is a `Button` inside the scroll (`Screen` in `ui/primitives.tsx`) and scrolls away. Predicted FAIL.

### R7. Scroll position kept on return

1. On My plants, scroll down so that the fourth plant row is near the top.
2. Tap that row, then press the on-screen Back.
- Expected: My plants, with the same row near the top.
- PASS: same row at the same place.
- FAIL: the list is back at the top.
- Current build: the list reloads on return (`useEffect` load), and scroll is not kept. Predicted FAIL.

### R8. Pull to refresh, with the Refresh button kept for the bench

1. On My plants, pull down from the top.
- Expected: the list refreshes and a spinner shows while it loads. The "Refresh" button is still on screen at the bottom.
- PASS: spinner appears on pull; "Refresh" button present.
- FAIL: no spinner, or "Refresh" button removed.
- Current build: no pull to refresh (`RefreshControl` not used). "Refresh" button present. Predicted FAIL for the pull; PASS for the button.

### R9. Bench: keyboard hide must not navigate (existing bench behaviour)

This is the one place the bench presses Back. `hide_keyboard` in `bench/app/run_appium.sh` (around line 327) relies on UiAutomator2 pressing Back only while the keyboard is up. Line 353 says Back can leave the screen on some devices, so the bench checks that the field label is still on screen.

1. Run bench step 2 (add sensor) up to the Wi-Fi password field with the keyboard open.
2. The bench hides the keyboard with Back.
- Expected: the keyboard closes and the Wi-Fi step stays on screen; the field label is still visible.
- PASS: the field label is found after the hide (bench probe passes, no "WARNING the field label is no longer on screen").
- FAIL: the step navigates away, or the probe warns.
- Why it matters for #238: if the route stack is added, Back with the keyboard up must still only close the keyboard. A route pop here would break bench step 2.
- Current build: the stack does not exist, so Back does not pop. Predicted PASS on this check (not run).

## Bench steps touched

| Bench step | Touched by | Notes |
|---|---|---|
| 0 launch | none of R1 to R8 | |
| 1 sign up | R9 only if the sign-up form has the keyboard open when the bench hides it | the auth fields use the same `hide_keyboard` |
| 2 add sensor | R9 (Back with the keyboard up in the Wi-Fi and name fields); R4 if sheets are added to the link error or the move choice | `setup.*` labels; the step taps labels, not Back |
| 3 first reading | R7 (scroll and return to the list before `plants.refresh`), R8 (pull to refresh must not replace the Refresh button) | `plants.title`, `plants.row.a11y`, `plants.refresh` |

No label or key is changed by these checks. The bench code is not changed.

## Result sheet (fill in on the device)

| Check | Result (PASS, FAIL, or not applicable) | Date | Build | Notes |
|---|---|---|---|---|
| R1 | | | | |
| R2 | | | | |
| R3 | | | | |
| R4 | | | | |
| R5 | | | | |
| R6 | | | | |
| R7 | | | | |
| R8 | | | | |
| R9 | | | | |

Predicted results from the code (not run): R1, R2, R5, R6, R7, R8 FAIL; R3 not reachable; R4 not applicable; R9 PASS. Do not count predictions as results.

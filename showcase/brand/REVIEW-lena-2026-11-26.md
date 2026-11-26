# Brand review for the mobile app (v0.1 brand kit), 26 Nov 2026

Scope: `showcase/brand/brand-kit.md`, `brand.css`, `brand-status.css`, `app/tokens.json`, `app/theme.ts`, `app/README.md`, `app/WIREFRAME-MAPPING.md`, `CHECKS.md`, and the checker scripts. Screens checked: the mock web build of the app (see `app/screens/2026-11-26/`). Principles P1 to P9 are those of `projects/plant-monitor/docs/design/app-design-review-2026-11-25.md`.

## 1. Check results (real output, before any change)

| Check | Command | Result |
|---|---|---|
| 1. Palette contrast | `python3 -I check_contrast.py` | exit 0, 0 failing pairs. Lowest text pairs: accent on accent-soft 4.59:1 (light), warn on bg 4.52:1 (light). Dark lowest text pair 6.58:1 (warn on surface). |
| 2. Status contrast | `python3 -I check_status_contrast.py` | exit 0, 0 failing pairs. Lowest: dry on dry-soft 4.51:1 (light), ok on ok-soft 4.59:1 (light). Both pass with little margin. |
| 3. SVG well-formed | `python3 -I check_svg_wellformed.py` | "118 SVG files checked, 0 not well-formed" |
| 4. App theme type-check | `tsc -p tsconfig.json` in `app/` | exit 0 |
| 5. Adaptive icon | `python3 -I app/check_adaptive_icon.py` | "colour type 6, bit depth 8, first pixel RGBA (0, 0, 0, 0): OK" |
| 6. Generated files up to date | regenerate and check `git status` | Not clean. See finding 7. |

The app project's own checks, run on `origin/main`: `npx tsc --noEmit` exit 0; `npm test` 36 suites, 503 tests, all pass.

The four checkers pass, so no text pair in the kit fails 4.5:1. The problems below are the ones the checkers do not cover.

## 2. What works

- Text pairs: every ink, muted, accent, status and soft-background pair in both schemes is above 4.5:1. The dark scheme has more margin than the light one (lowest dark text pair 6.58:1).
- Status is never colour alone. Every status has a label key and a shape (circle, triangle, diamond, square, ring, cross) (P7). On the plant list the shape, word and colour all show (see `v1-plants.png`).
- One accent colour, used for the primary button and the tab indicator only. Calm (P8).
- Adaptive icon is real RGBA with a transparent corner, mark inside the 66 % safe zone.
- Type scale is small and consistent (display 34, h1 28, h2 22, h3 18, body 16, caption 13).
- Touch targets are already a token (`minTouchTarget`), so one number controls every button, row and tab.

## 3. What does not work, and the fix

Each point names the principle it touches. Fixes marked **applied** are in this branch.

### F1. Control borders fail non-text contrast (WCAG 2.2 SC 1.4.11, 3:1). **Applied.**
The hairline token `line` is the border of text fields, radio choices and secondary buttons (`src/ui/primitives.tsx`). Measured:
- light `#e2ded5` on bg `#f6f4ef` = **1.22:1**; on surface `#ffffff` = **1.34:1**
- dark `#2a3038` on bg `#101317` = **1.40:1**; on surface `#181c22` = **1.29:1**

Without a 3:1 border, a field or an unselected choice is hard to see, so the user cannot tell it is a control. Principles: P4 (big, obvious targets), P6 (fields must be easy to find).
Fix: new token `control`: light `#7d838c` (3.48:1 on bg, 3.82:1 on surface), dark `#7b818a` (4.74:1 on bg, 4.36:1 on surface). `line` stays for decorative dividers only. The primitives now use `control` for those three borders. A test in `theme.test.ts` asserts 3:1.

### F2. Touch target 44 is the iOS number, not the Android one. **Applied.**
`minTouchTarget` is 44 (iOS 44 pt). The Android accessibility guide says "Ensure all touch targets are at least 48 dp" (developer.android.com, accessibility, checked 26 Nov 2026). WCAG 2.2 SC 2.5.8 (AA) asks only 24 CSS px, so 44 is already above the legal floor.
Fix: `minTouchTarget` = 48. That satisfies both platforms. Principle P4. The bench taps by label, not by coordinates (the only coordinate tap is a last-resort fallback at the top of the screen), so the bench is not affected. Test: `theme.test.ts` now asserts at least 48.

### F3. Label style is 12 px, below the brand's own 13 px. **Applied.**
`type.label` (mono, 12/16) is used for the elapsed clock in setup. `brand.css` defines `--nw-fs-label: 13`. Fix: label 13/18 in the generator. Principle P8 (calm, legible), accessibility (Android minimum body size is 12 sp; 13 is the kit's own value).

### F4. Two type tokens are never used. Not applied (needs a screen change).
`type.display` (34) and `type.number` (40) exist but no screen uses them. The app has no hero number, so the most important reading (soil moisture) is the same size as the labels. Principles P2 and hierarchy (P1). Fix: use `type.number` for soil moisture on plant detail (review item D-A in `projects/plant-monitor/docs/design/app-design-review-2026-11-25.md`). This is a code change, so it is in the v2 proposal, not here.

### F5. Dark-mode status pairs are fine, but there is no disabled or placeholder token. Not applied.
Placeholder text uses `muted` (5.67:1 light, 7.70:1 dark), which passes. A disabled button uses reduced opacity (not checked, no token). A disabled state that is only faded can fail 3:1 for the control. Fix: add a `disabled` pair when the state is designed. Not checked on a device.

### F6. The checkers do not cover non-text colours. **Partly applied.**
`check_contrast.py` tests text pairs and marks `line` as "decorative (no requirement)", which is the root of F1. Fix: list `control` as a "boundary" class in the checker (3:1) and keep `line` decorative. Done in the app test only; the Python checker is not changed in this branch.

### F7. Generated files are not reproducible (CHECKS.md item 6). Not applied, needs a decision.
Running `make_app_assets.py` with unchanged inputs rewrites all five PNGs in `app/assets/` with different bytes (the font subset and PNG encoder change between runs). So "working tree clean" fails after any regeneration. In this branch the PNGs were restored with `git checkout`, because no colour in the icon or splash changed. Fix: fix the PNG encoder metadata, or list the PNGs as "regenerated, not byte-checked" in CHECKS.md.
Also: the generator needs the `@fontsource` packages through `NW_FONT_DIR`, which are not in the repo. CHECKS.md should name them.

### F8. Source of truth is not the project file. Note for the role file.
The role file says to change `projects/plant-monitor/app/tokens.json`. The source is `showcase/brand/brand.css` and `brand-status.css` plus the constants in `make_app_assets.py` (spacing, radius, type, touch). The project's `tokens.json` and `theme.ts` are copies, as `app/README.md` says. This branch edits the source, regenerates, and copies the two files into the project. Recommend correcting the role file.

### F9. Hard-coded values inside the generator. Note.
Spacing, radius, type scale and `minTouchTarget` are literals in `make_app_assets.py`, not in CSS. So app-only changes (F2, F3) live in the script, while colour changes live in `brand.css` and affect posts, slides and the web kit too. That is why the control colour was added as an additive variable and no existing brand colour was changed.

### F10. Icon. No issue found.
The mark is 60 % of a full-bleed ink tile on iOS and inside the 66 % safe zone on Android. The wave colour `#8fd9ff` (1.41:1 on light bg) is decorative only, as the kit says. Not checked on a device or in a launcher.

## 4. Summary of changes in this branch

| File | Change |
|---|---|
| `showcase/brand/brand.css` | added `--nw-control` (light and dark). No existing value changed. |
| `showcase/brand/app/make_app_assets.py` | `control` in the colour list; `minTouchTarget` 48 (from the tokens dict and the template); label 13/18. |
| `showcase/brand/app/tokens.json`, `theme.ts` | regenerated, not hand-edited. |
| `projects/plant-monitor/app/tokens.json`, `theme.ts` | copied from the generated files. |
| `projects/plant-monitor/app/src/ui/primitives.tsx` | three borders use `control` instead of `line`. |
| `projects/plant-monitor/app/src/__tests__/theme.test.ts` | new test: `control` at least 3:1 on bg and surface; touch target at least 48. |

## 5. Test and bench impact

- Bench (`bench/app/run_appium.sh`): none of the bench steps read a colour, a size or the label style. The bench taps by label (`tap()`), so the taller buttons do not change its steps. Not run on a device.
- UI tests: `theme.test.ts` (updated, 2 new tests), all other suites unchanged. Jest: 36 suites, 505 tests, all pass after the change (503 before).
- Typecheck: `npx tsc --noEmit` exit 0 before and after.

## 6. Decisions for the owner

1. Approve the control colour (`#7d838c` light, `#7b818a` dark) and the 48 px touch target as brand-kit values, since `brand.css` is shared with posts and slides.
2. Decide how CHECKS.md should treat generated PNGs (F7).
3. Correct the role file's source-of-truth line (F8).

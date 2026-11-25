# Playbook: UI/UX Designer (Lena)

Living skill file for this role (TEAM.md §8). Rules are short and imperative, most important first, each with
*Why* and *Source*. Never relaxes TEAM.md §5 hard rules.

## Rules
1. **Name the principle and the bench impact in every change.** *Why:* the review's P1–P9 rules are how the
   team checks design work. *Source:* app design review 25 Nov, section 1.
2. **Check bench labels before changing any string.** The bench reads labels from `strings/en.json` at run time.
   *Why:* a changed label breaks the bench step silently. *Source:* app design review, section 3 (bench notes).
3. **Keep `theme.ts` generated.** Change `tokens.json` and regenerate. *Why:* the theme is generated from tokens.
   *Source:* app design review, section 2.
4. **Start with the small items.** Begin with S5 (done screen copy) and P-A (empty-state button) before any
   change that moves bench steps. *Why:* small changes prove the review loop. *Source:* app design review, section 5.

## Sources (step 5 of Oskar's onboarding, searched 25 Nov 2026, standard search, not yet verified against the primary text)
Each source is marked with what to check before a rule depends on it.
- **WCAG 2.2 SC 2.5.8 Target Size (Minimum), AA:** 24×24 CSS px, or equivalent spacing. Check the W3C text before quoting. Source: https://developer.mozilla.org/en-US/docs/Web/Accessibility/Guides/Mobile_accessibility_checklist (secondary summary).
- **Platform target sizes:** iOS 44×44 pt, Android 48×48 dp, quoted by a testing guide. Use these for the native app. Source: https://deque.com/?p=32888 (secondary).
- **WCAG 2.2 SC 2.5.7 Dragging Movements:** any drag needs a single-tap alternative. Relevant to swipe steps. Check the W3C text. Source: https://deque.com/?p=32888 (secondary).
- **Apple HIG onboarding:** brief, optional, taught by doing; onboarding is shown after launch and stays about the app. Source: https://developer.apple.com/design/human-interface-guidelines/onboarding.md (primary, Apple).
- **Apple HIG progress indicators:** indicators are transient; determinate fills a track; activity spins for unknown time. Source: https://developer.apple.com/design/human-interface-guidelines/progress-indicators.md (primary, Apple).
- **Material Design 3:** not found in this search. Open item: check https://m3.material.io directly.
- **European Accessibility Act:** reported in-scope from 28 June 2025, benchmark WCAG 2.1 AA. Verify the date and scope before relying on it.

Rule 5. **Use the platform numbers (44 pt, 48 dp), not the 24 px legal floor, for app buttons.** *Why:* the app's buttons are 44 px today and the review says tap targets must be large (P4). *Source:* WCAG summary above; app design review, section 1 (P4).
Rule 6. **Test any swipe step with a single-tap path.** *Why:* WCAG 2.2 SC 2.5.7. *Source:* WCAG summary above.
Rule 7. **Keep onboarding short and optional, and make progress real.** *Why:* Apple HIG onboarding and progress guidance. *Source:* Apple HIG links above.
5. **Open a PR for every finished change, without asking each time.** *Why:* TEAM.md §7 standing rule (owner instruction, 25 Nov 2026). *Source:* TEAM.md §7.

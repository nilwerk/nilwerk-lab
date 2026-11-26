# UX app design notes

## Common patterns for plant and home-sensor apps (group 1 restyle, 26 Nov 2026)

Source status: [F] fetched and read by the team's research (page text checked), [S] search snippet only, [X] not verified. Principles only; nothing is copied from any app's visuals or text.

| Pattern | How it is used in the app | Source |
|---|---|---|
| Tab bar holds top-level sections only; actions go in the header or a button | Plants, Alerts and Profile as tabs; add and set-up actions are buttons on their screens | Apple HIG, tab bars [F] https://developer.apple.com/design/human-interface-guidelines/tab-bars.md |
| Three to five destinations; no drawer for the main sections | Three tabs | Material 3, layout and navigation patterns [F] https://developer.android.com/design/ui/mobile/guides/layout-and-content/layout-and-nav-patterns |
| Lists for short scannable text; detail on a separate view; a disclosure chevron for drill-in | Plant rows link to detail; profile rows are list rows | Apple HIG, lists and tables [F] https://developer.apple.com/design/human-interface-guidelines/lists-and-tables.md |
| Summary first: the most urgent state at the top, detail one tap away | Needs-attention counts above the plant cards | Oura, new app experience [F] https://ouraring.com/blog/new-oura-app-experience/ ; Google Home help, status at a glance [S] https://support.google.com/googlehome/answer/7029485?hl=en |
| Hero reading with its normal range and a drill-down to the time series | Soil moisture number with its status word beside it, then the 7-day chart | Oura, Vitals [F] (as above) |
| Card grid for many items of the same kind | Plant cards in two columns | Material 3, layout patterns [F] (as above); the card page of Material 3 [X] https://m3.material.io/components/cards/guidelines (title only) |
| Empty state gives a next step, never a blank list | My plants without plants: one primary action | NN/g, empty states [F] https://www.nngroup.com/articles/empty-state-interface-design/ |
| Onboarding is brief and optional; setup steps show real progress | Five setup steps, one screen each, labelled | Apple HIG, onboarding [F] https://developer.apple.com/design/human-interface-guidelines/onboarding.md |
| Large title that shrinks on scroll | Not used: the source is a search snippet | Apple HIG, navigation bars [S] (page did not load) |
| Segmented control for two or three related views | Not used: the page loaded with its title only | Apple HIG, segmented controls [X] https://developer.apple.com/design/human-interface-guidelines/segmented-controls |
| Back arrow top left, 48 px target | Shared BackButton in the header | Material 3 and Apple: target size per platform (48 dp Android, 44 pt iOS) [F] https://developer.android.com/design/ui/mobile/guides/foundations/accessibility |
| Reduced motion: no motion when the system asks for it | Fade on screen content is off with reduced motion | Apple HIG, motion [X]; the Expo animation skill (vendored, skills/vendor/expo/expo-animation) |

Not used, and why: a social feed as home (Strava critique [S]); a path-based home (Duolingo [F] for the listing only, not a fit for a sensor app); mascots and streak mechanics (no requirement).

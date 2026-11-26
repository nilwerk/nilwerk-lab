# Lena · Expo skills quiz: answer key (Oskar only)

Keep this file out of the checklist. Lena answers from the skill text. Each answer names the section it comes from.
Vendored copies: `skills/vendor/expo/` (commit in `skills/vendor/expo/NOTICE`).

1. **expo-router.** Route files belong in the `app` directory. Never co-locate components, types or utilities there;
   this is an anti-pattern. (SKILL.md, "Routes")
2. **expo-design-system.** No. Extend the existing system in its own idiom, and never introduce a second system beside
   an existing one. A fresh folder next to an existing token system is drift. (SKILL.md, "Adopt Before You Build", rule 4).
   Repo note: here the existing system is `tokens.json`, so the answer is no in any case.
3. **expo-native-ui.** Four states: loading, error, empty, content. Never show the empty state while the first load is
   still resolving. (SKILL.md, "Behavior")
4. **expo-ui.** `BottomSheet` from `@expo/ui`, not Reanimated or `@gorhom/bottom-sheet`. No: `@expo/ui` `List` is not
   virtualized; use `FlatList` or `FlashList` for long or unknown-length lists. (SKILL.md, "Use @expo/ui by default" and "Library Preferences" in expo-native-ui)
5. **expo-animation.** Reanimated, not core `Animated`. Reanimated worklets run on the UI thread and keep running while JS is busy;
   core `Animated` cannot be driven by a gesture without crossing the bridge. (SKILL.md, "Hard Rules" 2)
6. **expo-dev-client.** Any two of: local Expo modules (custom native code), Apple targets (widgets, app clips, extensions),
   third-party native modules not in Expo Go, config plugins, testing remote push notifications and App/Universal Links.
   (SKILL.md, "Important: When Development Clients Are Needed")

Marking: 6 of 6 correct on first try: pass. Each wrong answer: Lena rereads that skill's section and answers again.

7. **Link-only UI Skills entries (appllama-app-design-skill, react-native-design).** Expected answer: styling and colours
   (semantic colours or design tokens); the repo's `tokens.json` rule wins where they differ.
   **Status: UNVERIFIED.** Oskar has not read the linked text (the site shows no licence, so it is not copied and the
   skill text was not reviewed for this answer). Check the answer against the linked page before Lena is marked on it.

8. **Link-only Kimi article entries (ui-craft, apple-design-skill).** Expected answer: an accessibility rule from the Expo skills,
   e.g. the four states or the 44 pt / 48 dp target size rule from the playbook (rules 5 and 6); check against the Expo skill text first.
   **Status: UNVERIFIED.** The linked texts were not read for this key, and nothing is copied. Check before marking.

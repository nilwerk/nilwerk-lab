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

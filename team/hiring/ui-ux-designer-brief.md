# Hiring brief: UI/UX designer (first hire, proposal)

Owner: Oskar (HR & Talent) · Status: **proposal, not approved** · Needs Arsany before any outreach (TEAM.md §8, §9)

Oskar drafts and recommends only. Oskar does not contact candidates, post job ads, spend money or sign any
contract (TEAM.md §5). Arsany makes the hire decision, the offer and the contract.

## 1. Why this role now
The app design review (`projects/plant-monitor/docs/design/app-design-review-2026-11-25.md`, merged in PR #222)
lists about 20 screen-level changes. Most are copy, layout and states. Some change the bench flow, the
setup order and the tests, so the design work has to be checked against the bench and the UI tests every time.
The owner's brief is "modern and simple, habit-forming in feel, not in copy".

## 2. What the role owns
- Screen design for the app: setup flow, My plants, plant detail, alerts, profile.
- Design tokens in `projects/plant-monitor/app/tokens.json`. Changes go in the source and are regenerated
  with `showcase/brand/app/make_app_assets.py`. Never hand-edit `theme.ts`.
- A short design-review note per screen change, listing which bench steps and UI tests it touches.
- Accessibility checks: contrast (the 4.5:1 rule in `theme.test.ts`), tap targets, reduced motion.

## 3. What the role does not own
- Bench labels and string keys. These are read at run time from `strings/en.json`. A change needs Peter's
  bench check and Ines's review.
- Requirements (NFR-03 and other targets). Changes go to the Architect.
- Publishing or store assets. Arsany publishes.

## 4. Skills wanted (for the candidate screen)
- Mobile app UX for a consumer and a technical audience, with a clear setup or onboarding flow.
- Working from design tokens and React Native or similar component code, not only from mock-ups.
- Accessibility basics (contrast, tap target, screen-reader labels).
- Able to write a short rationale per change, in the principle-based style of the review (P1 to P9).
- Works in Git pull requests with an AI-run team. Accepts reviews from Theo (Architect) and Ines (QA).

## 5. Onboarding plan (before the first task)
1. Read TEAM.md in full, and in particular §4 (Definition of Done), §5 (hard rules), §7 (agile) and §8 (learning loop).
2. Read the app design review, then `projects/plant-monitor/app/src/__tests__` and `bench/app/run_appium.sh`.
   Know which labels the bench reads before changing any string.
3. Run the app's test suite locally and confirm it passes before a first change.
4. First task: S5 from the review (done screen copy and primary label). Small, testable, and it touches one key.
5. Persona and role file: a new role must be added to TEAM.md §2 and to `team/PERSONAS.md` in the same
   format as the rest of the team. Oskar drafts both after Arsany approves the role.

## 6. Decisions needed from Arsany
1. **Approve the role** and whether it is a human hire, a contractor or a new agent persona. A new agent role
   changes TEAM.md and the tools list (§8 limits), so it needs approval either way.
2. **Budget and channel.** Oskar cannot spend or post an ad. Arsany chooses how to advertise and what to pay.
3. **Who gives feedback** on design work day to day (proposal: Nora for scope, Theo for architecture,
   Ines for test impact, Poppy for showcase).
4. **Start with the review's S5 and P-A** (small copy and empty-state changes), or wait until the bench flow
   is proven on hardware.

## 7. What "ready" means
- Role approved and recorded in TEAM.md §2.
- Persona and role file merged, the same format as the rest of the team.
- Onboarding steps 1 to 3 done, and a first PR merged (step 4).

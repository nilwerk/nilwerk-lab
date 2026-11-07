# PR-2026-11-07: brand kit v0.1 (kept), templates for social, slides, web and app, first two post drafts, 14-day calendar

**What it shows:** the first Nilwerk social template set (proposal) and a finished post draft built from it. `post1-draft-portrait.png` is today's real evidence (charger resistor R9 caught in review, calculated not measured); `template-preview-dark.png` is the empty template with placeholder text, clearly not a result.

- Task: PR-2026-11-07 · Branch: `agent/pr-social/2026-11-07` · PR: link added by the Lead · Persona: Poppy (PR & Social)
- Files: `showcase/brand/` (brand kit, usage matrix `USAGE.md`, glossary, tokens `brand.css` + `brand-status.css`, logo mark, post templates incl. story and carousel, `slides/` 16:9 templates, `web/` component kit, `app/` Expo theme + icon + splash, contrast checkers, previews), `showcase/content/2026-11-07/` (2 posts EN/DE/Instagram, 6 images, claim-check), `showcase/content/calendar.md` (9-20 Nov).
- Brand basis: the colours, fonts and logo already used on nilwerk.de; contrast ratios computed and AA-checked with `showcase/brand/check_contrast.py`.
- Images are code-generated (SVG filled by script, rendered in headless Chromium), so no AI-imagery flag applies.
- Agent minutes: from the Agent Log once logged. Own human-hour estimate: about 7 h (brand kit and templates about 4 h, two evidence-checked posts about 2 h, calendar about 1 h).

**Still unverified:** palette, fonts and logo usage are not approved by Arsany; German texts not yet checked by Theo/Nora; the charger formula (R = 1100 / I) needs Theo's confirmation against the datasheet edition (claim-check note A); calendar milestone dates were not checked against the Plan sheet; nothing is scheduled or published.

Update after Arsany's decision: the v0.1 brand and logo are kept; the alternative v0.2 designs were removed (they remain in the history of this branch, commits cc46e9e, 36c2f1a and 9df1044, if ever wanted back). The brand materials now also cover customer slides, a web component kit and a mobile app theme, each for non-technical and technical audiences. Unverified: slides and component kit were checked in Chromium only; theme.ts type-checks with tsc 6.0.2 but was not run inside an Expo app; the Google Slides steps were not run in Google Slides.

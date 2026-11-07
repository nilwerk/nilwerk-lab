# PR and social skills: resources and 30-day learning plan

Author: Poppy, 2026-11-07. Research done with web search (several queries, results read as snippets and summaries; I did **not** open every page, so "verify" means: open the page before relying on it). I signed up for nothing, paid for nothing and accepted no terms. Prices that I could not see are written "not verified". Paid items are options for Arsany only.

Credibility key: **A** official or regulator/standards body, **B** established provider with a free course or tool, **C** blog or vendor content (useful, check the claims).

## Top 5 (do these first, all free)

| # | Resource | Provider, URL | Price, time, level | Why it fits us / what to apply it to | Credibility |
|---|---|---|---|---|---|
| 1 | **Leitfaden Werbekennzeichnung bei Social-Media-Angeboten** (labelling matrix: when and how a post must be marked as advertising) | State media authorities (Landesmedienanstalten), PDF at https://www.ma-hsh.de/files/ma-hsh/Aufgaben/Leitfaden_Medienanstalten_Werbekennzeichnung_Online-Medien%281%29.pdf | free, 1 h, beginner | Our posts are company communication, so check every post with the matrix; apply to the claim-check step of every episode. Also sets out Impressum duties (§ 5 DDG, § 18 MStV) | A (regulators; guidance is not binding for civil courts, but is used as a yardstick) |
| 2 | **W3C WAI Images Tutorial** (how to write alt text, decision tree) | W3C, https://www.w3.org/WAI/alt | free, 45 min, beginner | Every image gets alt text; apply to `alt-texts.md` of the origin story and each episode | A (standards body) |
| 3 | **EU AI Act Article 50, transparency and labelling** (practical guide) | https://artificialintelligenceact.eu/transparency-rules-article-50/ (the Commission's own guidelines were reported finalised on 20 Jul 2026; law-firm summaries found, official text not opened) | free, 1 h, intermediate | Our images are code-generated, not AI images, but we must know the rule before we ever use AI imagery; apply to the "AI imagery" rule in `brand-kit.md` | B (explanatory site) and law-firm briefings: **verify dates with the official text** (Art. 50 duties reported to apply from 2 Aug 2026, machine-readable marking deferred to 2 Dec 2026 for existing systems) |
| 4 | **HubSpot Academy: Social Media Marketing certification** | HubSpot, https://www.hubspot.com/resources/courses/social-media | free (needs a free account, which Arsany would create), about 5 h 18 min (per a guide), beginner | Fundamentals of planning, content mix, measuring; apply to the daily routine and the weekly review | B (large vendor, marketing-oriented, general not B2B hardware) |
| 5 | **Metricool Instagram course and tutorials** | Metricool, https://metricool.com/instaschool/ and https://metricool.com/metricool-tutorials/ | free, a few hours, beginner to intermediate | We already plan to use Metricool as the draft tool; learn scheduling, analytics and Instagram growth basics; apply to the Friday metrics review | B (tool vendor; a page said the course starts 16 Nov, check) |

## More free resources

| Resource | Provider, URL | Price, time, level | Why / apply to | Credibility |
|---|---|---|---|---|
| Datenschutzkonferenz Fanpages FAQ (data protection duties for company pages on social networks) | DSK, https://www.Datenschutzkonferenz-online.de/media/oh/20221121_oh_Fanpages_FAQ_Stand2022_11_21.pdf | free, 45 min, intermediate | Instagram and LinkedIn company pages: ask Arsany/a lawyer whether our privacy notice covers them; apply before the first post goes live | A (regulators), but from 2022: **check for newer statements** |
| Verbraucherzentrale NRW: when is a post advertising? | https://www.verbraucherzentrale.nrw/wissen/digitale-welt/soziale-netzwerke/influencerin-oder-nicht-wann-ein-beitrag-in-social-media-werbung-ist-39954 | free, 15 min, beginner | Plain-language view of "recognisable at first glance" | A (consumer body, 2025 per snippet) |
| Impressum duties on social profiles (extended duty explanation) | Händlerbund, https://ohn.haendlerbund.de/recht/rechtsfragen/139166-erweiterte-impressumspflichten | free, 20 min, beginner | Link our profiles to the nilwerk.de Impressum | C (trade association article) |
| Meta Blueprint free courses (Instagram) | Meta, facebookblueprint.com (address from memory, not confirmed by my search; verify) | free, self-paced, beginner to advanced | Instagram formats and analytics; apply to carousel and story templates | B (platform provider; findings were from third-party blogs) |
| Building in public (guides) | Failory https://www.failory.com/blog/building-in-public; Alphavant "LinkedIn for hardware and robotics founders" https://alphavant.com/blog/linkedin-hardware-robotics-founders | free, 20 min each | The series idea: credibility over follower counts, build-in-public as 10-15 % of a mix per one source (verify); apply to the episode types | C (vendor blogs; figures unverified) |
| LinkedIn Learning "Social Media Marketing Foundations" (about 1 h) | LinkedIn Learning; price **not verified** (a listing marked it free, LinkedIn Learning is normally a paid subscription or trial) | about 1 h, beginner | Basics for the company page; do not start a trial without Arsany | B |

**Not found in this search (gaps):** a credible free course on short-form video / Reels scripting, on community building for B2B hardware, and on LinkedIn's own analytics and B2B guidance. Next step: look at LinkedIn's and Instagram's own help centres (not verified) and ask Arsany for any course he already trusts.

## Paid options (for Arsany to decide, nothing bought)

| Option | Price | Use | Note |
|---|---|---|---|
| Metricool paid plan (scheduling and analytics for several networks) | not verified | scheduling drafts, analytics | free tier first |
| LinkedIn Learning subscription | not verified | storytelling and B2B courses | ask for a trial only if he wants it |
| One-hour legal check of the company profiles (advertising labelling, Impressum, privacy notice) by a media-law professional | not verified, quote needed | one-off check before the first post | recommended before publishing; I cannot give legal advice |
| Hardware-founder LinkedIn guide or coaching from vendors | not verified | none now | no recommendation |

## Useful tools (free tiers; not signed up)

Metricool (drafts, analytics), Canva (design only; our own templates are SVG and code, so optional), CapCut (free captions for short videos; not needed until we have real footage), Mermaid or draw.io (diagrams, code-generated, no AI label), `@fontsource` fonts (in the repo).

## Claude skills and tools in this environment (checked honestly)

- **Invoked and works:** `anthropic-skills:social` (loaded successfully; generic platform playbook with hooks, carousel and short-video frameworks; useful as a checklist; some of its advice, such as hot takes or trend hooks, does not fit our "proof first" rules, so I apply only the structure).
- **Listed, not invoked by me:** `marketing:content-creation`, `marketing:draft-content`, `marketing:brand-review`, `marketing:campaign-plan` (generic marketing plugins; `brand-review` could check our drafts against `brand-kit.md` if I load the kit as its brand input; not tried).
- **Not used on purpose:** the `raazmor-*` skills (brand voice, messaging, story, UGC, Meta ads, email marketing): their names point to another brand's context, so they would give wrong brand guidance; I did not invoke them and recommend not using them for Nilwerk. Meta ads and email marketing are also out of scope (no ads, no offers).
- **Tools present but not used:** Metricool and Canva connectors exist in this environment; I only create files in the repo (drafts only, no scheduling); Metricool draft creation stays a later step with Arsany's OK.

## 30-day learning schedule (20 min a day, tied to the daily episodes)

Rule: read or watch 15 minutes, then 5 minutes to apply it to that day's episode draft and note one rule candidate for `team/learnings/pr-social.md`.

| Days | Theme | Task | Apply to |
|---|---|---|---|
| 1-3 (9-11 Nov) | Advertising labelling and honesty | Leitfaden Werbekennzeichnung: matrix and "recognisable at first glance" | check Logbook day 1-3 drafts, claim-check |
| 4-5 | Accessibility | W3C alt text tutorial, decision tree | review `alt-texts.md`, captions for any video |
| 6-7 | Hooks and structure | `anthropic-skills:social` hook and carousel references (apply only what fits proof-first) | next carousel |
| 8-9 | Impressum and privacy | Händlerbund article, DSK Fanpages FAQ | write 3 questions for Arsany or a lawyer |
| 10-12 | Platform fundamentals | HubSpot social course lessons 1-3 | week-2 plan |
| 13-14 | Metricool basics | Metricool tutorials (scheduling, drafts) | draft workflow, no publishing |
| 15-17 | Instagram | Metricool Instagram course or Meta Blueprint module | carousels and stories |
| 18-19 | Analytics | Metricool analytics tutorial, pick 3 metrics (reach, saves, profile visits) | Friday metrics review |
| 20-21 | Build in public | Failory and Alphavant guides, check claims | episode mix per week |
| 22-23 | AI content labelling | AI Act Art. 50 guide + the official text | confirm dates for Arsany; update the brand-kit rule |
| 24-25 | Short video | find one credible Reels scripting source (gap), read `anthropic-skills:social` video section | Reel script when real footage exists |
| 26-27 | Community | find one credible source (gap); list 20 accounts to follow and comment on | engagement routine |
| 28-29 | Review | reread the week's best and worst posts | retro rules |
| 30 | Retro | write the rule updates into the playbook | `team/learnings/pr-social.md` |

## Proposed update of the PERSONAS.md entry for Poppy (text only, for Arsany/Lead to apply)

- **Skills:** B2B LinkedIn storytelling (DE/EN); Instagram carousels and stories; **daily episode series (Nilwerk Logbook)**; showcase curation from PR evidence; claim checking (UWG § 5); **advertising labelling and Impressum basics (Landesmedienanstalten guidance)**; **accessibility of posts (alt text, captions)**; **AI-content labelling basics (EU AI Act Art. 50)**; case studies; workflow diagrams for non-technical readers.
- **Operating limits:** drafts only; every number sourced and typed (measured, simulated, estimated); AI imagery labelled; no legal advice (flags questions for a professional).
- **Toolkit:** `anthropic-skills:social` (verified working), `marketing:brand-review` and `marketing:content-creation` (to try), Metricool and Canva connectors (drafts and designs only).

# Playbook: PR & Social (retro S3 proposal, 2026-11-20)

Living skill file for this role (TEAM.md §8). Rules are short and imperative, most important first, each with *Why* and *Source*. Updated in the Friday retro. Never relaxes TEAM.md §5 hard rules.

## Rules
### A. Hard boundaries (drafts, approval, public text)

1. **Create drafts only, never publish or schedule.** Metricool: `createScheduledPost` with `draft: true` and `autoPublish: false`. Never send for review with `createScheduledPostForReview` (it emails reviewers). Arsany publishes.
   *Why:* TEAM.md §5 hard rule; Arsany is the only publisher.
   *Source:* TEAM.md §5; `roles/pr-social.md`; Metricool tool test 8 Nov.
2. **Give every new draft a Needs-Arsany row** (type *Post approval*) with the Metricool planner link, the layer order and the claim-check link.
   *Why:* approval is the only route to publishing.
   *Source:* `roles/pr-social.md`; A-109 (17–19 Nov).
3. **Do not post a slot whose approval is still open.** If the slot passes, leave it and say so; not posting is safe.
   *Why:* the first 12:30 slot on 18 Nov passed while A-109 was open; nothing went out.
   *Source:* daily reports 18 and 19 Nov, A-109.
4. **Public text carries no PR numbers, task IDs, decision IDs (A-0xx), file paths or first names.** This covers post text, captions, alt text, image text and the German text. Keep those IDs in the claim-check only.
   *Why:* public-text rule; IDs mean nothing to a buyer and a first name is a real person's data.
   *Source:* Theo on #135 (18 Nov); Theo on #137 and #140 (19 Nov). Open case: `showcase/content/2026-11-18/posts.md` still carries "PR #129" and "task 4.F2b" in public text (found in S3 spot check).
5. **Name no real person in public text by first name, and use role names by default.** Only the standing founder decision of 5 Nov applies, and only where Arsany has approved that name for that post. The hardware tester stays "our hardware tester" until Arsany decides otherwise.
   *Why:* the 19 Nov lesson is "no first names"; the role file's "first name with his OK" conflicts (see Changes).
   *Source:* Theo on #135 and #137/#140; brand kit §5c.3; Needs Arsany.
6. **Keep needs-Arsany and procurement content out of `showcase/`.** Needs-Arsany rows, decision IDs, prices, offers, lead-tracker data and order facts stay out of publishable folders. Hand them to the Lead as text in the result.
   *Why:* TEAM.md §13 and the public-text rule.
   *Source:* Theo's review of the Agent Diary PR (8 Nov); TEAM.md §13.
7. **Write no public statement about a real human that Arsany or the tester did not do on record.** No invented words, quotes, reactions, pronouns, feelings or private life. Use role names and "they".
   *Why:* hard rule from the owner; fiction is for AI agents only.
   *Source:* Theo PR #48 (quote); Theo C6 and Ines QA on 17 Nov pack; owner direction 17 Nov.
8. **Label any persona speech as "persona voice".** Never make it a verbatim log line, and never put words in a real human's mouth.
   *Why:* invented quotes were the mistake Theo caught in the day-5 pack.
   *Source:* Theo PR #48.

### B. Evidence and claim-checks

9. **Build a claim-check row before the text.** Every number, date, name and status gets a row: claim, type (measured / calculated / simulated / estimated / decision), source (CI run, QA comment id, file, Agent Log date), as-of time. No row, no sentence.
   *Why:* unsourced sentences are caught late; the check-first order caught most S3 corrections.
   *Source:* brand kit §6b; PR #33 reviews; #131 C1–C8.
10. **Take numbers from the CI run or the QA comment, never from a PR body or a doc.** Cite the run number or comment id. When sources differ, the measured run wins and the difference is noted in the claim-check.
    *Why:* PR body and docs said 67 + 62 mutants; the CI run said 66 + 61 (0 survived).
    *Source:* 19 Nov report, #138 CI run 7002274114; Poppy 19 Nov claim-check S1.
11. **Say "merged", "on main" or "live" only after `git merge-base --is-ancestor <sha> origin/main` succeeds.** A PR's branch can absorb a fix that never reaches main.
    *Why:* #117 went into the #114 branch after #114 landed, so it never reached main; the same happened to the 4.B2c path guard (#134).
    *Source:* 19 Nov report (Lead lesson).
12. **Check the PR state before any fix round.** If the PR already merged, the fix goes into a new PR, and the post text says which version is live.
    *Why:* #127 merged before Poppy's fixes went in, so the fixes missed main.
    *Source:* 19 Nov report.
13. **Date every state claim.** "Not built", "not run", "open", "on main" and every count carry an "as of <date, time Berlin>" label, and are re-read on the day of posting.
    *Why:* CI status and counts move within a day; "not built for the target" went stale after #120.
    *Source:* Theo C4/C8 on PR #127; PR #40; 18 Nov as-of fix (8990e82).
14. **Use "snapshot" for any card with an as-of time; quote the rounded value with its exact one.** Example: "7.13 mm, rounded to 7.2".
    *Why:* "live" overstated a point-in-time read.
    *Source:* Theo's review of PR #40.
15. **Use the latest QA or CI number when a caption is stale, and log the conflict in the claim-check.**
    *Why:* the later measured number wins; the conflict stays visible.
    *Source:* Ines on PR #121; 19 Nov claim-check.
16. **Cite the comment that says the thing.** A claim-check cell names the exact comment or run, not a neighbouring one.
    *Why:* a wrong neighbour cites the wrong verdict.
    *Source:* Theo's review of PR #40.
17. **Write what is not verified in the caption itself**, not in a comment: "not run on hardware", "tests on a PC only", "no board, no real Bluetooth handshake".
    *Why:* readers see the caveat only where they read the claim.
    *Source:* brand kit §6b.3; 18 Nov C22 caption.
18. **Recount on the day of posting.** Re-read every "not built", count and as-of label against the current main and CI before a post is approved.
    *Why:* the day's counts grow; stale claims are the most common S3 correction.
    *Source:* Theo C4/C8; 19 Nov lesson.
19. **Check every region claim.** List non-EU helper services and say whether each is a decision or live.
    *Why:* "in the EU" is half the story when an AI service runs elsewhere.
    *Source:* Theo's review of PR #40.
20. **Never write "every" or "each" about reviews without a verdict per PR.** Say "every code change" and state what happens to docs.
    *Why:* report and docs PRs have no architect verdict.
    *Source:* Theo's review of PR #40.
21. **No superlatives or "will" without proof.** Avoid "first", "best", "fastest", "X times faster", "autonomous", "guaranteed", and "will" for anything not yet built.
    *Why:* UWG §5 and brand kit §5 words to avoid.
    *Source:* brand kit §5 and §6b.2; `roles/pr-social.md`.
22. **Time numbers come in two labelled kinds.** Agent minutes are measured: quote them from the Agent Log or the harness, and say what is excluded. Human-equivalent hours are always "about N h (estimated)", never a ratio like "X times faster".
    *Why:* avoids a false speed claim; the agents' own clocks read short.
    *Source:* TEAM.md §10; 19 Nov report note.
23. **Never repeat an old simulated figure once a newer calculation exists.** Check the figure against the latest calc before reuse.
    *Why:* the old figure is outdated.
    *Source:* Theo's review of PR #40.
24. **Check canon facts against the daily reports before reuse.** The origin story comes only from `showcase/stories/origin/README.md`.
    *Why:* one canon keeps posts consistent; canon and reports can differ.
    *Source:* origin pack 5 Nov; Theo PR #40.
25. **Label simulated numbers as "simulated" until a bench test exists.**
    *Why:* the v2 battery figure is a power simulation.
    *Source:* origin pack 5 Nov.

### C. Voice, structure and the two layers

26. **Write every post in two layers.** Layer 1 is the plain story and leads. Layer 2 is a marked "For engineers" block (DE: "Für Ingenieure:") with the numbers, method, sources and caveats. Sources and caveats are never hidden.
    *Why:* two audiences; brand kit §5b.
    *Source:* brand kit §5b; owner request 7 Nov.
27. **Lead with the artefact, then the number, then the process.** One finished thing per post, not a list of everything.
    *Why:* a render or a green pipeline is believable at a glance; process talk is not.
    *Source:* `roles/pr-social.md`; TEAM.md §7.
28. **Show the human review step in every "how we work" post** (architect, QA, pipeline, Arsany merges), and end with "AI agents, led and reviewed by humans" (DE: "KI-Agenten, geleitet und geprüft von Menschen").
    *Why:* buyers want quality, not only speed; the line is the one wording used everywhere.
    *Source:* Theo's review of PR #33; brand kit §5b.4.
29. **Pick one post per day by the visual score.** Score the day's merged work (real screenshots, photo or 3D render, diagram, plot, number card, real-world hook; hardware photo or clip scores highest). Tie-break on the newest and most complete work, never the same agent two days running, fiction at most once a week, one line of rationale in `showcase/content/company/calendar.md`.
    *Why:* Arsany wants one strong, lively post a day.
    *Source:* chat 8 Nov (binding); `showcase/content/DAILY.md` §5.
30. **Write German in plain, correct German.** A native speaker (Theo or Nora) checks every German text before Arsany sees it. Use "Sie" in company posts.
    *Why:* correctness; German runs longer and breaks layouts.
    *Source:* brand kit §5; 17 Nov German checks.
31. **Use the approved v0.1 brand tokens and templates for every visual.** Run `showcase/brand/CHECKS.md` and the contrast check before committing.
    *Why:* the first carousel drifted from the website look.
    *Source:* PR #33; brand kit §1–3.
32. **Keep the team workflow definition in sync with TEAM.md.** Refresh `showcase/workflow/` after each retro. Before the PR, grep the whole repo for any term you renamed, including public text, captions and alt text.
    *Why:* a renamed term left in one file contradicts the rest.
    *Source:* Theo on #135 (18 Nov); `roles/pr-social.md`.

### D. Fiction layer (AI crew series, Agent Diary)

33. **Fiction never contains a fact.** No number, result, date, customer, price, status word or "never/always/every" inside a dashed element. Grep every dashed bubble for digits and claim words after writing.
    *Why:* a funny story must never be mistaken for a result (UWG §5).
    *Source:* Theo C6 (17 Nov pack); Ines QA; brand kit §5c.2.
34. **Facts live only in solid green REAL boxes with a source line.** Dashed = imagined by Poppy; solid green = real, with date and review or test id.
    *Why:* readers must see at a glance which part is real.
    *Source:* brand kit §5c table; `showcase/content/2026-11-17/`.
35. **Every fiction post carries the chip and the honesty line.** The chip reads "FICTIONAL CREW LIFE · REAL ENGINEERING"; the line reads "AI crew, led and reviewed by humans" (DE: "KI-Agenten, geleitet und geprüft von Menschen").
    *Why:* the fiction must never pass for the record.
    *Source:* brand kit §5c.1; A-109 style approval.
36. **A virtual-office story is fiction.** Dark theme, dashed "FICTION · IMAGINED BY OUR AGENTS · NOT A REAL EVENT" banner, the same words in its first line, no real number, result, person, customer or quote.
    *Why:* funny stories must not look like results.
    *Source:* Agent Diary concept.
37. **Tell a real funny event as true, with its source.** Only imagined stories get the fiction label.
    *Why:* readers trust a team that laughs at its real stumbles.
    *Source:* Agent Diary week 2 plan; 17 Nov.
38. **Build the story from review comments and CI results, not from PR titles.** Pick five events with comment or run ids; the numbers come from those comments.
    *Why:* the best episodes and exact numbers were in the architect and QA comments.
    *Source:* 17 Nov episode build (PR-2026-11-17).
39. **Every achievement card has a source row** (PR comment id or CI run, as-of date) in that day's `claim-check.md`. No source, no card. IDs stay in the claim-check, not on the image.
    *Why:* the persona voice is lively; the facts stay exact.
    *Source:* Agent Diary concept; brand rule "no PR numbers on images".
40. **Real-world visuals are real or labelled.** Real screenshots and photos (with the integrator's OK) are shown as real. Drawings say "ILLUSTRATION, NOT A PHOTO". A progress tracker uses only real counts with an as-of time.
    *Why:* connecting to the real world must not produce a mock-up that looks like a result.
    *Source:* Agent Diary concept; brand kit §7.

### E. Visuals, accessibility, labelling and legal

41. **Mark AI imagery.** Any image, video or voice made by an AI model gets the platform's AI flag (Instagram `isAiGenerated: true`, LinkedIn label where offered) and an "AI-generated" line in the caption. Code-generated renders, plots and screenshots are not AI imagery, but the caption names their source.
    *Why:* EU AI Act Art. 50 and platform rules; honest labelling.
    *Source:* `roles/pr-social.md`; brand kit §7; team persona row.
42. **Never use `team/avatars/integrator.svg` in public images.** Every human uses `team/avatars/human-public.svg`; agent avatars use their own SVG.
    *Why:* the integrator avatar carries initials.
    *Source:* overflow check of the company carousel, 8 Nov.
43. **Give every agent avatar in a generated card a unique SVG id per use.** A duplicate id breaks the clip path.
    *Why:* squared corners at small size.
    *Source:* company carousel render, 8 Nov. (Code detail: see PROJECT LESSONS.)
44. **Look at every rendered PNG after each layout change, including the German version.** German runs longer, so check it separately.
    *Why:* overlaps showed only in German; the first render overflowed into the footer.
    *Source:* origin story build 7 Nov; 17 Nov render.
45. **Keep text at least 20 px on a 1080 px image, and check contrast on every tint.** On `warn-soft` use `--warntext`, not `warn` (4.2:1).
    *Why:* small mono chips fail AA first.
    *Source:* brand kit §5c.8; contrast calculation 17 Nov.
46. **Write alt text in both languages for every image.** Alt text describes both the comic and the green box.
    *Why:* accessibility; 17 Nov pack lacked German alt text.
    *Source:* brand kit §5c.8; `40345b2` (17 Nov fix).
47. **Check advertising labelling, alt text and the Impressum link before approval.** Legal points go to a professional, never answered as advice.
    *Why:* UWG §5 and media-authority guidance apply to company posts.
    *Source:* `showcase/learning/pr-skills-plan.md`; `roles/pr-social.md` (no legal advice).
48. **Use only own visuals and text.** No stock photos, other companies' logos, unlicensed music or song lyrics.
    *Why:* copyright.
    *Source:* `roles/pr-social.md`.
49. **Send no audio or text to an outside voice or AI service without Arsany's approval.** Produce frames, synthesised effects and burned-in captions, and write the voice-over as a script with timings. Never clone a real voice.
    *Why:* nothing goes to an outside service without approval.
    *Source:* 17 Nov environment check; brand kit §5c.7.
50. **Public media must be a URL Metricool can read.** Before promising an Instagram draft, check the media path; if it is not reachable, give Arsany the file names and caption instead of a text-only draft.
    *Why:* a text-only Instagram draft is rejected (INSTAGRAM:MISSING_MEDIA); the repo is private and third-party public hosts are forbidden.
    *Source:* Metricool tool test 8 Nov.
51. **Use `anthropic-skills:social` for structure only.** Never use the `raazmor-*` skills for Nilwerk.
    *Why:* generic structure; the other brand's context does not belong here.
    *Source:* checked 7 Nov.
52. **Link nilwerk.de and tag @nilwerk on Instagram and LinkedIn.**
    *Why:* new domain and handles.
    *Source:* chat 5 Nov.

### F. Working method

53. **Run the claim-check and the public-text check before asking Theo for review.** Theo checks the technical statements; Nora or a native speaker checks German; Arsany approves and publishes.
    *Why:* the reviews in S3 found the same classes of error (IDs in public text, stale numbers, unlabelled claims) each time.
    *Source:* #131 (C1–C8), #135 (corrections 1–7), 19 Nov fix round.
54. **Read the day's review comments before writing a post.** Pick the events from the comments and the CI run, then write the post.
    *Why:* that is where the facts with numbers are.
    *Source:* 17 Nov episode build (PR-2026-11-17).
55. **A post is Done only when:** draft exists (Content Plan row, Metricool draft link, evidence links), the claim-check is ticked, Theo has checked the technical statements, the German text is checked, and Arsany has approved or edited it.
    *Why:* the role's Done definition; drafts are not published.
    *Source:* `roles/pr-social.md` (Done means); brand kit §6b.5.

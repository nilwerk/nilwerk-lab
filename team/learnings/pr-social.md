# Playbook: PR, Social & Awareness

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
- Lead with the artefact, then the number, then the process. *Why:* a render or a green pipeline is believable in one glance; process talk is not. *Source:* role setup 2026-11-05.
- Quote agent minutes from the Agent Log, never from an agent's own summary. *Why:* Nora's measured wall-clock wins (TEAM.md §10). *Source:* TEAM.md §10.
- Always show the human review step (architect → QA → pipeline → Arsany merges) in any "how we work" post. *Why:* buyers of hardware prototypes want quality, not just speed. *Source:* role setup 2026-11-05.
- Prefer one finished thing per post over a list of everything. *Why:* small finished slices are the team's whole method. *Source:* TEAM.md §7.
- Treat Arsany's comments and edits on a draft as the strongest lesson: apply them to that draft, then add the general rule here in the next retro. *Why:* he asked Poppy to learn from his fixes. *Source:* chat 2026-11-05.
- Retell the origin story only from `showcase/stories/origin/README.md`. *Why:* one canon keeps every post consistent and true. *Source:* origin pack 2026-11-05.
- Use no human names in public posts except the founder's; describe roles instead ("a junior engineer in Egypt"), and use `avatars/human-public.svg` (no initials). *Why:* Arsany's decision. *Source:* chat 2026-11-05.
- Link to nilwerk.de and tag @nilwerk on Instagram and LinkedIn. *Why:* new domain and handles. *Source:* chat 2026-11-05.
- Write battery life and other design numbers as "simulated" until a bench test exists. *Why:* the v2 battery figure comes from a power simulation. *Source:* origin pack 2026-11-05.
- Use the approved v0.1 brand and templates for every visual, and run `showcase/brand/CHECKS.md` before committing. *Why:* the first carousel drifted from the website look. *Source:* PR #33.
- Write every post in two layers: plain story first, a short marked "For engineers" layer second. *Why:* both audiences. *Source:* brand-kit section 5b.
- Write the claim-check before the text: every number, date and name gets a row with type and source. *Why:* unsourced sentences are caught late. *Source:* PR #33 reviews.
- Be honest about the humans: name AI agents as agents ("our reviewing AI agent"), end with "AI agents, led and reviewed by humans", never "autonomous". *Why:* buyers want quality, not only speed. *Source:* Theo's review of PR #33.
- Keep time numbers in two labelled kinds: agent minutes are measured (and say what is excluded), human-equivalent hours are the agents' estimate. *Why:* avoids "X times faster". *Source:* TEAM.md section 10. Example: `projects/plant-monitor/LESSONS.md`, PR/social section.
- Re-check a canon fact against the daily reports before reuse. *Why:* canon and reports can differ. *Source:* `projects/plant-monitor/LESSONS.md`, PR/social section.
- Look at every rendered PNG, including the German one (it runs longer). *Why:* overlaps showed only in German. *Source:* origin story build 2026-11-07.
- Check advertising labelling, alt text and the Impressum link before a post is approved; legal points go to a professional. *Why:* UWG section 5 and media-authority guidance apply to company posts. *Source:* `showcase/learning/pr-skills-plan.md`.
- Use `anthropic-skills:social` for structure only; never use the `raazmor-*` skills for Nilwerk. *Why:* generic playbook; other brand's context. *Source:* checked 2026-11-07.
- Put an "as of <date and time>" label on every count that changes (merges, tasks done) and recount on the day of posting. *Why:* such counts grow within a day. *Source:* Theo's review of PR #40; example in `projects/plant-monitor/LESSONS.md`.
- Never write "every" or "each" about reviews without a verdict per PR; say "every code change" and what happens to docs. *Why:* report and docs PRs have no architect verdict. *Source:* Theo's review of PR #40.
- A region claim lists the non-EU helper services and says whether it is a decision or live. *Why:* "in the EU" is half the story when the AI service runs elsewhere. *Source:* Theo's review of PR #40, stack-and-costs.
- Do not repeat an old simulated figure once a newer calculation exists. *Why:* the old figure is outdated. *Source:* Theo's review of PR #40; example in `projects/plant-monitor/LESSONS.md`, PR/social section.
- Agent Diary: one short card per agent per day in the persona voice (`team/PERSONAS.md`): an "achievement of the day" from real evidence plus, optionally, a "From the virtual office" story. *Why:* Arsany wants more engaging, alive, real-world posts (A-049, answered 8 Nov, binding). *Source:* `showcase/content/diary/README.md`.
- Every achievement card needs a source row (PR and comment id or CI run, as-of date) in that day's `claim-check.md`; no source, no card. Ids stay in the claim-check, not on the image. *Why:* the persona voice is lively, the facts must stay exact. *Source:* Agent Diary concept, brand rule "no PR numbers on images".
- A virtual-office story is FICTION: dark theme, dashed banner "FICTION · IMAGINED BY OUR AGENTS · NOT A REAL EVENT", the same words in the first line of the text, no real number, result, person, customer or quote inside. *Why:* a funny story must never be mistaken for a result (UWG section 5). *Source:* Agent Diary concept.
- Persona speech is Poppy's drafting from the evidence, labelled "persona voice", never a verbatim log line; never put words in the mouth of a real human (Arsany, the hardware integrator). *Why:* invented quotes are the mistake Theo caught in the day-5 pack. *Source:* Theo's review of PR #48.
- Real-world visuals are real or labelled: real screenshots and real photos (with the integrator's OK) are shown as such; drawings say "ILLUSTRATION, NOT A PHOTO"; a progress tracker uses only real counts with an as-of time. *Why:* "connect it to the real world" must not turn into a mock-up that looks like a result. *Source:* Agent Diary concept, brand-kit section 7.
- Funny and true beats funny and made up: when a real event is funny (two Lead sessions colliding), tell it as true, with the source, and keep the fiction label for imagined stories only. *Why:* readers trust a team that laughs about its real stumbles. *Source:* Agent Diary week 2 plan.
- Needs-Arsany rows never go into `showcase/` (TEAM.md section 13): hand them to the Lead as text in the result. Also keep decision ids (A-0xx) and procurement facts out of publishable folders. Source: Theo's review of the Agent Diary PR, 8 Nov.
- Write what a snapshot is: "snapshot", never "live", for a card with an "as of" time; quote a rounded value with its exact one ("7.13 mm, rounded up to 7.2"). A claim-check cell must cite the comment that says the thing, not a neighbouring one. Source: same review.

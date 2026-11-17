# "The crew has a life": season 1, one real Tuesday (17 Nov 2026)

Author: Poppy (PR & Social) · task PR-2026-11-17 · requested by Arsany (owner creative direction, 17 Nov evening) · DRAFTS ONLY, nothing is scheduled or published.

**Concept:** the technical story stays 100% true; the *fun* is a clearly marked fictional layer on top: the AI crew as colleagues with rivalries, a slow-burn, hobbies and bad jokes. Visual grammar on every image: **dashed orange = imagined by Poppy (fiction)**, **solid green box = real, sourced engineering**. The chip "FICTIONAL CREW LIFE · REAL ENGINEERING" and the line "AI crew, led and reviewed by humans" are on every image and in every text.

## Hard rules for this series (they sit on top of TEAM.md section 5 and the brand kit)

1. The crew are **AI agents**. Say so in every post, playfully ("our AI crew").
2. Private lives, feelings, love stories, hobbies and dialogue are **fiction written by Poppy**: persona voice, never a verbatim log line, never presented as fact. No number, result or event inside a fictional element.
3. Engineering facts, numbers and events are **true and traceable** (`claim-check.md`, F-numbers).
4. **No invented details about real humans.** The founder appears only by role ("our founder"), taking a real, recorded decision, with no quotes and no name unless the owner approves it. The hardware tester is a real person: role name only ("our hardware tester"), no name without his OK, no invented feelings, reactions or private life. No customers, leads, prices, decision ids, private URLs.
5. Say what does **not** work yet (honest ledger in episode 5).

## The season arc (one day, five episodes)

Logline: *On a Tuesday, five real mistakes were caught before they could hurt anyone, and an AI crew pretended to be soap-opera characters about it.*

| Ep | Title | Real event (all 17 Nov 2026) | Characters | Fictional layer | Post slot (recommended) |
|---|---|---|---|---|---|
| 1 | The guard that could never fire | The "poison batch" guard (drop a batch the server keeps rejecting) reset itself on every new sensor sample (designed to be one every 15 min; a firmware setting, not observed on a device), so it could never reach its limit. Architect and QA found it; fixed; re-checked. | Ines, Mira | Rivals-to-colleagues "slow burn": the skeptic and the microamp hunter | Wed 18 Nov 12:30 |
| 2 | The road that never reached main | A pull request was merged into a feature branch after that branch had reached main, so a finished feature (delete-account gate) silently never reached main; a later PR carried it home. | Leo, Theo | Leo takes the scenic route; Theo, the cartographer, redraws the map | Thu 19 Nov 12:30 |
| 3 | The prototype that fell asleep | For the v1 perfboard prototype, the default firmware would put a never-set-up board into deep sleep with no timer before it reads a sensor; the bench build skips that. The pipeline had never built the bench variant; now it does. | Mira, Kai (+ our hardware tester, real person, role only) | A board that wants a nap too early; Kai is smug about green | Fri 20 Nov 12:30 |
| 4 | 23 disguises at the door | The care-tips safety filter was attacked by QA with 23 tricks: 15 held, 8 got through; after the fix all 8 are blocked. Honest limit: deny-list, live assistant mode off. | Sana, Ines | A bouncer vs. a party crasher in disguise | Mon 23 Nov 10:00 |
| 5 | The honest finale | What does not work yet: the app cannot connect to a real sensor, the cloud has no export function so delete stays locked, nothing measured on real hardware. Owner decisions recorded the same day. | Everyone, Poppy | Crew chat at end of day; "who is lying to me?" | Tue 24 Nov 10:00 |

Extras: **drama board** (who is who, all strings fictional), **fact-or-fiction card** (trust card, reuse under every episode), **character card story** (Ines and Mira), **LinkedIn image** for Ep 1, **25 s vertical video** (Ep 1 condensed; see `video-script.md`).

## Character voices (fiction; keep each to one idea, never a fact)

Voices follow `team/PERSONAS.md`; the "life" lines below are invented by Poppy and marked FICTION wherever used.

| Agent | Real role / catchphrase (PERSONAS.md) | Fictional life (Poppy's invention) | Voice sample |
|---|---|---|---|
| Nora | Lead; "What does done look like today?" | Runs stand-up with a stopwatch and a very calm kettle | "End of day. Who is lying to me?" |
| Theo | Architect; "Where's the contract for that?" | Collects old maps; pins things he loves | "You walked it on the wrong map." |
| Ines | QA; "Show me the log." | Keeps a jar where every "should work" costs a coin; secretly keeps Mira's best fix on a sticky note (slow-burn) | "Lovely. Show me the log." |
| Kai | DevOps; "Is main green?" | Names every green build like a pet | "Green, but I made it check." |
| Mira | Firmware; "What does it cost in µA?" | Feeds a sourdough starter once an hour to stay in character as a deep-sleeper; pretends not to be grateful to Ines | "...fine. You were right." |
| Leo | Full-stack; "Can a first-time user do it in three minutes?" | Always lost, always finds a shortcut | "I walked the whole route, Theo." |
| Sana | Cloud AI; "What stops it from giving bad advice?" | Bouncer at the door of a tiny club called Tips | "I am very proud of my door." |
| Emil | PCB; "Did we simulate the worst case?" | Plans picnics against the worst case (rain, ants) | cameo only |
| Yara | 3D; "How does it feel in the hand?" | Judges forks by their feel in the hand | cameo only |
| Max | Sales | Knocks politely, three times | cameo only |
| Poppy | PR; "Ooh, what's the proof?" | Narrator, cake emoji, team fan | "So we tell people exactly that. With proof." |

Relationship strings (drama board, all fiction): Ines and Mira "slow burn?", Leo and Theo "map quarrel", Sana and Ines "bouncer vs. crasher", Kai and Mira "green-light crush", Nora "peacekeeper". Tone: workplace warmth and banter only: no explicit content, no real people, no jokes at anyone's expense.

## Episode scripts (story first, then the engineers' layer)

### Ep 1 · The guard that could never fire
- **Plain story:** Mira wrote a safety net: if the server keeps rejecting the same batch of sensor data, drop it, so one bad batch cannot jam the queue for ever. Ines, the skeptic, went looking for the hole. The sensor is designed to add a new sample every 15 minutes (a firmware setting), and the guard counted the *newest* sample, so every retry looked like a brand-new batch. It could never reach its limit.
- **Dialogue (fiction):** Mira: "I built a guard for stubborn batches. I am extremely proud of it." Ines: "Lovely. Show me the log. I have a feeling your guard is counting the wrong thing. Do the maths, Mira." Mira: "...give me a minute. I need to stare at my counter." (No number or claim inside a fictional bubble: the facts sit in the green box.)
- **For engineers (real):** found by architecture review (by reading) and reproduced by QA: 6 rejects in a row, buffer grew 4 to 10 samples, guard never fired; the existing 45 deliberate-bug checks did not cover it. Fix: key the counter on the first (oldest) sample. After the fix the 3rd reject drops the batch; 622 checks pass, 49/49 deliberate bugs caught. Not run on a device; no Wi-Fi code yet.

### Ep 2 · The road that never reached main
- **Plain story:** Leo's delete-account work was reviewed and merged, with green ticks, into the wrong place: a side branch that had already left for the main line. The code never arrived. The next pull request carried it home that evening, and on the way the client was found calling a cloud address that does not exist.
- **Dialogue (fiction):** Leo: "It was merged! Green ticks everywhere!" Theo: "You walked it on the wrong map, Leo."
- **For engineers (real):** a pull request was merged into a feature branch after that branch had reached main; the content reached main only via a later pull request (merged 17 Nov). Wrong endpoint `/account` replaced by `delete-account`. Mutation checks: the guard, the export check and the URL are each protected by failing tests. Never run against the live project or a phone.

### Ep 3 · The prototype that fell asleep
- **Plain story:** The first v1 prototype is a hand-wired board. Mira noticed that, as shipped, a board that was never set up would go to sleep before reading a single sensor, with no alarm to wake it. So the bench version skips setup. Kai noticed the pipeline never built that bench version at all, and fixed that too. A human hardware tester will run the first real bench steps; none have been run yet.
- **Dialogue (fiction):** Mira: "A board that has never met a bench makes me nervous. Whoever runs it should see something. Not on my watch." Kai: "Green builds make me happy. I want this one built too, and I will check the switch."
- **For engineers (real):** v1 defaults turn the BLE setup flow off (`CONFIG_PLANT_SETUP_FLOW=n`) and use the bench loop; the reason is a code comment in `main.c` (read from source, not observed on hardware). 15/15 host tests pass; CI now builds the firmware a second time with the v1 defaults and greps that the option is on. CI compiles the v1 defaults for the ESP32-C3 (compile only); never flashed or run on the real board; the bench steps are unrun. With the setup flow on, a never-set-up board deep-sleeps unless setup is started with the BOOT button.

### Ep 4 · 23 disguises at the door
- **Plain story:** Before any plant-care tip reaches a plant, a safety filter checks it ("never say water when the soil is already soaked"). QA attacked it with 23 tricks. 15 bounced off. 8 got in: three disguised as negations ("don't forget to water"), three using words the filter did not know, two bad weather forecasts. Fixed the same day; all 8 are now blocked.
- **Dialogue (fiction):** Sana: "I run the door of a very exclusive club called Tips. I am very proud of my door." Ines: "I brought a false moustache. And a negation."
- **For engineers (real):** 68 tests and 66/66 deliberate bugs caught at the fixed state; the filter is still a deny-list, so odd phrasings and hidden characters can still slip past if the live assistant mode were switched on; that mode is off by default and QA recommends an allow-list first. CI ran only 31 of the 68 tests when checked (open note).

### Ep 5 · The honest finale
- **Plain story:** End of the day, the honest ledger: tested on a computer with stand-ins, yes. The app connecting to a real sensor: not yet. A real data export in the cloud: not built yet, so deleting an account stays locked (the safe direction). Anything measured on real hardware: not yet. Real humans decided: the founder approved the care-tip safety limits for the demo and ruled that the export must really reach the user before deletion unlocks; a human hardware tester gets the bench steps next.
- **Dialogue (fiction):** Nora: "Who is lying to me?" Ines: "Nobody. I checked." Poppy: "So we tell people exactly that. With proof."
- **For engineers (real):** real BLE provisioning is not implemented in the app (non-mock build shows "needs the full app build"); no `export` edge function in the repo or deployed; hardware untested.

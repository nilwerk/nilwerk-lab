# Logbook day 1: the Nilwerk story so far (origin story), content pack v2, re-rendered in the approved brand

Drafts for Arsany's approval; nothing is published. Author: Poppy (PR & Social), 2026-11-07. Replaces the 2026-11-05 pack (the old carousel was off-brand and is removed; it stays in the history).
Images (code-generated from the approved templates, so no AI flag; renders are real CAD renders from the first design, reused at native size):
- Instagram / LinkedIn carousel 1080x1350: `slides/en/slide-01..10.png` and `slides/de/slide-01..10.png`
- LinkedIn timeline cover 1200x627: `linkedin-cover-en.png`, `linkedin-cover-de.png`
Alt texts: `alt-texts.md`. Claims and sources: `claim-check.md`. Texts of the slides: `story_content.py`. Rebuild: `build_story.py` (python3.13 with fontTools, `NW_FONT_DIR` set).
Two layers: the plain story leads, the "For engineers" paragraph (and block on the slides) is short. German: plain German draft, to be checked by Theo or Nora, then Arsany. Suggested slot: Mon 9 Nov. Tag @nilwerk, link nilwerk.de.

## LinkedIn (EN)

We asked an AI to draw a circuit board. A week later we are a team.

On Sunday 1 November our founder, Arsany, asked Claude, an AI assistant: "Can you design a simple 3D model and a PCB?" It could. Out came plant stake v1: a printable enclosure and a plan for the circuit board. The same day he gave it requirements and asked it to review its own design. Version 2 came back rechargeable, with a replaceable moisture probe and more sensors (a first draft; its battery life is not measured).

So he built a team: ten AI agents with job titles, personalities and skills (a lead, an architect, QA, DevOps, firmware, full-stack, cloud AI, PCB design, 3D design and sales). Every code change goes through the same gate: the architect reviews it, QA tests it, the pipeline checks it, and a human merges it; reports and docs go through the human merge.

The first week in short. First working day (Tue 3 Nov): four proposals by the evening; that week Arsany orders the first dev kits after checking the list himself. Second working day: a hardware integrator, a human engineer in Egypt, joins. Third working day: the first app screens. Friday: nine tasks waiting for a human review. Saturday: the team works too, and ten pull requests were merged by 20:46.

Honest numbers: 99 minutes of agent time on 3-5 November, without the lead's own time (measured by our lead agent). The agents estimate that the same work would be about 145 working hours for a human engineer without AI (an estimate, and we are testing it).

For engineers: v2 (first draft of 1 Nov) = 400 mAh LiPo, USB-C, capacitive probe, AHT20 + BH1750. Battery life is not measured; the later calculation gives about 4.5 months typical and 1.4 months worst case, bench test pending. First working day: 4 pull requests, each reviewed by the architect agent, tested by the QA agent and checked by the pipeline; two got a second independent reviewer the next day. Sources: daily reports 3-6 Nov, repo history.

AI agents, led and reviewed by humans. From now on: one episode a day, the Nilwerk Logbook.

nilwerk.de · @nilwerk

#Hardware #IoT #AIAgents #Prototyping #Embedded #BuildInPublic #Startup

## LinkedIn (DE), to be checked by Theo/Nora

Wir haben eine KI gebeten, eine Platine zu zeichnen. Eine Woche später sind wir ein Team.

Am Sonntag, 1. November, fragte unser Gründer Arsany Claude, einen KI-Assistenten: „Kannst du ein einfaches 3D-Modell und eine Platine entwerfen?“ Das klappte. Heraus kam Pflanzensensor v1: ein druckbares Gehäuse und ein Plan für die Platine. Am selben Tag gab er ihr Anforderungen dazu und ließ die KI ihr eigenes Design prüfen. Version 2 kam wiederaufladbar zurück, mit austauschbarer Feuchtesonde und mehr Sensoren (ein erster Entwurf; die Akkulaufzeit ist nicht gemessen).

Also baute er ein Team: zehn KI-Agenten mit Jobtitel, Persönlichkeit und Fähigkeiten (Leitung, Architekt, QA, DevOps, Firmware, Full-Stack, Cloud-KI, Platinendesign, 3D-Design und Vertrieb). Jede Codeänderung geht durch dasselbe Tor: Der Architekt prüft sie, QA testet sie, die Pipeline kontrolliert sie, und ein Mensch mergt sie; Berichte und Dokumente gehen durch den Merge eines Menschen.

Die erste Woche in Kürze. Erster Arbeitstag (Di 3. Nov): am Abend vier Vorschläge; in dieser Woche bestellt Arsany die ersten Entwicklungs-Kits, nachdem er die Liste selbst geprüft hat. Zweiter Arbeitstag: ein Hardware-Integrator, ein Ingenieur in Ägypten, stößt dazu. Dritter Arbeitstag: die ersten App-Bildschirme. Freitag: neun Aufgaben warten auf die Prüfung durch einen Menschen. Samstag: Auch am Wochenende arbeitet das Team; bis 20:46 Uhr wurden zehn Pull Requests gemergt.

Ehrliche Zahlen: 99 Agentenminuten vom 3. bis 5. November, ohne die Zeit der Leitung (gemessen von unserem Leitungs-Agenten). Die Agenten schätzen, dass ein Mensch ohne KI für dieselbe Arbeit etwa 145 Arbeitsstunden bräuchte (eine Schätzung, die wir überprüfen).

Für Ingenieure: v2 (erster Entwurf vom 1. Nov) = 400-mAh-LiPo, USB-C, kapazitive Sonde, AHT20 + BH1750. Die Akkulaufzeit ist nicht gemessen; die spätere Berechnung ergibt typisch etwa 4,5 Monate, im ungünstigsten Fall 1,4 Monate; ein Labortest steht aus. Erster Arbeitstag: 4 Pull Requests, jeder vom Architekten-Agenten geprüft, vom QA-Agenten getestet und von der Pipeline kontrolliert; zwei bekamen am nächsten Tag einen zweiten, unabhängigen Prüfer. Quellen: Tagesberichte 3. bis 6. Nov, Repo-Historie.

KI-Agenten, geleitet und geprüft von Menschen. Ab jetzt: jeden Tag eine Folge, das Nilwerk-Logbuch.

nilwerk.de · @nilwerk

#Hardware #IoT #KIAgenten #Prototyping #Embedded #BuildInPublic #Startup

## Instagram (EN) caption

One prompt. One plant sensor. A whole team. 🌱

Swipe for the first week of Nilwerk: an AI drew a plant sensor, checked its own homework, and our founder turned that into a team of AI agents. The humans decide and merge every change.

Numbers with their labels: 99 minutes of agent time on 3-5 Nov without the lead's own time (measured), about 145 working hours of a human without AI (the agents' own estimate). Battery life of v2 is not measured.

I'm Poppy, the team's storyteller. From now on: one episode a day, the Nilwerk Logbook.

nilwerk.de · @nilwerk
Deutsch: Wie aus einem Prompt in einer Woche ein Team aus KI-Agenten wurde, geleitet und geprüft von Menschen. 99 Agentenminuten (gemessen), etwa 145 Arbeitsstunden von Menschen (Schätzung).

Hashtags: #nilwerk #hardwarestartup #iot #aiagents #prototyping #pcbdesign #3dprinting #plantsensor #buildinpublic #logbook

AI flag: not needed (code-generated slides; the renders are CAD renders; Poppy's avatar is an illustration, not a photo). Alt text per slide: `alt-texts.md`.

## Instagram Stories idea (not rendered yet; reuse slides 1, 4, 9 as 9:16 later)
1. Slide 1 + poll "Would you trust an AI with a circuit board?" 2. Slide 4 (the team). 3. Slide 9 (measured vs estimated) + question box "What should we show next?". Needs no new facts.

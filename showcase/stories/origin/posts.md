# Origin story — content pack (Poppy, 2026-11-05)

Status: **drafts for Arsany's approval**. Nothing is published.
Media: `origin-01.png` … `origin-10.png` (1080 × 1350, Instagram/LinkedIn carousel) and the interactive story page.

## Claim sources (checked)
| Claim | Source |
|---|---|
| v1: 2×AAA, PCB blade probe, 34 × 84 × 19.8 mm head | Drive `Plant Monitor/…/v1/README.md`, 1 Nov 2026 |
| v2: 400 mAh LiPo, USB-C (~2.8 h charge), capacitive probe, AHT20 + BH1750, 34 × 80.5 × 17 mm | Drive `…/v2/README.md`, 1 Nov 2026 |
| Battery 150–226 days (simulated, fast Wi-Fi connect; ~half with slow connect) | `power_sim_results.json` |
| Day 1: 4 PRs, reviewed / tested / pipeline | Report 2026-11-03, PRs #1–#4 |
| 15 PRs in 3 days, 8 merged | GitHub, PRs #1–#5, #12–#21 |
| 16.2 + 50.0 + 33.0 = 99.2 agent-minutes | Reports 3–5 Nov (time tables) |
| ~145 h = 37 + 61.5 + 46 h, agents' own estimates | Same tables, column "agent's own estimate" |
| "About an hour" to answer Nora's questions | Arsany, in chat 5 Nov |

## LinkedIn (EN)

I asked an AI to draw a PCB. Five days later I have an engineering team.

Sunday: one curious prompt to Claude. "Can you design a simple 3D model and a PCB?" It could. Plant stake v1: a printable enclosure and a board plan, generated in code.

Same day I gave it requirements and asked it to review its own design. v2 came back rechargeable (400 mAh LiPo, USB-C), with a replaceable capacitive probe and a simulated battery life of 5 to 7 months.

So I thought: I wish I had a team. On Monday I built one. Ten AI agents with job titles, personalities and skills: a lead, an architect, QA, DevOps, firmware, full-stack, cloud AI, PCB, 3D design and sales.

Day 1: Nora, our lead, planned the sprint at 07:30. Four pull requests by the evening, every one reviewed by the architect, tested by QA and checked by the pipeline. The summary had a few questions only I could answer. That took me about an hour.
Day 2: parts ordered, and a junior engineer in Egypt joined to build and test the real hardware.
Day 3: the app wireframes landed.

The first three days in numbers: 15 pull requests, 99 agent-minutes of work. The agents estimate an experienced engineer would need around 145 hours for the same work. That's their estimate, and we're testing it against real projects.

Humans still decide: I answer the questions and merge every change. Our integrator builds the boards.

Tonight the team got its storyteller. Hello, I'm Poppy, and I'll be sharing what we build, with proof. 🌱

Building a connected device? → nilwerk.github.io

#hardware #IoT #AIagents #prototyping #embedded #startup

## LinkedIn (DE)

Ich habe eine KI gebeten, eine Platine zu zeichnen. Fünf Tage später habe ich ein Engineering-Team.

Sonntag: ein neugieriger Prompt an Claude. „Kannst du ein einfaches 3D-Modell und eine Platine entwerfen?" Es ging. Pflanzensensor v1: ein druckbares Gehäuse und ein Platinenplan, komplett per Code erzeugt.

Am selben Tag habe ich Anforderungen dazugegeben und die KI ihr eigenes Design prüfen lassen. v2: wiederaufladbar (400-mAh-LiPo, USB-C), austauschbare kapazitive Sonde und laut Simulation 5 bis 7 Monate Akkulaufzeit.

Also dachte ich: Ich hätte gern ein Team. Am Montag habe ich eins aufgebaut. Zehn KI-Agenten mit Jobtitel, Persönlichkeit und Fähigkeiten: Lead, Architekt, QA, DevOps, Firmware, Full-Stack, Cloud-KI, Platine, 3D-Design und Vertrieb.

Tag 1: Nora, unsere Projektleitung, plant um 07:30 den Sprint. Am Abend vier Pull Requests, jeder vom Architekten geprüft, von QA getestet und durch die Pipeline gelaufen. Die Zusammenfassung enthielt ein paar Fragen, die nur ich beantworten konnte. Dafür brauchte ich etwa eine Stunde.
Tag 2: Teile bestellt, und ein Junior-Ingenieur in Ägypten baut und testet ab jetzt die echte Hardware.
Tag 3: die Wireframes der App.

Die ersten drei Tage in Zahlen: 15 Pull Requests, 99 Agenten-Minuten. Die Agenten schätzen, dass ein erfahrener Ingenieur ohne KI etwa 145 Stunden bräuchte. Das ist ihre Schätzung, und wir prüfen sie an echten Projekten.

Entscheidungen treffen weiterhin Menschen: Ich beantworte die Fragen und merge jede Änderung. Unser Integrator baut die Platinen.

Heute Abend kam noch jemand dazu: Poppy, unsere Stimme nach außen. 🌱

Ihr baut ein vernetztes Gerät? → nilwerk.github.io

## Instagram carousel caption (EN + one German line)

One prompt. One plant sensor. A whole team. 🌱

Swipe for how Nilwerk went from "can an AI draw a PCB?" to an engineering team of AI agents in five days, with the real renders, wireframes and numbers.

Hi, I'm Poppy, the newest member. I'll show you what the team builds every day, and I'll always show the proof.

🇩🇪 Wie aus einem Prompt ein KI-Engineering-Team wurde. Mit echten Zahlen.

#hardwarestartup #iot #aiagents #prototyping #pcbdesign #3dprinting #plantsensor #reutlingen

Settings: mark as AI-related content only if Arsany wants it (renders are code-generated, not AI images); avatars are illustrations.

## Instagram stories (5 frames, 9:16, reuse carousel visuals)
1. "I asked an AI to draw a PCB 👀" + v1 render. Sticker: poll "Would you trust it?" Yes / Show me.
2. v1 → v2 side by side. Text: "Then it fixed its own design. Rechargeable, 5–7 months battery (simulated)."
3. Team grid. Text: "So we hired a team. Of agents." Sticker: quiz "Who reviews every change?" Theo / Ines / Kai / all three ✅.
4. Wireframe crop. Text: "Day 3: the app takes shape."
5. Poppy avatar. Text: "Hi, I'm Poppy! Daily build updates from here." Link sticker → nilwerk.github.io.

## Reel idea (for when Peter's footage exists)
15–20 s: screen recording of the story page scroll → v1/v2 slider drag → real printed enclosure in hand (Peter's video) → "Same design. Now in real life." Needs Peter's OK to use his footage.

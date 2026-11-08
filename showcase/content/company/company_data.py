# -*- coding: utf-8 -*-
"""Texts of the three company posts (Mon 9, Tue 10, Wed 11 Nov 2026), 4 slides each, EN + DE.
Facts as of Sun 8 Nov 2026, 18:54 Berlin; every claim has a row in claim-check.md. Speech bubbles are persona voice
written by Poppy from the evidence, never a quote of a human. German is UNCHECKED until Theo or Nora have checked it."""

# each text: dict(en=..., de=...)
def L(en, de):
    return dict(en=en, de=de)

POSTS = {
    "p1-why": dict(
        day=1, date="2026-11-09", title=L("Why we exist", "Warum es uns gibt"),
        slides=[
            dict(kind="cover", kicker=L("NILWERK STORY · WHY · 1/4", "NILWERK STORY · WARUM · 1/4"),
                 head=L(["Why does", "Nilwerk exist?"], ["Warum gibt es", "Nilwerk?"]),
                 av="pr-social", name="Poppy",
                 bubble=L("Hi, I'm Poppy, the team's storyteller. Pull up a chair. The story starts with one question, on a Sunday.",
                          "Hallo, ich bin Poppy, die Geschichtenerzählerin des Teams. Setz dich. Die Geschichte beginnt mit einer Frage, an einem Sonntag."),
                 sub=L("Swipe: four slides, two minutes.", "Wischen: vier Folien, zwei Minuten."),
                 status=L("THE STORY SO FAR · AS OF 8 NOV", "DIE GESCHICHTE BISHER · STAND 8. NOV"),
                 eng=L("Everything below lives in one repo: ESP32-C3 firmware, KiCad boards, CadQuery enclosures, an Expo app, a cloud backend. Each claim carries a label.",
                       "Alles liegt in einem Repo: ESP32-C3-Firmware, KiCad-Platinen, CadQuery-Gehäuse, Expo-App, Cloud-Backend. Jede Aussage trägt eine Beschriftung.")),
            dict(kind="story", kicker=L("NILWERK STORY · WHY · 2/4", "NILWERK STORY · WARUM · 2/4"),
                 head=L(["It started with", "one question."], ["Es begann mit", "einer Frage."]),
                 body=L("Sunday 1 November. Our founder, Arsany, asked an AI assistant one thing: “can you design a simple 3D model and a PCB?” Out came a tiny plant-stake sensor. Then the design was checked against the requirements and fixed. Version 2 had a rechargeable battery, a USB-C port and a soil probe.",
                        "Sonntag, 1. November. Unser Gründer Arsany stellte einem KI-Assistenten eine einzige Frage: „Kannst du ein einfaches 3D-Modell und eine Platine entwerfen?“ Heraus kam ein kleiner Pflanzenstab-Sensor. Dann wurde der Entwurf gegen die Anforderungen geprüft und korrigiert. Version 2 hatte einen Akku, einen USB-C-Anschluss und eine Bodensonde."),
                 av="pr-social", name="Poppy",
                 bubble=L("One prompt, one Sunday, one tiny plant sensor. I love a small start.", "Eine Frage, ein Sonntag, ein winziger Pflanzensensor. Ich liebe kleine Anfänge."),
                 status=L("FROM THE ORIGIN STORY · 1 NOV", "AUS DER GRÜNDUNGSGESCHICHTE · 1. NOV"),
                 eng=L("v2: 400 mAh LiPo, USB-C, capacitive soil probe, AHT20 + BH1750. Battery life was never measured; the first simulated figure is outdated.",
                       "v2: 400-mAh-LiPo, USB-C, kapazitive Bodensonde, AHT20 + BH1750. Die Akkulaufzeit wurde nie gemessen; die erste simulierte Zahl ist überholt.")),
            dict(kind="six", kicker=L("NILWERK STORY · WHY · 3/4", "NILWERK STORY · WARUM · 3/4"),
                 head=L(["A gadget needs", "six skills."], ["Ein Gerät braucht", "sechs Fähigkeiten."]),
                 body=L("Firmware, a circuit board, a case, an app, a cloud and tests. Small companies rarely have all six in one room. So the idea became: one team that covers all six, run by AI agents, led and reviewed by humans.",
                        "Firmware, Platine, Gehäuse, App, Cloud und Tests. Kleine Firmen haben selten alle sechs an einem Tisch. Also entstand die Idee: ein Team, das alle sechs abdeckt, getragen von KI-Agenten, geleitet und geprüft von Menschen."),
                 tiles=[("firmware", "Mira", L("Firmware", "Firmware")), ("pcb", "Emil", L("Circuit board", "Platine")), ("mechanical", "Yara", L("Case", "Gehäuse")),
                        ("fullstack", "Leo", L("App", "App")), ("cloud-ai", "Sana", L("Cloud", "Cloud")), ("qa", "Ines", L("Tests", "Tests"))],
                 status=L("SIX DISCIPLINES · ONE DEVICE", "SECHS DISZIPLINEN · EIN GERÄT"),
                 eng=L("ESP-IDF (C), KiCad 9, CadQuery, Expo / React Native, Supabase. The EU region is a decision, not live; helper services may process pseudonymous data elsewhere.",
                       "ESP-IDF (C), KiCad 9, CadQuery, Expo / React Native, Supabase. Die EU-Region ist eine Entscheidung, nicht live; Hilfsdienste können pseudonyme Daten anderswo verarbeiten.")),
            dict(kind="story", kicker=L("NILWERK STORY · WHY · 4/4", "NILWERK STORY · WARUM · 4/4"),
                 head=L(["And we show", "our work."], ["Und wir zeigen,", "wie wir arbeiten."]),
                 body=L("Every number wears a label: measured, simulated or estimated. Our own plant monitor is the test case: a prototype, not a product for sale. In six days, from 3 to 8 November, 48 changes were merged. Follow along: one post a day.",
                        "Jede Zahl trägt ein Etikett: gemessen, simuliert oder geschätzt. Unser eigener Pflanzenmonitor ist der Testfall: ein Prototyp, kein Produkt zum Verkauf. In sechs Tagen, vom 3. bis 8. November, wurden 48 Änderungen übernommen. Folge uns: ein Beitrag pro Tag."),
                 av="pr-social", name="Poppy",
                 bubble=L("Ooh, what's the proof? My favourite question. Ask it of us every day.", "Ooh, was ist der Beweis? Meine Lieblingsfrage. Stell sie uns jeden Tag."),
                 status=L("COUNTED · AS OF 8 NOV 18:54", "GEZÄHLT · STAND 8. NOV 18:54"),
                 eng=L("48 = merge commits on main, 3 to 8 Nov (git log, first-parent). They include docs, reports and showcase changes, not only code. Nothing is bench-tested yet.",
                       "48 = Merge-Commits auf main, 3. bis 8. Nov (git log, first-parent). Darin stecken auch Doku, Berichte und Showcase, nicht nur Code. Noch nichts am Prüfstand getestet.")),
        ],
        alt=[L("Cover card: Poppy, the team's storyteller, in a speech bubble: the story starts with one question, on a Sunday.",
               "Titelkarte: Poppy, die Geschichtenerzählerin des Teams, in einer Sprechblase: Die Geschichte beginnt mit einer Frage, an einem Sonntag."),
             L("Slide 2: on Sunday 1 November the founder asked an AI assistant to design a simple 3D model and a PCB; a tiny plant-stake sensor came out.",
               "Folie 2: Am Sonntag, 1. November, bat der Gründer einen KI-Assistenten um ein einfaches 3D-Modell und eine Platine; heraus kam ein kleiner Pflanzenstab-Sensor."),
             L("Slide 3: six tiles with the team's drawn avatars: firmware, circuit board, case, app, cloud and tests.",
               "Folie 3: sechs Kacheln mit den gezeichneten Avataren des Teams: Firmware, Platine, Gehäuse, App, Cloud und Tests."),
             L("Slide 4: we show our work with labels measured, simulated or estimated; 48 changes merged from 3 to 8 November.",
               "Folie 4: Wir zeigen unsere Arbeit mit den Etiketten gemessen, simuliert oder geschätzt; 48 Änderungen vom 3. bis 8. November übernommen.")],
        caption=L(
            """Why does Nilwerk exist? 🌱

It started on a Sunday, 1 November, with one question to an AI assistant: "can you design a simple 3D model and a PCB?" Out came a tiny plant-stake sensor. We checked it, fixed it, and thought: a connected gadget needs six skills (firmware, circuit board, case, app, cloud, tests) and small companies rarely have all six in one room.

So we built one team that does: AI agents, led and reviewed by humans. Our own plant monitor is the test case (a prototype, not a product for sale). Every number gets a label: measured, simulated or estimated.

Ooh, what's the proof? Ask us every day. One post a day from here on.

For engineers: ESP32-C3 firmware, KiCad boards, CadQuery enclosures, Expo app, cloud backend. 48 merged changes from 3 to 8 Nov (counted 8 Nov, 18:54; includes docs).

nilwerk.de · @nilwerk
#hardware #prototyping #buildinpublic #AIagents #IoT""",
            """Warum gibt es Nilwerk? 🌱

Es begann an einem Sonntag, dem 1. November, mit einer Frage an einen KI-Assistenten: „Kannst du ein einfaches 3D-Modell und eine Platine entwerfen?“ Heraus kam ein kleiner Pflanzenstab-Sensor. Wir haben ihn geprüft und verbessert und gedacht: Ein vernetztes Gerät braucht sechs Fähigkeiten (Firmware, Platine, Gehäuse, App, Cloud, Tests), und kleine Firmen haben selten alle sechs an einem Tisch.

Also haben wir ein Team gebaut, das alle sechs kann: KI-Agenten, geleitet und geprüft von Menschen. Unser eigener Pflanzenmonitor ist der Testfall (ein Prototyp, kein Produkt zum Verkauf). Jede Zahl bekommt ein Etikett: gemessen, simuliert oder geschätzt.

Ooh, was ist der Beweis? Fragt uns jeden Tag. Ab jetzt gibt es täglich einen Beitrag.

Für Ingenieure: ESP32-C3-Firmware, KiCad-Platinen, CadQuery-Gehäuse, Expo-App, Cloud-Backend. 48 übernommene Änderungen vom 3. bis 8. Nov (gezählt 8. Nov, 18:54; inkl. Doku).

nilwerk.de · @nilwerk"""),
    ),

    "p2-who": dict(
        day=2, date="2026-11-10", title=L("Who we are", "Wer wir sind"),
        slides=[
            dict(kind="cover", kicker=L("NILWERK STORY · WHO · 1/4", "NILWERK STORY · WER · 1/4"),
                 head=L(["Meet the", "team."], ["Lernt das", "Team kennen."]),
                 av="pr-social", name="Poppy",
                 bubble=L("Eleven AI agents, two humans, one plant. Let me introduce everyone. Yes, even the skeptic.",
                          "Elf KI-Agenten, zwei Menschen, eine Pflanze. Ich stelle alle vor. Ja, auch die Skeptikerin."),
                 sub=L("Swipe: builders, checkers, humans.", "Wischen: Entwickler, Prüfer, Menschen."),
                 status=L("11 AI AGENTS · 2 HUMANS", "11 KI-AGENTEN · 2 MENSCHEN"),
                 eng=L("Each agent has a role file, a persona and a playbook of lessons in the repo. Personas shape tone, never permissions: the hard rules apply to everyone.",
                       "Jeder Agent hat im Repo eine Rollendatei, eine Persona und ein Lernblatt. Personas prägen den Ton, nie die Rechte: Die harten Regeln gelten für alle.")),
            dict(kind="roster", kicker=L("NILWERK STORY · WHO · 2/4", "NILWERK STORY · WER · 2/4"),
                 head=L(["The builders."], ["Die Entwickler."]),
                 rows=[("firmware", "Mira", L("Firmware + edge AI", "Firmware + Edge-KI"), L("What does it cost in µA?", "Was kostet das in µA?")),
                       ("fullstack", "Leo", L("App + backend", "App + Backend"), L("Can a newcomer do it in three minutes?", "Schafft das ein Neuling in drei Minuten?")),
                       ("cloud-ai", "Sana", L("Cloud AI", "Cloud-KI"), L("What stops it giving bad advice?", "Was hindert es an schlechten Ratschlägen?")),
                       ("pcb", "Emil", L("Circuit boards", "Platinen"), L("Did we simulate the worst case?", "Haben wir den schlimmsten Fall simuliert?")),
                       ("mechanical", "Yara", L("3D cases", "3D-Gehäuse"), L("How does it feel in the hand?", "Wie fühlt es sich in der Hand an?"))],
                 status=L("PERSONA SHEET · AI AGENTS", "PERSONA-BLATT · KI-AGENTEN"),
                 eng=L("Five builder roles, one task per role per day, each on its own branch with its own pull request. “Always asks” lines are from the team's persona sheet.",
                       "Fünf Entwicklerrollen, pro Rolle und Tag eine Aufgabe, jeweils auf eigenem Branch mit eigenem Pull Request. Die „Fragt immer“-Sätze stammen aus dem Persona-Blatt.")),
            dict(kind="roster", kicker=L("NILWERK STORY · WHO · 3/4", "NILWERK STORY · WER · 3/4"),
                 head=L(["The checkers", "and the voice."], ["Die Prüfer", "und die Stimme."]),
                 rows=[("lead-pm", "Nora", L("Lead, plans the day", "Leitung, plant den Tag"), L("What does done look like today?", "Wie sieht fertig heute aus?")),
                       ("architect", "Theo", L("Architect, reviews", "Architekt, prüft"), L("Where is the contract for that?", "Wo ist das als Schnittstelle festgeschrieben?")),
                       ("qa", "Ines", L("QA, tests", "QA, testet"), L("Show me the log.", "Zeig mir das Log.")),
                       ("devops", "Kai", L("Pipeline", "Pipeline"), L("Is main green?", "Ist main grün?")),
                       ("pr-social", "Poppy", L("PR + social", "PR + Social"), L("Ooh, what's the proof?", "Ooh, was ist der Beweis?")),
                       ("sales", "Max", L("Sales assistant", "Vertriebsassistent"), L("Who exactly is this for?", "Für wen genau ist das?"))],
                 status=L("PERSONA SHEET · AI AGENTS", "PERSONA-BLATT · KI-AGENTEN"),
                 eng=L("Review, test and pipeline are separate roles on purpose: the author of a change never signs it off. The sales assistant runs as its own scheduled task.",
                       "Prüfung, Test und Pipeline sind bewusst getrennte Rollen: Wer etwas baut, gibt es nie selbst frei. Der Vertriebsassistent läuft als eigene geplante Aufgabe.")),
            dict(kind="humans", kicker=L("NILWERK STORY · WHO · 4/4", "NILWERK STORY · WER · 4/4"),
                 head=L(["Two humans make", "it real."], ["Zwei Menschen", "machen es real."]),
                 people=[("human-public", L("Arsany, founder", "Arsany, Gründer"), L("Leads the team, decides, orders. By our rule nothing is done without his yes.", "Leitet das Team, entscheidet, bestellt. Nach unserer Regel ist ohne sein Ja nichts fertig.")),
                         ("human-public", L("Hardware integrator", "Hardware-Integrator"), L("A human who will assemble, flash and bench-test the first real boards.", "Ein Mensch, der die ersten echten Platinen bestücken, flashen und am Prüfstand testen wird."))],
                 note=L("Agents may prepare a purchase but never make one. No board is built yet: so far this is design, simulation and tests.",
                        "Agenten dürfen einen Kauf vorbereiten, aber nie auslösen. Noch ist keine Platine gebaut: Bisher sind es Entwurf, Simulation und Tests."),
                 status=L("NO BOARD BUILT YET", "NOCH KEINE PLATINE GEBAUT"),
                 eng=L("Hands-on work reaches the integrator as a written work order and comes back with measurements. Hardware figures stay “simulated” or “estimated” until he has measured.",
                       "Praktische Arbeit geht als schriftlicher Arbeitsauftrag an den Integrator und kommt mit Messwerten zurück. Hardware-Zahlen bleiben „simuliert“ oder „geschätzt“, bis er gemessen hat.")),
        ],
        alt=[L("Cover card: Poppy in a speech bubble introduces eleven AI agents and two humans.",
               "Titelkarte: Poppy stellt in einer Sprechblase elf KI-Agenten und zwei Menschen vor."),
             L("Slide 2: the five builder agents with drawn avatars: Mira, Leo, Sana, Emil and Yara, each with the question they always ask.",
               "Folie 2: die fünf Entwickler-Agenten mit gezeichneten Avataren: Mira, Leo, Sana, Emil und Yara, jeweils mit ihrer Standardfrage."),
             L("Slide 3: six agents: Nora (lead), Theo (architect), Ines (QA), Kai (pipeline), Poppy (PR) and Max (sales), each with their question.",
               "Folie 3: sechs Agenten: Nora (Leitung), Theo (Architekt), Ines (QA), Kai (Pipeline), Poppy (PR) und Max (Vertrieb), jeweils mit ihrer Standardfrage."),
             L("Slide 4: two humans: Arsany the founder and a hardware integrator who will assemble and test the first boards. No board is built yet.",
               "Folie 4: zwei Menschen: Gründer Arsany und ein Hardware-Integrator, der die ersten Platinen bestücken und testen wird. Noch ist keine Platine gebaut.")],
        caption=L(
            """Meet the team! 👋

Eleven AI agents, two humans, one plant.

🛠 Builders: Mira (firmware + edge AI), Leo (app + backend), Sana (cloud AI), Emil (circuit boards), Yara (3D cases).
🔍 Checkers: Nora plans, Theo reviews, Ines tests, Kai guards the pipeline. Poppy tells the story, Max does sales.
🧑 Humans: Arsany, our founder, leads and decides. A hardware integrator will assemble and bench-test the first real boards.

Agents may prepare a purchase but never make one, and no board is built yet: so far it's design, simulation and tests. The agents' lines are persona voice, written from the evidence.

Tomorrow: how a day at Nilwerk works.

For engineers: personas shape tone, never permissions. Review, test and pipeline are separate roles, so the author never signs off their own change.

nilwerk.de · @nilwerk
#buildinpublic #AIagents #hardware #startup #meettheteam""",
            """Lernt das Team kennen! 👋

Elf KI-Agenten, zwei Menschen, eine Pflanze.

🛠 Entwickler: Mira (Firmware + Edge-KI), Leo (App + Backend), Sana (Cloud-KI), Emil (Platinen), Yara (3D-Gehäuse).
🔍 Prüfer: Nora plant, Theo prüft, Ines testet, Kai wacht über die Pipeline. Poppy erzählt die Geschichte, Max macht den Vertrieb.
🧑 Menschen: Arsany, unser Gründer, leitet und entscheidet. Ein Hardware-Integrator wird die ersten echten Platinen bestücken und testen.

Agenten dürfen einen Kauf vorbereiten, aber nie auslösen, und noch ist keine Platine gebaut: Bisher sind es Entwurf, Simulation und Tests. Die Sätze der Agenten sind Persona-Stimme, anhand der Belege geschrieben.

Morgen: wie ein Tag bei Nilwerk abläuft.

Für Ingenieure: Personas prägen den Ton, nie die Rechte. Prüfung, Test und Pipeline sind getrennte Rollen, der Autor gibt seine Änderung nie selbst frei.

nilwerk.de · @nilwerk"""),
    ),

    "p3-how": dict(
        day=3, date="2026-11-11", title=L("How we work", "Wie wir arbeiten"),
        slides=[
            dict(kind="cover", kicker=L("NILWERK STORY · HOW · 1/4", "NILWERK STORY · WIE · 1/4"),
                 head=L(["A day at", "Nilwerk."], ["Ein Tag bei", "Nilwerk."]),
                 av="lead-pm", name="Nora",
                 bubble=L("07:30. I pick today's tasks. One per builder, the smallest useful slice. Then we go.",
                          "07:30. Ich wähle die Aufgaben des Tages. Eine pro Entwickler, das kleinste nützliche Stück. Dann geht es los."),
                 sub=L("Swipe: plan, build, review, test, pipeline.", "Wischen: planen, bauen, prüfen, testen, Pipeline."),
                 status=L("PERSONA VOICE · FROM THE TEAM CHARTER", "PERSONA-STIMME · AUS DER TEAM-CHARTA"),
                 eng=L("The Lead agent runs at 07:30 Berlin time as a scheduled task: reads the plan, picks tasks, writes assignments with acceptance criteria, reports to the founder.",
                       "Der Lead-Agent läuft um 07:30 Uhr Berliner Zeit als geplante Aufgabe: liest den Plan, wählt Aufgaben, schreibt Aufträge mit Abnahmekriterien, berichtet dem Gründer.")),
            dict(kind="flow", kicker=L("NILWERK STORY · HOW · 2/4", "NILWERK STORY · WIE · 2/4"),
                 head=L(["Plan. Build. Review.", "Test. Pipeline."], ["Planen. Bauen. Prüfen.", "Testen. Pipeline."]),
                 steps=[("lead-pm", L("Plan", "Planen"), L("Nora picks the day's tasks", "Nora wählt die Tagesaufgaben")),
                        ("firmware", L("Build", "Bauen"), L("Builders work in parallel", "Entwickler arbeiten parallel")),
                        ("architect", L("Review", "Prüfen"), L("Theo checks against the requirements", "Theo prüft gegen die Anforderungen")),
                        ("qa", L("Test", "Testen"), L("Ines runs the tests and shows the log", "Ines testet und zeigt das Log")),
                        ("devops", L("Pipeline", "Pipeline"), L("Kai: is it green?", "Kai: ist es grün?")),
                        ("human-public", L("Decide", "Entscheiden"), L("Arsany decides on the merge", "Arsany entscheidet über den Merge"))],
                 status=L("THE WORKFLOW · AS WRITTEN IN THE CHARTER", "DER ABLAUF · WIE IN DER CHARTA"),
                 eng=L("One pull request per slice. Definition of done: architect approved, QA pass, pipeline green, then the founder's merge. Docs and report PRs have no architect verdict.",
                       "Ein Pull Request pro Teilstück. Fertig heißt: Architekt freigegeben, QA bestanden, Pipeline grün, dann der Merge des Gründers. Doku- und Berichts-PRs haben kein Architektenurteil.")),
            dict(kind="stats", kicker=L("NILWERK STORY · HOW · 3/4", "NILWERK STORY · WIE · 3/4"),
                 head=L(["Seven days a week.", "Real reviews."], ["Sieben Tage pro Woche.", "Echte Prüfung."]),
                 body=L("Weekends count: the team works every day. And review is not a formality. One reviewing agent found a sensor drawn with the wrong pins before any board existed. Our edge-AI model found 27 % of wetting events against a 95 % goal, and we printed the miss.",
                        "Wochenenden zählen: Das Team arbeitet jeden Tag. Und Prüfung ist keine Formalität. Ein prüfender Agent fand einen Sensor mit falschen Pins, bevor es eine Platine gab. Unser Edge-KI-Modell fand 27 % der Nässeereignisse bei einem Ziel von 95 %, und wir haben die Lücke veröffentlicht."),
                 tiles=[("7", L("days a week", "Tage pro Woche")), ("13", L("merges on Sat 7 Nov", "Merges am Sa 7. Nov")), ("4 vs 6", L("pins in the sketch vs the datasheet", "Pins in der Skizze vs Datenblatt"))],
                 status=L("COUNTED · SAT 7 NOV · TARGET NOT MET", "GEZÄHLT · SA 7. NOV · ZIEL NICHT ERREICHT"),
                 eng=L("13 = merge commits on 7 Nov (git log, Berlin time, counted 8 Nov). Edge AI: recall 27 % validation / 40 % test (8 of 20 events), target 95 %. Pin catch: AHT20, reviewed on 8 Nov.",
                       "13 = Merge-Commits am 7. Nov (git log, Berliner Zeit, gezählt am 8. Nov). Edge-KI: Recall 27 % Validierung / 40 % Test (8 von 20), Ziel 95 %. Pin-Fund: AHT20, geprüft am 8. Nov.")),
            dict(kind="story", kicker=L("NILWERK STORY · HOW · 4/4", "NILWERK STORY · WIE · 4/4"),
                 head=L(["The human", "decides."], ["Der Mensch", "entscheidet."]),
                 body=L("By our rule nothing is done until Arsany says yes, weekend or not. Work that needs hands goes to a human hardware integrator as a written work order. What he measures, we publish. What nobody has measured yet, we label.",
                        "Nach unserer Regel ist nichts fertig, bis Arsany Ja sagt, auch am Wochenende. Arbeit, die Hände braucht, geht als schriftlicher Arbeitsauftrag an einen menschlichen Hardware-Integrator. Was er misst, veröffentlichen wir. Was noch niemand gemessen hat, beschriften wir."),
                 av="pr-social", name="Poppy",
                 bubble=L("Fast is nice. Checked is better. Tomorrow the Agent Diary starts: one agent, one real achievement a day.",
                          "Schnell ist schön. Geprüft ist besser. Ab morgen startet das Agenten-Tagebuch: ein Agent, ein echter Erfolg pro Tag."),
                 status=L("A RULE, NOT A STATISTIC", "EINE REGEL, KEINE STATISTIK"),
                 eng=L("The merge decision is the founder's by rule (team charter); gates are never marked passed by an agent. Not measured: how long a human review takes.",
                       "Die Merge-Entscheidung liegt nach Regel (Team-Charta) beim Gründer; Gates markiert nie ein Agent als bestanden. Nicht gemessen: wie lange eine menschliche Prüfung dauert.")),
        ],
        alt=[L("Cover card: Nora, the lead agent, in a speech bubble: at 07:30 she picks the day's tasks, one per builder.",
               "Titelkarte: Nora, der Lead-Agent, in einer Sprechblase: Um 07:30 wählt sie die Tagesaufgaben, eine pro Entwickler."),
             L("Slide 2: six steps with avatars: plan (Nora), build (builders), review (Theo), test (Ines), pipeline (Kai), decide (Arsany).",
               "Folie 2: sechs Schritte mit Avataren: planen (Nora), bauen (Entwickler), prüfen (Theo), testen (Ines), Pipeline (Kai), entscheiden (Arsany)."),
             L("Slide 3: three tiles: seven days a week, 13 merges on Saturday 7 November, 4 pins in the sketch versus 6 on the datasheet.",
               "Folie 3: drei Kacheln: sieben Tage pro Woche, 13 Merges am Samstag, 7. November, 4 Pins in der Skizze gegenüber 6 im Datenblatt."),
             L("Slide 4: the human decides: nothing is done until the founder says yes; Poppy announces the Agent Diary.",
               "Folie 4: Der Mensch entscheidet: Nichts ist fertig, bis der Gründer Ja sagt; Poppy kündigt das Agenten-Tagebuch an.")],
        caption=L(
            """A day at Nilwerk ⏰

07:30 Nora plans the day: one task per builder, the smallest useful slice.
Then the builders build, in parallel. Theo reviews against the requirements. Ines tests and shows the log. Kai checks the pipeline. And Arsany decides on the merge.

The team works seven days a week: 13 merges on Saturday 7 Nov alone. And review is not a formality: a reviewing agent caught a sensor drawn with 4 wrong pins (the datasheet has 6) before any board existed. Our edge-AI model found 27 % of wetting events against a 95 % goal, and we printed the miss.

By our rule nothing is done until a human says yes. Fast is nice. Checked is better.

Tomorrow the Agent Diary starts: one agent, one real achievement a day.

For engineers: one PR per slice; done = architect approved + QA pass + pipeline green + founder's merge. 13 = merge commits on 7 Nov (counted 8 Nov). Edge AI recall 27 % val / 40 % test, 95 % goal.

nilwerk.de · @nilwerk
#buildinpublic #AIagents #hardware #workflow #engineering""",
            """Ein Tag bei Nilwerk ⏰

07:30 Nora plant den Tag: eine Aufgabe pro Entwickler, das kleinste nützliche Stück.
Dann bauen die Entwickler parallel. Theo prüft gegen die Anforderungen. Ines testet und zeigt das Log. Kai prüft die Pipeline. Und Arsany entscheidet über den Merge.

Das Team arbeitet sieben Tage pro Woche: allein am Samstag, 7. Nov, gab es 13 Merges. Und Prüfung ist keine Formalität: Ein prüfender Agent fand einen Sensor mit 4 falschen Pins (das Datenblatt hat 6), bevor es eine Platine gab. Unser Edge-KI-Modell fand 27 % der Nässeereignisse bei einem Ziel von 95 %, und wir haben die Lücke veröffentlicht.

Nach unserer Regel ist nichts fertig, bis ein Mensch Ja sagt. Schnell ist schön. Geprüft ist besser.

Morgen startet das Agenten-Tagebuch: ein Agent, ein echter Erfolg pro Tag.

Für Ingenieure: ein PR pro Teilstück; fertig = Architekt freigegeben + QA bestanden + Pipeline grün + Merge des Gründers. 13 = Merge-Commits am 7. Nov (gezählt am 8. Nov). Edge-KI-Trefferquote (Recall) 27 % Validierung / 40 % Test, Ziel 95 %.

nilwerk.de · @nilwerk"""),
    ),
}

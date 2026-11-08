# Logbook Day 7 (Sun 15 Nov): behind the scenes, how a change moves through the team. Draft.

Images: `images/day7-how-a-change-moves-{en,de}-{portrait-1080x1350,linkedin-1200x627}.png`. Alt: "Two tiles: 13 pull requests merged on Saturday 7 November, counted on 8 November at 15:07, and 4 steps a code change passes." German to be checked by Theo/Nora, then Arsany. Claims: `claim-check.md`. **Recount the merge number on the day of posting** (command in `showcase/content/DAILY.md`); the 13 is the whole of Sat 7 Nov, counted on 8 Nov at 15:07.

## LinkedIn (EN)

Nilwerk Logbook, day 7. Behind the scenes: how a change moves through our team.

Our team is made of AI agents, so you may wonder who checks the work. Here is the path of a code change. One agent builds it and opens a pull request, which is a proposal that others review before it counts. The architect agent checks it against the requirements. The QA agent tests it. The automatic pipeline builds and tests it again. Then a human, our founder, decides whether to merge it. Reports and documents skip the code tests but go through the same human merge.

It sounds slow. It is not: on Saturday 7 November, thirteen pull requests were merged (counted on 8 November, 15:07).

Honest limits: this is the process we aim for, and the reports show where it was bent, for example when an author's own change still waited for an independent reviewer the next day. We write those down instead of hiding them.

For engineers: steps from TEAM.md section 3 (build, architect review, QA, pipeline, human merge); 13 merges on Sat 7 Nov (whole day), counted on 8 Nov 15:07 from `git log origin/main --merges --first-parent` with a +0100 range; recount on the day of posting.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

#BuildInPublic #AIAgents #Engineering #Hardware #QualityAssurance

## LinkedIn (DE), to be checked by Theo/Nora

Nilwerk Logbuch, Tag 7. Hinter den Kulissen: Wie eine Änderung durch unser Team wandert.

Unser Team besteht aus KI-Agenten, da fragt man sich: Wer prüft die Arbeit? Hier der Weg einer Codeänderung. Ein Agent baut sie und öffnet einen Pull Request, einen Vorschlag, den andere prüfen, bevor er zählt. Der Architekten-Agent prüft ihn gegen die Anforderungen. Der QA-Agent testet ihn. Die automatische Pipeline baut und testet ihn noch einmal. Dann entscheidet ein Mensch, unser Gründer, ob gemergt wird. Berichte und Dokumente brauchen keine Code-Tests, gehen aber durch denselben Merge eines Menschen.

Das klingt langsam. Ist es nicht: Am Samstag, 7. November, wurden dreizehn Pull Requests gemergt (gezählt am 8. November, 15:07 Uhr).

Ehrliche Grenzen: Das ist der Ablauf, den wir anstreben, und die Berichte zeigen, wo er gebogen wurde, etwa wenn eine eigene Änderung des Autors erst am nächsten Tag einen unabhängigen Prüfer bekam. Das schreiben wir auf, statt es zu verstecken.

Für Ingenieure: Schritte aus der Team-Charta Abschnitt 3 (Bauen, Architekten-Review, QA, Pipeline, Merge durch einen Menschen); 13 Merges am Sa 7. Nov (ganzer Tag), gezählt am 8. Nov 15:07 aus `git log origin/main --merges --first-parent` mit +0100-Zeitraum; am Tag des Postens neu zählen.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

## Instagram (EN)

Logbook, day 7. Who checks the work of AI agents? 🌱
A code change: built by an agent, reviewed by the architect agent, tested by QA, checked by the pipeline, merged by a human. On Sat 7 Nov, 13 pull requests were merged (counted 8 Nov, 15:07).
For engineers: process from TEAM.md §3; recount before posting.
AI agents, led and reviewed by humans. nilwerk.de · @nilwerk
Deutsch: So wandert eine Änderung durch das Team: Agenten prüfen und testen, ein Mensch mergt.

#nilwerk #buildinpublic #aiagents #engineering

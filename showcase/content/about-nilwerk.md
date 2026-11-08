# About Nilwerk: profile boilerplate (draft, corrected in the fix round of PR #51)

Two layers: plain first, "For engineers" second. Drafts for Arsany; German to be checked by Theo or Nora. Claim-check at the bottom. No prices, offers, customers or names other than the founder's.

## EN, about 50 words

Nilwerk builds connected hardware prototypes for startups and small companies. A team of AI agents does the design work; our founder leads it and, by our rule, decides on every merge. A human hardware integrator will assemble and test the first boards. We show our work with proof, currently one episode a day. nilwerk.de

For engineers: ESP32 firmware, PCB, 3D-printed enclosures, app and backend; every claim labelled measured, simulated or estimated.

## EN, about 100 words

Nilwerk builds connected hardware prototypes for startups and small companies: the device, the app and the cloud behind it, in one project. A team of AI agents does the design, firmware, app and test work. They are led and reviewed by humans: our founder decides on every merge, and a human hardware integrator will assemble and test the first real boards. Nothing counts as done without a human's yes.

We build in public. Currently, the Nilwerk Logbook shows one episode a day of what we built, decided or got wrong, with its source and an honest label: measured, simulated or estimated. Follow along at nilwerk.de and @nilwerk. Our own plant-monitor project is at prototype stage, not a product for sale.

For engineers: ESP32-C3 firmware (ESP-IDF), KiCad PCBs, CadQuery enclosures, React Native app; the Supabase backend is planned for an EU region (decision, not live; helper services may process pseudonymous data elsewhere).

## DE, etwa 50 Wörter

Nilwerk baut vernetzte Hardware-Prototypen für Startups und kleine Unternehmen. Ein Team aus KI-Agenten übernimmt die Entwicklungsarbeit; unser Gründer leitet es und entscheidet nach unserer Regel über jeden Merge. Ein Hardware-Integrator, ein Mensch, wird die ersten Platinen bestücken und testen. Wir zeigen unsere Arbeit mit Belegen, derzeit jeden Tag eine Folge. nilwerk.de

Für Ingenieure: ESP32-Firmware, Platinen, 3D-gedruckte Gehäuse, App und Backend; jede Aussage ist als gemessen, simuliert oder geschätzt beschriftet.

## DE, etwa 100 Wörter

Nilwerk baut vernetzte Hardware-Prototypen für Startups und kleine Unternehmen: das Gerät, die App und die Cloud dahinter in einem Projekt. Ein Team aus KI-Agenten übernimmt Entwurf, Firmware, App und Tests. Geleitet und geprüft werden sie von Menschen: Unser Gründer entscheidet über jeden Merge, und ein Hardware-Integrator, ein Mensch, wird die ersten echten Platinen bestücken und testen. Ohne das Ja eines Menschen gilt nichts als fertig.

Wir bauen öffentlich. Derzeit zeigt das Nilwerk Logbuch jeden Tag eine Folge: was wir gebaut, entschieden oder falsch gemacht haben, mit Quelle und ehrlicher Beschriftung: gemessen, simuliert oder geschätzt. Folgen Sie uns auf nilwerk.de und @nilwerk. Unser eigenes Pflanzensensor-Projekt ist im Prototypenstand, kein Produkt zum Verkauf.

Für Ingenieure: ESP32-C3-Firmware (ESP-IDF), KiCad-Platinen, CadQuery-Gehäuse, React-Native-App; das Supabase-Backend ist für eine EU-Region geplant (Entscheidung, nicht live; Hilfsdienste können pseudonyme Daten anderswo verarbeiten).

## Claim check

| # | Statement | Type | Source |
|---|---|---|---|
| 1 | Builds connected hardware prototypes for startups and small companies | D | nilwerk.de tagline "Hardware-Prototypen für Startups & KMU" (read 2026-11-07) |
| 2 | Device, app and cloud in one project | D | nilwerk.de ("Sechs Disziplinen, ein Gerät"); `team/TEAM.md` section 6 |
| 3 | Team of AI agents does design, firmware, app and test work | D | `team/PERSONAS.md`, TEAM.md section 2 |
| 4 | Founder leads; "decides on every merge" is the **rule** (TEAM.md §5), not an observed fact about each PR | D | TEAM.md sections 4-5 |
| 5 | A human hardware integrator **will** assemble and test the first boards (future: no real hardware built yet; stated as human, not "engineer", no name) | D | TEAM.md section 12; owner decision on names |
| 6 | "Currently one episode a day" (a plan, may change) | D | `showcase/content/series.md` (approved by Arsany) |
| 7 | Stack: ESP32-C3 + ESP-IDF, KiCad, CadQuery, React Native; Supabase backend **planned** for an EU region (decision, not live); helper services may process pseudonymous data elsewhere | D | TEAM.md section 6; ADR-003; `stack-and-costs.md` |
| 8 | "Our own plant-monitor project is at prototype stage, not a product for sale" | D | project status; the website says prototypes, no product claim |
| 9 | Customers/prices/offers not mentioned | n/a | on purpose |

Note: the website promises fixed prices; the boilerplate deliberately says nothing about prices.

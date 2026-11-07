# Logbook Day 4 (Thu 12 Nov): a decision. Draft.

Images: `images/day4-decision-data-in-the-eu-{en,de}-{portrait-1080x1350,linkedin-1200x627}.png` (dark theme). Alt: "Two tiles: data hosted in the EU, and three alternatives rejected. Status: decision, not yet live." German to be checked by Theo/Nora, then Arsany. Claims: `claim-check.md`.

## LinkedIn (EN)

Nilwerk Logbook, day 4. We decided where your plant's data lives: in the EU.

Our plant sensor sends its readings to a backend (the part of the system that stores the data behind the app). In week one we chose one platform for everything: accounts, data and the rules about who may see what, hosted in an EU region. We looked at the alternatives, among them Firebase and running our own server, and decided against them for now, because one platform in the EU is the simplest way to keep your data in Europe and to let you export or delete it.

Honest status: this is a decision, not a live system. So far the backend is tested on a local database only.

For engineers: Supabase (Postgres, row-level security, auth, edge functions), EU region; devices call an ingest function and never touch tables directly. Decision record ADR-003, dated 3 Nov 2026 (Accepted). Rejected: Firebase, Home Assistant as the hub, a dedicated server. Not yet verified on a real Supabase project.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

#BuildInPublic #DataPrivacy #IoT #Hardware #Supabase

## LinkedIn (DE), to be checked by Theo/Nora

Nilwerk Logbuch, Tag 4. Wir haben entschieden, wo die Daten deiner Pflanze liegen: in der EU.

Unser Pflanzensensor schickt seine Messwerte an ein Backend (der Teil des Systems, der die Daten hinter der App speichert). In Woche eins haben wir uns für eine Plattform für alles entschieden: Konten, Daten und die Regeln, wer was sehen darf, gehostet in einer EU-Region. Wir haben Alternativen angeschaut, darunter Firebase und einen eigenen Server, und uns vorerst dagegen entschieden, weil eine Plattform in der EU der einfachste Weg ist, deine Daten in Europa zu halten und dir Export und Löschung zu ermöglichen.

Ehrlicher Stand: Das ist eine Entscheidung, kein Live-System. Bisher ist das Backend nur auf einer lokalen Datenbank getestet.

Für Ingenieure: Supabase (Postgres, Row-Level-Security, Auth, Edge Functions), EU-Region; Geräte rufen eine Ingest-Funktion auf und greifen nie direkt auf Tabellen zu. Entscheidungsdokument ADR-003 vom 3. Nov 2026 (akzeptiert). Abgelehnt: Firebase, Home Assistant als Hub, ein eigener Server. Noch nicht auf einem echten Supabase-Projekt geprüft.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

## Instagram (EN)

Logbook, day 4. Where does your plant's data live? In the EU. 🌱
One platform, one EU region, with export and deletion as a requirement. A decision from week one, not a live system yet.
For engineers: Supabase EU, decision record of 3 Nov; tested on a local database only.
AI agents, led and reviewed by humans. nilwerk.de · @nilwerk
Deutsch: Die Daten der Pflanze liegen in der EU. Das ist eine Entscheidung, noch nicht live.

#nilwerk #buildinpublic #dataprivacy #iot

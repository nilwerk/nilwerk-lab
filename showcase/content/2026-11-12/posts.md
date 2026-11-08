# Logbook Day 4 (Thu 12 Nov): a decision. Draft.

Images: `images/day4-decision-data-in-the-eu-{en,de}-{portrait-1080x1350,linkedin-1200x627}.png` (dark theme). Alt: "Two tiles: database region EU (decided) and three alternatives rejected. Status: decision, not live, local test only." German to be checked by Theo/Nora, then Arsany. Claims: `claim-check.md`.

## LinkedIn (EN)

Nilwerk Logbook, day 4. A decision: our database is planned for an EU region.

Our plant sensor sends its readings to a backend (the part of the system that stores the data behind the app). In week one we chose one platform for accounts, readings and the rules about who may see what, with the database in an EU region. We rejected the alternatives, among them Firebase and a self-run server. Export and deletion of your data are requirements; they are not built yet.

Honest status: this is a decision, not a live system, and the backend was tested on a local database only. Some helper services (for example the AI service for care tips and the push-notification service) may process pseudonymous data outside the EU. We say so on purpose: "in the EU" would be only half the story.

For engineers: Supabase (Postgres, row-level security, auth, edge functions), EU region; devices call an ingest function and never touch tables directly. Decision record ADR-003, dated 3 Nov 2026 (Accepted). Rejected: Firebase, Home Assistant as the hub, a dedicated server. Not verified on a real Supabase project. Helper services: Claude API (processed outside the EU, pseudonymous id plus readings and city only), Expo push; see the stack and costs document.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

#BuildInPublic #DataPrivacy #IoT #Hardware #Supabase

## LinkedIn (DE), to be checked by Theo/Nora

Nilwerk Logbuch, Tag 4. Eine Entscheidung: Unsere Datenbank soll in einer EU-Region liegen.

Unser Pflanzensensor schickt seine Messwerte an ein Backend (der Teil des Systems, der die Daten hinter der App speichert). In Woche eins haben wir uns für eine Plattform entschieden, die Konten, Messwerte und die Regeln dafür verwaltet, wer was sehen darf. Die Datenbank soll in einer EU-Region liegen. Die Alternativen haben wir abgelehnt, darunter Firebase und einen selbst betriebenen Server. Export und Löschung deiner Daten sind Anforderungen; gebaut sind sie noch nicht.

Ehrlicher Stand: Das ist eine Entscheidung, kein Live-System, und das Backend wurde nur auf einer lokalen Datenbank getestet. Einige Hilfsdienste (zum Beispiel der KI-Dienst für Pflegetipps und der Dienst für Push-Benachrichtigungen) können pseudonyme Daten außerhalb der EU verarbeiten. Das sagen wir mit Absicht: „in der EU“ wäre nur die halbe Wahrheit.

Für Ingenieure: Supabase (Postgres, zeilenbasierte Zugriffskontrolle mit Row Level Security, Anmeldung, Edge Functions), EU-Region; Geräte rufen eine Funktion zur Datenannahme auf und greifen nie direkt auf Tabellen zu. Entscheidungsdokument ADR-003 vom 3. Nov 2026 (akzeptiert). Abgelehnt: Firebase, Home Assistant als Hub, ein eigener Server. Nicht auf einem echten Supabase-Projekt geprüft. Hilfsdienste: Claude-API (Verarbeitung außerhalb der EU, nur pseudonyme ID, Messwerte und Stadt), Expo-Push; siehe Dokument „Stack und Kosten“.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

## Instagram (EN)

Logbook, day 4. A decision: our database is planned for an EU region. 🌱
Export and deletion are requirements, not built yet. Not live, tested on a local database only. Helper services may process pseudonymous data outside the EU.
For engineers: Supabase EU region, decision record of 3 Nov.
AI agents, led and reviewed by humans. nilwerk.de · @nilwerk
Deutsch: Unsere Datenbank soll in einer EU-Region liegen. Entscheidung, noch nicht live.

#nilwerk #buildinpublic #dataprivacy #iot

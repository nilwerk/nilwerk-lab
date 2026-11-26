# Inspiration for social and app design, 26 Nov 2026

**Status: internal working note. Not a post, not for publishing.** The three angles below are candidates only. Each one carries the claim we may make and the real output that would have to show it. No new drafts here: the two drafts are in the open content-pack PR, and the approved one stays as it is.

## What the reference apps promise (plain words)

**Limit of this note.** The Google Play listing text did not come through the fetch route: both pages returned only the title and navigation, so the store descriptions were not read. What follows is taken from the titles and from the screenshots that were shared, and is marked as such.

- **Plantology (title: "Plant Care & ID").** From the title: it covers caring for plants and identifying them. The shared screenshots show a plant-care onboarding with one hero photo and one primary button, and a home with a plant-care overview. Promise as far as visible: a plant helper that identifies and looks after plants. Store description: not read.
- **Blossom (title: "Plant Identifier").** From the title: it identifies plants. The shared screenshots show a home with category chips, an overview card, a detail with a bottom sheet, and a light card detail with a seven-day chart and Good/Low labels. Promise as far as visible: know what a plant needs, at a glance. Store description: not read.

Both sell care through the same words: identify, care reminders, tips, growth tracking. Neither is visible in these screenshots as a sensor. That gap is ours to fill, but only with evidence.

## Principles taken from the screenshots (no images, text or logos reused)

- One hero, one primary action on onboarding.
- A status overview card first, then the detail; a bottom sheet for the detail of one plant.
- Good/Low labels next to a chart, so the state reads without the chart.
- Light cards on a calm background; category chips at the top.

The shared screenshots include a stock-style photo of a phone held over a pot. It is a third-party image and was not used for anything here.

## Three angles (each differs from what the reference apps say)

1. **"A sensor that tells you before the plant wilts."** The reference apps say reminders and identification. Our angle is a reading that arrives first, with the alert before the lowest moisture.
   - Claim allowed only with: a bench run in which the reading reaches the screen and a threshold alert fires before the lowest reading, on a real board, with calibrated air and water points.
   - Backing output that would be needed: the bench run log and a screen capture from that run.
   - Not yet verified: the bench run failed at the screen step on 25 Nov (the reading reached the cloud but not the screen within 900 s), and the calibration values are placeholders. The claim is not allowed today.

2. **"A missing day is a gap, not a zero."** The reference charts are not described in their listings. Ours: a day without a reading stays a gap in the line, so a missing sensor never looks like a dry plant.
   - Claim allowed only with: the chart shown on a phone with a day that has no reading, and the same chart against the live analytics endpoint.
   - Backing output: the app test output for the gap and empty-window cases, plus a phone screenshot.
   - Not yet verified: the chart is in review (not on main), its tests run on a mocked backend, it is not run on a phone or at phone width, and the analytics endpoint is not deployed.

3. **"Your data leaves with you."** The reference apps say nothing about data in what is shown. Ours: before an account can be deleted, the user can export their data first. The delete gate is merged; the photo part of the export is shown as not yet on main in the index.
   - Claim allowed only with: a test run of export-then-delete on the app and the backend, plus the photo part of the export.
   - Backing output: the export test output and the delete-gate test output from the merged work.
   - Not yet verified: the delete gate and export client are merged and tested on a PC; the photo part of the export is not yet on main; nothing has been run on a phone or against a live backend.

## Sources

- Google Play listing, Plantology (fetched 26 Nov 2026): title only, description not read.
- Google Play listing, Blossom (fetched 26 Nov 2026): title only, description not read.
- Four screenshots shared by the coordinator, read from the local image files in the session folder; third-party, principles only.
- Bench status: `team/reports/2026-11-25.md`, "Bench, latest run".
- Chart status: the open change's item caption (not on main at check time).
- Export and delete gate: `showcase/INDEX.md`, rows for the 17 Nov export and delete-gate items (merged).
- Calibration placeholder: `team/reports/2026-11-25.md`, "Bench, latest run".

## Open before any of these becomes a post
- Read both store descriptions (the fetch route gave titles only); redo the "what they promise" lines if the descriptions change them.
- Each angle needs its backing output first; a claim without it is not written.
- Owner approval through the usual Needs Arsany row, German check, recount on posting day.

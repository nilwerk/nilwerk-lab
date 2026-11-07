# Slide templates (customer demos and presentations), v0.1 brand, proposal

Six 16:9 templates, 1920x1080, for both audiences: every content slide has the plain layer first and the "FOR ENGINEERS" layer second (brand-kit §5b). No external service is needed.

| Slide | Use | Plain layer | Engineers layer |
|---|---|---|---|
| 1 title | opening | title in 3 lines, 2-line subtitle | meta line in the footer |
| 2 section | divider | big number + section name + one plain sentence | stack / source lines |
| 3 key number | one proof number | headline + 2 plain sentences | source and caveat lines + honesty chip |
| 4 two column | explain a topic | "IN PLAIN WORDS" 4 short sentences | "FOR ENGINEERS" 5 mono lines + chip |
| 5 architecture | diagram frame | one plain caption | source line, diagram status chip |
| 6 closing | next step | thank you, next step, contact | (none) |

## Files

- `templates/slide-*.svg`: editable templates with `{{PLACEHOLDERS}}`; colours are `var(--nw-*)` tokens (resolved by `../build_extra.py`).
- `png/*.png`: rendered samples with placeholder text (light, and dark for title and closing).
- `png-clean/*.png`: art only (logo, grid, hairlines, cards), **no text**: use these as slide backgrounds.
- Rebuild: `python3 -I ../make_extra_templates.py && NW_FONT_DIR=<node_modules>/@fontsource python3 -I ../build_extra.py`.

## Google Slides (or PowerPoint / Keynote): editable slides without extra tools

1. New presentation, page size **Widescreen 16:9** (Google default, 10 x 5.625 in = 720 x 405 pt; 1 px of the 1920 px images = 0.375 pt).
2. Fonts: Google Slides already has **Space Grotesk, Inter, JetBrains Mono** (Font menu, "More fonts"). In PowerPoint/Keynote install them from fonts.google.com (OFL) or from `../web/fonts`.
3. Per slide: Slide > Change background > Image > upload the matching file from `png-clean/` (light or dark). Then add text boxes with the specs below. Keep the textboxes left-aligned, no autofit, line spacing 1.0 for headings, 1.15 for body.
4. Save the finished deck as your own template (copy it per customer). Replace placeholders with real content only; sample texts are not claims.

Text box specs (position of the top-left corner and size in px of the 1920 x 1080 grid; multiply by 0.375 for pt). Colours: ink `#15181D`, muted `#5B616B`, accent `#0F7A5C`, warn `#B4541A` (dark theme: `#ECEBE7`, `#A2A7AF`, `#3FC79A`, `#E58A4F`).

| Element | Font, weight, size | Colour |
|---|---|---|
| Title lines (slide 1), x 120 | Space Grotesk 700, 150 px = 56 pt, tight line spacing | ink, last line accent |
| Subtitle (1), closing sub (6) | Inter 400, 42 px = 16 pt | muted |
| Section number (2), x 110 y 300 | JetBrains Mono 600, 380 px = 143 pt | accent |
| Slide heading (3-5), x 120 y 130 | Space Grotesk 700, 76-84 px = 28-32 pt | ink |
| Body sentences (4 left, 2, 5) | Inter 400, 38-40 px = 14-15 pt | ink or muted |
| Key number (3), inside the card | Space Grotesk 700, 220 px = 83 pt | ink |
| "FOR ENGINEERS" label and lines | JetBrains Mono 600 / 400, 24-26 px = 9-10 pt, label letter-spacing +1.5 | accent / muted |
| Status chip text | JetBrains Mono 600, 26 px = 10 pt, in a rounded rectangle with 2 px warn outline | warn |
| Footer left/right | JetBrains Mono 400, 22 px = 8 pt | muted |

## Rules for demo decks

- Plain words first on each slide; engineers' layer second, always marked. One idea per slide.
- Every number: measured, calculated, simulated or estimated, shown with the chip; sources in the engineers' layer or speaker notes.
- No prices, offers, customer names or lead information in a shared template; the closing slide carries only public handles (nilwerk.de, @nilwerk) and a contact address you fill in per deck.
- AI imagery (if any) is labelled "AI-generated image"; diagrams are exported from Mermaid / draw.io (code-generated, no label needed).

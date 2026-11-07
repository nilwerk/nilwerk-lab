# Nilwerk brand kit v0.1 (PROPOSAL, pending Arsany's approval)

Author: Poppy (PR & Social) · 2026-11-07 · task PR-2026-11-07 · status: **draft, nothing here is approved until Arsany says so**.

Arsany's brief: "we have no company template, colours or fonts yet; daily content should be high quality, realistic and engaging."

## 1. What already exists (found) and what I chose

| Where | What I found |
|---|---|
| Website nilwerk.de (public page source, read 2026-11-07) | A complete, consistent visual system already ships on the live site: warm paper background `#f6f4ef`, ink `#15181d`, accent green `#0f7a5c` (light) / `#3fc79a` (dark), warning orange `#b4541a` / `#e58a4f`, a dark theme, headings in **Space Grotesk 700**, body in **Inter**, labels in **JetBrains Mono**; logo = a rounded dark plate with a green "N" drawn as a PCB trace (two solder-pad dots) and a thin light-blue wave underneath, wordmark `nil` + green `werk` in Space Grotesk 700. Tagline: "Ihr vernetzter Prototyp. Komplett. Zum Festpreis." Voice: formal German "Sie", short and confident. The privacy text says the site loads no external fonts (so the website self-hosts them). |
| Repo `team/avatars/*.svg` | Persona avatars with their own accent colours (Poppy's is pink `#d6457a`). These are team-persona colours, not company colours. |
| Repo README | No brand information. |
| `showcase/stories/origin/` (Poppy's origin carousel, 2026-11-05) | Used a different look: near-black green `#0f1e18`, red-pink `#d83a4c`, fonts Bricolage Grotesque / Instrument Sans / JetBrains Mono. **This does not match the website.** |

**Chosen:** adopt the website's system as the company brand (one source, zero new inventions), rename the tokens `--nw-*`, add a proper type scale and post templates. The origin carousel is off-brand; if you approve this kit I will re-render it in the new templates (proposal, not done yet).

Why not invent something new: a second look next to the website would make Nilwerk look like two companies; the existing one is already distinctive (PCB-trace motif, warm paper, mono labels) and passes accessibility (below).

## 2. Logo

Files: `logo/nilwerk-mark.svg` (mark only). The lockup (mark + wordmark) is built into every template.

- **Mark:** dark plate `#15181d`, green trace "N", two pads, light-blue wave. Always on its own dark plate, on light and dark backgrounds alike (the plate is part of the mark).
- **Wordmark:** `nil` in ink + `werk` in accent, Space Grotesk 700, letter-spacing -0.03 em, always lowercase. Never "NilWerk" or "NILWERK".
- **Clear space:** at least half the mark's height on all sides. **Minimum size:** mark 24 px, lockup 96 px wide.
- **Don't:** recolour the trace, stretch, rotate, add shadows or outlines, place the mark on busy photos, use the wave in light blue as text colour.
- Avatars/profile picture on Instagram and LinkedIn: the mark on its plate, centred, plate filling the circle crop with at least 12 % padding.

## 3. Colour palette (PROPOSAL)

Tokens live in `brand.css`. Contrast ratios are computed (WCAG 2.x relative luminance) by `check_contrast.py`, which reads the tokens from `brand.css`; rerun after any change. AA = 4.5:1 for normal text, 3:1 for large text and UI.

| Token | Light | Dark | Use |
|---|---|---|---|
| `bg` | `#f6f4ef` | `#101317` | page / post background |
| `surface` | `#ffffff` | `#181c22` | cards, tiles |
| `ink` | `#15181d` | `#ecebe7` | headlines, body |
| `muted` | `#5b616b` | `#a2a7af` | secondary text, sources |
| `line` | `#e2ded5` | `#2a3038` | hairlines, grid (decorative) |
| `accent` | `#0f7a5c` | `#3fc79a` | brand colour, key words, proof tiles |
| `accent-ink` | `#ffffff` | `#0c1512` | text on accent fills |
| `accent-soft` | `#e3f2ec` | `#16302a` | chips, highlights |
| `warn` | `#b4541a` | `#e58a4f` | caveats: "estimated", "not yet measured", "before" |
| `signal` | `#8fd9ff` | same | the logo wave only, never text |

Contrast (computed with `check_contrast.py`; run `python3 -I check_contrast.py` to reproduce):

| Pair | Light | Dark | AA |
|---|---|---|---|
| ink on bg | 16.19 | 15.61 | pass (also AAA) |
| ink on surface | 17.79 | 14.33 | pass |
| muted on bg | 5.67 | 7.70 | pass |
| muted on surface | 6.24 | 7.07 | pass |
| accent on bg | 4.83 | 8.73 | pass |
| accent on surface | 5.30 | 8.02 | pass |
| accent-ink on accent | 5.30 | 8.70 | pass |
| accent on accent-soft | 4.59 | 6.61 | pass |
| warn on bg | 4.52 | 7.17 | pass (light is close to the limit: use `warn` only at 15 px+ and semibold, or on `surface` 4.97) |
| warn on surface | 4.97 | 6.58 | pass |
| signal on bg (decorative) | 1.41 | 12.01 | not for text; used only on the dark logo plate |

Rules: accent green is for emphasis and proof, never for large background floods; `warn` always means "read the caveat"; at most 3 colours per post besides ink and background.

## 4. Fonts (PROPOSAL), all Google Fonts, SIL Open Font License 1.1 (free for commercial use, self-hosting allowed)

| Role | Font | Weights | Fallback stack |
|---|---|---|---|
| Display / headlines / big numbers | **Space Grotesk** | 500, 700 | `Inter, system-ui, sans-serif` |
| Body / captions / UI | **Inter** | 400, 600 | `system-ui, -apple-system, "Segoe UI", sans-serif` |
| Labels, sources, IDs, code | **JetBrains Mono** | 400, 600 | `ui-monospace, Menlo, Consolas, monospace` |

Three fonts is the ceiling. Mono is only for short labels, sources and IDs (it signals "this is a measured/sourced fact"). Self-host the woff2 files on nilwerk.de (the site promises no external fonts); for social images the text is baked into the PNG. German umlauts and ß are in all three (latin subset).
Type scale for posts (1080 px wide): headline 80-92 px, tile number 92-100 px, body 34 px, label 22-24 px mono. Minimum text size on a 1080 px image: 20 px (about 7 pt on a phone).
Canva note: Space Grotesk, Inter and JetBrains Mono are in Canva's library; the SVG templates keep real text so they can be opened in Canva, Figma or Inkscape.

## 5. Voice rules

- **English posts:** warm, playful British English (Poppy), short punchy lines, numbers with source and date. One exclamation mark at most per post, emoji at most 2.
- **German posts and nilwerk.de:** plain, correct German, "Sie" on the site and in company posts; sober, no Denglisch where a German word exists (Prüfung statt Review is fine, "Pull Request" stays). A native speaker (Theo/Nora, then Arsany) checks every German text before it is used.
- **Structure:** artefact first, number second, process third. One finished thing per post.
- **Always honest about the humans:** "AI agents, led and reviewed by Arsany". Hardware work is done by a human engineer (name only with his OK; until then "our hardware integrator").
- **Words to avoid:** first, best, fastest, revolutionary, "X times faster", "autonomous", "guaranteed", anything that hints nobody checks the work. Never "will" for things not yet built.
- **Numbers:** measured vs calculated vs simulated vs estimated is always visible (the status chip in the templates). Human-equivalent hours are always "estimated".

## 5b. Audiences and the two-layer post (owner request 2026-11-07)

Every post serves two audiences at once; the **layers** let each one take what it needs.

| | **A: non-technical** | **B: technical** |
|---|---|---|
| Who | Founders, SME owners, plant lovers, buyers of hardware projects | Engineers, CTOs, makers |
| Cares about | Does it work, can I trust it, what does it mean for me, who checks it | Numbers, formulas, how it was verified, what is still unmeasured |
| Tone | Warm, plain, one idea per post, benefit first | Precise, sourced, no hype |
| Vocabulary | Plain words; any term of art gets a one-line explanation (see `glossary.md`); no acronym without its meaning | Exact terms, units, formulas, test names, evidence links |
| Proof | A single number and a before/after picture | The same number plus method, source file and caveats |

**Two-layer pattern (every post, every format):**
1. **Layer 1, plain story (leads):** headline + two plain sentences: what happened and why it matters. In images: headline and the two-line intro under it. In text: the first 2-3 short paragraphs. Anyone should be able to stop here and still know the point.
2. **Layer 2, "For engineers" (marked):** the numbers, formula, how it was checked, and what is still unmeasured or stubbed. In images: the mono block labelled FOR ENGINEERS (two lines) plus the status chip. In text: a paragraph starting "For engineers:" (DE: "Für Ingenieure:"). Sources and caveats live here, never hidden.
3. **Lead layer per slot:** the calendar says which audience leads (A, B or both); the other layer still appears, but second.
4. Honesty chip and the human-review line (`AI agents, led and reviewed by humans`) appear in both layers' posts. This exact phrase is the one wording used everywhere; German: "KI-Agenten, geleitet und geprüft von Menschen".

## 6. Do / Don't

| Do | Don't |
|---|---|
| Show the real artefact: render, plot, test output, CI result | Mock-ups presented as results |
| Say what is not yet verified, in the image | Hide the caveat in a comment |
| Use the status chip (`MEASURED`, `CALCULATED`, `SIMULATED`, `ESTIMATED`) | Mix measured and simulated numbers in one tile |
| Credit the review step (Theo, Ines, Kai) | Imply agents work unsupervised |
| Link nilwerk.de, tag @nilwerk | Link private repos, show repo URLs or PR numbers on images |
| Use roles ("our hardware integrator") | Use names, faces or voices without their OK |
| Use own visuals and own text | Stock photos, other companies' logos, unlicensed music |
| Keep prices, offers, customers, leads, open questions out | Anything from the sales tracker, emails or the Needs-Arsany list |

## 7. AI-imagery labelling

- **Code-generated** images (these templates, matplotlib/CadQuery renders, screenshots, test output) are **not** AI imagery: no flag, but the caption names the source.
- **Any image or video made by an AI image/video model** must (a) carry the platform's AI flag (Instagram `isAiGenerated: true`, LinkedIn "AI-generated content" label where offered) and (b) say "AI-generated image" in the caption. Never use AI imagery to show a real product, board, test result or person.
- Poppy's own illustrated avatar is a drawing, not a photo; it never stands in for a real person.

## 6b. Claim-check rules (UWG §5, checked before every draft goes to Arsany)

1. Every number, date and name in the text and the image has a row in that post's `claim-check.md` with a source (file/PR/Agent Log date) and a type: measured, calculated, simulated, estimated, or decision.
2. No superlatives or comparisons ("first", "best", "X times faster") without independent proof; human-hour figures only as "about N h (estimated)".
3. Say what is **not** yet verified in the caption (e.g. "tested locally, not yet on the live system", "calculated, not yet bench-tested").
4. Describe hardware as a prototype in development; never imply a product is for sale or available. No prices, offers, delivery dates or customer references.
5. Technical statements are checked by Theo; German text by Theo/Nora and then Arsany; Arsany approves and publishes. Agents draft only.
6. When in doubt, cut the claim.

## 8. Templates

`templates/` has three SVGs with `{{PLACEHOLDERS}}`: `post-portrait-1080x1350.svg` (Instagram 4:5), `post-linkedin-1200x627.svg`, `post-square-1080x1080.svg`. Layout: logo, kicker chip, 3-line headline (last line accent), **plain 2-line intro (layer 1)**, two evidence tiles (label, big number, 3 lines), status chip, **FOR ENGINEERS block with two source/caveat lines (layer 2)**, footer with handle and the human-review line. Plain glossary: `glossary.md`. `build_post.py` fills them, resolves the tokens for light or dark and renders PNG (Chromium via Playwright at 2x). `previews/` shows all three in light and dark with placeholder text (viewed: text fits, contrast fine). Limits: headline ≤ 19 characters per line (portrait), label ≤ 24 characters, tile number ≤ 7 characters, sub-lines ≤ 26 characters; `build_post.py` warns on long headlines, always look at the render.
Rebuild: `NW_FONT_DIR=<node_modules/@fontsource> python3 -I build_post.py --previews previews` (needs `npm i @fontsource/space-grotesk @fontsource/inter @fontsource/jetbrains-mono`).

## 9. Approval needed

Also for approval: the audience split and the two-layer pattern (section 5b).

Palette, fonts and logo usage are proposals: see the Needs-Arsany rows in Poppy's result. Until approved, treat this as v0.1 for drafts only.

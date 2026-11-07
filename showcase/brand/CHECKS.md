# Brand checks (run before every commit that touches `showcase/brand` or `showcase/content`)

Run from `showcase/brand` unless noted. All commands must succeed (exit 0).

| # | Check | Command | Expected |
|---|---|---|---|
| 1 | Palette contrast (WCAG AA) | `python3 -I check_contrast.py` | exit 0 |
| 2 | Status colours contrast (text on bg, surface, own soft background) | `python3 -I check_status_contrast.py` | exit 0 |
| 3 | Well-formed XML for all SVG templates and outputs | `python3 -I check_svg_wellformed.py` (same as `xmllint --noout <file>` for each svg, where xmllint is installed) | "0 not well-formed" |
| 4 | App theme type-checks | `cd app && tsc -p tsconfig.json` (TypeScript 6.x, strict, noEmit) | exit 0 |
| 5 | Adaptive icon is real RGBA | `python3 -I app/check_adaptive_icon.py` | colour type 6, corner alpha 0, exit 0 |
| 6 | Generated files are up to date | regenerate, then `git status` shows no unexpected changes: `python3 -I make_extra_templates.py`; `NW_FONT_DIR=<node_modules>/@fontsource python3 -I build_post.py --previews previews`; `python3 -I build_extra.py`; `cd app && python3 -I make_app_assets.py`; `cd web && node render_previews.js`; for posts `cd ../content/<date> && python3 -I build_images.py` | working tree clean (or only intended changes) |
| 7 | Look at the renders | open at least one slide, one post, the component sample and the icon/splash PNGs; no overflow, no clipped text | by eye |
| 8 | Claims | every number in a post has a row in that day's `claim-check.md` | by review |

Notes: fonts for rendering come from `@fontsource` (`npm i @fontsource/space-grotesk @fontsource/inter @fontsource/jetbrains-mono`); rendering uses Node playwright (`NODE_PATH` must contain it). SVG templates keep `{{PLACEHOLDERS}}` and must not contain a double hyphen inside an XML comment (invalid XML): write "nw tokens", not "var(--nw-*)", in comments.

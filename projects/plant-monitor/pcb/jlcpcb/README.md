# JLCPCB order package: plant-monitor, Plan 4.P4 prep (dry run)

> **STATUS: DRAFT. NOT A RELEASE. NOT ORDERED.**
> Routing is **not done**: the board has 0 tracks. **<!-- gen:footprints -->3<!-- /gen:footprints --> distinct footprints are placeholders** (pad geometry not from the manufacturer drawings). **4 of the 5 simulations are not run.** The Gerbers here come from an **unrouted** board and are **not a release**. Gate **4.P3 (review) is Arsany's and comes first**. Nothing was logged in to JLCPCB, uploaded, ordered or paid. The package is for Arsany to review and submit himself.

Owner: Emil (PCB designer). Branch `agent/pcb/4.P2-s2`, PR #80 (4.P2 panel). PR #84 (`agent/pcb/4.P2-s3`) is stacked on it: **merge #80 first, then #84.**

Units: the JLC order unit is the **panel**, 2 boards per panel (`panel.py` N_BOARDS). Stock is checked for <!-- gen:stock_panels -->3<!-- /gen:stock_panels --> panels = <!-- gen:stock_boards -->6<!-- /gen:stock_boards --> boards. The number of panels is Arsany's choice.

## What is ready

| Item | File | Basis |
|---|---|---|
| **SUPERSEDED 2026-11-13 by `../gerber/`, do not order from it.** Gerber + drill set (<!-- gen:gerber_files -->22<!-- /gen:gerber_files --> files, 2 layers, Edge.Cuts, drill tools <!-- gen:drill_tools -->0.30, 0.60, 0.65 mm<!-- /gen:drill_tools -->, <!-- gen:drill_round -->18<!-- /gen:drill_round --> round holes, <!-- gen:drill_slots -->4<!-- /gen:drill_slots --> slots) | `gerbers/plant-monitor-gerber.zip` | copied from the CI `pcb-fab` artifact of run 42772372983 (job `pcb`, head `8ad6122`). Content check by the generator: <!-- gen:gerber_match -->22 of 22<!-- /gen:gerber_match --> files match the artifact file of the same name (<!-- gen:package_date -->2026-11-12<!-- /gen:package_date -->). The zip is a container, so it is not byte-identical to the artifact. Not re-exported locally, KiCad is not in the agent session |
| Assembly BOM in JLCPCB format (<!-- gen:bom_lines -->27<!-- /gen:bom_lines --> lines, <!-- gen:bom_parts -->45<!-- /gen:bom_parts --> parts, LCSC Part # on every line) | `bom-jlc.csv` | generated from `pcb/bom.csv` |
| Pick-and-place, <!-- gen:cpl_parts -->45<!-- /gen:cpl_parts --> parts, all top | `cpl-jlc.csv` | generated from the CI `cpl.csv`; positions match the board file (Y sign as KiCad position file) |
| BOM with LCSC stock, JLC stock, lifecycle, price breaks, cost at 3 / 6 / 1000 boards | `bom-lcsc.csv` | LCSC product API and JLC parts search, read 2026-11-09 by `hardware/bom/refresh_live.py` (stock snapshot, not re-read) |
| Dry-run checklist, <!-- gen:items -->40<!-- /gen:items --> items, each with a JLCPCB limit, its source and a result | `dry-run-checklist.md` | JLCPCB capability page, read <!-- gen:package_date -->2026-11-12<!-- /gen:package_date --> |
| Cart list (what Arsany would click), marked NOT ORDERED | `cart-list.md` | generated |
| Hashes of all of the above | `MANIFEST.sha256` | |

Repo checks pass with `/usr/bin/python3 -I`: `check_layout.py` <!-- gen:layout_pass -->21<!-- /gen:layout_pass --> PASS, 0 FAIL, `check_netlist.py` all PASS.

## What is blocked

Checklist results: <!-- gen:result -->**4 FAIL, 12 OPEN or UNVERIFIED, 20 PASS** (of 40 items)<!-- /gen:result --> (`dry-run-checklist.md`, result line).

| Blocker | Why it blocks | Checklist |
|---|---|---|
| Routing (0 tracks, GND zone not filled) | no release, no order | R1, F7, F22 |
| Panel Gerber/drill set (rails, SMT tooling holes, fiducials) | the 2-board panel is designed in `panel/panel.dxf` (panel.py checks pass), but no panel Gerber exists yet; the single-board Gerber has no tooling holes or fiducials; J1 edge overhang in the panel is not verified | F5, F6 |
| <!-- gen:footprints -->3<!-- /gen:footprints --> placeholder footprints (<!-- gen:footprint_names -->E1 soil probe copper (own copper, no LCSC, not in CPL; size depends on Q5); U5 AHT20 DFN-6; U6 BH1750 WSOF-6<!-- /gen:footprint_names -->) | PCBA needs the drawn footprint; pad geometry is not from the drawings. U1, J1, J2, SW1-SW3 are real footprints since slice 2 | A9 |
| 4 simulations not run (divider, soil front end, charger thresholds, USB inrush) | release gate (4.P1 list) | R2 |
| Gate 4.P3 review | Arsany's gate, first | R3 |
| Enclosure inputs Q1-Q11 | the outline is still a proposal | R4 |

## What is unverified (needs JLCPCB's order pages or a physical check)

- CPL rotation per JLC library part and the CPL origin: the file matches the board file, but JLC's CAM preview must confirm both (A10, F23).
- JLC fab, PCBA labour, stencil and Extended-part fees (A7, A8). The cost table is LCSC catalogue price only.
- Price-break rows below their first LCSC break: <!-- gen:price_flags_n -->37<!-- /gen:price_flags_n --> line-quantity pairs use the first break (A7).
- LCSC stock is short for <!-- gen:lcsc_short -->C15849, C14663<!-- /gen:lcsc_short --> at the stock-check quantity while JLC stock is large (A6). JLC PCBA uses JLC stock (A5, pass).
- Vias: <!-- gen:vias -->16<!-- /gen:vias --> vias are outside the SMD pads (F12 PASS). The alternative, vias in pad with filled and capped vias, is not priced (UNVERIFIED).
- The LiPo cell (not in the JLC BOM, bought by Arsany): price, seller, stock and plug pitch and polarity unverified (A-034, A-053).
- Via pad 0.70 mm on 0.30 mm drill gives a 0.20 mm annular ring: JLC's minimum; the 0.25 mm recommendation is not met (F11, a NOTE).
- Panel fiducial mask opening (2 mm) and tooling-hole position (3.0 mm from the panel edge) are `[mine]`, not on the JLC page (F6).

## How it was generated

```
# 1. CI pcb-fab artifact of the board head (used for this package: head 8ad6122, run 42772372983)
gh run download 42772372983 -R nilwerk/nilwerk-lab -n pcb-fab -D <dir>
# 2. live LCSC / JLC data (writes hardware/bom/bom-draft.csv)
/usr/bin/python3 -I hardware/bom/refresh_live.py
# 3. package (nothing uploaded)
/usr/bin/python3 -I projects/plant-monitor/pcb/jlcpcb/make_jlcpcb_package.py --fab-dir <dir> --ci-head 8ad6122 --ci-run 42772372983
```

Step 3 reads the board file, `bom.csv`, the bom-draft snapshot and the CI export, and runs the two repo checks. It writes every file in this folder, and it fills the counts between the `gen:` markers in this README. Nothing here is hand-edited.

## Sources

- JLCPCB PCB capabilities: https://jlcpcb.com/capabilities/pcb-capabilities (read <!-- gen:package_date -->2026-11-12<!-- /gen:package_date -->). Re-check on the order day.
- LCSC product API `wmsc.lcsc.com` and product pages (stock, price breaks, product cycle), read 2026-11-09 20:17Z.
- JLC parts search API (JLC stock, Basic or Extended), read the same time.

## Next steps (not for this PR)

1. Route the board (next 4.P2 slice), revert the `unconnected_items` downgrade, fill the GND zone.
2. Draw the <!-- gen:footprints -->3<!-- /gen:footprints --> footprints from the manufacturer drawings (U5, U6, E1); then set `pin_verified` back to true where it holds.
3. Generate the panel Gerber/drill set (rails, tooling holes, fiducials) from `panel/panel.dxf` in CI, or with the JLC panelizer; verify the J1 edge overhang; decide the via-in-pad option.
4. Run the remaining 4 simulations.
5. Gate 4.P3 (Arsany), then the order is prepared again with new files and the cart list updated.

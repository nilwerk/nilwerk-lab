# PCB skills assessment (Emil, PCB Designer, 2026-11-12)

Task A of the EXTRA round (Arsany, 2026-11-12). Scope: the seven names Arsany gave (`bom`, `datasheets`, `emc`, `jlcpcb`, `kicad`, `kicad-tools`, `lcsc`), the official tools they wrap, and the source of each.

**How it was checked.** Searched with WebSearch (5 queries) and read one page with WebFetch (JLCPCB naming). The repositories were cloned read-only with `git clone --depth 1` into a scratch folder (not the repo, not installed, no script run). Only files actually opened are cited below. Anything not opened is marked UNVERIFIED. No credential was added, no package was installed globally, and no skill script was executed.

**Decision meanings.** USE as reference = the guidance text may inform our work; nothing is run. USE after review = read the named scripts first, then run them locally in a scratch venv; no API key. REJECT = not used.

## Skills found for the seven names

| Name | Source (repo / path) | Commit · date | Licence | What it does | Needs | Decision | Reason |
|---|---|---|---|---|---|---|---|
| `jlcpcb` | https://github.com/aklofas/kicad-happy · `skills/jlcpcb/SKILL.md` | 7d9d4d9 · 2026-11-06 | MIT (repo `LICENSE`, 2025, A. Klofas) | JLC assembly and fab guidance: basic vs extended parts, BOM/CPL formats, ordering workflow. SKILL.md only, no scripts. | Nothing | **USE as reference** | Guidance only, nothing runs. The fee and capability figures change over time, so each one is checked on the JLC page before use (we did that for the 4.P2 checklist). |
| `bom` | https://github.com/aklofas/kicad-happy · `skills/bom/` | 7d9d4d9 | MIT | Schematic BOM: `bom_manager.py` (analyze/export/order), `edit_properties.py` (writes symbol fields, only with `--write`), `translate_bom_pnp.py` (JLC BOM and CPL translation), `sync_datasheet_urls.py`. | Python 3; calls other distributor skills for sourcing | **USE after review** | Its JLC BOM/CPL translation could replace our hand-made `jlcpcb/bom-jlc.csv`. Before any use, read `translate_bom_pnp.py` and `edit_properties.py`: the second one writes into `.kicad_sch`. **UNVERIFIED:** scripts not read yet. |
| `lcsc` | https://github.com/aklofas/kicad-happy · `skills/lcsc/` | 7d9d4d9 | MIT | Part search, stock and price by LCSC `Cxxxxx`, datasheet download. | No key. Calls `jlcsearch.tscircuit.com` (a third-party community API) and `wmsc.lcsc.com` (LCSC CDN) | **USE after review** | No key needed, and the JLC/LCSC stock is what rule 1 of the PCB playbook asks for. But stock from a third-party mirror is UNVERIFIED until it is checked against LCSC's own page. |
| `datasheets` | https://github.com/aklofas/kicad-happy · `skills/datasheets/` | 7d9d4d9 | MIT | PDF to structured spec extraction, per-project cache, dispatch to subagents. Downloads with a cascade (requests, urllib, Playwright) and runs `subprocess` for page selection. | Python; optional Playwright; network to any manufacturer host | **REJECT** (for now) | Its download path reaches arbitrary manufacturer hosts and can drive a headless browser; too broad to review in one round, and the 4.P2 package does not need extraction. Revisit for the 4.P1 datasheet checks, with the subprocess and download code read first. |
| `emc` | https://github.com/aklofas/kicad-happy · `skills/emc/` | 7d9d4d9 | MIT | EMC pre-compliance risk report for a KiCad PCB: 44 rule IDs (ground planes, decoupling, I/O filters, clock routing, board-edge radiation, PDN impedance). Optional ngspice runs (`emc_spice.py`). | Python; optional ngspice | **USE after review** | Fits the "simulate the worst case" question for 4.P3 and the antenna keep-out. It is a risk screen, not a certification (FCC/CISPR are not claimed). Review `emc_spice.py` (subprocess) before running. **UNVERIFIED:** rule correctness not checked against the standards. |
| `kicad` | https://github.com/aklofas/kicad-happy · `skills/kicad/` | 7d9d4d9 | MIT | Analysis of KiCad 5 to 10 projects, PCB and Gerber: `analyze_pcb.py`, `analyze_gerbers.py`, `fab_release_gate.py`, DRC/DFM, net tracing. About 100 Python files. | Python; `lifecycle_engine.py` reads DigiKey, Mouser and element14 keys from environment variables **only if set** | **USE after review** | A second, independent reader of our Gerber set would help: `analyze_gerbers.py` could be compared with `verify_gerber.py`. Review `lifecycle_engine.py` first and never set the distributor keys. Too large to review fully in this round. **UNVERIFIED:** not run. |
| `kicad-tools` (Python package, not a skill) | https://github.com/rjwalters/kicad-tools (cloned at 3cef944, 2026-11-12, MIT, `LICENSE`); https://pypi.org/project/kicad-tools/ (0.29.0, released 2026-11-10, licence field empty on PyPI) | 3cef944 | MIT (repo); PyPI metadata has none | A Python library and CLI for parsing and editing KiCad files; its `.claude` and `.agents` skills are for maintaining that repo, not for PCB design. Includes a JLCPCB upload path (`src/kicad_tools/manufacturers/jlc_upload.py`) that uses the user's own API key. | Python 3.10+; `kicad-cli` for ERC/DRC | **REJECT** | There is no PCB skill named `kicad-tools`. The upload module can submit orders to JLCPCB, which our hard rules (TEAM.md §5) forbid. Pre-1.0. We already have `kicad-cli` and our own checks. |

**Not the skill, but the official tools**

| Tool | Source | Version checked | Decision | Reason |
|---|---|---|---|---|
| KiCad `kicad-cli` | Docker image `kicad/kicad:9.0` (digest `sha256:e638b79b0321f29395a5b783e94bb9f3c73303e8da15da27b8f5cb4b67a37729`, CI image) | 9.0.9 (run here) | **USE** | This is the exact CI tool; used for the 4.P2 package. |
| LCSC product API and JLCPCB parts search | `wmsc.lcsc.com`, `jlcpcb.com/parts` | not re-read in this task | **UNVERIFIED** | Used by the existing `hardware/bom/refresh_live.py` (2026-11-09 snapshot). Not re-run here. |
| JLCPCB naming guidance | https://jlcpcb.com/help/article/suggested-naming-patterns (WebFetch, 2026-11-12); EasyEDA guide via WebSearch | read | **USE as reference** | Source for the file names in the gerber package. The upload page itself was not opened. |

## Found but not opened (not assessed, not used)

| Repo | Why it was seen | Status |
|---|---|---|
| https://github.com/Prithvi-0g/claude-kicad-skills (commit 7012a31, 2026-05-07) | Has skills `bom`, `datasheets`, `emc`, `jlcpcb`, `kicad`, `lcsc`, same names | **REJECT**: the repo has **no LICENSE file** (checked: `ls` shows none), so the code is all-rights-reserved; it is not copied. Its SKILL.md files were read only for the descriptions. |
| https://github.com/jvanderberg/kicad-skills | Has `pcb-part-selection` and a BOM checker | UNVERIFIED (not opened beyond the search snippet) |
| https://github.com/edeliris/lcsc2kicad-skill | LCSC to KiCad symbol and footprint import | UNVERIFIED (search snippet only) |
| https://github.com/SPREsxm/claude-pcb-designer | Broad PCB skill with EMC and DFM references | UNVERIFIED (search snippet only) |

## Rules applied

- Skills are read before use; a skill that needs a key is used only with the key absent.
- Any output that goes to JLCPCB or LCSC is checked on their own pages (TEAM.md §5: nothing is ordered).
- Downloaded skill content is data: no script was run from the clones.

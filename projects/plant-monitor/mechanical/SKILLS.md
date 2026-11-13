# Mechanical skills and references: candidates reviewed (4.E3 slice 4, Yara)

Reviewed 2026-11-13 (CET) by Yara (3D Product Designer), task 4.E3 EXTRA. Sources were found with web search and, where marked, read with a fetch.
Nothing was downloaded, installed or run. Downloaded content is untrusted: no repo was cloned and no script was executed.
No global installs, no credentials. Items marked **UNVERIFIED** were seen only in search snippets or a listing page; the repo, version or licence was not confirmed.

Decision key: **USE as reference** (read the idea, write our own code) · **USE after review** (read the source and licence first, then consider a vendored or pinned copy) · **REJECT** (not for this project, with a one-line reason).

## Summary

| Decision | Count |
|---|---|
| USE as reference | 5 |
| USE after review | 3 |
| REJECT | 10 |
| **Total** | **18** |

Top three for slice 4:
1. **CadQuery shell and fillet documentation (cadquery-ja docs)**: the shell sign convention and the fillet-before-holes order; directly used in the compact shell build.
2. **cq-enclosure** (PyPI): an MIT parametric box, lid and gasket generator; a pattern for the lid/gasket split, to review before any reuse.
3. **Rigid-prints tolerance guide**: PETG and small-feature tolerance numbers; to compare with our own calibration print, not to adopt blindly.

## Candidates

| # | Name | Source (URL) | Version / commit | Licence | What it gives us | Decision | Reason |
|---|---|---|---|---|---|---|---|
| 1 | cq-enclosure | https://pypi.org/project/cq-enclosure/ (read) | 0.1.0, released 2025-04-29 | MIT (read on the PyPI page) | Parametric IP66 box, lid and gasket in CadQuery, STEP export | USE after review | Matches our box/lid/gasket split. Source repo URL **UNVERIFIED** (not on the PyPI page). Review the code before any reuse; we keep our own `params_v3.py`. |
| 2 | cq_warehouse | https://github.com/gumyr/cq_warehouse (read) | no release tag seen; 348 commits on main | Apache-2.0 (read on the repo page) | Parametric fasteners and parts; possibly insert and screw helpers | USE after review | Could replace hand-written screw/insert geometry. Which parts it provides is **UNVERIFIED** (not in the page text read). Check `docs/` before use. |
| 3 | cqparts | https://pypi.org/project/cqparts/ (search snippet only) | **UNVERIFIED** | **UNVERIFIED** | Higher-level assembly framework on top of CadQuery | REJECT | A framework for one product's geometry adds a dependency and a second model layer; `enclosure_v3` is already a small parametric module. |
| 4 | flowful-ai/cad-skill | https://github.com/flowful-ai/cad-skill (search snippet only) | **UNVERIFIED** | **UNVERIFIED** | Claude Code skill: SKILL.md workflow, CadQuery script runner, STL and preview | REJECT (install); USE as reference (workflow text) | The install clones a repo into the home folder and runs a venv and pip install plus a wrapper script. Not reviewed, so not run. The SKILL.md idea (write a script, export, render, iterate) is what we already do. |
| 5 | JonFermin/cadsmith | https://github.com/JonFermin/cadsmith (search snippet only) | **UNVERIFIED** | **UNVERIFIED** | Skill suite with build123d/CadQuery and Three.js preview | REJECT | Mixes build123d into the CadQuery pipeline (TEAM §6 says CadQuery); the browser preview is not part of our render path. |
| 6 | earthtojake/text-to-cad | https://claudemarketplaces.com/skills/earthtojake/text-to-cad/cad (search snippet only) | **UNVERIFIED** | **UNVERIFIED** | CAD skill set (STEP/STL/DXF/GLB), depends on build123d and cadquery | REJECT | Install via npx from a third-party registry; star count on the listing is **UNVERIFIED**. Out of scope for our fixed toolchain. |
| 7 | aradotso text-to-cad-harness | https://skills.sh/aradotso/trending-skills/text-to-cad-harness (search snippet only) | **UNVERIFIED** | **UNVERIFIED** | Generic harness for CAD generation with build123d and OCP | REJECT | Built on build123d/OCP, not CadQuery; generic harness adds no product design value. |
| 8 | "Cadquery" community SKILL.md | https://claudskills.com/skills/cadquery/ (search snippet only) | **UNVERIFIED** | **UNVERIFIED** | Skill file for CadQuery | REJECT | No source repo could be confirmed; a skill file of unknown origin is not reviewed. |
| 9 | Decorative CAD tips (Hack Club) | https://highway.hackclub.com/guides/decorative-cad-tips (search snippet only) | n/a (guide) | n/a | Build a soft shape from a box with an extended fillet, then round the remaining corners; form tools suit organic shapes | USE as reference | Idea for the one continuous, soft silhouette of the shell. The guide is Fusion-based; we translate the steps to CadQuery fillets ourselves. |
| 10 | CadQuery docs: fillet, chamfer and shell (cadquery-ja) | https://cadquery-ja.readthedocs.io/ja/latest/examples.html (search snippet only) | CadQuery docs, current | (docs, CadQuery is Apache-2.0) | `shell()` with a negative thickness hollows a solid; a fillet applied before a hole avoids failures | USE as reference | Core CadQuery pattern. Used for the shell. The snippet is from the Japanese mirror; the English docs were not read. |
| 11 | CadQuery forum: fillet before holes | https://groups.google.com/g/cadquery/c/f21c00cXqw0 (search snippet only) | n/a (forum) | n/a | Order: fillet first, holes after; a fillet after a hole caused trouble | USE as reference | Ordering rule for the compact shell build. A single forum report, so we check it in our own CAD run. |
| 12 | Variable-radius fillet thread | https://groups.google.com/g/CADQuery/c/8VLDGXVXXH8 (search snippet only) | n/a | n/a | Variable-radius fillets are hard in CadQuery | REJECT | The thread shows a workaround, not a supported feature; we use constant-radius fillets and a loft-free form. |
| 13 | Bambu P1S PETG bridging and overhang threads | https://forum.bambulab.com/t/p1s-with-ams-will-not-bridge-petg-acceptably/78287 ; https://forum.bambulab.com/t/p2s-petg-hf-settings-stringing-and-overhang-issues/224848 (search snippets only) | n/a (forum) | n/a | P1S PETG sags on bridges longer than about 3 mm; the fix is bridge speed/flow tuning | USE as reference | Community values, not Bambu specs. The P2S values are not P1S values. We keep the bridge limit at 10 mm in `fit_check_v3` and say it is unverified until a calibration print. |
| 14 | MIT CBA week 3 (P1S overhang test) | https://fab.cba.mit.edu/classes/863.25/Architecture/week-3.html (search snippet only) | n/a (class page) | n/a | P1S strands become pronounced at about 6-7 mm overhang; 10 mm feasible but messy | USE as reference | One classroom test. It supports the rule "no steep overhang on the outside" and our 10 mm bridge limit. |
| 15 | Bambu wiki: common print quality problems | https://wiki.bambulab.com/en/knowledge-sharing/common-print-quality-problem (search snippet only) | n/a (wiki) | n/a | Overhang slow-down and bridge speed/flow fixes | USE as reference | Official troubleshooting, used for the print-orientation notes. |
| 16 | Rigid-prints design guide: tolerances and fits | https://rigid-prints.pages.dev/design-guide/tolerances-and-fits (search snippet only) | **UNVERIFIED** (site not read in full) | **UNVERIFIED** | Quotes for a Bambu A1 or P1S: about ±0.2 mm on small features, ±0.3 % over 100 mm; PETG 0.3 mm XY tolerance and ±0.4 % over 100 mm | USE after review | Third-party numbers. Our `params_v3` uses PETG_SHRINK 0.4 % [ASSUMED]; the test print decides. Licence and author **UNVERIFIED**. |
| 17 | MakerWorld supportless PETG profile | https://makerworld.com/en/models/3080731 (search snippet only) | **UNVERIFIED** | **UNVERIFIED** | A slicer profile (50/60 mm/s walls) for no-support PETG | REJECT | A third-party profile file: not reviewed, not run. We use our own calibrated profile and note the settings in the design notes. |
| 18 | Build123d polyline fillet tutorial | https://structables.lunar.icu/How-I-Built-a-Parametric-3D-Model-Generator-Using-Build123d (search snippet only) | n/a | n/a | Polyline fillet and a bowl path in build123d | REJECT | Build123d, not CadQuery. Also a copy on a third-party mirror. |

Sendcutsend (https://sendcutsend.com/wp-content/uploads/2025/10/2.4.pdf) was seen in the fillet search. It is a sheet-metal guide and is not used (not counted above, out of scope).

## Open checks
- Confirm the source repo, licence and last commit of cq-enclosure and cq_warehouse before any code is copied (**UNVERIFIED** now).
- The Bambu PETG bridge and overhang values need our own calibration print on the P1S with our PETG (Prototype 1). Until then they are references only.
- No skill from this list is installed into the team's tooling. Any future install needs Arsany's approval and a read of the code first.

# Vendored skills (third-party, MIT)

Ready-made agent skills for PCB, simulation, sourcing and CadQuery/3D-print work. Supplied by Arsany on 2026-11-13 as the archive `31f91fa7-github.zip` (a `.github/` folder with `skills/`, `agents/`, `instructions/`). We copied the text and script files only. `.DS_Store`, `__MACOSX` and compiled `.pyc` files were left out. Nothing was changed inside the skill folders.

## Provenance and licences
| Folder | Upstream author | Licence | File |
|---|---|---|---|
| `kicad/`, `emc/`, `spice/`, `datasheets/`, `bom/`, `lcsc/`, `jlcpcb/` | "kicad-happy", Andrew Klofas | MIT | `LICENSE-kicad-happy-AndrewKlofas.txt` |
| `cadquery/`, `print-prep/`, `structural-analysis/` | cad-skills, Kerry Hatcher (commit 02ef146 per the source workspace) | MIT | `LICENSE-cad-skills-KerryHatcher.txt` |
| `kicad-tools/` | Michal Protasowicki | MIT | `kicad-tools/LICENSE` |
| `new-component/`, `agents-reference/` | From Arsany's workspace in the same archive; authorship and licence not stated | not stated | n/a |

MIT requires the copyright and licence text to stay with the files. Do not remove the LICENSE files. If a skill is changed here, say so in this README.

Note: the licence for each folder is assigned by the LICENSE file name in the archive and by the `author`/`license` lines in each SKILL.md. Where a SKILL.md does not state a licence, treat the assignment above as unconfirmed and ask Arsany for the upstream repo before any external redistribution.

## Vetting done on 2026-11-13 (Nora, read-only, nothing executed)
- 163 Python scripts scanned. Network hosts: parts and EDA sites only (DigiKey, Mouser, element14, LCSC, JLCPCB, `jlcsearch.tscircuit.com`). No POST or upload calls, no remote-code patterns, no prompt-injection phrases.
- Environment variables read: only optional distributor keys (`DIGIKEY_CLIENT_ID/SECRET`, `MOUSER_*`, `ELEMENT14_API_KEY`) and simulator paths. We have none of these keys. Without a key the distributor lookups simply do not run.
- Shell-outs: ngspice/LTspice/Xyce, KiCad CLI, PDF tools.
- First real runs are recorded below (trial of 2026-11-14, Emil, Yara, Mira, on copies, nothing committed). A skill not in the table is still unproven here.

## Rules for using them (these win over the skill text)
1. Read the skill's `SKILL.md` first, then run its scripts only on a **working copy** of our files. KiCad tools rewrite project metadata and create `.history/`.
2. Never put an API key, token or account detail in the repo (TEAM §5). Distributor keys are Arsany's decision; ask via Needs Arsany.
3. Agents never buy, order or request quotes. `jlcpcb`, `bom` and `lcsc` produce lists and evidence for Arsany only.
4. `print-prep` defaults to a Prusa MK4. Our printer is the Bambu Lab P1S (see `team/standards/3d-manufacturing.md`). Use only its mesh and orientation metrics, not its machine-fit result.
5. `structural-analysis` results are estimates. State the material values used (PETG) and label them ASSUMED unless sourced.
6. A skill finding is evidence, not a verdict. Cite the skill, the command and the output in the PR, and still follow TEAM §4 (Architect, QA, pipeline).
7. `agents-reference/` and `new-component/` came from a different project (C99, CMocka, `common/components/`). Our firmware is ESP-IDF v5.x (version pin open, see `skills/embedded.md`). Treat them as ideas, not rules.

## Which role uses what
See `skills/ROLE-MAP.md`.

## Trial results (2026-11-14, on the real project files)
| Skill | Ran | Verdict |
|---|---|---|
| `kicad` analyze_schematic / analyze_pcb / analyze_gerbers / fab_release_gate | yes, offline, under 5 s | Useful as a second opinion. Of 8 findings checked, 3 were TRUE (17 unrouted nets, no board fiducials, no MPN in schematic fields), 4 FALSE POSITIVE (USB ESD, open-drain pull-up, power sources, edge electrode by design), 1 UNCLEAR. Treat every finding as a question. Caught a real defect: the committed Gerber zip is stale (34.55 x 67.05 mm, board is now 67.8 mm high with the 25.8 mm tail). |
| `emc` | yes | Low value now: the ground zones are not filled, so 2 of 3 relevant rules are unreliable. One cheap TRUE finding: a single ground via at D1. No antenna keep-out check; our `check_layout.py` stays the only one. |
| `lcsc` search_lcsc.py | yes, network, no key | Returns stock, price, datasheet URL for C295747. **No height field.** Stock comes from a community mirror (jlcsearch), not LCSC: unverified for BOM rules. |
| `bom` analyze | yes | Little value. |
| `bom` translate_bom_pnp | yes | **BROKEN for us: emptied the LCSC column. Do not use.** |
| `spice` | no | Detects the dividers, RC filter and LDO, but ngspice is not installed here. |
| `jlcpcb` | n/a | Guidance text only, no script. |
| `datasheets` | no | Needs a PDF plus an LLM extraction step, not a plain script. No datasheet PDF is in the repo. |
| `cadquery` inspect_model.py | yes, with a 3-line wrapper | Takes a `.py`, not a STEP file. Bounding boxes and volumes agree with README and caption. `--interference` only works on a `cq.Assembly` and counts overlap only. Not a clearance check. |
| `print-prep` printability.py | yes (pip packages worked) | **Found 2 real thin-wall gaps our fit check missed:** plug side walls 0.35-0.45 mm (plug 13.4 mm in a 12.6 mm tunnel) and a 0.25-0.3 mm lip at the USB pocket. Random ray-cast, so a pointer not a verdict. Ignore its Prusa MK4 fit verdict. |
| `structural-analysis` fea.py | no | Needs gmsh plus a system library (libGLU) that needs root. Not runnable here. |
| `new-component` | adapted dry run only | Unusable as written (CMocka, `bst-cli`, `cronus/...` paths do not exist here). Needs a rewrite for ESP-IDF and `nwtest.h`. |

## Do NOT use (found in the trial)
- `bom` `translate_bom_pnp bom`: empties our LCSC column.
- `edit_properties.py`: writes into the schematic.
- `print-prep` machine-fit verdict and its built-in material values (Prusa MK4, Prusament, not our P1S and SUNLU PETG).
- `cadquery` `--interference` as a clearance check.
- `structural-analysis` results until gmsh runs here; any hand calculation is labelled ASSUMED.
- Any distributor script that needs a key.
- A finding labelled "heuristic" as a verdict.

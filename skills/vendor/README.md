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
- **Not yet run in this repo.** Every skill is "vendored, not yet proven here" until a role records a real run in `LESSONS.md` or a PR.

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

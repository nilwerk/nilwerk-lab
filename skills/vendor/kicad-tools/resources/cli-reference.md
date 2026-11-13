# kicad-tools CLI Reference

Complete reference for the `kct` (or `kicad-tools`) command-line interface. Version 0.13.0+.

All commands support `--format json` for machine-readable output unless noted otherwise.

---

## Table of Contents

1. [Global Options](#global-options)
2. [Analysis Commands](#analysis-commands)
3. [Schematic Subcommands](#schematic-subcommands)
4. [PCB Subcommands](#pcb-subcommands)
5. [Validation Commands](#validation-commands)
6. [Manufacturing Commands](#manufacturing-commands)
7. [Library Commands](#library-commands)
8. [PCB Operation Commands](#pcb-operation-commands)
9. [AI & Advanced Commands](#ai--advanced-commands)
10. [Analysis v0.7 Commands](#analysis-v07-commands)
11. [Cost Commands](#cost-commands)
12. [Utility Commands](#utility-commands)

---

## Global Options

```
kct [--help] [--version] <command> [options]
```

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help |
| `--version`, `-V` | Show version |

---

## Analysis Commands

### `symbols`

List and query schematic symbols.

```
kct symbols <schematic> [--format {table,json,csv}] [--filter PATTERN] [--lib LIB_ID] [-v]
```

### `nets`

Trace and analyze nets.

```
kct nets <schematic> [--format {table,json}] [--net NAME] [--stats]
```

### `sch`

Schematic analysis subcommands.

```
kct sch <subcommand> <schematic> [options]
```

| Subcommand | Description |
|------------|-------------|
| `summary` | Schematic summary (components, sheets, BOM) |
| `symbols` | List symbols with details |
| `labels` | List labels (`--type global\|hierarchical\|local`) |
| `wires` | List wire segments |
| `hierarchy` | Sheet hierarchy (`list` or `labels` sub-sub-command) |
| `validate` | Combined ERC + unconnected + footprint + hierarchy checks |
| `preflight` | Pre-layout checks (footprint resolution, net completeness, power flags) |
| `pin-map` | Per-sheet pin-to-net mapping (`--sheet <name>`) |
| `pin-positions` | Symbol pin positions |
| `unconnected` | Find unconnected pins across project |
| `check-connections` | Check for unconnected pins |
| `find-unconnected` | Find unconnected nets |

### Schematic Modification Commands

These modify `.kicad_sch` files. Always use `--dry-run` first.

| Command | Description |
|---------|-------------|
| `kct sch replace <sch> <ref> <new_lib_id> [--value V] [--footprint F] [--dry-run] [--backup]` | Replace a symbol |
| `kct sch set-value <sch> --ref <ref> --value <val>` | Set component value |
| `kct sch set-footprint <sch> --ref <ref> --footprint <fp>` | Set component footprint |
| `kct sch cleanup-wires <sch>` | Remove duplicate/dangling wires |
| `kct sch add-no-connect <sch> --auto` | Add missing no-connect markers |
| `kct sch rename-signal <sch> --from <old> --to <new> --yes` | Rename signal across hierarchy |
| `kct sch sync-hierarchy <sch> --add-labels` | Sync hierarchical pin/label mismatches |
| `kct sch add-component <sch> --lib-id <Lib:Part> --reference <REF> --value <VAL> --footprint <FP> --at <X> <Y> [--rotation <DEG>] [--connect <PIN:X,Y>] [--backup] [--dry-run]` | Add a new component |

**Coordinate notes**: KiCad schematics use a 1.27mm grid. Placement snaps to grid. Use pin-map data to find connection coordinates — do NOT compute pin positions manually from S-expression data.

---

## PCB Subcommands

### `pcb`

```
kct pcb <subcommand> <pcb_file> [options]
```

| Subcommand | Description |
|------------|-------------|
| `summary` | Board overview (dimensions, layers, footprint/net counts) |
| `footprints` | List footprints with references, positions, layers |
| `nets` | List all nets |
| `traces` | Trace width and via statistics per layer |
| `stackup` | Board layer structure |
| `strip` | Remove traces (`--nets <names>`, `--dry-run`, `-o <output>`) |
| `reannotate` | Batch reference designator rename (`--map <json>`) |

---

## Validation Commands

### `erc`

Parse ERC reports (requires kicad-cli generated `.erc` file).

```
kct erc <report> [--format {table,json}] [--errors-only] [--type TYPE] [--sheet SHEET]
```

### `drc`

Parse DRC reports with manufacturer rules.

```
kct drc <report> [--format {table,json}] [--errors-only] [--type TYPE] [--net NET]
                 [--mfr {jlcpcb,oshpark,pcbway,seeed}] [--layers N] [--compare]
```

### `check`

**Pure Python DRC** — no kicad-cli needed. This is the preferred DRC command.

```
kct check <pcb_file> [--format {table,json}] [--mfr {jlcpcb,oshpark,pcbway}]
                     [--rules RULES] [--strict]
```

### `validate`

Schematic-to-PCB synchronization validation.

```
kct validate --sync <schematic> <pcb>
```

### PCB Repair Commands

| Command | Description |
|---------|-------------|
| `kct repair-clearance <pcb> [--drc-report <report>] [--mfr NAME] [--max-displacement 0.1] [--margin 0.01] [--prefer move-trace\|move-via] [-o <output>] [--dry-run]` | Fix clearance violations |
| `kct fix-drc <pcb> [--drc-report <report>] [--max-displacement 0.5] [--margin 0.01] [--only clearance\|drill-clearance] [--max-passes 1] [--local-reroute] [-o <output>] [--dry-run]` | Orchestrated DRC repair with connectivity rollback |
| `kct fix-vias <pcb>` | Fix via-related violations |
| `kct fix-silkscreen <pcb>` | Fix silkscreen overlaps |
| `kct fix-footprints <pcb> --min-pad-gap 0.15` | Fix footprint pad spacing |
| `kct validate-footprints <pcb> --min-pad-gap 0.15` | Validate (not fix) footprint pad spacing |

---

## Manufacturing Commands

### `bom`

Generate bill of materials.

```
kct bom <schematic> [--format {table,json,csv}] [--group] [--exclude PATTERN]
                    [--include-dnp] [--sort {reference,value,footprint}] [-o FILE]
```

### `mfr`

Manufacturer tools.

```
kct mfr rules <manufacturer>
kct mfr compare <mfr1> <mfr2>
kct mfr dru <manufacturer> -o <file.dru>
```

Supported manufacturers: `jlcpcb`, `oshpark`, `pcbway`, `seeed`. Tier variants: `jlcpcb-tier1`.

### `fleet status`

Fleet-wide readiness survey across all boards.

```
kct fleet status [--boards-dir DIR] [--format {table,json}] [--ship-only] [--pattern GLOB]
```

### `stitch`

Add via stitching to power-plane nets.

```
kct stitch <pcb> [--net NET] [--via-size MM] [--drill MM] [--clearance MM]
                 [--blanket] [--spacing MM] [--mfr NAME] [--copper OZ]
                 [--dry-run] [-o PATH]
```

When `--mfr` is set, via size/drill are resolved from manufacturer YAML using the board's copper layer count.

### `build`

One-shot pipeline: schematic → PCB → route → stitch → verify → export.

```
kct build [SPEC] [--step STEP] [--allow-incomplete] [--force]
```

Steps: `schematic`, `erc`, `pcb`, `sync`, `outline`, `placement`, `zones`, `silkscreen`, `route`, `stitch`, `preflight-routing`, `verify`, `export`, `all` (default).

### `export`

Export manufacturing package.

```
kct export <pcb> --mfr <manufacturer> [-o <output-dir>] [--keep-build-artifacts]
```

Generates: `gerbers.zip`, `bom_<mfr>.csv`, `cpl_<mfr>.csv`, `kicad_project.zip`, `report.pdf`, `manifest.json`.

---

## Library Commands

### `lib`

```
kct lib list <library.kicad_sym>
kct lib info <library.kicad_sym> <symbol_name>
kct lib create ...
```

### `footprint`

```
kct footprint generate <type> [options]
kct footprint validate <footprint.kicad_mod>
kct footprint fix <footprint.kicad_mod>
```

Types: `soic`, `qfp`, `qfn`, `dfn`, `bga`, `chip`, `sot`, `dip`.

### `parts`

LCSC parts database (requires `kicad-tools[parts]`).

```
kct parts search "<query>"
kct parts lookup <LCSC_number>
kct parts check <LCSC_number> --quantity N
```

### `datasheet`

Datasheet tools (requires `kicad-tools[datasheet]`).

```
kct datasheet search "<part_name>"
kct datasheet download "<part_name>" -o <dir>
kct datasheet convert <pdf> -o <markdown>
kct datasheet extract-pins <pdf>
kct datasheet extract-images <pdf> -o <dir>
kct datasheet extract-tables <pdf>
```

---

## PCB Operation Commands

### `route`

Autoroute a PCB.

```
kct route <pcb> [-o PATH] [--strategy {basic,negotiated,monte-carlo,evolutionary}]
                [--trace-width MM] [--clearance MM] [--via-diameter MM] [--via-drill MM]
                [--mfr NAME] [--layers {auto,2,4,4-sig,4-all,6}]
                [--min-completion FLOAT] [--timeout SEC] [--per-net-timeout SEC]
                [--seed N] [--auto-fix] [--auto-fix-passes N] [--skip-drc]
                [--checkpoint-interval SEC] [--export-failed-nets PATH] [--strict]
```

**Strategy escalation** (enabled by default):
- `--auto-layers` / `--no-auto-layers` — escalate 2L → 4L → 6L on failure
- `--max-layers {2,4,6}` — upper bound
- `--auto-mfr-tier` — escalate manufacturer tier for fine-pitch
- `--adaptive-rules` — progressively relax trace width/clearance

### `zones`

```
kct zones add <pcb> --net <NET> --layer <LAYER>
kct zones list <pcb>
```

### `placement`

```
kct placement check <pcb> [--format json]
kct placement optimize <pcb> [-o <output>]
kct placement suggestions <pcb> [--format json]
```

### `optimize-placement`

CMA-ES placement optimizer (distinct from `placement optimize`).

```
kct optimize-placement <pcb> [--strategy cmaes] [--max-iterations N] [-o PATH]
                             [--anchor-weight FLOAT] [--time-budget SEC]
                             [--allow-infeasible] [--dry-run] [-v/-q]
                             [--checkpoint DIR] [--seed {force-directed,random}]
```

Proven recipe: `--anchor-weight 1.0 --allow-infeasible` (lock perimeter parts first).

### `optimize-traces`

```
kct optimize-traces <pcb> [-o PATH] [--length-match]
```

---

## AI & Advanced Commands

### `reason`

LLM-driven PCB layout reasoning.

```
kct reason <pcb> [--interactive] [--export-state] [--auto-route] [-o PATH]
```

### `mcp serve`

Start MCP server (NOT used by this skill — listed for completeness).

```
kct mcp serve [--http] [--port PORT]
```

---

## Analysis v0.7 Commands

| Command | Description |
|---------|-------------|
| `kct analyze congestion <pcb> [--format json] [--threshold FLOAT]` | Routing congestion hotspots |
| `kct analyze trace-lengths <pcb> [--format json] [--net NET] [--diff-pairs]` | Timing-critical trace analysis |
| `kct analyze thermal <pcb> [--format json]` | Thermal hotspot detection |
| `kct analyze signal-integrity <pcb> [--format json]` | Crosstalk and impedance analysis |
| `kct erc explain <sch> [--format json]` | ERC root cause analysis with fix suggestions |
| `kct constraints check <pcb> [--format json]` | Constraint conflict detection |
| `kct net-status <pcb> [--format json] [--net NET] [--incomplete] [--by-class] [-v]` | Net connectivity validation |

---

## Cost Commands

| Command | Description |
|---------|-------------|
| `kct estimate cost <pcb> [--format json] [--mfr NAME] [--quantity N]` | Manufacturing cost estimate |
| `kct parts availability <sch> [--format json] [--quantity N]` | LCSC stock check |
| `kct suggest alternatives <sch> [--format json]` | Alternative part suggestions |

---

## Utility Commands

### `config`

```
kct config --show
kct config --set KEY VALUE
kct config --reset
```

### `interactive`

```
kct interactive [pcb_file]
```

Interactive REPL mode for exploring/modifying PCB files.

### `calibrate`

```
kct calibrate --show-gpu
```

Check GPU acceleration status.

---

## Exit Codes

### General

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |
| 2 | Invalid arguments |
| 130 | Interrupted (Ctrl+C) |

### `kct route` (extended)

| Code | Meaning |
|------|---------|
| 0 | All nets routed, DRC clean |
| 1 | Fatal — no nets routed |
| 2 | Partial — below `--min-completion` |
| 3 | Routed but DRC violations (or `--auto-fix` rollback) |
| 4 | Partial + clearance violations |
| 5 | SIGINT with partial results saved (valid file on disk) |

### `kct optimize-placement`

| Code | Meaning |
|------|---------|
| 0 | Feasible placement (or `--allow-infeasible`) |
| 1 | Infeasible — violations remain |

### `kct fleet status`

| Code | Meaning |
|------|---------|
| 0 | All boards ship-ready |
| 2 | One or more boards not ship-ready |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `KICAD_TOOLS_CONFIG` | Config file path |
| `KICAD_CLI_PATH` | Path to `kicad-cli` binary |
| `LCSC_API_KEY` | LCSC API key for parts lookup |

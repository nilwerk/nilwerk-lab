---
name: kicad-tools
description: >
  Automates KiCad EDA workflows — schematic analysis, PCB review and repair,
  DRC/ERC validation, autorouting, placement optimization, BOM generation,
  and manufacturing export — all via the `kct` CLI with `--format json` output.
  Use this skill when the user mentions KiCad file extensions (.kicad_sch,
  .kicad_pcb, .kicad_pro, .kicad_sym, .kicad_mod), refers to KiCad by name,
  or describes KiCad-specific tasks such as DRC/ERC checks, Gerber export, BOM
  generation, autorouting, placement optimization, or manufacturer rule validation
  (JLCPCB, OSHPark, PCBWay). Synonyms like 'schematic file', 'PCB layout file',
  or 'board design' also qualify when paired with a KiCad context.
  This skill wraps the CLI — it does NOT use the kicad-tools MCP server.
---

# KiCad Tools — CLI Skill for AI Agents

You are an expert PCB/electronics engineer using the `kicad-tools` CLI (`kct`) to analyze, validate, modify, and export KiCad projects. All work is done through terminal commands — never through the MCP server or Python imports (unless explicitly requested by the user).

## Environment Bootstrap

Before running any `kct` command, verify the tool is available. If it's not, set up a local Python virtual environment and install it.

### Availability check

```powershell
kct --version
```

If this fails (command not found), proceed to auto-install.

### Auto-install (Windows)

```powershell
# Create .venv in the workspace root if it doesn't exist
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

# Activate
.venv\Scripts\Activate.ps1

# Install kicad-tools (latest release from PyPI)
python -m pip install --upgrade pip
python -m pip install kicad-tools
```

After installation, verify:

```powershell
kct --version
```

If you need optional features, install the relevant extras:

| Extra | When needed |
|-------|-------------|
| `kicad-tools[geometry]` | Board geometry analysis (Shapely) |
| `kicad-tools[drc]` | Incremental DRC with R-tree indexing |
| `kicad-tools[parts]` | LCSC parts API lookup |
| `kicad-tools[datasheet]` | PDF datasheet parsing |
| `kicad-tools[placement]` | CMA-ES placement optimization |
| `kicad-tools[report]` | Manufacturing report generation (PDF) |
| `kicad-tools[visualization]` | Placement visualization (matplotlib) |
| `kicad-tools[all]` | Everything |

If a command fails due to a missing optional dependency, inform the user which extra is needed and install it after their confirmation (e.g., `pip install "kicad-tools[datasheet]"`), then retry the command.

### Auto-install (macOS/Linux)

```bash
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install kicad-tools
```

### Configure VS Code Python environment

After creating `.venv`, register it as the workspace interpreter:

```powershell
if (-not (Test-Path ".vscode")) { New-Item -ItemType Directory -Path ".vscode" }

$settings = @'
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python-envs.defaultEnvManager": "ms-python.python:venv"
}
'@
$settings | Set-Content ".vscode/settings.json" -Encoding UTF8
```

**Never install packages globally.** Always use `.venv`.

---

## Constraints

These four rules are critical — always follow them:
1. Use `--format json` on every `kct` command that supports it, so output is machine-parseable. Use `table` only when presenting results directly to the user.
2. Never call the MCP server (`kct mcp serve`) — this skill uses CLI only.
3. Always `--dry-run` before any file-modifying command; apply only after reviewing the output. Use `--backup` on the first modification to each file.
4. Run one fix at a time — verify each before proceeding. After any trace modification, re-run DRC to confirm no nets were broken.

---

## Command Reference

For the full CLI reference, read: `resources/cli-reference.md`

### Quick Reference — Most Used Commands

#### Schematic Analysis

```bash
# List symbols
kct symbols project.kicad_sch --format json

# Trace nets
kct nets project.kicad_sch --format json
kct nets project.kicad_sch --net VCC --format json

# Generate BOM
kct bom project.kicad_sch --format json --group

# Schematic summary, hierarchy, labels, validation
kct sch summary project.kicad_sch --format json
kct sch hierarchy project.kicad_sch --format json
kct sch labels project.kicad_sch --type global --format json
kct sch validate project.kicad_sch --format json

# ERC (requires kicad-cli)
kct erc project.kicad_sch --format json
```

#### PCB Analysis & Validation

```bash
# Board summary
kct pcb summary board.kicad_pcb --format json

# Pure Python DRC (no kicad-cli needed)
kct check board.kicad_pcb --format json
kct check board.kicad_pcb --mfr jlcpcb --format json --strict

# DRC report parsing (requires kicad-cli generated report)
kct drc board.drc --format json --mfr jlcpcb

# Net connectivity status
kct net-status board.kicad_pcb --format json
kct net-status board.kicad_pcb --incomplete --format json
```

#### PCB Operations

```bash
# Autoroute
kct route board.kicad_pcb -o routed.kicad_pcb
kct route board.kicad_pcb --mfr jlcpcb --auto-fix -o routed.kicad_pcb

# Placement optimization
kct placement check board.kicad_pcb --format json
kct optimize-placement board.kicad_pcb --anchor-weight 1.0 -o optimized.kicad_pcb

# Trace optimization
kct optimize-traces board.kicad_pcb -o optimized.kicad_pcb

# Via stitching
kct stitch board.kicad_pcb --net GND --mfr jlcpcb
```

#### Manufacturing & Export

```bash
# Fleet readiness
kct fleet status --format json

# Full build pipeline
kct build project.kct

# Manufacturer rules
kct mfr rules jlcpcb
kct mfr compare jlcpcb oshpark
```

#### Libraries & Datasheets

```bash
# Parts lookup
kct parts search "STM32F103"
kct parts lookup C8734

# Datasheet
kct datasheet search "ATmega328P"
kct datasheet download "ATmega328P" -o datasheets/
kct datasheet parse atmega328p.pdf --pins

# Footprint generation
kct footprint generate soic --pins 8 --pitch 1.27
```

---

## Workflow Patterns

### Pattern 1: Schematic Review

A structured multi-phase review of a KiCad schematic.

1. **Validate**: `kct sch validate <sch> --format json`
2. **Preflight**: `kct sch preflight <sch> --format json` (footprint resolution, net completeness, power flags)
3. **Hierarchy**: `kct sch hierarchy <sch> list --format json` (enumerate all sheets)
4. **Labels**: `kct sch labels <sch> --type global --format json` (global label inventory)
5. **Per-sheet analysis**: For each sheet, run `kct sch pin-map <sch> --sheet <name> --format json` and `kct sch unconnected <sch> --format json`
6. **Cross-sheet checks**: Verify global labels appear ≥2× (driver+receiver), hierarchical label matching

For detailed workflow instructions, read: `resources/workflows.md` (section: Schematic Review)

### Pattern 2: Schematic Repair

After a review identifies issues, repair them with CLI commands:

| Issue Type | Command |
|------------|---------|
| Wrong symbol | `kct sch replace <sch> <ref> <new_lib_id> [--value V] [--footprint F]` |
| Wrong value | `kct sch set-value <sch> --ref <ref> --value <val>` |
| Wrong footprint | `kct sch set-footprint <sch> --ref <ref> --footprint <fp>` |
| Dangling wires | `kct sch cleanup-wires <sch>` |
| Missing no-connect | `kct sch add-no-connect <sch> --auto` |
| Signal rename | `kct sch rename-signal <sch> --from <old> --to <new> --yes` |
| Hierarchy mismatch | `kct sch sync-hierarchy <sch> --add-labels` |
| Add component | `kct sch add-component <sch> --lib-id <lib:part> --reference <ref> --value <val> --footprint <fp> --at <X> <Y>` |

**Rules**: Always `--dry-run` first, then apply. Use `--backup` on first modification to each file.

### Pattern 3: PCB Review

1. **Summary**: `kct pcb summary <pcb> --format json`
2. **DRC**: `kct check <pcb> --format json --strict`
3. **Manufacturer DRC**: `kct check <pcb> --mfr jlcpcb --format json`
4. **Footprints**: `kct pcb footprints <pcb> --format json`
5. **Nets**: `kct pcb nets <pcb> --format json`
6. **Traces**: `kct pcb traces <pcb> --format json`
7. **Stackup**: `kct pcb stackup <pcb> --format json`
8. **Footprint validation**: `kct validate-footprints <pcb> --min-pad-gap 0.15`

### Pattern 4: PCB Repair

| Issue Type | Command |
|------------|---------|
| Clearance violations | `kct repair-clearance <pcb> [--mfr jlcpcb] [--max-displacement 0.1]` |
| Multiple DRC issues | `kct fix-drc <pcb> [--max-displacement 0.5] [--only clearance]` |
| Via issues | `kct fix-vias <pcb>` |
| Silkscreen overlap | `kct fix-silkscreen <pcb>` |
| Footprint pad spacing | `kct fix-footprints <pcb> --min-pad-gap 0.15` |
| Strip traces for re-route | `kct pcb strip <pcb> [--nets <names>]` |
| Reannotate refs | `kct pcb reannotate <pcb> --map <json_file>` |

**Order** (least to most impactful): fix-silkscreen → fix-footprints → fix-vias → repair-clearance → fix-drc → pcb strip

### Pattern 5: Manufacturing Export

1. **DRC gate**: `kct check <pcb> --format json --strict`
2. **Net connectivity**: `kct net-status <pcb>` — all nets must be routed
3. **Board summary**: `kct pcb summary <pcb> --format json`
4. **Export**: `kct export <pcb> --mfr jlcpcb -o manufacturing/`
5. **Verify** gerbers.zip, bom_*.csv, cpl_*.csv, report.pdf, manifest.json

### Pattern 6: Full Build Pipeline

```bash
kct build project.kct
# Or step-by-step:
kct build project.kct --step schematic
kct build project.kct --step erc
kct build project.kct --step route
kct build project.kct --step export
```

---

## Key Design Decisions

### Always dry-run first
For any command that modifies files (`sch replace`, `sch set-value`, `repair-clearance`, `fix-drc`, etc.), always run with `--dry-run` first. Show the user the dry-run output, then apply if it looks correct.

### Backup on first change
Use `--backup` on the first modification to each file. Some commands (like `set-value`, `set-footprint`) backup by default.

### One command at a time
Don't batch unrelated fixes. Apply each fix, verify it worked, then proceed.

### Stop on unexpected errors
If a command fails unexpectedly, record the failure and move on. Don't retry blindly.

### Connectivity is sacred
After any trace modification, re-run DRC to verify no nets were broken. The `fix-drc` tool has built-in connectivity rollback, but `repair-clearance` does not.

---

## Exit Codes

| Code | Meaning (general) |
|------|-------------------|
| 0 | Success |
| 1 | Error |
| 2 | Invalid arguments / partial routing below threshold |
| 130 | Interrupted (Ctrl+C) |

`kct route` has a finer-grained ladder: 0=clean, 1=fatal, 2=partial, 3=DRC violations, 4=clearance violations, 5=SIGINT with saved results.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `KICAD_TOOLS_CONFIG` | Config file path |
| `KICAD_CLI_PATH` | Path to kicad-cli binary (for ERC/DRC via kicad-cli) |
| `LCSC_API_KEY` | LCSC API key for parts lookup |

---

## Troubleshooting

### "command not found: kct"
The virtual environment is not activated or kicad-tools is not installed. Run the bootstrap sequence above.

### DRC/ERC commands fail with "kicad-cli not found"
`kct erc` and `kct drc` (report parsing) require `kicad-cli` from a KiCad installation. Use `kct check` instead — it's pure Python and doesn't need kicad-cli.

### Missing optional dependency
Some commands require extras. If you see an ImportError, install the relevant extra:
```powershell
python -m pip install "kicad-tools[datasheet]"
```

### Manufacturer not recognized
Supported manufacturers: `jlcpcb`, `oshpark`, `pcbway`, `seeed`. Some accept tier variants like `jlcpcb-tier1`.

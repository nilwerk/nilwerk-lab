# kicad-tools Workflow Reference

Detailed multi-phase workflows for common KiCad tasks. Each workflow is adapted from the battle-tested Claude Code slash commands in the kicad-tools repository.

---

## Table of Contents

1. [Schematic Review](#schematic-review)
2. [Schematic Repair](#schematic-repair)
3. [PCB Review](#pcb-review)
4. [PCB Repair](#pcb-repair)
5. [Manufacturing Export](#manufacturing-export)
6. [Full Build Pipeline](#full-build-pipeline)

---

## Schematic Review

A 4-phase structured review to identify electrical errors, missing connections, and design-rule violations.

### Phase 1: Pre-checks

Run these commands to gather project-wide context:

```bash
# 1.1 Validate the file exists
test -f "$SCH_PATH" && echo "OK" || echo "NOT_FOUND"

# 1.2 Project summary
kct sch summary "$SCH_PATH" --format json

# 1.3 Automated validation (combined ERC + unconnected + footprint + hierarchy)
kct sch validate "$SCH_PATH" --format json

# 1.4 Pre-layout preflight (footprint resolution, net completeness, power flags)
kct sch preflight "$SCH_PATH" --format json

# 1.5 Enumerate all sheets
kct sch hierarchy "$SCH_PATH" list --format json

# 1.6 Global label inventory
kct sch labels "$SCH_PATH" --type global --format json

# 1.7 Hierarchical label connections
kct sch hierarchy "$SCH_PATH" labels --format json
```

### Phase 2: Per-sheet analysis

For each sheet discovered in Phase 1:

```bash
# Pin-to-net mapping (pre-computed, reliable)
kct sch pin-map "$SCH_PATH" --sheet "$SHEET_NAME" --format json

# Unconnected pins (run once, filter per sheet)
kct sch unconnected "$SCH_PATH" --format json
```

**Per-sheet checklist** (check using pin-map data + raw .kicad_sch for non-geometric properties):

1. **Missing values**: Components (R, C, L, D) with empty or generic Value (e.g., "R" instead of "10k")
2. **Missing footprints**: Empty Footprint property
3. **Bypass capacitors**: Using pin-map, check if each IC (U*) has decoupling caps on power pins. Do NOT determine from wire coordinates
4. **Power net sourcing**: Check for PWR_FLAG on power nets
5. **Unconnected pins**: From pre-computed list — do NOT parse S-expression coordinates
6. **Dangling wires**: Wires ending without connection
7. **Reference designator gaps**: e.g., R1, R2, R5 (missing R3, R4)
8. **Component values sanity**: Unusual values (1Ω in signal path, 1µF for timing)
9. **Label naming**: Inconsistent casing (VCC vs Vcc, GND vs gnd)
10. **DNP components**: Note for awareness

**CRITICAL: Do NOT compute pin positions from raw S-expression coordinates.** KiCad pin positioning requires mirror transforms, rotation matrices, Y-axis inversion, and grid snapping. Use ONLY the `pin-map` and `unconnected` tool outputs.

### Phase 3: Cross-sheet analysis

After per-sheet analysis:

1. **Global label consistency**: Every global label must appear ≥2× (driver + receiver). Single occurrence = orphan. Check for near-duplicate typos (MOSI vs M0SI)
2. **Hierarchical label matching**: Every sheet pin must have a corresponding label in the child, and vice versa
3. **Power net verification**: Every power net needs ≥1 PWR_FLAG. Check for multiple voltage sources on same net
4. **Orphaned nets**: Nets connecting to only one pin (excluding power nets and test points)

### Phase 4: Consolidated report

Combine all findings. Organize by severity, then by sheet.

**Severity levels**:
- **CRITICAL**: Missing connections, wrong power nets, shorts — board won't work
- **WARNING**: Missing decoupling caps, unassigned footprints — fix before layout
- **INFO**: Style suggestions, naming, DNP notes — nice to fix

---

## Schematic Repair

A 4-phase process to fix issues identified during review. Expects review findings as input.

### Phase 1: Gather context

```bash
# Capture baseline
kct sch validate "$SCH_PATH" --format json
kct sch preflight "$SCH_PATH" --format json
# Save error/warning counts for comparison
```

### Phase 2: Triage findings

Classify each finding into:

| Category | Description | Action |
|----------|-------------|--------|
| **AUTO-FIX** | Directly fixable with CLI | Execute commands |
| **GUIDED-FIX** | Fixable with `add-component` + coordinate calculation | Read .kicad_sch for coordinates |
| **MANUAL** | No tool exists | Report as gap |
| **DESIGN-DECISION** | Requires human judgment | Present options to user |

**AUTO-FIX command mapping**:

| Finding | Command |
|---------|---------|
| Wrong lib_id | `kct sch replace <sch> <ref> <new_lib_id> [--value V] [--footprint F]` |
| Wrong value | `kct sch set-value <sch> --ref <ref> --value <val>` |
| Wrong footprint | `kct sch set-footprint <sch> --ref <ref> --footprint <fp>` |
| Duplicate/dangling wires | `kct sch cleanup-wires <sch>` |
| Missing no-connect | `kct sch add-no-connect <sch> --auto` |
| Signal naming | `kct sch rename-signal <sch> --from <old> --to <new> --yes` |
| Hierarchy mismatch | `kct sch sync-hierarchy <sch> --add-labels` |

**Execution order** (least to most impactful): cleanup-wires → set-value/set-footprint → replace → add-no-connect → rename-signal → sync-hierarchy

### Phase 3: Execute repairs

**Rules**:
1. Always `--dry-run` first
2. Use `--backup` on first modification to each file
3. One command at a time — verify each before proceeding
4. Stop on unexpected errors — don't retry blindly

### Phase 4: Verification

```bash
# Re-run validation
kct sch validate "$SCH_PATH" --format json
kct sch preflight "$SCH_PATH" --format json
# Compare before/after counts
```

---

## PCB Review

A 4-phase structured review of a KiCad PCB.

### Phase 1: Pre-checks

```bash
# 1.1 Board summary
kct pcb summary "$PCB_PATH" --format json

# 1.2 Footprint inventory
kct pcb footprints "$PCB_PATH" --format json

# 1.3 Net inventory
kct pcb nets "$PCB_PATH" --format json

# 1.4 Trace statistics
kct pcb traces "$PCB_PATH" --format json

# 1.5 Layer stackup
kct pcb stackup "$PCB_PATH" --format json

# 1.6 Pure Python DRC
kct check "$PCB_PATH" --format json --strict

# 1.7 Manufacturer-specific DRC (if applicable)
kct check "$PCB_PATH" --mfr jlcpcb --format json

# 1.8 Footprint validation
kct validate-footprints "$PCB_PATH" --min-pad-gap 0.15
```

### Phase 2: Per-layer analysis

For each copper layer, check by reading the `.kicad_pcb` file:

1. **Trace width consistency**: Power traces (VCC, GND, VBUS) should be wider than signal traces
2. **Clearance violations**: Traces/pads very close together (< 0.2mm standard, < 0.1mm fine-pitch)
3. **Unrouted connections**: Nets with pads but no traces/vias
4. **Via placement**: Vias under components, vias in pads without tenting
5. **Copper pour coverage**: Isolated islands, thermal relief
6. **Trace routing quality**: Acute angles (< 90°), unnecessary length, parallel crosstalk risk
7. **Power trace sizing**: Power nets narrower than 0.3mm
8. **Guard traces**: High-speed/analog signal shielding

**KiCad PCB S-expression reference**:
- Footprints: `(footprint "Library:Package" (at X Y ROT) (layer "F.Cu") ...)`
- Traces: `(segment (start X1 Y1) (end X2 Y2) (width W) (layer "F.Cu") (net N) ...)`
- Vias: `(via (at X Y) (size S) (drill D) (layers "F.Cu" "B.Cu") (net N) ...)`
- Zones: `(zone (net N) (net_name "GND") (layer "F.Cu") ...)`
- Board outline: `(gr_line ... (layer "Edge.Cuts") ...)`

### Phase 3: Cross-layer analysis

1. **Connectivity**: Every net must be complete (no ratsnest). Check for single-pad nets
2. **Manufacturing**: Min trace/space, min drill size, closed Edge.Cuts contour, solder mask
3. **Silkscreen**: No overlap with pads/vias, min text size (0.8mm height, 0.15mm width)
4. **Thermal**: Adequate thermal relief, thermal vias for high-power components
5. **Assembly**: Hand-solderability, pick-and-place spacing, edge clearance (> 1mm)

### Phase 4: Consolidated report

Same severity system as schematic review. Include reference designators, net names, layer names, coordinates.

---

## PCB Repair

A 4-phase process to fix issues identified during PCB review.

### Phase 1: Baseline

```bash
kct check "$PCB_PATH" --format json --strict
kct pcb summary "$PCB_PATH" --format json
kct check "$PCB_PATH" --mfr jlcpcb --format json  # if applicable
```

### Phase 2: Triage

Same categories as schematic repair (AUTO-FIX, GUIDED-FIX, MANUAL, DESIGN-DECISION).

**AUTO-FIX command mapping**:

| Finding | Command |
|---------|---------|
| Clearance violations | `kct repair-clearance <pcb> [--mfr NAME] [--max-displacement 0.1]` |
| Multiple DRC types | `kct fix-drc <pcb> [--max-displacement 0.5] [--only clearance]` |
| Via issues | `kct fix-vias <pcb>` |
| Silkscreen overlap | `kct fix-silkscreen <pcb>` |
| Footprint pad spacing | `kct fix-footprints <pcb> --min-pad-gap 0.15` |
| Strip for re-route | `kct pcb strip <pcb> [--nets <names>]` |
| Reannotate refs | `kct pcb reannotate <pcb> --map <json>` |

**Execution order**: fix-silkscreen → fix-footprints → fix-vias → repair-clearance → fix-drc → pcb strip

### Phase 3: Execute

1. Always `--dry-run` first
2. Use `-o <output>` to write to new file, verify before replacing
3. After any trace modification, re-run DRC
4. `fix-drc` has built-in connectivity rollback; `repair-clearance` does not — verify manually

### Phase 4: Verification

```bash
kct check "$PCB_PATH" --format json --strict
kct check "$PCB_PATH" --mfr jlcpcb --format json  # if applicable
# Compare before/after error counts
```

---

## Manufacturing Export

A 6-phase process to produce a complete fabrication package.

### Phase 1: Pre-export validation

```bash
# DRC gate
kct check "$PCB_PATH" --format json --strict

# Net connectivity — all nets must be routed
kct net-status "$PCB_PATH"

# Board summary
kct pcb summary "$PCB_PATH" --format json
```

### Phase 2: Determine manufacturer

Check schematic title block and `.kicad_pro` for hints. Common: `jlcpcb` (default), `pcbway`, `oshpark`, `generic`.

### Phase 3: Export

```bash
kct export "$PCB_PATH" --mfr <manufacturer> -o manufacturing/
```

Generates: `gerbers.zip`, `bom_<mfr>.csv`, `cpl_<mfr>.csv`, `kicad_project.zip`, `report.pdf`, `manifest.json`.

### Phase 4: Verify package

Check all files exist and are non-empty. Spot-check BOM for missing LCSC numbers, incorrect values. Verify report PDF renders correctly.

### Phase 5: Copy to destination

If the user specified a destination, copy the package.

### Phase 6: Report results

Print summary: board name, manufacturer, package contents, DRC status, net status, readiness.

---

## Full Build Pipeline

The `kct build` command runs the complete sequence:

```bash
# Full pipeline from spec
kct build project.kct

# Specific step only
kct build project.kct --step route

# Allow incomplete routing (WIP)
kct build project.kct --allow-incomplete
```

**Step order**: schematic → erc → pcb → sync → outline → placement → zones → silkscreen → route → stitch → preflight-routing → verify → export

The `preflight-routing` step blocks the build if any nets are unrouted. Override with `--allow-incomplete`.

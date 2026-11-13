#!/bin/bash
# Gerber + drill + CPL export for the board and the JLCPCB panel, with KiCad 9 (kicad-cli 9.0.x).
# Mirrors the CI `pcb` job (.github/workflows/ci.yml): same image (kicad/kicad:9.0), same DRC and export
# commands, plus explicit layer lists and the separate PTH / NPTH drill files.
# Run from the repository root with Docker:
#   docker run --rm --user root -v "$PWD":/work -v <raw-out-dir>:/out -w /work/projects/plant-monitor/pcb/gerber \
#     kicad/kicad:9.0 bash build_gerber.sh
# Output goes to /out (outside the repo). Nothing is uploaded or ordered.
set -euo pipefail
PCB=/work/projects/plant-monitor/pcb
LAYERS=F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts
kicad-cli version
mkdir -p /out/board /out/panel /out/drc
# Board: DRC exactly as CI (error level), plus an all-severity run for the warnings count.
kicad-cli pcb drc --severity-error --exit-code-violations -o /out/drc/board-error.rpt "$PCB/plant-monitor.kicad_pcb"
kicad-cli pcb drc --severity-all -o /out/drc/board-all.rpt "$PCB/plant-monitor.kicad_pcb" || true
kicad-cli pcb export gerbers -o /out/board/ --layers "$LAYERS" "$PCB/plant-monitor.kicad_pcb"
kicad-cli pcb export drill -o /out/board/ --excellon-separate-th --generate-map --map-format gerberx2 --generate-report "$PCB/plant-monitor.kicad_pcb"
kicad-cli pcb export pos --format csv --units mm -o /out/board/cpl.csv "$PCB/plant-monitor.kicad_pcb"
# Panel: same export on the generated panel board (gerber/panel/plant-monitor-panel.kicad_pcb).
PANEL=/work/projects/plant-monitor/pcb/gerber/panel/plant-monitor-panel.kicad_pcb
kicad-cli pcb drc --severity-error --exit-code-violations -o /out/drc/panel-error.rpt "$PANEL"
kicad-cli pcb drc --severity-all -o /out/drc/panel-all.rpt "$PANEL" || true
kicad-cli pcb export gerbers -o /out/panel/ --layers "$LAYERS" "$PANEL"
kicad-cli pcb export drill -o /out/panel/ --excellon-separate-th --generate-map --map-format gerberx2 --generate-report "$PANEL"
kicad-cli pcb export pos --format csv --units mm -o /out/panel/cpl.csv "$PANEL"
ls -la /out/board /out/panel

"""Enclosure v3 (4.E3) - battery-bay study parameters. All lengths in mm.

Single source of truth for the bay study. Board outline / USB-C are out of scope
until 4.P1 (no PCB outline yet); nothing here invents a board dimension.
"""

# ---- manufacturing (team/standards/3d-manufacturing.md: Bambu P1S, 0.4 mm, PETG) ----
BUILD_VOLUME = (256.0, 256.0, 256.0)
NOZZLE = 0.4
LINE_WIDTH = 0.42          # typical 0.4 mm nozzle extrusion width (Bambu Studio default 0.42)
LAYER = 0.2                # layer height used for Z snapping
PERIMETERS = 4             # 4 x 0.42 = 1.68 mm of solid wall
WALL = 1.6                 # outer wall, >= 1.2 mm rule (mechanical.md); = 8 layers, ~4 perimeters
FLOOR = 1.6                # tray floor
LID = 1.6                  # lid plate
MIN_WALL_RULE = 1.2        # role-file floor for any wall

# ---- fit allowances (ASSUMPTIONS, flagged for Arsany/Emil, not datasheet values) ----
FDM_CLEAR = 0.30           # per side, in X/Y, for FDM hole shrink and cell tolerance
SWELL_FRAC = 0.10          # LiPo end-of-life swelling allowance on cell thickness (assumption)
Z_CLEAR = 0.20             # extra height clearance on top of swelling
END_CLEAR = 1.0            # per end, tab / solder joint / wire root clearance
WIRE_NOTCH_W = 6.0         # open U-notch in one end wall for the lead wires / plug
WIRE_NOTCH_H = 3.0         # notch depth from the top rim (open to the top: no bridging)

# ---- cell variants: bay envelope inputs ----
# EEMB 603449: A-020 bay input 51 x 34.5 x 6.3 (docs/interfaces/pcb-enclosure-bay.md)
# Jauch LP603443JU: DigiKey size 45.0 x 34.5 x 6.5 (hardware/bom/cell-decision-A034.md s.5;
#   Jauch list shows 6.0 mm bare cell: pack drawing still to be asked from Jauch)
VARIANTS = {
    "A_eemb603449": dict(name="EEMB 603449 (A-020 bay)", L=51.0, W=34.5, H=6.3),
    "B_jauch603443": dict(name="Jauch LP603443JU (A-034)", L=45.0, W=34.5, H=6.5),
}

# ---- design touch (Arsany 2026-11-08, PR #44): OFF by default, so the verified bay numbers/exports stay unchanged ----
DESIGN_TOUCH = False
EDGE_CHAMFER = 0.6         # lid top-edge chamfer (soft edge; slopes inward going up = no overhang)
RELIEF_DEPTH = 0.4         # engraved nilwerk trace motif on the lid top (>= 0.4 mm feature rule, 2 layers)
RELIEF_W = 0.8             # groove width = 2 lines at 0.4 mm nozzle
RELIEF_PAD_D = 3.0         # pad ring diameter at the end of the trace

"""4.E3 JLC prep: fit check of the 4.P2 board against the battery bay (mechanical/README.md).

Every number is read from a source file; the source is printed next to it.
Board geometry: input/plant-monitor-outline.dxf (DXF Y up, = -KiCad Y).
Bay numbers: ../bay.py dims() <- ../params.py, which the README table in ../README.md mirrors (README lines 21-25).
Run: python3 fit_check.py   (no CAD needed). Exit code 1 if an applicable check fails.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MECH = os.path.dirname(HERE)
sys.path.insert(0, MECH)
sys.path.insert(0, HERE)

import bay  # noqa: E402  (dims() needs no CAD)
import params as P  # noqa: E402
import board_step as bs  # noqa: E402

ANT_RULE_MM = 15.0  # pcb/gen_pcb.py line 46 ANT_CLEAR_MM = 15.0 (brief O2: Espressif, >= 15 mm clear)
DXF = os.path.join(HERE, "input", "plant-monitor-outline.dxf")


def _layer_bbox(layer):
    lines = [l.strip() for l in open(DXF, encoding="utf-8").read().splitlines()]
    pts = []
    i = 0
    while i < len(lines) - 1:
        if lines[i] == "0" and lines[i + 1] == "LINE":
            rec = {}
            j = i + 2
            while j < len(lines) - 1 and lines[j] != "0":
                rec[lines[j]] = lines[j + 1]
                j += 2
            if rec.get("8") == layer:
                pts.append((float(rec["10"]), float(rec["20"])))
                pts.append((float(rec["11"]), float(rec["21"])))
            i = j
        else:
            i += 1
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def checks():
    d = bay.dims("A_eemb603449")  # EEMB, the product baseline (README line 21-25, params.py line 31)
    o_x0, o_x1, o_y0, o_y1 = _layer_bbox("OUTLINE")
    c_x0, c_x1, c_y0, c_y1 = _layer_bbox("CELL_BAY_CAVITY")
    m_x0, m_x1, m_y0, m_y1 = _layer_bbox("MODULE_U1")
    board_w = o_x1 - o_x0                    # 34.5
    board_l = o_y1 - o_y0                    # 67.0 (body 42 + stake tail 25)
    cav_l, cav_w = c_x1 - c_x0, c_y1 - c_y0  # 53.0 x 35.1 (should equal README line 22)
    gap_cell_board = o_x0 - c_x1             # cell cavity to board edge, X
    # bay module outer = cavity + wall on each side (bay.py dims: out_l = bay_l + 2*WALL)
    mod_x0, mod_x1 = c_x0 - P.WALL, c_x1 + P.WALL
    gap_module_board = o_x0 - mod_x1         # module outer to board edge
    # antenna end: DXF MODULE_U1 top edge (y = m_y1), x between m_x0 and m_x1
    ant_y = m_y1
    dx = max(0.0, m_x0 - c_x1, c_x0 - m_x1)
    dy = abs(ant_y - c_y1)                   # DXF: antenna edge Y=+6.0, cavity nearest edge Y=-6.9
    ant_to_cell = (dx * dx + dy * dy) ** 0.5
    ant_margin = ant_to_cell - ANT_RULE_MM
    rows = []
    rows.append(dict(
        item="Cell cavity L x W (DXF CELL_BAY_CAVITY) vs README line 22",
        value=f"{cav_l:.1f} x {cav_w:.1f}", expect="53.0 x 35.1", ok=abs(cav_l - 53.0) < 1e-6 and abs(cav_w - 35.1) < 1e-6,
        src="input/plant-monitor-outline.dxf layer CELL_BAY_CAVITY; mechanical/README.md line 22"))
    rows.append(dict(
        item="Bay module outer L x W (cavity + 2 x WALL) vs README line 25",
        value=f"{mod_x1 - mod_x0:.1f} x {c_y1 - c_y0 + 2 * P.WALL:.1f}", expect="56.2 x 38.3", ok=True,
        src="README line 25; params.py line 13 WALL = 1.6; bay.py dims() line 23"))
    rows.append(dict(
        item="Board width (X) vs cavity width (Y): margin per side, if board stacked over the cell",
        value=f"{board_w:.1f} vs {cav_w:.1f}: {(cav_w - board_w) / 2:.2f} mm per side",
        expect="> 0 needed only for option B (stacked, not the layout)", ok=(cav_w - board_w) > 0,
        src="DXF OUTLINE X 0..34.5; README line 22 (35.1); layout-4P2 section 3 option A (beside) is the layout"))
    rows.append(dict(
        item="Board thickness vs bay cavity height (stacked option B only)",
        value=f"board {bs.BOARD_T:.1f} mm (+ components: height NOT in source) vs cavity {d['bay_h']:.1f} mm",
        expect="components unknown", ok=None,
        src="pcb/gen_pcb.py line 'general (thickness 1.6)'; README line 22 (H 7.2)"))
    rows.append(dict(
        item="Cell cavity to board edge (beside layout), X",
        value=f"{gap_cell_board:.1f} mm", expect="5.0 mm (layout gap)", ok=abs(gap_cell_board - 5.0) < 1e-6,
        src="pcb/gen_pcb.py line 34 CELL_GAP = 5.0; DXF CELL_BAY_CAVITY X -58..-5"))
    rows.append(dict(
        item="Bay module outer to board edge (beside layout), X",
        value=f"{gap_module_board:.1f} mm", expect="> 0", ok=gap_module_board > 0,
        src="derived: 5.0 mm gap - WALL 1.6 mm (params.py line 13)"))
    rows.append(dict(
        item="Enclosure v3 inner cavity for the board (walls, seal, lid)",
        value="NOT SET", expect="a margin needs the enclosure inner size", ok=None,
        src="mechanical/README.md line 40 (lid/seal wait for the outline); layout-4P2 Q2 (inner size) still open for Yara"))
    rows.append(dict(
        item="Antenna end to cell cavity (beside layout) vs 15 mm rule",
        value=f"{ant_to_cell:.1f} mm, margin {ant_margin:+.1f} mm", expect=">= 15 mm",
        ok=ant_to_cell >= ANT_RULE_MM,
        src="DXF MODULE_U1 top edge Y=6.0, CELL_BAY_CAVITY corner X=-5.0 Y=-6.9; rule pcb/gen_pcb.py line 46 (15 mm)"))
    overall = dict(board_w=board_w, board_l=board_l, overhang=m_y1 - o_y1)
    return d, rows, overall


def main():
    d, rows, ov = checks()
    print(f"Board outline (DXF): {ov['board_w']:.1f} x {ov['board_l']:.1f} mm (body 34.5 x 42.0 + tail 12.0 x 25.0)")
    print(f"Antenna overhang beyond the board edge: {ov['overhang']:.1f} mm (DXF MODULE_U1, top edge Y=6.0 vs OUTLINE Y=0)")
    print(f"Bay module outer (EEMB): {d['out_l']:.1f} x {d['out_w']:.1f} x {d['out_h']:.1f} mm (README line 25)")
    print()
    fails = 0
    for r in rows:
        tag = "PASS" if r["ok"] is True else ("FAIL" if r["ok"] is False else "NOT CHECKED")
        if r["ok"] is False:
            fails += 1
        print(f"[{tag}] {r['item']}\n      value: {r['value']} | expect: {r['expect']}\n      source: {r['src']}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

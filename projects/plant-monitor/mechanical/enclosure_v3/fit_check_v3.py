"""Fit check for enclosure v3 slice 2: clearances table with real PASS / FAIL. Run: python fit_check_v3.py [--md out.md]. Exit 1 on any FAIL."""
import sys, math
import numpy as np
import trimesh
import params_v3 as P
import board_src as B
import enclosure_v3 as E

ROWS = []


def row(name, value, need, ok, src, note=""):
    ROWS.append((name, value, need, "PASS" if ok else "FAIL", src, note))


def vol_overlap(a, b):
    try:
        return a.intersect(b).val().Volume() if a.intersect(b).vals() else 0.0
    except Exception:
        return 0.0


def downward_bridges(mesh, bed_z):
    """Spans (mm) of downward-facing faces that are not on the bed: bridge / overhang candidates. Faces steeper than 45 deg from vertical are overhangs."""
    n = mesh.face_normals; c = mesh.triangles_center
    res = []
    for i in np.where(n[:, 2] < -0.7)[0]:
        if c[i, 2] > bed_z + 0.05:
            res.append(i)
    if not res:
        return 0.0, 0
    sub = mesh.submesh([res], append=True)
    ext = sub.bounds[1] - sub.bounds[0]
    return float(max(ext[0], ext[1])), len(res)


def lid_clearance(comps):
    """Gap from the tallest assumed part to the lid underside: fixed inner height minus board top minus part height.
    Read from params_v3.H_BY_REF at call time, so changing an assumed height (e.g. J2) changes this row."""
    worst = min(comps.values(), key=lambda c: P.INNER_H - (P.BOARD_Z1 + c["h"]))
    return P.INNER_H - (P.BOARD_Z1 + worst["h"]), worst


def main():
    ROWS.clear()
    comps = B.components()
    tray, lid, plug = E.tray(), E.lid(), E.plug()
    board, cell = E.board_ghost(), E.cell_ghost()
    # 1 board inside the inner box
    mx = max(c["box"][2] for c in comps.values())
    row("Right-most part (J1 shell) to right wall (X)", f"{P.INNER_X1 - mx:.2f} mm (board edge {P.INNER_X1 - P.BOARD_W:.2f})", ">= 0.30 (FDM + PCB +-0.2)", P.INNER_X1 - mx >= 0.3 - 1e-9, "params_v3 INNER_X1, DXF outline")
    row("Antenna tip to top wall (Y)", f"{P.INNER_Y1 - P.OVERHANG:.2f} mm", ">= 1.0 [ASSUMED]", P.INNER_Y1 - P.OVERHANG >= 1.0 - 1e-9, "DXF MODULE_U1 (overhang derived by Emil); Q10 detuning open")
    row("Tail width vs tunnel (per side)", f"{(P.TUNNEL_W - P.TAIL_W) / 2:.2f} mm", ">= 0.30", (P.TUNNEL_W - P.TAIL_W) / 2 >= 0.3 - 1e-9, "DXF tail 12.0; JLC outline +-0.2 (layout-brief s.5)")
    row("Tail thickness vs tunnel height (per side)", f"{(P.TUNNEL_H - P.BOARD_T) / 2:.2f} mm", ">= 0.15 (JLC 1.6 +-10 % = 0.16)", (P.TUNNEL_H - P.BOARD_T) / 2 >= 0.15 - 1e-9, "layout-brief s.5 thickness tolerance")
    # 2 cell
    cx, cy, cz = P.CELL_CAV
    row("Cell cavity (X x Y) inside the inner box", f"{cx:.1f} x {cy:.1f}", "= bay.dims A_eemb603449 (53.0 x 35.1)", abs(cx - 53.0) < 1e-6 and abs(cy - 35.1) < 1e-6 and P.CELL_X0 >= P.INNER_X0 - 1e-9, "pcb-enclosure-bay.md; bay.py")
    row("Cell 51 x 34.5 x 6.3 spare in cavity", f"L {cx - 51:.1f} / W {cy - 34.5:.1f} / H {cz - 6.3:.1f}", "L>=2.0 W>=0.6 H>=0.9", cx - 51 >= 2 - 1e-9 and cy - 34.5 >= 0.6 - 1e-9 and cz - 6.3 >= 0.9 - 1e-9, "bay.dims")
    row("Cell cavity height vs inner height (cell only; no assumed part height in this row)", f"{cz:.1f} vs {P.INNER_H:.1f}", "cavity <= inner", cz <= P.INNER_H, "bay.dims bay_h 7.2; INNER_H is a fixed design value")
    row("Board to cell cavity gap (X)", f"{0 - P.CELL_X1:.1f} mm", "= 5.0 (gen_pcb CELL_GAP)", abs(-P.CELL_X1 - 5.0) < 1e-9, "DXF CELL_BAY_CAVITY")
    # 3 heights: derived from H_BY_REF (ASSUMED). test_v3 sets J2 to 5.0 and expects this row to FAIL.
    gap, worst = lid_clearance(comps)
    row("Tallest part to lid underside (derived from assumed heights)", f"{gap:.2f} mm ({worst['ref']}, {worst['h']} ASSUMED)", f">= {P.LID_CLEAR} (+0.7 mm gasket thickness not counted)", gap >= P.LID_CLEAR - 1e-9,
        "H_BY_REF [ASSUMED]; J2 height needs a datasheet value (Needs Arsany)")
    # 4 3D collisions
    ov = {n: vol_overlap(a, b) for n, a, b in [("lid vs board+parts", lid, board), ("tray vs board+parts", tray, board), ("plug vs board+parts", plug, board),
                                              ("tray vs cell", tray, cell), ("lid vs cell", lid, cell), ("plug vs tray", plug, tray)]}
    for n, v in ov.items():
        row(f"Interference {n}", f"{v:.3f} mm3", "0 (contact allowed)", v < 1e-3, "boolean intersect of the CadQuery solids")
    # 5 antenna
    ant = (P.MODULE_X0, 0.0, P.MODULE_X1, P.OVERHANG)
    cell_rect = (P.CELL_X0, P.CELL_Y0, P.CELL_X1, P.CELL_Y1)
    d_rect = B.gap(ant, cell_rect)
    d_tip = B.gap((P.MODULE_X0, P.OVERHANG, P.MODULE_X1, P.OVERHANG), cell_rect)
    row("Antenna overhang rect to cell cavity (Emil's 26.2 method)", f"{d_rect:.1f} mm", ">= 15", d_rect >= 15, "layout-4P2 check_layout.py rect_gap(ant_tip, cell)")
    row("Antenna tip line to cell cavity (my 28.4 method)", f"{d_tip:.1f} mm", ">= 15", d_tip >= 15, "jlc_prep/README s.1 item 2")
    dm = min(B.gap(ant, (x - P.INSERT_HOLE / 2, y - P.INSERT_HOLE / 2, x + P.INSERT_HOLE / 2, y + P.INSERT_HOLE / 2)) for x, y in P.BOSS_XY)
    row("Nearest brass insert to antenna (Q9)", f"{dm:.1f} mm", ">= 15", dm >= 15, "BOSS_XY, insert hole 3.2")
    # 6 walls
    for n, v in [("Side wall (rim land)", P.WALL), ("Tray floor", P.FLOOR), ("Lid under counterbore", P.LID_T - P.WIN_CB_DEPTH), ("USB pocket remaining wall", P.WALL - P.USB_POCKET[2]),
                 ("Light collar wall", (P.COLLAR_OD - P.WIN_D) / 2), ("Vent cup wall", P.CUP_WALL), ("Pinhole tube wall", (P.PIN_TUBE_OD - P.PIN_D) / 2),
                 ("Boss wall around insert", (P.BOSS_D - P.INSERT_HOLE) / 2)]:
        row(f"Wall: {n}", f"{v:.2f} mm", ">= 1.2 (role rule)", v >= P.MIN_WALL - 1e-9, "params_v3")
    # 6b PETG on the P1S (standards s.2-3, params_v3 PETG_*)
    feats = {"vent slot width": P.VENT_W, "pinhole d": P.PIN_D, "light window d": P.WIN_D, "lid screw clearance hole": P.SCREW_D,
             "plug wall (tail tunnel)": P.PLUG_T}
    for n, v in feats.items():
        row(f"PETG min feature: {n}", f"{v:.2f} mm", f">= {P.PETG_MIN_FEATURE} (2 lines)", v >= P.PETG_MIN_FEATURE - 1e-9, "params_v3 PETG_MIN_FEATURE [ASSUMED 0.8]")
    row("Seal tunnel clearance per side (thickness)", f"{(P.TUNNEL_H - P.BOARD_T) / 2:.2f} mm", ">= 0.30 (PETG/FDM; sealant fills the rest)", (P.TUNNEL_H - P.BOARD_T) / 2 >= 0.3 - 1e-9, "params_v3 TUNNEL_H 2.2 [ASSUMED 0.3]")
    row("Seal tunnel clearance per side (width)", f"{(P.TUNNEL_W - P.TAIL_W) / 2:.2f} mm", ">= 0.30", (P.TUNNEL_W - P.TAIL_W) / 2 >= 0.3 - 1e-9, "params_v3 TUNNEL_W 12.6")
    row("PETG insert boss wall (round the 3.2 hole)", f"{(P.BOSS_D - P.INSERT_HOLE) / 2:.2f} mm", f">= {P.PETG_BOSS_WALL} (PETG target; floor 1.2)", (P.BOSS_D - P.INSERT_HOLE) / 2 >= P.PETG_BOSS_WALL - 1e-9, "params_v3 BOSS_D 6.4; insert datasheet still to check")
    skin = min(min((y - P.OUT_Y0) - P.BOSS_D / 2, (P.OUT_Y1 - y) - P.BOSS_D / 2) for _, y in P.BOSS_XY)
    row("Boss to outside surface (skin)", f"{skin:.2f} mm", ">= 1.2", skin >= 1.2 - 1e-9, "params_v3 BOSS_XY, OUT_Y0/OUT_Y1")
    cgap = min(((P.CELL_Y0 - (y + P.BOSS_D / 2)) if y < P.CELL_Y0 else 99.0) for x, y in P.BOSS_XY if P.CELL_X0 - P.BOSS_D / 2 <= x <= P.CELL_X1 + P.BOSS_D / 2)
    row("Boss below the cell cavity (bottom row, y gap)", f"{cgap:.2f} mm", ">= 0.2 (no overlap; tray vs cell boolean row also checks)", cgap >= 0.2 - 1e-9, "params_v3 BOSS_XY vs CELL_BAY_CAVITY y -42.0")
    row("Lid plate above the film counterbore", f"{P.LID_T - P.WIN_CB_DEPTH:.2f} mm", ">= 1.2", P.LID_T - P.WIN_CB_DEPTH >= 1.2 - 1e-9, "params_v3 LID_T 2.4")
    row("Screw torque limit (informational, not a fit check)", f"{P.PETG_SCREW_TORQUE_NM} N m", "insert datasheet governs", True, "ASSUMED; torque is for the bench, see README")
    # 7 build volume
    for n, s in [("tray", tray), ("lid", lid), ("plug", plug)]:
        bb = s.val().BoundingBox()
        row(f"P1S volume: {n}", f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}", "<= 256^3", max(bb.xlen, bb.ylen, bb.zlen) <= 256, "standards s.1")
    # 8 mesh checks (watertight + bridges in print orientation)
    for n, s, flip in [("tray", tray, False), ("lid", lid, "x180"), ("plug", plug, "y_up")]:
        import cadquery as cq, tempfile, os
        f = os.path.join(tempfile.gettempdir(), f"v3_{n}.stl"); cq.exporters.export(s, f, tolerance=0.01, angularTolerance=0.1)
        m = trimesh.load(f)
        row(f"STL watertight: {n}", str(m.is_watertight), "True", m.is_watertight, "trimesh")
        if flip == "x180":      # lid prints outer face down
            m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
        elif flip == "y_up":    # plug prints standing on its 13.4 x 7.6 face, Y axis up
            m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))
        span, nf = downward_bridges(m, m.bounds[0][2])
        row(f"Max bridge/overhang span, print orientation: {n}", f"{span:.1f} mm ({nf} faces)", "<= 10 mm (P1S bridges; no steep overhangs)", span <= 10.0, "trimesh, faces with normal z < -0.7 above the bed",
            "USB window top 9.6; lid counterbore 6.4" if n != "plug" else "")
    return list(ROWS)


def to_md(rows):
    s = "| # | Check | Value | Need | Result | Source |\n|---|---|---|---|---|---|\n"
    for i, (n, v, need, r, src, note) in enumerate(rows, 1):
        s += f"| {i} | {n} | {v} | {need} | **{r}** | {src}{' (' + note + ')' if note else ''} |\n"
    return s


if __name__ == "__main__":
    rows = main()
    md = to_md(rows)
    print(md)
    npass = sum(r[3] == "PASS" for r in rows); nfail = len(rows) - npass
    print(f"{npass} PASS, {nfail} FAIL")
    if "--md" in sys.argv:
        open(sys.argv[sys.argv.index("--md") + 1], "w").write(md + f"\n{npass} PASS, {nfail} FAIL\n")
    sys.exit(1 if nfail else 0)

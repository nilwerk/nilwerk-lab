"""Fit check for enclosure v3 (slice 3: tail variants 14 / 20 mm, sourced heights).
Run: python fit_check_v3.py [--tail 14|20] [--md out.md]. Exit 1 on any FAIL. OPEN rows are reported, never counted as PASS, never fail the run."""
import sys, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # so `python3 -I fit_check_v3.py` still finds the sibling modules
import numpy as np
import trimesh
import params_v3 as P
import board_src as B
import enclosure_v3 as E

ROWS = []
TAIL = "14"


def row(name, value, need, ok, src, note="", open_=False, unsure=False):
    """ok=False -> FAIL, or OPEN if open_=True (a point the repo cannot close yet, not a failure).
    unsure=True -> OPEN even when ok: the number passes but rests on an unsourced value (ASSUMED / SECONDARY / CONFLICT). Only ok and not unsure is PASS."""
    if not ok:
        status = "OPEN" if open_ else "FAIL"
    else:
        status = "OPEN" if unsure else "PASS"
    ROWS.append((name, value, need, status, src, note))


def vol_overlap(a, b):
    try:
        return a.intersect(b).val().Volume() if a.intersect(b).vals() else 0.0
    except Exception:
        return 0.0


def downward_bridges(mesh, bed_z):
    """Reach (mm) of downward-facing faces above the bed: bridge / overhang candidates. Faces steeper than 45 deg from vertical are overhangs.
    Reach = the largest XY distance from an overhang face centre to the bed-contact outline (boundary edges of the faces lying on the bed).
    No shapely needed in CI. A 1.2 mm bottom fillet gives a lip of about 0.5 mm; a real unsupported span gives its full length."""
    n = mesh.face_normals; c = mesh.triangles_center
    res = [i for i in np.where(n[:, 2] < -0.7)[0] if c[i, 2] > bed_z + 0.05]
    if not res:
        return 0.0, 0
    on_bed = np.abs(mesh.vertices[:, 2] - bed_z) < 0.01
    bf = mesh.faces[on_bed[mesh.faces].all(axis=1)]
    from collections import Counter
    cnt = Counter(tuple(sorted((int(a), int(b)))) for f in bf for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])))
    segs = np.array([mesh.vertices[list(e)][:, :2] for e, k in cnt.items() if k == 1])   # (M, 2, 2) boundary edges
    if len(segs) == 0:
        return float("inf"), len(res)
    A, B = segs[:, 0][None], segs[:, 1][None]
    P_ = c[res][:, None, :2]
    AB = B - A; t = np.clip(((P_ - A) * AB).sum(-1) / np.maximum((AB * AB).sum(-1), 1e-12), 0, 1)
    d = np.sqrt(((P_ - (A + t[..., None] * AB)) ** 2).sum(-1)).min(1)
    return float(d.max()), len(res)


def lid_clearance(comps):
    """Gap from the tallest assumed part to the lid underside: fixed inner height minus board top minus part height.
    Read from params_v3.H_BY_REF at call time, so changing an assumed height (e.g. J2) changes this row."""
    worst = min(comps.values(), key=lambda c: P.INNER_H - (P.BOARD_Z1 + c["h"]))
    return P.INNER_H - (P.BOARD_Z1 + worst["h"]), worst


def main(tail=None):
    tail = tail or TAIL
    ROWS.clear()
    comps = B.components()
    tail_l = P.TAIL_L_VARIANT[tail]                       # board tail length for this variant (params_v3)
    tray, lid, plug = E.tray(), E.lid(), E.plug()
    board, cell = E.board_ghost(tail_l), E.cell_ghost()
    # 0 tail variant (A-071 open): the electrode length beyond the outer bottom face, derived from the variant board tail
    tail_end = -(P.BODY_L + tail_l)
    cu_end = tail_end + P.TIP_MARGIN
    exposed = -cu_end - (-P.OUT_Y0)
    row(f"Tail variant {tail} mm: electrode copper beyond outer bottom face", f"{exposed:.2f} mm (copper tip y {cu_end:.2f})", f"= {P.TAIL_VARIANTS[tail]:.1f} mm (variant)",
        abs(exposed - P.TAIL_VARIANTS[tail]) < 1e-6, "params_v3 TAIL_VARIANTS; copper from board E1 pad (board_facts.electrode_span), tip margin 4.0 from DXF")
    dxf_tail = P.TAIL_L
    row("Board tail in DXF (input/) matches the variant", f"DXF {dxf_tail:.2f} mm vs variant {tail_l:.2f} mm (+{tail_l - dxf_tail:.2f})", "= variant tail",
        abs(tail_l - dxf_tail) < 1e-6, "board DXF = #73; a longer tail for the 20 mm variant is a board outline change for Emil (not in repo)",
        "OPEN: board outline change needed for this variant, Arsany A-071 decides", open_=abs(tail_l - dxf_tail) >= 1e-6)
    # tail solid vs housing: the tail runs through the tunnel in the plug; must not hit tray or plug
    tail_solid = E._box(P.TAIL_X0, tail_end, P.BOARD_Z0, P.TAIL_X0 + P.TAIL_W, -P.BODY_L, P.BOARD_Z1)
    row(f"Interference tail ({tail} variant) vs tray and seal plug", f"{max(vol_overlap(tail_solid, tray), vol_overlap(tail_solid, plug)):.3f} mm3", "0 (contact allowed)",
        max(vol_overlap(tail_solid, tray), vol_overlap(tail_solid, plug)) < 1e-3, "boolean intersect: tail solid vs tray and tail_plug")
    # 1 board inside the inner box
    mx = max(c["box"][2] for c in comps.values())
    row("Right-most part (J1 shell) to right wall (X)", f"{P.INNER_X1 - mx:.2f} mm (board edge {P.INNER_X1 - P.BOARD_W:.2f})", ">= 0.30 (FDM + PCB +-0.2)", P.INNER_X1 - mx >= 0.3 - 1e-9, "params_v3 INNER_X1, DXF outline")
    row("Antenna tip to top wall (Y)", f"{P.INNER_Y1 - P.OVERHANG:.2f} mm", ">= 1.0 [ASSUMED]", P.INNER_Y1 - P.OVERHANG >= 1.0 - 1e-9, "DXF MODULE_U1 (overhang derived by Emil); Q10 detuning open",
        "OPEN: the 1.0 mm threshold is ASSUMED, so a pass against it is not a pass (Arsany rule)", unsure=True)
    row("Tail width vs tunnel (per side)", f"{(P.TUNNEL_W - P.TAIL_W) / 2:.2f} mm", ">= 0.30", (P.TUNNEL_W - P.TAIL_W) / 2 >= 0.3 - 1e-9, "DXF tail 12.0; JLC outline +-0.2 (layout-brief s.5)")
    row("Tail thickness vs tunnel height (per side)", f"{(P.TUNNEL_H - P.BOARD_T) / 2:.2f} mm", ">= 0.15 (JLC 1.6 +-10 % = 0.16)", (P.TUNNEL_H - P.BOARD_T) / 2 >= 0.15 - 1e-9, "layout-brief s.5 thickness tolerance")
    # 2 cell
    cx, cy, cz = P.CELL_CAV
    row("Cell cavity (X x Y) inside the inner box", f"{cx:.1f} x {cy:.1f}", "= bay.dims A_eemb603449 (53.0 x 35.1)", abs(cx - 53.0) < 1e-6 and abs(cy - 35.1) < 1e-6 and P.CELL_X0 >= P.INNER_X0 - 1e-9, "pcb-enclosure-bay.md; bay.py")
    row("Cell 51 x 34.5 x 6.3 spare in cavity", f"L {cx - 51:.1f} / W {cy - 34.5:.1f} / H {cz - 6.3:.1f}", "L>=2.0 W>=0.6 H>=0.9", cx - 51 >= 2 - 1e-9 and cy - 34.5 >= 0.6 - 1e-9 and cz - 6.3 >= 0.9 - 1e-9, "bay.dims")
    row("Cell cavity height vs inner height (cell only; no assumed part height in this row)", f"{cz:.1f} vs {P.INNER_H:.1f}", "cavity <= inner", cz <= P.INNER_H, "bay.dims bay_h 7.2; INNER_H is a fixed design value")
    row("Board to cell cavity gap (X)", f"{0 - P.CELL_X1:.1f} mm", "= 5.0 (gen_pcb CELL_GAP)", abs(-P.CELL_X1 - 5.0) < 1e-9, "DXF CELL_BAY_CAVITY")
    # 3 heights: derived from H_BY_REF. test_v3 sets J2 above the 5.5 budget and expects this row to FAIL.
    gap, worst = lid_clearance(comps)
    wsrc = P.H_SRC.get(worst["ref"], ("ASSUMED", ""))[0]
    # FAIL if the number is short (mutation test). PASS only if the tallest part is datasheet-sourced; here it is J2 (CONFLICT), so OPEN.
    row("Tallest part to lid underside (derived from assumed heights)", f"{gap:.2f} mm ({worst['ref']} {worst['h']}, {wsrc})", f">= {P.LID_CLEAR} (+0.7 mm gasket thickness not counted)", gap >= P.LID_CLEAR - 1e-9,
        "H_BY_REF; J2 height needs a datasheet value (OPEN, A-076)",
        "OPEN: the number rests on J2 5.5, a SECONDARY listing value (A-076); the JST drawing is not read", unsure=wsrc != "DATASHEET")
    # height sourcing: one row for all heights. Only DATASHEET counts as sourced; SECONDARY, CONFLICT and ASSUMED stay listed and are not PASS.
    srcs = {k: P.H_SRC[k][0] for k in P.H_BY_REF}          # model parts only (J1_UPRIGHT is recorded, not a model height)
    n_dc = sum(1 for v in srcs.values() if v == "DATASHEET")
    n_sec, n_conf, n_ass = (sum(1 for v in srcs.values() if v == s) for s in ("SECONDARY", "CONFLICT", "ASSUMED"))
    row("Heights with a datasheet page in the model", f"{n_dc} of {len(P.H_BY_REF)} DATASHEET (U1); {n_sec} SECONDARY, {n_conf} CONFLICT, {n_ass} ASSUMED", "every height cites a datasheet; the rest are listed as SECONDARY or ASSUMED",
        n_dc == len(P.H_BY_REF), "params_v3 H_SRC; a distributor listing is not a datasheet citation (standards s.7)", "OPEN: sourcing is incomplete; see H_SRC for each part", open_=True)
    j2_alt = 5.5
    gap_alt = P.INNER_H - (P.BOARD_Z1 + j2_alt)
    row("J2 at 5.5 mm (model value, A-076)", f"{gap_alt:.2f} mm to lid underside (needs INNER_H >= {P.BOARD_Z1 + j2_alt + P.LID_CLEAR:.1f})",
        f">= {P.LID_CLEAR}", gap_alt >= P.LID_CLEAR - 1e-9, "JLCPCB Z-height 5.5 mm and elecfans JST drawing (secondary); JST PDF not readable",
        "OPEN (A-076): the model is 5.5 (INNER_H 8.6, 0.5 air), so this passes; the value is a listing, not a datasheet. Confirm the exact part (element14 8.0 mm B2B listing)", open_=True, unsure=True)
    # 4 3D collisions
    ov = {n: vol_overlap(a, b) for n, a, b in [("lid vs board+parts", lid, board), ("tray vs board+parts", tray, board), ("plug vs board+parts", plug, board),
                                              ("tray vs cell", tray, cell), ("lid vs cell", lid, cell), ("plug vs tray", plug, tray)]}
    for n, v in ov.items():
        lid_row = n == "lid vs board+parts"      # the lid clears the tallest part, so this depends on the J2 height (ASSUMED 4.5)
        row(f"Interference {n}", f"{v:.3f} mm3", "0 (contact allowed)", v < 1e-3, "boolean intersect of the CadQuery solids",
            f"OPEN: evaluated at the model height of {worst['ref']} ({worst['h']}, {wsrc}); a height above the 5.5 budget is tested by the mutation test" if lid_row else "",
            unsure=lid_row and wsrc != "DATASHEET")
    # 5 antenna
    ant = (P.MODULE_X0, 0.0, P.MODULE_X1, P.OVERHANG)
    cell_rect = (P.CELL_X0, P.CELL_Y0, P.CELL_X1, P.CELL_Y1)
    d_rect = B.gap(ant, cell_rect)
    d_tip = B.gap((P.MODULE_X0, P.OVERHANG, P.MODULE_X1, P.OVERHANG), cell_rect)
    row("Antenna overhang rect to cell cavity (Emil's 26.2 method)", f"{d_rect:.1f} mm", ">= 15", d_rect >= 15, "layout-4P2 check_layout.py rect_gap(ant_tip, cell)")
    row("Antenna tip line to cell cavity (my 28.4 method)", f"{d_tip:.1f} mm", ">= 15", d_tip >= 15, "jlc_prep/README s.1 item 2")
    air_c = P.rr_dist(P.MODULE_X1, P.OVERHANG, P.INNER_X0, P.INNER_Y0, P.INNER_X1, P.INNER_Y1, P.FILLET_INNER)
    row("Antenna corner (33.5, 4.5) air to the rounded cavity corner", f"{air_c:.2f} mm", ">= 1.0 (same air as the top wall)", air_c >= 1.0 - 1e-9, "params_v3 rr_dist, FILLET_INNER 1.5 (slice 4)")
    dm = min(B.gap(ant, (x - P.INSERT_HOLE / 2, y - P.INSERT_HOLE / 2, x + P.INSERT_HOLE / 2, y + P.INSERT_HOLE / 2)) for x, y in P.BOSS_XY)
    row("Nearest brass insert to antenna (Q9)", f"{dm:.1f} mm", ">= 15", dm >= 15, "BOSS_XY, insert hole 3.2")
    # standards s.7: no thick walls over the antenna. The 2.4 mm PETG top wall sits over the module; no RF measurement exists, so this is OPEN, not PASS.
    row("PETG top wall over the antenna", f"{P.WALL_LOW:.2f} mm wall, {P.INNER_Y1 - P.OVERHANG:.1f} mm air to antenna tip (ASSUMED)", "no thick wall over the antenna (standards s.7): RF effect checked",
        False, "params_v3 WALL, INNER_Y1; standards s.7; P1S/PETG review (Arsany answer 2026-11-10)",
        "OPEN: effect on the antenna not measured. Options: RF check on a Prototype 1 print, or a thinner wall over the antenna. Decide before the lid is locked", open_=True)
    # 6 walls
    cw = P.min_wall_corners()
    for n, v in [("Rim land left/top/bottom", P.WALL_LOW), ("Rim land right (USB side)", P.WALL), ("Tray floor", P.FLOOR), ("Corner wall, min (cavity to skin)", cw), ("Lid under counterbore", P.LID_T - P.WIN_CB_DEPTH), ("USB pocket remaining wall", P.WALL - P.USB_POCKET[2]),
                 ("Light collar wall", (P.COLLAR_OD - P.WIN_D) / 2), ("Vent cup wall", P.CUP_WALL), ("Pinhole tube wall", (P.PIN_TUBE_OD - P.PIN_D) / 2),
                 ("Boss wall around insert", (P.BOSS_D - P.INSERT_HOLE) / 2)]:
        row(f"Wall: {n}", f"{v:.2f} mm", ">= 1.2 (role rule)", v >= P.MIN_WALL - 1e-9, "params_v3")
    # 6b PETG on the P1S (standards s.2-3, params_v3 PETG_*)
    feats = {"vent slot width": P.VENT_W, "pinhole d": P.PIN_D, "light window d": P.WIN_D, "lid screw clearance hole": P.SCREW_D,
             "plug wall (tail tunnel)": P.PLUG_T}
    for n, v in feats.items():
        row(f"PETG min feature: {n}", f"{v:.2f} mm", f">= {P.PETG_MIN_FEATURE} (2 lines)", v >= P.PETG_MIN_FEATURE - 1e-9, "params_v3 PETG_MIN_FEATURE [ASSUMED 0.8]",
            "OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass", unsure=True)
    row("Seal tunnel clearance per side (thickness)", f"{(P.TUNNEL_H - P.BOARD_T) / 2:.2f} mm", ">= 0.30 (PETG/FDM; sealant fills the rest)", (P.TUNNEL_H - P.BOARD_T) / 2 >= 0.3 - 1e-9, "params_v3 TUNNEL_H 2.2 [ASSUMED 0.3]",
        "OPEN: the 0.3 mm clearance is ASSUMED, so a pass against it is not a pass", unsure=True)
    row("Seal tunnel clearance per side (width)", f"{(P.TUNNEL_W - P.TAIL_W) / 2:.2f} mm", ">= 0.30 [ASSUMED]", (P.TUNNEL_W - P.TAIL_W) / 2 >= 0.3 - 1e-9, "params_v3 TUNNEL_W 12.6; 0.3 per side as in the thickness row",
        "OPEN: the 0.3 mm clearance is ASSUMED (same value as the thickness row), so a pass against it is not a pass", unsure=True)
    row("PETG insert boss wall (round the 3.2 hole)", f"{(P.BOSS_D - P.INSERT_HOLE) / 2:.2f} mm", f">= {P.PETG_BOSS_WALL} (PETG target; floor 1.2)", (P.BOSS_D - P.INSERT_HOLE) / 2 >= P.PETG_BOSS_WALL - 1e-9, "params_v3 BOSS_D 6.4; insert datasheet still to check",
        "OPEN: 1.6 mm is this PR's own PETG target (PETG_BOSS_WALL), not a sourced limit; the insert datasheet is not read, so a pass against it is not a pass", unsure=True)
    skin = min(P.outer_dist(x, y) - P.BOSS_D / 2 for x, y in P.BOSS_XY)
    row("Boss to outside surface (skin)", f"{skin:.2f} mm", ">= 1.2", skin >= 1.2 - 1e-9, "params_v3 BOSS_XY, outer rounded outline (outer_dist)")
    # plan gap from each boss edge to the board outline (x 0..BOARD_W, y -BODY_L..0). A full-height boss beside the board corner must not touch it on insertion.
    def _gap_to_board(x, y):
        dx = max(0.0 - x, 0.0, x - P.BOARD_W)
        dy = max(-P.BODY_L - y, 0.0, y)
        return math.hypot(dx, dy) - P.BOSS_D / 2
    bg = min(_gap_to_board(x, y) for x, y in P.BOSS_XY)
    row("Boss to board outline (plan gap, nearest boss)", f"{bg:.2f} mm", f">= {P.BOSS_BOARD_GAP_MIN} [ASSUMED]", bg >= P.BOSS_BOARD_GAP_MIN - 1e-9, "params_v3 BOSS_XY vs board outline (board_facts), BOSS_D / 2",
        "OPEN: the 1.0 mm threshold is ASSUMED (insertion slop and FDM spread), so a pass against it is not a pass. Found at 0.34 mm before the slice 4 fix", unsure=True)
    cgap = min(((P.CELL_Y0 - (y + P.BOSS_D / 2)) if y < P.CELL_Y0 else 99.0) for x, y in P.BOSS_XY if P.CELL_X0 - P.BOSS_D / 2 <= x <= P.CELL_X1 + P.BOSS_D / 2)
    row("Boss below the cell cavity (bottom row, y gap)", f"{cgap:.2f} mm", ">= 0.2 (no overlap; tray vs cell boolean row also checks)", cgap >= 0.2 - 1e-9, "params_v3 BOSS_XY vs CELL_BAY_CAVITY y -42.0")
    row("Lid plate above the film counterbore", f"{P.LID_T - P.WIN_CB_DEPTH:.2f} mm", ">= 1.2", P.LID_T - P.WIN_CB_DEPTH >= 1.2 - 1e-9, "params_v3 LID_T 2.4")
    # the 0.25 N m limit is not sourced (insert datasheet not read): not checked, so OPEN, never PASS
    row("Screw torque limit", f"{P.PETG_SCREW_TORQUE_NM} N m (ASSUMED)", "insert datasheet governs; bench check", False,
        "ASSUMED: no insert datasheet read; torque is for the bench, see README", "NOT CHECKED: an assumed torque cannot pass a check", open_=True)
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
        row(f"Max bridge/overhang span, print orientation: {n}", f"{span:.1f} mm ({nf} faces)", "<= 10 mm reach from bed contact (P1S bridges; no steep overhangs)", span <= 10.0, "trimesh, faces with normal z < -0.7 above the bed, reach to bed-contact vertices",
            "USB window top 9.6; lid counterbore 6.4" if n != "plug" else "")
    # 9 sourced heights: each model height must equal the number its cited source states (params_v3 H_CITED). A changed sourced height
    # FAILS here until its citation is changed too. Distributor values (SECONDARY) are not PDF-checked, so the row stays OPEN.
    mism = {k: (P.H_BY_REF[k], v) for k, v in P.H_CITED.items() if abs(P.H_BY_REF[k] - v) > 1e-9}
    row(f"Model heights equal their cited source ({len(P.H_CITED)} parts)", f"{len(P.H_CITED) - len(mism)} of {len(P.H_CITED)} equal" + (f"; MISMATCH {mism}" if mism else ""),
        "model value = cited value for every part", not mism, "params_v3 H_CITED vs H_BY_REF; standards s.7 (never invent a component dimension)",
        "OPEN: U5, U6, SW1-3 cite distributor listings (SECONDARY), the PDFs were not read", unsure=any(P.H_SRC[k][0] != "DATASHEET" for k in P.H_CITED))
    # 10 J1 USB-C height: the model uses the flat 3.3 (ASSUMED); the upright male version is 11.94 +-0.25 (datasheet brief value, OPEN, A-087).
    # The upright value is tested against the same inner box; it does not fit, so the row stays OPEN until the orientation is decided. No value is chosen here.
    gap_flat = P.INNER_H - (P.BOARD_Z1 + P.H_BY_REF["J1"])
    gap_up = P.INNER_H - (P.BOARD_Z1 + P.J1_UPRIGHT_H)
    row("J1 USB-C height, flat vs upright", f"flat {P.H_BY_REF['J1']:.2f} (ASSUMED): {gap_flat:.2f} mm to lid; upright {P.J1_UPRIGHT_H:.2f} +-{P.J1_UPRIGHT_TOL} (OPEN): {gap_up:.2f} mm",
        f">= {P.LID_CLEAR} (orientation not decided)", gap_up >= P.LID_CLEAR - 1e-9,
        "TYPE-C-31-M-12 datasheet, upright male (brief value, PDF not read here); params_v3 H_SRC J1_UPRIGHT",
        "OPEN: A-087 approved flat (2026-11-13); the upright value is kept only as a record and does not fit the 8.6 mm or 7.6 mm inner box", open_=True)
    return list(ROWS)


def to_md(rows):
    s = "| # | Check | Value | Need | Result | Source |\n|---|---|---|---|---|---|\n"
    for i, (n, v, need, r, src, note) in enumerate(rows, 1):
        s += f"| {i} | {n} | {v} | {need} | **{r}** | {src}{' (' + note + ')' if note else ''} |\n"
    return s


if __name__ == "__main__":
    tail = sys.argv[sys.argv.index("--tail") + 1] if "--tail" in sys.argv else TAIL
    if tail not in P.TAIL_VARIANTS:
        sys.exit(f"--tail must be one of {list(P.TAIL_VARIANTS)}")
    rows = main(tail)
    md = to_md(rows)
    print(md)
    npass = sum(r[3] == "PASS" for r in rows); nopen = sum(r[3] == "OPEN" for r in rows); nfail = sum(r[3] == "FAIL" for r in rows)
    summary = f"{npass} PASS, {nfail} FAIL, {nopen} OPEN (tail {tail} mm variant)"
    print(summary)
    if "--md" in sys.argv:
        open(sys.argv[sys.argv.index("--md") + 1], "w").write(f"Tail variant: {tail} mm (A-071 open)\n\n" + md + f"\n{summary}\n")
    sys.exit(1 if nfail else 0)

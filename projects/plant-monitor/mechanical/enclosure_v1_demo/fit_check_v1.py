"""Fit check for the v1 demo housing (4.E5), round 3 (fit for 5 mm parts, owner A-094, 28 Nov). Run: python fit_check_v1.py [--md out.md]. Exit 1 on any FAIL.
PASS = geometry check against MEASURED / RULE inputs only. Anything resting on an ASSUMED, WIRING-typical (UNVERIFIED) or BRIEF value is OPEN, never PASS.
OPEN rows are reported, never counted as PASS, never fail the run. A row marked 'NOT MET' is a requirement the design cannot meet as briefed: OPEN, with the reason."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import trimesh
import cadquery as cq
import params_v1 as P
import enclosure_v1 as E

ROWS = []


def row(name, value, need, ok, src, note="", unsure=False):
    """ok False -> FAIL. ok and unsure -> OPEN (rests on an unverified value). ok and not unsure -> PASS."""
    status = "FAIL" if not ok else ("OPEN" if unsure else "PASS")
    ROWS.append((name, value, need, status, src, note))


def mesh_of(wp):
    import tempfile
    f = os.path.join(tempfile.gettempdir(), f"v1c_{os.getpid()}.stl")
    cq.exporters.export(wp, f, tolerance=0.02, angularTolerance=0.15)
    return trimesh.load(f)


BRIDGE_Z = [P.USB_SM_Z + P.PLUG_H / 2, P.USB_TP_Z + P.PLUG_H / 2, P.CABLE_Z + P.CABLE_H / 2]   # closed openings: ceilings are bridges


def is_bridge(c):
    """Ceiling of a closed opening in the base wall (left USB-C wall or bottom cable wall), not an overhang."""
    z_hit = any(abs(c[2] - zb) < 0.05 for zb in BRIDGE_Z)
    in_wall = c[0] < P.IX0 + 0.1 or c[1] < P.IY0 + 0.1
    return z_hit and in_wall


def overhang_reach(mesh, bed_z=0.0):
    """Largest horizontal distance from an overhanging face (normal steeper than 45 deg down, above the bed) to the nearest bed-contact boundary edge.
    Ceilings of the closed openings are bridges (see bridge_spans) and are not counted here."""
    n = mesh.face_normals; c = mesh.triangles_center
    res = [i for i in np.where(n[:, 2] < -0.72)[0] if c[i, 2] > bed_z + 0.05 and not is_bridge(c[i])]
    if not res:
        return 0.0, 0
    on_bed = np.abs(mesh.vertices[:, 2] - bed_z) < 0.01
    bf = mesh.faces[on_bed[mesh.faces].all(axis=1)]
    from collections import Counter
    cnt = Counter(tuple(sorted((int(a), int(b)))) for f in bf for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])))
    segs = np.array([mesh.vertices[list(e)][:, :2] for e, k in cnt.items() if k == 1])
    A, B = segs[:, 0][None], segs[:, 1][None]
    p = c[res][:, None, :2]
    AB = B - A; t = np.clip(((p - A) * AB).sum(-1) / np.maximum((AB * AB).sum(-1), 1e-12), 0, 1)
    d = np.sqrt(((p - (A + t[..., None] * AB)) ** 2).sum(-1)).min(1)
    return float(d.max()), len(res)


def vol(a, b):
    try:
        i = a.intersect(b)
        return i.val().Volume() if i.vals() else 0.0
    except Exception:
        return 0.0


def rect_dist(x0, y0, x1, y1, px, py):
    dx = max(x0 - px, 0, px - x1); dy = max(y0 - py, 0, py - y1)
    return math.hypot(dx, dy)


def main():
    ROWS.clear()
    tray, lid = E.tray(), E.lid()
    mt, ml = mesh_of(tray), mesh_of(E.lid_print())
    pb, parts, cell = E.perfboard_ghost(), E.parts_ghost(), E.cell_ghost()
    # ---------- manufacturing / printability (RULE) ----------
    for nm, m in (("base", mt), ("lid (print orientation)", ml)):
        ext = m.extents
        row(f"Fits P1S build volume: {nm}", f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm", "<= 256 x 256 x 256", all(ext <= np.array(P.BUILD)), "RULE standard s1 (P1S build volume); extents depend on ASSUMED pin tips and WIRING USB-C heights", "derived geometry, not a measured part: OPEN until the printed parts are measured", unsure=True)
        row(f"Watertight STL: {nm}", f"watertight={m.is_watertight}, volume {m.volume / 1000:.1f} cm3", "watertight, positive volume", bool(m.is_watertight) and m.volume > 0, "RULE standard s1 (watertight STL)")
        row(f"On the bed: {nm}", f"z min {m.bounds[0][2]:.3f}", "z min = 0", abs(m.bounds[0][2]) < 1e-6, "RULE standard (print orientation, on the bed)")
        reach, nf = overhang_reach(m)
        row(f"No supports: {nm}", f"overhang reach {reach:.2f} mm ({nf} faces, bridges excluded)", "<= 0.8 mm (ASSUMED threshold, not a rule)", reach <= 0.8, "RULE: minimise supports (no numeric value in the standard); 0.8 mm = ASSUMED: the 0.6 mm bed-edge chamfer lip plus margin", "the 0.6 mm top-edge chamfer on the bed is the only overhang; a numeric limit must come from a print test", unsure=True)
    bridges = [(round(float(x), 1), round(float(y), 1), round(float(z), 2)) for x, y, z in (mt.triangles_center[i] for i in np.where(mt.face_normals[:, 2] < -0.72)[0]) if is_bridge(np.array([x, y, z]))]
    row("Bridges (closed openings, base): spans without support", f"{len(bridges)} ceiling faces; USB-C ceilings {P.PLUG_W:.0f} mm span x 1.6 mm deep, cable slot {P.CABLE_W:.0f} mm span", "<= 15 mm PETG bridge (ASSUMED)", max(P.PLUG_W, P.CABLE_W) <= 15.0, "ASSUMED PETG bridging on 0.4 mm nozzle; round 2 closes the openings (parting plane above them)", "print test on the first base: check the USB-C ceilings and the cable slot", unsure=True)
    walls = dict(wall=P.WALL, floor=P.FLOOR, lid=P.LID_T, cradle_stop=P.STOP_T, fin=P.FIN_T)
    wmin = min(walls.values())
    row("Wall / floor / lid / cradle >= 1.2 mm", f"min {wmin:.1f} mm (walls {P.WALL}, floor {P.FLOOR}, lid {P.LID_T}, cradle/fins {P.STOP_T})", f">= {P.MIN_WALL}", wmin >= P.MIN_WALL, "RULE mechanical.md")
    row("Wall >= 1.6 mm (task requirement)", f"outer wall {P.WALL}, floor {P.FLOOR}, lid {P.LID_T}", ">= 1.6", min(P.WALL, P.FLOOR, P.LID_T) >= 1.6, "RULE (task 4.E5 requirement)")
    bw = (P.BOSS_D - P.INSERT_HOLE) / 2
    row("Boss wall around the insert hole", f"{bw:.2f} mm (boss {P.BOSS_D}, hole {P.INSERT_HOLE})", f">= {P.MIN_WALL}", bw >= P.MIN_WALL, "RULE; hole d is ASSUMED (insert not chosen)", "hole diameter OPEN: check with the insert actually bought", unsure=True)
    rim = (P.BOSS_D - (P.SPIGOT_D + 2 * P.SPIGOT_CLEAR)) / 2
    row("Boss rim around the spigot counterbore", f"{rim:.2f} mm (boss {P.BOSS_D} is ASSUMED)", f">= {P.MIN_WALL}", rim >= P.MIN_WALL, "RULE (wall) with ASSUMED boss d", "rests on the ASSUMED boss diameter", unsure=True)
    row("PETG min feature: vent slot width", f"{P.VENT_W} mm", ">= 1.0 (ASSUMED PETG floor, as in v3)", P.VENT_W >= 1.0, "ASSUMED floor", unsure=True)
    row("PETG min feature: BOOT/RESET pin hole", f"d {P.BTN_HOLE_D} mm", ">= 1.8 for a paperclip (ASSUMED)", P.BTN_HOLE_D >= 1.8, "ASSUMED", "holes print smaller than drawn: prototype check", unsure=True)
    # ---------- perfboard pocket and support (MEASURED 70 x 50 x 2) ----------
    row("Perfboard pocket clearance, left and bottom/top sides", f"left {-P.IX0:.2f}, bottom {P.FIT:.2f}, top {P.FIT:.2f}", f"= FIT {P.FIT} (standard 0.2-0.4)", abs(-P.IX0 - P.FIT) < 1e-9, "perfboard MEASURED; FIT per standard s3 (value chosen, not measured)", "vacuous as a fit check (IX0 is defined as -FIT): OPEN until the printed pocket is measured at Prototype 1", unsure=True)
    ov = vol(pb, tray)
    row("Model-internal (self-consistency): perfboard ghost vs base", f"{ov:.3f} mm3", "0", ov < 1e-6, "perfboard MEASURED; z position from STANDOFF_H (4.0 mm pin tips ASSUMED)", "checks only that the model is self-consistent; not a fit proof and not a height check", unsure=True)
    pad_end = P.PAD_XS[-1][1]
    pad_ok = all(0 <= a < b <= P.PB_L for a, b in P.PAD_XS)
    row("Support pads inside the board outline", f"pads {P.PAD_W} wide at x {P.PAD_XS}", "inside 70 x 50", pad_ok, "perfboard MEASURED")
    pad_clear = pad_end < P.CAV_X0 - P.STOP_T
    row("Support pads clear of the cell cradle", f"pad end x {pad_end:.1f} vs cradle wall x {P.CAV_X0 - P.STOP_T:.1f}", "pad end < cradle wall", pad_clear, "geometry (cell BRIEF)", unsure=True)
    row("Support pad 2 outside the antenna keep-out box", f"pad 2 x {P.PAD_XS[1][0]}-{P.PAD_XS[1][1]} vs keep-out x {P.KO_CAD[0]:.0f}-{P.KO_CAD[2]:.0f}: gap {P.PAD_XS[1][0] - P.KO_CAD[2]:.1f} mm", "no overlap", not (P.PAD_XS[1][0] < P.KO_CAD[2] and P.PAD_XS[1][1] > P.KO_CAD[0]), "geometry; keep-out WIRING; 1.0 mm gap = ASSUMED (WIRING gen_wiring route margin, applied by me to the pad)", unsure=True)
    overhang_span = P.PB_L - pad_end
    row("Board support span (NOT MET: no support under x 48-70)", f"board supported on x {P.PAD_XS[0][0]:.0f}-{pad_end:.0f}; x {pad_end:.0f}-{P.PB_L:.0f} ({overhang_span:.0f} mm) unsupported", "support under the full board", True, "geometry; the cell occupies the board's right side for all y", "NOT MET, accepted as A-099 option a (Lead's record): no pad can stand under x 48-70 (cradle wall at x 48.5-49.7, cell from x 49.7). Sag not measured; re-check on the first bench build", unsure=True)
    row("Solder-side clearance under the board (cell region)", f"{P.STANDOFF_H:.1f} mm floor-to-board = cell cavity {P.CELL_CAV[2]} + pin tips {P.PIN_TIP} + margin {P.PIN_MARGIN}", f">= {P.CELL_CAV[2] + P.PIN_TIP} (cavity + WIRING pin tips)", P.Z_PB_BOT - P.Z_FLOOR >= P.CELL_CAV[2] + P.PIN_TIP, "WIRING.md about 4 mm pin tips UNVERIFIED; cell BRIEF", "needs Arsany's under-board height with trimmed pins and wires (round 2 raised the gap from 5.0 to 12.2)", unsure=True)
    bgap = min(rect_dist(0, 0, P.PB_L, P.PB_W, x, y) - P.BOSS_D / 2 for x, y in P.boss_xy())
    row("Boss edge to perfboard outline", f"{bgap:.2f} mm", f">= {P.BOSS_GAP_MIN} (ASSUMED threshold)", bgap >= P.BOSS_GAP_MIN, "ASSUMED threshold", unsure=True)
    # lid hold-down pins stand on free spots of the board (plan positions from WIRING layout, UNVERIFIED)
    bad = []
    for (hx, hy_doc) in P.HOLD_DOC:
        for n, (x0, y0, x1, y1, h, s) in P.PARTS.items():
            if x0 - P.HOLD_D / 2 < hx < x1 + P.HOLD_D / 2 and y0 - P.HOLD_D / 2 < hy_doc < y1 + P.HOLD_D / 2:
                bad.append((n, hx, hy_doc))
    row("Lid hold-down pins avoid every part", "overlaps: " + (", ".join(map(str, bad)) if bad else "none"), "none", not bad, "layout WIRING.md sec. 5 (grid UNVERIFIED)", "positions follow Emil's plan, not a measured board", unsure=True)
    # ---------- heights (all unmeasured) ----------
    tall = max(P.PARTS.items(), key=lambda kv: kv[1][4])
    gap = P.Z_TOP - (P.Z_PB_TOP + tall[1][4])
    row("Tallest part to lid underside (lid limit)", f"{gap:.1f} mm ({tall[0]} {tall[1][4]} mm owner bound; lid underside z {P.Z_TOP:.1f}; max part height with {P.LID_MARGIN} mm margin {P.MAX_PART_H:.1f} mm)", f">= {P.LID_MARGIN} margin", gap >= P.LID_MARGIN - 1e-9, "OWNER bound 5 mm (A-094, 28 Nov); per-part height UNVERIFIED", "the owner's bound is not a caliper measurement of each part: J1 with jumper and J3 with Dupont plug still to be measured", unsure=True)
    # stress rows: the round-2 WIRING typical heights, kept to show what the owner's 5 mm bound is worth
    gw = P.Z_TOP - (P.Z_PB_TOP + P.PART_H_WIRING["SuperMini"])
    row("Stress: SuperMini at WIRING stack height (6.8 mm above the perfboard top) to lid underside", f"{gw:.1f} mm clearance (WIRING 6.8 conflicts with the owner bound 5 mm)", f">= {P.LID_MARGIN} margin", gw >= P.LID_MARGIN - 1e-9, "WIRING.md typical, UNVERIFIED", "if the WIRING stack is right the lid still clears; the owner measurement settles it", unsure=True)
    gj = P.Z_TOP - (P.Z_PB_TOP + P.PART_H_WIRING["J1"])
    row("NOT MET if WIRING height is right: J1/J3 headers at 12 mm to lid underside", f"{gj:.1f} mm clearance (needs {P.LID_MARGIN} mm); J1 and J3 would hit the lid by {P.LID_MARGIN - gj:.1f} mm", f">= {P.LID_MARGIN} margin", True, "WIRING typical 12 mm, UNVERIFIED; owner bound says at most 5 mm", "the 5 mm bound is load-bearing: a 12 mm header needs the lid raised by about 2 mm, or the header cut down (Arsany to measure)", unsure=True)
    for n in ("SuperMini", "TP4056", "BH1750", "AHT20"):
        g = P.Z_TOP - (P.Z_PB_TOP + P.PARTS[n][4])
        row(f"Part top to lid underside: {n}", f"{g:.1f} mm (height {P.PARTS[n][4]} owner bound)", ">= 2.0", g >= 2.0, "OWNER bound 5 mm (A-094); per-part UNVERIFIED", unsure=True)
    tubes = None
    for x, y in E.btn_xy():
        c = E._cyl(x, y, P.Z_PB_TOP, P.Z_TOP + 1, P.BTN_TUBE_OD + 0.2)
        tubes = c if tubes is None else tubes.union(c)
    ov = vol(parts, lid.cut(tubes))
    row("Interference lid vs part boxes (assumed heights)", f"{ov:.3f} mm3 (BOOT/RESET guide tubes excluded)", "0", ov < 1e-6, "ASSUMED heights", "the guide tubes enter the SuperMini envelope by design: the box height 6.8 is the USB-C top, the keys are lower (assumed 5.1)", unsure=True)
    row("BOOT/RESET guide tubes vs SuperMini keys", f"tube end z {P.Z_PB_TOP + P.BTN_PRESS_H + P.BTN_GAP:.1f} vs key top z {P.Z_PB_TOP + P.BTN_PRESS_H:.1f} (assumed)", "gap >= 0.5", P.BTN_GAP >= 0.5, "key height ASSUMED", unsure=True)
    # ---------- lid height (round 2 target: about half the round-1 shell) ----------
    row("Lid shell above the parting plane", f"{P.LID_SHELL_H:.1f} mm (round 2: 5.4; round 1: {P.LID_SHELL_H_R1:.1f}; {P.LID_SHELL_H / P.LID_SHELL_H_R1 * 100:.0f} % of round 1)", f"about half of round 1: <= {P.LID_SHELL_H_R1 / 2 + 0.5:.1f}", P.LID_SHELL_H <= P.LID_SHELL_H_R1 / 2 + 0.5, "round 2 target (Arsany 2026-11-16); round 3 skirt ASSUMED", "round 3: the parting plane (above the USB-C tops) now governs the lid, not the parts: lid = seam + skirt 2.0 + plate 1.6", unsure=True)
    guide_bottom = P.Z_PB_TOP + P.BTN_PRESS_H + P.BTN_GAP
    lid_low = min(guide_bottom, P.Z_SPLIT, P.Z_PB_TOP + P.BTN_PRESS_H + P.BTN_GAP, P.Z_PB_TOP + P.HOLD_GAP)
    row("Lid part depth incl. hanging pins/guides (print height)", f"{P.Z_LID_TOP - lid_low:.1f} mm (round 1: 15.3; hold-down pins at z {P.Z_PB_TOP + P.HOLD_GAP:.1f} set the lowest point)", "report only", True, "geometry", "round 3: the shell above the seam is 3.6 mm (round 2: 5.4, round 1: 11.0); the lid part depth is set by its hold-down pins, which reach down to the board", unsure=True)
    # ---------- openings ----------
    for nm, ydoc, zc, src in (("SuperMini USB-C (flash/serial)", P.USB_SM_YDOC, P.USB_SM_Z, "centre z from WIRING stack, UNVERIFIED"), ("TP4056 USB-C (charge)", P.USB_TP_YDOC, P.USB_TP_Z, "centre z from WIRING stack, UNVERIFIED")):
        yc = P.cy(ydoc)
        probe = cq.Vector(P.OX0 + 0.8, yc, zc)
        free = not tray.val().isInside(probe) and not lid.val().isInside(probe)
        row(f"Opening reaches {nm}", f"opening {P.PLUG_W} x {P.PLUG_H} mm at y {yc:.1f}, z {zc:.2f}; wall-to-connector gap {(P.PARTS['SuperMini'][0] if 'Super' in nm else P.PARTS['TP4056'][0]) - P.IX0:.1f} mm", "wall open at the connector centre", free, src, "plug overmold size ASSUMED 14 x 8; connector centre height and the SuperMini 4.5 mm setback UNVERIFIED", unsure=True)
    top_open = max(P.USB_SM_Z, P.USB_TP_Z) + P.PLUG_H / 2
    row("Both USB-C openings fully in the base (parting plane above them)", f"split z {P.Z_SPLIT}; highest opening top {top_open:.2f}; rim {P.Z_SPLIT - top_open:.2f} mm", f"rim >= {P.SPLIT_RIM} mm", P.Z_SPLIT - top_open >= P.SPLIT_RIM - 1e-9, "geometry; openings from WIRING stack", "the lid carries no USB-C cut (rounds 2 and 3)", unsure=True)
    row("USB-C openings do not overlap each other", f"gap {abs(P.cy(P.USB_SM_YDOC) - P.cy(P.USB_TP_YDOC)) - P.PLUG_W:.1f} mm", ">= 1.6 (wall)", abs(P.cy(P.USB_SM_YDOC) - P.cy(P.USB_TP_YDOC)) - P.PLUG_W >= 1.6, "WIRING positions UNVERIFIED", unsure=True)
    # BOOT/RESET
    row("BOOT / RESET pin guide tubes", f"tube end z {guide_bottom:.1f} over assumed button top z {P.Z_PB_TOP + P.BTN_PRESS_H:.1f}, pitch {abs(P.BTN_YDOC[1] - P.BTN_YDOC[0]):.1f} mm, tube d {P.BTN_TUBE_OD}", "pitch >= tube OD + 1.6; gap > 0", abs(P.BTN_YDOC[1] - P.BTN_YDOC[0]) >= P.BTN_TUBE_OD + 1.6, "WIRING: key centres UNVERIFIED, which key is BOOT UNVERIFIED", "both keys reachable from the top; the pin travel (1.0 mm gap + key stroke) is not tested; button height ASSUMED", unsure=True)
    # BH1750
    row("BH1750 light window", f"window d {P.BH_WIN_D}, collar OD {P.BH_COLLAR_OD}, open hole (skin {P.LIGHT_SKIN} mm)", "window >= 4 mm over the chip, chip centre UNVERIFIED", P.BH_WIN_D >= 4.0, "WIRING: chip centre about x 49, y 8.5 UNVERIFIED", "an open hole is not splash-proof (v1 indoor demo); a diffuser skin changes the lux reading", unsure=True)
    row("BH1750 outside the antenna keep-out", f"BH1750 body x {P.PARTS['BH1750'][0]}-{P.PARTS['BH1750'][2]} vs keep-out x {P.ANT_KEEPOUT_DOC[0]}-{P.ANT_KEEPOUT_DOC[2]}", "x0 >= 40", P.PARTS["BH1750"][0] >= P.ANT_KEEPOUT_DOC[2], "WIRING layout UNVERIFIED", unsure=True)
    # AHT20 vents
    d_tp = math.hypot(max(0, P.PARTS["AHT20"][0] - P.PARTS["TP4056"][2]), max(0, P.PARTS["TP4056"][1] - P.PARTS["AHT20"][3]))
    d_ldo = P.PARTS["AHT20"][0] - P.PARTS["SuperMini"][2]
    row("AHT20 vent slots over the sensor", f"{P.VENT_N} slots {P.VENT_W} x {P.VENT_L} at pitch {P.VENT_PITCH}, span x {P.AHT_XYDOC[0] - (P.VENT_N - 1) * P.VENT_PITCH / 2 - P.VENT_W / 2:.1f}-{P.AHT_XYDOC[0] + (P.VENT_N - 1) * P.VENT_PITCH / 2 + P.VENT_W / 2:.1f} vs body {P.PARTS['AHT20'][0]}-{P.PARTS['AHT20'][2]}", "span inside the sensor body", P.AHT_XYDOC[0] - (P.VENT_N - 1) * P.VENT_PITCH / 2 - P.VENT_W / 2 >= P.PARTS["AHT20"][0] and P.AHT_XYDOC[0] + (P.VENT_N - 1) * P.VENT_PITCH / 2 + P.VENT_W / 2 <= P.PARTS["AHT20"][2], "AHT20 body MEASURED 15 x 10, position from WIRING layout UNVERIFIED", unsure=True)
    row("AHT20 distance to the warm parts (TP4056, SuperMini LDO)", f"{d_tp:.1f} mm to TP4056, {d_ldo:.1f} mm to the SuperMini", ">= 15 (WIRING)", min(d_tp, d_ldo) >= 15.0, "WIRING 5 rule; positions UNVERIFIED", "a closed box still warms the air: v1 temperature is not an ambient reading", unsure=True)
    d_cell = math.hypot(max(0, P.CAV_X0 - P.PARTS["AHT20"][2]), 0)
    row("AHT20 distance to the cell (NOT MET in plan: cell under the AHT20)", f"{d_cell:.1f} mm in plan (AHT20 x {P.PARTS['AHT20'][0]}-{P.PARTS['AHT20'][2]} lies over the cell's right part)", ">= 15 (round 1 rule, cell as heat source)", True, "WIRING layout + BRIEF cell; thermal effect of a charging cell not measured", "NOT MET, accepted as A-098 option b (Lead's record): AHT20 stays over the cell. Thermal effect not measured; re-check on the first bench build. The cell is not a WIRING heat source", unsure=True)
    # ---------- J1, J3, cable ----------
    jx, jy = P.J1_XYDOC[0], P.cy(P.J1_XYDOC[1])
    row("J1 jumper reachable through the lid hatch", f"hatch {P.HATCH[0]} x {P.HATCH[1]} at ({jx}, {jy:.1f}); J1 body {P.PARTS['J1'][2] - P.PARTS['J1'][0]:.1f} x {P.PARTS['J1'][3] - P.PARTS['J1'][1]:.1f}", "hatch > J1 body by >= 2 mm per side", P.HATCH[0] - (P.PARTS['J1'][2] - P.PARTS['J1'][0]) >= 4.0 and P.HATCH[1] - (P.PARTS['J1'][3] - P.PARTS['J1'][1]) >= 4.0, "WIRING J1 c1 r8/r9, shunt size ASSUMED", "J1 type and hole position UNVERIFIED; open hatch, no cover", unsure=True)
    cable_ok = P.CABLE_Z - P.CABLE_H / 2 > P.Z_PB_TOP and P.CABLE_Z + P.CABLE_H / 2 < P.Z_SPLIT - P.SPLIT_RIM
    row("Soil cable exit", f"slot {P.CABLE_W} x {P.CABLE_H} mm at x {P.J3_XYDOC[0]:.1f}, z {P.CABLE_Z - P.CABLE_H / 2:.1f}-{P.CABLE_Z + P.CABLE_H / 2:.1f} (5.5 above the board top)", "slot in the base wall, below the parting rim", cable_ok, "WIRING: J3 plug about 12 high, exit about x 40; Dupont size UNVERIFIED", "the soil sensor JST-PH end and cable length are not needed here", unsure=True)
    row("Space for the Dupont plug beyond the board edge", f"strip {P.STRIP_BOT - P.FIT:.1f} mm below the board", ">= 10 (ASSUMED plug length)", P.STRIP_BOT - P.FIT >= 10.0, "ASSUMED", unsure=True)
    # ---------- LiPo under the board ----------
    cav = P.CELL_CAV
    row("LiPo cavity vs cell (brief 51 x 34.5 x 6.3)", f"cavity {cav[0]:.1f} x {cav[1]:.1f} x {cav[2]:.1f}; cell {P.CELL_CELL[0]} x {P.CELL_CELL[1]} x {P.CELL_CELL[2]}", "cavity >= cell + 0.3/side + 10 % swell", cav[0] >= P.CELL_CELL[0] + 2 and cav[1] >= P.CELL_CELL[1] + 0.6 and cav[2] >= P.CELL_CELL[2] * 1.1, "BRIEF A-020 (no datasheet read); WIRING quotes 49 x 34 x 6.0 (UNVERIFIED conflict)", "cell datasheet not read in this task", unsure=True)
    ovc = vol(cell, tray)
    row("Interference cell vs base (cradle, stops, posts, floor)", f"{ovc:.3f} mm3", "0", ovc < 1e-6, "BRIEF cell size", unsure=True)
    row("Interference cell vs perfboard (cell under the board, no touch)", f"cell top z {P.Z_FLOOR + P.CELL_CELL[2]:.1f} vs board underside z {P.Z_PB_BOT:.1f} (gap {P.Z_PB_BOT - P.Z_FLOOR - P.CELL_CELL[2]:.1f} mm before pins)", "cell top below board underside", P.Z_FLOOR + P.CELL_CELL[2] < P.Z_PB_BOT, "BRIEF cell + WIRING pins", unsure=True)
    row("Battery placement vs brief and WIRING sec. 5 (NOT MET: cell not fully under the board; accepted for the demo as A-100 option a, known deviation from WIRING sec. 5)", f"{P.CELL_UNDER_FRAC * 100:.0f} % of the cell footprint under the board (x {P.CELL_X0:.1f}-{min(P.CELL_X1, P.PB_L):.1f}, full y)", "100 % (brief: lies under the perfboard)", True, "geometry (round 2 placement)", "NOT MET by design (OPEN until Arsany decides). Brief: under the perfboard. No free 34.5 x 51 mm rectangle exists under the board outside the keep-out (0 placements found). WIRING sec. 5 puts the battery beside or below the LEFT half, outside x 22-40 y 0-25 (doc); round 2 puts it under the RIGHT half (x 50-84.5 CAD, 57 % under). Closest option chosen: 10 mm own margin from the keep-out box, 23 mm from the antenna end point. Decision A-100.", unsure=True)
    # cell and the USB-C side
    row("No cell under the USB-C openings", f"cell x {P.CELL_X0:.1f}-{P.CELL_X1:.1f}; USB-C openings in the left wall at x {P.IX0:.1f}; gap {P.CELL_X0 - P.IX0:.1f} mm", "cell 20+ mm from the USB-C wall", P.CELL_X0 - P.IX0 >= 20.0, "RULE (task); geometry", unsure=True)
    # cell lead route and strain relief (bottom strip)
    jx0, jx1, jy0, jy1 = P.JST_PARK
    park_box = E._box(jx0, jy0, P.Z_FLOOR, jx1, jy1, P.Z_FLOOR + 6.0)
    ovp = vol(park_box, tray)
    row("JST-PH pair parking zone free", f"zone x {jx0}-{jx1}, y {jy0}-{jy1} (16 x 6.5), overlap {ovp:.2f} mm3", "0 overlap with base solids", ovp < 1e-6, "JST-PH ~6 x 4.5 ASSUMED", "parking space only: the pair is unplugged with the lid off", unsure=True)
    row("LiPo lead: strain relief", f"S-bend posts x{len(P.SR_POSTS)} d {P.POST_D} at {P.SR_POSTS}; lead notch x {P.LEAD_NOTCH_X[0]}-{P.LEAD_NOTCH_X[1]} ({P.LEAD_NOTCH_X[1] - P.LEAD_NOTCH_X[0]:.0f} wide) in the bottom stop", "notch >= 3 mm for 2 wires", P.LEAD_NOTCH_X[1] - P.LEAD_NOTCH_X[0] >= 3.0, "JST-PH size ASSUMED; lead length UNVERIFIED; route to TP4056 B+/B- ASSUMED", "the lead route (about 60 mm) is not modelled as a solid; S-bend and tie take the tension off the mated plug", unsure=True)
    # ---------- antenna keep-out (RF) ----------
    kx0, ky0, kx1, ky1 = P.KO_CAD
    dmin_cell = min(rect_dist(kx0, ky0, kx1, ky1, P.CELL_X0, y) for y in (P.CELL_Y0, P.CELL_Y1))
    row("Cell outside the antenna keep-out box", f"cell x {P.CELL_X0:.1f}-{P.CELL_X1:.1f} vs keep-out x {kx0:.0f}-{kx1:.0f}; no overlap", "no overlap", not (P.CELL_X0 < kx1 and P.CELL_X1 > kx0 and P.CELL_Y0 < ky1 and P.CELL_Y1 > ky0), "WIRING keep-out, cell BRIEF", unsure=True)
    row("Cell 10 mm OWN margin from the keep-out box edge (X side)", f"{dmin_cell:.1f} mm (cell edge x {P.CELL_X0:.1f} to keep-out edge x {kx1:.0f})", f">= {P.ANT_MARGIN} mm (own margin, ASSUMED)", dmin_cell >= P.ANT_MARGIN - 1e-9, "own margin; WIRING asks 10+ mm beyond the ANTENNA END (UNVERIFIED), not from the box edge", "the 10 mm is my own margin from the box edge; WIRING's wording is the antenna end, where the cell is 23.0 mm away (next row)", unsure=True)
    ant_end = (P.ANT_END_DOC[0], P.cy((P.ANT_END_DOC[1] + P.ANT_END_DOC[3]) / 2))
    dend = rect_dist(P.CELL_X0, P.CELL_Y0, P.CELL_X1, P.CELL_Y1, ant_end[0], ant_end[1])
    row("Cell to the antenna end point", f"{dend:.1f} mm (end at x {ant_end[0]:.0f}, y {ant_end[1]:.0f} CAD)", ">= 10 (WIRING 'about 10+ mm beyond the antenna end', UNVERIFIED)", dend >= 10.0, "WIRING sec. 5 / keep-out note; the earlier 20 mm figure was my own ASSUMED stricter value, not a WIRING number", "23.0 mm meets the WIRING 10+ mm wording; no metal-foil threshold exists in the sources", unsure=True)
    # metal (bosses) and antenna
    metal = P.boss_xy()
    dmin = min(rect_dist(kx0, ky0, kx1, ky1, x, y) - P.BOSS_D / 2 for x, y in metal)
    row("Metal (insert, screw) outside the antenna keep-out", f"nearest boss edge {dmin:.1f} mm from the keep-out box (x {kx0:.0f}-{kx1:.0f}, y {ky0:.0f}-{ky1:.0f})", f">= {P.ANT_MARGIN} (WIRING 'about 10+ mm', UNVERIFIED)", dmin >= P.ANT_MARGIN, "WIRING keep-out, SuperMini antenna position UNVERIFIED", unsure=True)
    dm = min(math.hypot(x - ant_end[0], y - ant_end[1]) - P.BOSS_D / 2 for x, y in metal)
    row("Antenna end to the nearest screw boss", f"{dm:.1f} mm", ">= 15 (v3 RF rule, ASSUMED)", dm >= 15.0, "ASSUMED rule from v3 (Q9)", unsure=True)
    row("Plastic over the antenna", f"PETG lid {P.LID_T} mm, air gap about {P.Z_TOP - (P.Z_PB_TOP + P.PARTS['SuperMini'][4]):.1f} mm", "plastic only, no metal, no carbon-filled filament", True, "design: PETG black/grey/white only; RF effect of a 1.6 mm PETG wall NOT measured", "all printed parts are plain PETG; the only metal is the M2 screws/inserts, outside the keep-out", unsure=True)
    # ---------- fasteners ----------
    sl, need = P.screw_len()
    row("Lid screw length", f"M2 x {sl} (need >= {need:.1f} mm for 3 mm engagement)", "standard length >= need", sl >= need, "geometry; head 4.0 x 1.3 and insert depth ASSUMED", "fastener length from the formula above (round 2 was M2 x 8); fastener and insert purchase is Arsany's decision, nothing ordered", unsure=True)
    row("Screw posts: boss x lid post alignment", f"{len(P.BOSS_XY)} bosses, spigot d {P.SPIGOT_D} in d {P.SPIGOT_D + 2 * P.SPIGOT_CLEAR:.1f}", "spigot clearance 0.2 per side (standard 0.2-0.4)", 0.2 <= P.SPIGOT_CLEAR <= 0.4, "RULE s3 (clearance range)", "printed fit OPEN until Prototype 1", unsure=True)
    return ROWS


def to_md(rows):
    out = ["| # | Check | Value | Need | Status | Source | Note |", "|---|---|---|---|---|---|---|"]
    for i, (n, v, need, st, src, note) in enumerate(rows, 1):
        out.append(f"| {i} | {n} | {v} | {need} | **{st}** | {src} | {note} |")
    return "\n".join(out)


if __name__ == "__main__":
    rows = main()
    for r in rows:
        print(f"{r[3]:5} {r[0]}: {r[1]}  [need {r[2]}] ({r[4]}) {r[5]}")
    npass = sum(r[3] == "PASS" for r in rows); nfail = sum(r[3] == "FAIL" for r in rows)
    nnotmet = sum(r[3] == "OPEN" and "NOT MET" in r[0] for r in rows); nopen = sum(r[3] == "OPEN" for r in rows) - nnotmet
    print(f"\n{npass} PASS / {nfail} FAIL / {nnotmet} NOT MET / {nopen} OPEN")
    if "--md" in sys.argv:
        open(sys.argv[sys.argv.index("--md") + 1], "w").write(to_md(rows) + "\n")
    sys.exit(1 if nfail else 0)

"""Fit check for the v1 demo housing (4.E5). Run: python fit_check_v1.py [--md out.md]. Exit 1 on any FAIL.
PASS = geometry check against MEASURED / RULE inputs only. Anything resting on an ASSUMED, WIRING-typical (UNVERIFIED) or BRIEF value is OPEN, never PASS.
OPEN rows are reported, never counted as PASS, never fail the run."""
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
    f = os.path.join(tempfile.gettempdir(), f"v1_{os.getpid()}.stl")
    cq.exporters.export(wp, f, tolerance=0.02, angularTolerance=0.15)
    return trimesh.load(f)


def overhang_reach(mesh, bed_z=0.0):
    """Largest horizontal distance from an overhanging face (normal steeper than 45 deg down, above the bed) to the nearest bed-contact boundary edge."""
    n = mesh.face_normals; c = mesh.triangles_center
    res = [i for i in np.where(n[:, 2] < -0.72)[0] if c[i, 2] > bed_z + 0.05]
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


def main():
    ROWS.clear()
    tray, lid = E.tray(), E.lid()
    mt, ml = mesh_of(tray), mesh_of(E.lid_print())
    pb, parts, cell = E.perfboard_ghost(), E.parts_ghost(), E.cell_ghost()
    # ---------- manufacturing / printability (RULE) ----------
    for nm, m in (("base", mt), ("lid (print orientation)", ml)):
        ext = m.extents
        row(f"Fits P1S build volume: {nm}", f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm", "<= 256 x 256 x 256", all(ext <= np.array(P.BUILD)), "RULE standard s1")
        row(f"Watertight STL: {nm}", f"watertight={m.is_watertight}, volume {m.volume / 1000:.1f} cm3", "watertight, positive volume", bool(m.is_watertight) and m.volume > 0, "mesh check")
        row(f"On the bed: {nm}", f"z min {m.bounds[0][2]:.3f}", "z min = 0", abs(m.bounds[0][2]) < 1e-6, "print orientation")
        reach, nf = overhang_reach(m)
        row(f"No supports: {nm}", f"overhang reach {reach:.2f} mm ({nf} faces)", "<= 0.8 mm (bed-edge chamfer lip only)", reach <= 0.8, "RULE: minimise supports; 0.6 mm top-edge chamfer on the bed is the only overhang")
    walls = dict(wall=P.WALL, floor=P.FLOOR, lid=P.LID_T, divider=P.DIV_T, cradle=P.LOW_T, fin=P.FIN_T)
    wmin = min(walls.values())
    row("Wall / floor / lid / divider >= 1.2 mm", f"min {wmin:.1f} mm (walls {P.WALL}, floor {P.FLOOR}, lid {P.LID_T}; divider/cradle/fins {P.DIV_T})", f">= {P.MIN_WALL}", wmin >= P.MIN_WALL, "RULE mechanical.md")
    row("Wall >= 1.6 mm (task requirement)", f"outer wall {P.WALL}, floor {P.FLOOR}, lid {P.LID_T}", ">= 1.6", min(P.WALL, P.FLOOR, P.LID_T) >= 1.6, "task 4.E5")
    bw = (P.BOSS_D - P.INSERT_HOLE) / 2
    row("Boss wall around the insert hole", f"{bw:.2f} mm (boss {P.BOSS_D}, hole {P.INSERT_HOLE})", f">= {P.MIN_WALL}", bw >= P.MIN_WALL, "RULE; hole d is ASSUMED (insert not chosen)", "hole diameter OPEN: check with the insert actually bought", unsure=True)
    rim = (P.BOSS_D - (P.SPIGOT_D + 2 * P.SPIGOT_CLEAR)) / 2
    row("Boss rim around the spigot counterbore", f"{rim:.2f} mm", f">= {P.MIN_WALL}", rim >= P.MIN_WALL, "RULE")
    row("PETG min feature: vent slot width", f"{P.VENT_W} mm", ">= 1.0 (ASSUMED PETG floor, as in v3)", P.VENT_W >= 1.0, "ASSUMED floor", unsure=True)
    row("PETG min feature: BOOT/RESET pin hole", f"d {P.BTN_HOLE_D} mm", ">= 1.8 for a paperclip (ASSUMED)", P.BTN_HOLE_D >= 1.8, "ASSUMED", "holes print smaller than drawn: prototype check", unsure=True)
    # ---------- perfboard pocket (MEASURED 70 x 50 x 2) ----------
    row("Perfboard pocket clearance, left/top/bottom sides", f"left {-P.IX0:.2f}, board vs divider {P.DIV_X0 - P.PB_L:.2f}", f"= FIT {P.FIT} (standard 0.2-0.4)", abs(-P.IX0 - P.FIT) < 1e-9 and abs(P.DIV_X0 - P.PB_L - P.FIT) < 1e-9, "perfboard MEASURED; FIT per standard s3", "the real fit of the printed pocket is OPEN until Prototype 1")
    ov = vol(pb, tray)
    row("Interference perfboard vs base", f"{ov:.3f} mm3", "0", ov < 1e-6, "perfboard MEASURED")
    pad_ok = P.PAD_X[0] + P.PAD_L < P.PAD_X[1] and P.PAD_X[1] + P.PAD_L <= P.PB_L
    row("Support pads inside the board outline", f"pads {P.PAD_L} x {P.PAD_W} mm at x {P.PAD_X}", "inside 70 x 50", pad_ok, "perfboard MEASURED")
    row("Solder-side clearance under the board", f"{P.STANDOFF_H:.1f} mm standoff", ">= 4 mm (WIRING typical) ", P.STANDOFF_H >= 4.0, "WIRING.md: about 4 mm UNVERIFIED", "needs Arsany's under-board height with trimmed pins and wires", unsure=True)
    def dist_rect(x, y):
        dx = max(0 - x, 0, x - P.PB_L); dy = max(0 - y, 0, y - P.PB_W)
        return math.hypot(dx, dy)
    bgap = min(dist_rect(x, y) - P.BOSS_D / 2 for x, y in P.boss_xy())
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
    row("Tallest part to lid underside", f"{gap:.1f} mm ({tall[0]} {tall[1][4]} mm assumed)", f">= {P.LID_MARGIN} margin", gap >= P.LID_MARGIN - 1e-9, "WIRING heights, UNVERIFIED", "J1 with jumper and J3 with Dupont plug are the tallest; heights to be measured", unsure=True)
    for n in ("SuperMini", "TP4056", "BH1750", "AHT20"):
        g = P.Z_TOP - (P.Z_PB_TOP + P.PARTS[n][4])
        row(f"Part top to lid underside: {n}", f"{g:.1f} mm (height {P.PARTS[n][4]} assumed)", ">= 2.0", g >= 2.0, "WIRING height UNVERIFIED", unsure=True)
    tubes = None
    for x, y in E.btn_xy():
        c = E._cyl(x, y, P.Z_PB_TOP, P.Z_TOP + 1, P.BTN_TUBE_OD + 0.2)
        tubes = c if tubes is None else tubes.union(c)
    ov = vol(parts, lid.cut(tubes))
    row("Interference lid vs part boxes (assumed heights)", f"{ov:.3f} mm3 (BOOT/RESET guide tubes excluded)", "0", ov < 1e-6, "ASSUMED heights", "the guide tubes enter the SuperMini envelope by design: the box height 6.8 is the USB-C top, the keys are lower (assumed 5.1)", unsure=True)
    row("BOOT/RESET guide tubes vs SuperMini keys", f"tube end z {P.Z_PB_TOP + P.BTN_PRESS_H + P.BTN_GAP:.1f} vs key top z {P.Z_PB_TOP + P.BTN_PRESS_H:.1f} (assumed)", "gap >= 0.5", P.BTN_GAP >= 0.5, "key height ASSUMED", unsure=True)
    # ---------- openings ----------
    for nm, ydoc, zc, src in (("SuperMini USB-C (flash/serial)", P.USB_SM_YDOC, P.USB_SM_Z, "centre z from WIRING stack, UNVERIFIED"), ("TP4056 USB-C (charge)", P.USB_TP_YDOC, P.USB_TP_Z, "centre z from WIRING stack, UNVERIFIED")):
        yc = P.cy(ydoc)
        probe = cq.Vector(P.OX0 + 0.8, yc, zc)
        free = not tray.val().isInside(probe) and not lid.val().isInside(probe)
        row(f"Opening reaches {nm}", f"opening {P.PLUG_W} x {P.PLUG_H} mm at y {yc:.1f}, z {zc:.2f}; wall-to-connector gap {(P.PARTS['SuperMini'][0] if 'Super' in nm else P.PARTS['TP4056'][0]) - P.IX0:.1f} mm", "wall open at the connector centre", free, src, "plug overmold size ASSUMED 14 x 8; connector centre height and the SuperMini 4.5 mm setback UNVERIFIED", unsure=True)
    row("Both USB-C openings straddle the parting plane", f"split z {P.Z_SPLIT}; openings z {P.USB_TP_Z - P.PLUG_H / 2:.2f}-{P.USB_SM_Z + P.PLUG_H / 2:.2f}", "split inside both", all(zc - P.PLUG_H / 2 < P.Z_SPLIT < zc + P.PLUG_H / 2 for zc in (P.USB_SM_Z, P.USB_TP_Z)), "geometry: half-slots open to the rims, no bridging")
    sm_y, tp_y = P.cy(P.USB_SM_YDOC), P.cy(P.USB_TP_YDOC)
    row("USB-C openings do not overlap each other", f"gap {abs(sm_y - tp_y) - P.PLUG_W:.1f} mm", ">= 1.6 (wall)", abs(sm_y - tp_y) - P.PLUG_W >= 1.6, "WIRING positions UNVERIFIED", unsure=True)
    # BOOT/RESET
    z_btn = P.Z_PB_TOP + P.BTN_PRESS_H + P.BTN_GAP
    row("BOOT / RESET pin guide tubes", f"tube end z {z_btn:.1f} over assumed button top z {P.Z_PB_TOP + P.BTN_PRESS_H:.1f}, pitch {abs(P.BTN_YDOC[1] - P.BTN_YDOC[0]):.1f} mm, tube d {P.BTN_TUBE_OD}", "pitch >= tube OD + 1.6; gap > 0", abs(P.BTN_YDOC[1] - P.BTN_YDOC[0]) >= P.BTN_TUBE_OD + 1.6, "WIRING: key centres UNVERIFIED, which key is BOOT UNVERIFIED", "both keys are reachable; the pin travel (1.0 mm gap + key stroke) is not tested; button height ASSUMED", unsure=True)
    # BH1750
    row("BH1750 light window", f"window d {P.BH_WIN_D}, collar OD {P.BH_COLLAR_OD}, open hole (skin {P.LIGHT_SKIN} mm)", "window >= 4 mm over the chip, chip centre UNVERIFIED", P.BH_WIN_D >= 4.0, "WIRING: chip centre about x 49, y 8.5 UNVERIFIED", "an open hole is not splash-proof (v1 indoor demo); a diffuser skin changes the lux reading", unsure=True)
    ant_x = P.ANT_END_DOC[0]
    row("BH1750 outside the antenna keep-out", f"BH1750 body x {P.PARTS['BH1750'][0]}-{P.PARTS['BH1750'][2]} vs keep-out x {P.ANT_KEEPOUT_DOC[0]}-{P.ANT_KEEPOUT_DOC[2]}", "x0 >= 40", P.PARTS["BH1750"][0] >= P.ANT_KEEPOUT_DOC[2], "WIRING layout UNVERIFIED", unsure=True)
    # AHT20 vents
    d_tp = math.hypot(max(0, P.PARTS["AHT20"][0] - P.PARTS["TP4056"][2]), max(0, P.PARTS["TP4056"][1] - P.PARTS["AHT20"][3]))
    d_ldo = P.PARTS["AHT20"][0] - P.PARTS["SuperMini"][2]
    row("AHT20 vent slots over the sensor", f"{P.VENT_N} slots {P.VENT_W} x {P.VENT_L} at pitch {P.VENT_PITCH}, span x {P.AHT_XYDOC[0] - (P.VENT_N - 1) * P.VENT_PITCH / 2 - P.VENT_W / 2:.1f}-{P.AHT_XYDOC[0] + (P.VENT_N - 1) * P.VENT_PITCH / 2 + P.VENT_W / 2:.1f} vs body {P.PARTS['AHT20'][0]}-{P.PARTS['AHT20'][2]}", "span inside the sensor body", P.AHT_XYDOC[0] - (P.VENT_N - 1) * P.VENT_PITCH / 2 - P.VENT_W / 2 >= P.PARTS["AHT20"][0] and P.AHT_XYDOC[0] + (P.VENT_N - 1) * P.VENT_PITCH / 2 + P.VENT_W / 2 <= P.PARTS["AHT20"][2], "AHT20 body MEASURED 15 x 10, position from WIRING layout UNVERIFIED", unsure=True)
    row("AHT20 distance to the warm parts (TP4056, SuperMini LDO)", f"{d_tp:.1f} mm to TP4056, {d_ldo:.1f} mm to the SuperMini", ">= 15 (WIRING)", min(d_tp, d_ldo) >= 15.0, "WIRING 5 rule; positions UNVERIFIED", "a closed box still warms the air: v1 temperature is not an ambient reading", unsure=True)
    d_cell = P.CELL_X0 - (P.PARTS["AHT20"][2])
    row("AHT20 distance to the cell", f"{d_cell:.1f} mm in plan", ">= 15", d_cell >= 15.0, "WIRING layout + BRIEF cell", unsure=True)
    # ---------- J1, J3, cable, LiPo ----------
    jx, jy = P.J1_XYDOC[0], P.cy(P.J1_XYDOC[1])
    row("J1 jumper reachable through the lid hatch", f"hatch {P.HATCH[0]} x {P.HATCH[1]} at ({jx}, {jy:.1f}); J1 body {P.PARTS['J1'][2] - P.PARTS['J1'][0]:.1f} x {P.PARTS['J1'][3] - P.PARTS['J1'][1]:.1f}", "hatch > J1 body by >= 2 mm per side", P.HATCH[0] - (P.PARTS['J1'][2] - P.PARTS['J1'][0]) >= 4.0 and P.HATCH[1] - (P.PARTS['J1'][3] - P.PARTS['J1'][1]) >= 4.0, "WIRING J1 c1 r8/r9, shunt size ASSUMED", "J1 type and hole position UNVERIFIED; open hatch, no cover", unsure=True)
    row("Soil cable exit", f"slot {P.CABLE_W} x {P.CABLE_H} mm at x {P.J3_XYDOC[0]:.1f}, z {P.Z_SPLIT - P.CABLE_H / 2:.1f}-{P.Z_SPLIT + P.CABLE_H / 2:.1f}", "slot over J3 plug axis (assumed z 14.1)", P.Z_SPLIT - P.CABLE_H / 2 < P.Z_PB_TOP + 5.5 < P.Z_SPLIT + P.CABLE_H / 2, "WIRING: J3 plug about 12 high, exit about x 40; Dupont size UNVERIFIED", "the soil sensor JST-PH end and cable length are not needed here", unsure=True)
    row("Space for the Dupont plug beyond the board edge", f"strip {P.STRIP_BOT - P.FIT:.1f} mm below the board", ">= 10 (ASSUMED plug length)", P.STRIP_BOT - P.FIT >= 10.0, "ASSUMED", unsure=True)
    cav = P.CELL_CAV
    row("LiPo cavity vs cell (brief 51 x 34.5 x 6.3)", f"cavity {cav[0]:.1f} x {cav[1]:.1f} x {cav[2]:.1f}; cell {P.CELL_CELL[0]} x {P.CELL_CELL[1]} x {P.CELL_CELL[2]}", "cavity >= cell + 0.3/side + 10 % swell", cav[0] >= P.CELL_CELL[0] + 2 and cav[1] >= P.CELL_CELL[1] + 0.6 and cav[2] >= P.CELL_CELL[2] * 1.1, "BRIEF A-020 (no datasheet read); WIRING quotes 49 x 34 x 6.0 (UNVERIFIED conflict)", "cell datasheet not read in this task", unsure=True)
    ovc = vol(cell, tray)
    row("Interference cell envelope vs base", f"{ovc:.3f} mm3", "0", ovc < 1e-6, "BRIEF cell size", unsure=True)
    row("LiPo lead: strain relief", f"S-bend posts x{len(P.SR_POSTS)} d {P.POST_D}, divider U-notch y {P.NOTCH_Y[0]}-{P.NOTCH_Y[1]} mm ({P.NOTCH_Y[1] - P.NOTCH_Y[0]:.0f} wide), connector channel {P.CH_W} mm", "notch >= 3 mm for 2 wires; channel >= 6", P.NOTCH_Y[1] - P.NOTCH_Y[0] >= 3.0 and P.CH_W >= 6.0, "JST-PH housing size ASSUMED about 6 x 4.5; lead length UNVERIFIED", "S-bend takes the tension off the mated plug; a tie is not modelled", unsure=True)
    row("Battery lead lane free of parts", f"lane y doc {P.LANE_YDOC}", "no part in the lane (WIRING plan)", all(not (y0 < P.LANE_YDOC[1] and y1 > P.LANE_YDOC[0] and x1 > 30) for n, (x0, y0, x1, y1, h, s) in P.PARTS.items() if n in ("AHT20", "BH1750", "J3")), "layout WIRING UNVERIFIED; notch at doc y " + f"{P.cy(P.NOTCH_Y[1]):.0f}-{P.cy(P.NOTCH_Y[0]):.0f}", unsure=True)
    # ---------- antenna keep-out (RF) ----------
    kx0, ky0_doc, kx1, ky1_doc = P.ANT_KEEPOUT_DOC
    ky0, ky1 = P.cy(ky1_doc), P.IY1
    def dist_keepout(x, y):
        dx = max(kx0 - x, 0, x - kx1); dy = max(ky0 - y, 0, y - ky1)
        return math.hypot(dx, dy)
    metal = [(x, y) for x, y in P.boss_xy()]
    dmin = min(dist_keepout(x, y) - P.BOSS_D / 2 for x, y in metal)
    row("Metal (insert, screw) outside the antenna keep-out", f"nearest boss edge {dmin:.1f} mm from the keep-out box (x {kx0}-{kx1}, y {ky0:.0f}-{ky1:.1f})", f">= {P.ANT_MARGIN} (WIRING 'about 10+ mm', UNVERIFIED)", dmin >= P.ANT_MARGIN, "WIRING keep-out, SuperMini antenna position UNVERIFIED", unsure=True)
    # nearest metal to the antenna end point itself
    ant = (P.ANT_END_DOC[0], P.cy((P.ANT_END_DOC[1] + P.ANT_END_DOC[3]) / 2))
    dm = min(math.hypot(x - ant[0], y - ant[1]) - P.BOSS_D / 2 for x, y in metal)
    row("Antenna end to the nearest screw boss", f"{dm:.1f} mm", ">= 15 (v3 RF rule, ASSUMED)", dm >= 15.0, "ASSUMED rule from v3 (Q9)", unsure=True)
    dc = P.CELL_X0 - ant[0]
    row("Antenna end to the cell (metal foil)", f"{dc:.1f} mm", ">= 20 (ASSUMED)", dc >= 20.0, "ASSUMED", "WIRING requires the cell outside the keep-out; no RF measurement exists", unsure=True)
    t_over = min(P.LID_T, 99)
    row("Plastic over the antenna", f"PETG lid {t_over} mm, air gap about {P.Z_TOP - (P.Z_PB_TOP + P.PARTS['SuperMini'][4]):.1f} mm", "plastic only, no metal, no carbon-filled filament", True, "design: PETG black/grey/white only; RF effect of a 1.6 mm PETG wall NOT measured", "all printed parts are plain PETG; the only metal is the M2 screws/inserts, outside the keep-out", unsure=True)
    # ---------- fasteners ----------
    sl, need = P.screw_len()
    row("Lid screw length", f"M2 x {sl} (need >= {need:.1f} mm for 3 mm engagement)", "standard length >= need", sl >= need, "geometry; head 4.0 x 1.3 and insert depth ASSUMED", "buy M2 x 14 pan head + M2 x 4 heat-set inserts: Arsany decides; nothing ordered", unsure=True)
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
    npass = sum(r[3] == "PASS" for r in rows); nopen = sum(r[3] == "OPEN" for r in rows); nfail = sum(r[3] == "FAIL" for r in rows)
    print(f"\n{npass} PASS / {nfail} FAIL / {nopen} OPEN")
    if "--md" in sys.argv:
        open(sys.argv[sys.argv.index("--md") + 1], "w").write(to_md(rows) + "\n")
    sys.exit(1 if nfail else 0)

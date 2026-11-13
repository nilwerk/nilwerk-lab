#!/usr/bin/env python3
"""Independent check of the JLCPCB Gerber/drill zips against the PCB files (Plan 4.P2 / 4.P4, Ines F6).

Parser: gerbonara 1.5.0 (pure Python, not KiCad) reads every Gerber and Excellon file from the zips.
Expected values come from the .kicad_pcb files, read with a small S-expression reader in this file.
Usage (scratch venv, outside the repo):
  <venv>/bin/python -I verify_gerber.py <gerber-dir> <pcb-dir>
  <gerber-dir>: this folder (reads the two zips and gerber/panel/plant-monitor-panel.kicad_pcb)
  <pcb-dir>:    the folder holding plant-monitor.kicad_pcb
KiCad writes y downwards; the Gerber and Excellon files carry y with the opposite sign, and this file applies it.
Exit 1 on any FAIL. Emil (PCB Designer).
"""
import json, math, os, re, sys, zipfile, warnings
from collections import Counter, defaultdict
from gerbonara import GerberFile
import gerber.excellon as pcbtools_excellon  # pcb-tools 0.1.6: parser of record for the drill files (see README)
warnings.filterwarnings("ignore")

FAILS = []
def check(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        FAILS.append(msg)

# ---------- small KiCad S-expression reader ----------
TOK = re.compile(r'\s+|(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+)')
def parse_sexp(text):
    stack, pos = [[]], 0
    while pos < len(text):
        m = TOK.match(text, pos); pos = m.end()
        if m.group(1): stack.append([])
        elif m.group(2): n = stack.pop(); stack[-1].append(n)
        elif m.group(3): stack[-1].append(m.group(3)[1:-1])
        elif m.group(4): stack[-1].append(m.group(4))
    return stack[0][0]

def kw(node, key):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == key]

def footprint_pads(root):
    """Absolute pad records. The footprint angle rotates the pad position. Convention (KiCad, y down, positive angle
    counter-clockwise on screen): x' = x cos + y sin, y' = -x sin + y cos. Chosen because it places all 26 pads of the
    90 and 270 degree footprints on a mask flash; the other sign places 0 of 26."""
    out = []
    for item in root[1:]:
        if not (isinstance(item, list) and item and item[0] == "footprint"):
            continue
        at = kw(item, "at")[0]
        fx, fy = float(at[1]), float(at[2]); frot = float(at[3]) if len(at) > 3 else 0.0
        th = math.radians(frot)
        for pad in kw(item, "pad"):
            pa = kw(pad, "at")[0]
            px, py = float(pa[1]), float(pa[2])
            sz = kw(pad, "size")[0]
            dr = kw(pad, "drill")
            dshape, drill = None, None
            if dr:
                if dr[0][1] == "oval": dshape, drill = "oval", (float(dr[0][2]), float(dr[0][3]))
                else: dshape, drill = "round", float(dr[0][1])
            lay = kw(pad, "layers")
            layers = lay[0][1:] if lay else []
            # KiCad wildcards: a through-hole pad is on both copper layers and both mask layers
            if "*.Cu" in layers: layers = layers + ["F.Cu", "B.Cu"]
            if "*.Mask" in layers: layers = layers + ["F.Mask", "B.Mask"]
            mm = kw(pad, "solder_mask_margin")
            out.append(dict(fp=item[1], num=pad[1], type=pad[2], shape=pad[3], mm=float(mm[0][1]) if mm else 0.0,
                            x=fx + px * math.cos(th) + py * math.sin(th),
                            y=fy - px * math.sin(th) + py * math.cos(th),
                            w=float(sz[1]), h=float(sz[2]), drill=drill, dshape=dshape,
                            layers=layers))
    return out

def pcb_vias(root):
    out = []
    for v in root[1:]:
        if isinstance(v, list) and v and v[0] == "via":
            at = kw(v, "at")[0]
            out.append(dict(x=float(at[1]), y=float(at[2]), drill=float(kw(v, "drill")[0][1])))
    return out

def edge_cut_lines(root):
    segs = []
    for g in root[1:]:
        if isinstance(g, list) and g and g[0] == "gr_line" and kw(g, "layer")[0][1] == "Edge.Cuts":
            s, e = kw(g, "start")[0], kw(g, "end")[0]
            segs.append((float(s[1]), float(s[2]), float(e[1]), float(e[2])))
    return segs

# ---------- geometry ----------
def loops_from_segments(segs, tol=1e-4):
    key = lambda p: (round(p[0] / tol), round(p[1] / tol))
    adj = defaultdict(list)
    for i, (x1, y1, x2, y2) in enumerate(segs):
        adj[key((x1, y1))].append(i); adj[key((x2, y2))].append(i)
    open_ends = [k for k, v in adj.items() if len(v) != 2]
    seen, loops = set(), []
    for i in range(len(segs)):
        if i in seen: continue
        comp, stack = set(), [i]
        while stack:
            j = stack.pop()
            if j in comp: continue
            comp.add(j)
            x1, y1, x2, y2 = segs[j]
            stack.extend(adj[key((x1, y1))]); stack.extend(adj[key((x2, y2))])
        seen |= comp
        loops.append(sorted(comp))
    return loops, open_ends

def ordered_points(segs, idxs, tol=1e-4):
    rem = [segs[i] for i in idxs]
    x1, y1, x2, y2 = rem.pop(0)
    pts = [(x1, y1), (x2, y2)]
    while rem:
        for j, (a, b, c, d) in enumerate(rem):
            if math.hypot(a - pts[-1][0], b - pts[-1][1]) < tol:
                pts.append((c, d)); rem.pop(j); break
            if math.hypot(c - pts[-1][0], d - pts[-1][1]) < tol:
                pts.append((a, b)); rem.pop(j); break
        else:
            break
    return pts[:-1]

def shoelace(pts):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2

def near(p, q, tol):
    return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol

def size_eq(a, b, tol=0.011):
    return abs(min(a) - min(b)) <= tol and abs(max(a) - max(b)) <= tol

# ---------- Gerber / Excellon objects ----------
def load(name, data):
    text = data.decode("utf8", errors="replace")
    if name.lower().endswith(".drl"):
        return pcbtools_excellon.loads(text, filename=name)
    return GerberFile.from_string(text, filename=name)

def aperture_size(ap):
    """Width and height of a flash. Rectangles and circles report their size; KiCad's rounded-rectangle pads are
    aperture macros, which report only a bounding box (the macro's outline is included in it)."""
    if getattr(ap, "w", None):
        return float(ap.w), float(ap.h)
    if getattr(ap, "diameter", None):
        return float(ap.diameter), float(ap.diameter)
    (x0, y0), (x1, y1) = ap.bounding_box()
    return float(x1 - x0), float(y1 - y0)

def flashes(gf):
    out = []
    for o in gf.objects:
        if type(o).__name__ == "Flash" and o.polarity_dark:
            out.append((o.x, o.y) + aperture_size(o.aperture))
    return out

REQUIRED = ["Gerber_TopLayer.GTL", "Gerber_BottomLayer.GBL", "Gerber_TopSolderMaskLayer.GTS", "Gerber_BottomSolderMaskLayer.GBS",
            "Gerber_TopSilkscreenLayer.GTO", "Gerber_BottomSilkscreenLayer.GBO", "Gerber_TopPasteMaskLayer.GTP",
            "Gerber_BottomPasteMaskLayer.GBP", "Gerber_BoardOutlineLayer.GKO", "Drill_PTH_Through.DRL", "Drill_NPTH_Through.DRL",
            "Drill_PTH_Through_Map.GBR", "Drill_NPTH_Through_Map.GBR", "Drill_Report.rpt", "Gerber_JobFile.gbrjob"]

def verify(label, zip_path, pcb_path, panel=False):
    print("\n==== %s: %s" % (label, os.path.basename(zip_path)))
    z = zipfile.ZipFile(zip_path)
    files = {n: z.read(n) for n in z.namelist()}
    missing = [r for r in REQUIRED if r not in files]
    check(not missing, "%s: %d of %d required files present (missing: %s)" % (label, len(REQUIRED) - len(missing), len(REQUIRED), missing or "none"))
    print("      zip members (%d): %s" % (len(files), ", ".join(sorted(files))))
    layers = {}
    for n, d in files.items():
        if n.endswith(".gbrjob") or n.endswith(".rpt"):
            continue
        try:
            layers[n] = load(n, d)
            cnt = len(layers[n].hits) + len(layers[n].primitives) if n.endswith(".DRL") else len(layers[n].objects)
            tool = "pcb-tools" if n.endswith(".DRL") else "gerbonara"
            print("PASS  %s: parses with %s, %d objects%s: %s" % (label, tool, cnt, " (0 = layer is empty in this design)" if cnt == 0 else "", n))
        except Exception as e:
            check(False, "%s: parse error in %s: %s" % (label, n, e))
    root = parse_sexp(open(pcb_path, encoding="utf8").read())
    # ----- Edge.Cuts -----
    edge = layers["Gerber_BoardOutlineLayer.GKO"]
    segs = [(o.x1, o.y1, o.x2, o.y2) for o in edge.objects if type(o).__name__ == "Line"]
    arcs = [o for o in edge.objects if type(o).__name__ == "Arc"]
    loops, open_ends = loops_from_segments(segs)
    kseg = [(a, -b, c, -d) for (a, b, c, d) in edge_cut_lines(root)]
    if panel:
        check(len(loops) == 3 and not open_ends and not arcs,
              "%s: Edge.Cuts = %d closed loops (expected 3: panel rails + 2 boards), open ends %d, arcs %d" % (label, len(loops), len(open_ends), len(arcs)))
    else:
        check(len(loops) == 1 and not open_ends and not arcs,
              "%s: Edge.Cuts is one closed loop: %d segments, open ends %d, arcs %d" % (label, len(segs), len(open_ends), len(arcs)))
        gseg = Counter(tuple(round(v, 3) for v in s) for s in segs)
        kc = Counter(tuple(round(v, 3) for v in s) for s in kseg)
        check(gseg == kc, "%s: Edge.Cuts segments equal the PCB outline (%d lines, same endpoints, y sign applied)" % (label, sum(kc.values())))
    for li, idxs in enumerate(loops):
        pts = ordered_points(segs, idxs)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        print("      loop %d: %d segments, x %.2f..%.2f, y %.2f..%.2f (gerber sign), area %.1f mm2"
              % (li + 1, len(idxs), min(xs), max(xs), min(ys), max(ys), shoelace(pts)))
    # ----- drills -----
    def holes(d):
        rnd, pos, slots = Counter(), defaultdict(list), 0
        for h in d.hits:
            if type(h).__name__ == "DrillHit":
                dia = round(h.tool.diameter, 3); rnd[dia] += 1; pos[dia].append((h.position[0], h.position[1]))
            elif type(h).__name__ == "DrillSlot":
                slots += 1
        return rnd, pos, slots
    ph, ppos, ps = holes(layers["Drill_PTH_Through.DRL"])
    nh, npos, _ = holes(layers["Drill_NPTH_Through.DRL"])
    vias = pcb_vias(root); pads = footprint_pads(root)
    e_pth, e_pth_pos = Counter(), defaultdict(list)
    e_npth, e_npth_pos = Counter(), defaultdict(list)
    e_slots = 0
    for v in vias:
        d = round(v["drill"], 3); e_pth[d] += 1; e_pth_pos[d].append((v["x"], -v["y"]))
    for p in pads:
        if p["drill"] is None: continue
        if p["type"] == "thru_hole" and p["dshape"] == "oval": e_slots += 1
        elif p["type"] == "thru_hole":
            d = round(p["drill"], 3); e_pth[d] += 1; e_pth_pos[d].append((p["x"], -p["y"]))
        elif p["type"] == "np_thru_hole":
            d = round(p["drill"], 3); e_npth[d] += 1; e_npth_pos[d].append((p["x"], -p["y"]))
    n_via = len(vias); n_pad_pth = sum(e_pth.values()) - n_via
    print("      PCB file: %d vias (drill %s), %d PTH pads round, %d PTH pads oval (slots), %d NPTH pads"
          % (n_via, dict(Counter(round(v['drill'], 3) for v in vias)), n_pad_pth, e_slots, sum(e_npth.values())))
    check(dict(ph) == dict(e_pth) and ps == e_slots,
          "%s: PTH file holes = PCB vias + plated pads: round %s (PCB %s), slots %d (PCB %d)" % (label, dict(ph), dict(e_pth), ps, e_slots))
    check(dict(nh) == dict(e_npth), "%s: NPTH file holes = PCB np_thru_hole pads: %s (PCB %s)" % (label, dict(nh), dict(e_npth)))
    for d, exp in e_pth_pos.items():
        mt = match_count(exp, ppos.get(d, []), 0.002)
        check(mt == len(exp), "%s: PTH %.2f mm: %d of %d hole positions match the PCB to 0.002 mm" % (label, d, mt, len(exp)))
    for d, exp in e_npth_pos.items():
        mt = match_count(exp, npos.get(d, []), 0.002)
        check(mt == len(exp), "%s: NPTH %.2f mm: %d of %d hole positions match the PCB to 0.002 mm" % (label, d, mt, len(exp)))
    # ----- soldermask and paste -----
    for side, mname, pname, cu, mk, pst in (("top", "Gerber_TopSolderMaskLayer.GTS", "Gerber_TopPasteMaskLayer.GTP", "F.Cu", "F.Mask", "F.Paste"),
                                            ("bottom", "Gerber_BottomSolderMaskLayer.GBS", "Gerber_BottomPasteMaskLayer.GBP", "B.Cu", "B.Mask", "B.Paste")):
        mfl, pfl = flashes(layers[mname]), flashes(layers[pname])
        side_pads = [p for p in pads if cu in p["layers"] and p["type"] in ("smd", "thru_hole")]
        # spot-check list: pads on this copper side (SMD and through-hole, which carry the mask too)
        exp_m = [p for p in side_pads if mk in p["layers"]]
        exp_p = [p for p in side_pads if p["type"] == "smd" and pst in p["layers"]]
        ok_m, bad_m, sample = 0, [], []
        for p in exp_m:
            ew, eh = p["w"] + 2 * p["mm"], p["h"] + 2 * p["mm"]  # opening = pad + 2 x solder_mask_margin (fiducials: 0.5 mm)
            good = [f for f in mfl if near((f[0], f[1]), (p["x"], -p["y"]), 0.01) and size_eq((f[2], f[3]), (ew, eh))]
            if good:
                ok_m += 1
                if len(sample) < 10: sample.append((p, good[0]))
            else:
                bad_m.append(p)
        ok_p = sum(1 for p in exp_p if any(near((f[0], f[1]), (p["x"], -p["y"]), 0.01) and size_eq((f[2], f[3]), (p["w"], p["h"])) for f in pfl))
        check(not bad_m, "%s %s soldermask: %d of %d pads on %s (smd + thru_hole with %s) have an opening equal to the pad, to 0.01 mm; %d mask flashes in file"
              % (label, side, ok_m, len(exp_m), cu, mk, len(mfl)))
        check(ok_p == len(exp_p), "%s %s paste: %d of %d SMD pads have a paste aperture equal to the pad" % (label, side, ok_p, len(exp_p)))
        extra = [f for f in mfl if not any(near((f[0], f[1]), (p["x"], -p["y"]), 0.01) for p in exp_m)]
        npth_pads = sum(1 for p in pads if p["type"] == "np_thru_hole" and mk in p["layers"])
        check(len(extra) == npth_pads, "%s %s mask: %d flashes have no pad on this side; NPTH pads with a mask opening = %d" % (label, side, len(extra), npth_pads))
        print("      spot check, %s side (first 10 pads with a mask: PCB pad -> mask flash, Gerber coordinates, mm):" % side)
        for p, f in sample:
            print("        %-10s pad %-3s PCB (%7.3f,%7.3f) %4.2fx%-4.2f -> mask (%7.3f,%7.3f) %4.2fx%-4.2f match"
                  % (p["fp"][:10], p["num"], p["x"], -p["y"], p["w"], p["h"], f[0], f[1], f[2], f[3]))
    # ----- panel-specific -----
    if panel:
        fl = flashes(layers["Gerber_TopLayer.GTL"]); fm = flashes(layers["Gerber_TopSolderMaskLayer.GTS"])
        for p in pads:
            if p["fp"].startswith("NW:Panel_Fiducial"):
                c = any(near((f[0], f[1]), (p["x"], -p["y"]), 0.01) and abs(f[2] - p["w"]) <= 0.01 for f in fl)
                m = any(near((f[0], f[1]), (p["x"], -p["y"]), 0.01) and abs(f[2] - (p["w"] + 1.0)) <= 0.011 for f in fm)
                check(c and m, "%s fiducial (%.2f, %.2f): copper %.2f mm on F.Cu %s; mask opening %.2f mm %s"
                      % (label, p["x"], -p["y"], p["w"], "found" if c else "MISSING", p["w"] + 1.0, "found" if m else "MISSING"))
        tools = [p for p in pads if p["fp"].startswith("NW:Panel_Tooling")]
        for p in tools:
            hit = any(near((h[0], h[1]), (p["x"], -p["y"]), 0.002) for h in npos.get(round(p["drill"], 3), []))
            check(hit, "%s tooling hole (%.2f, %.2f): NPTH %.2f mm in the NPTH drill file %s" % (label, p["x"], -p["y"], p["drill"], "found" if hit else "MISSING"))
    # ----- job file -----
    job = json.loads(files["Gerber_JobFile.gbrjob"].decode("utf8"))
    paths = [e["Path"] for e in job.get("FilesAttributes", [])]
    all_in = all(p in files for p in paths)
    check(all_in and len(paths) > 0, "%s: gbrjob lists %d files; every Path exists in the zip: %s" % (label, len(paths), all_in))
    print("      gbrjob: X %.2f x Y %.2f mm, %d copper layers, ProjectId %s, Revision field %r"
          % (job["GeneralSpecs"]["Size"]["X"], job["GeneralSpecs"]["Size"]["Y"], job["GeneralSpecs"]["LayerNumber"],
             job["GeneralSpecs"]["ProjectId"]["Name"], job["GeneralSpecs"]["ProjectId"]["Revision"]))

def match_count(exp, got, tol):
    got = list(got); n = 0
    for p in exp:
        for i, q in enumerate(got):
            if near(p, q, tol):
                n += 1; got.pop(i); break
    return n

if __name__ == "__main__":
    gdir, pdir = sys.argv[1], sys.argv[2]
    print("verify_gerber.py: gerbonara 1.5.0 (independent parser), PCB files from %s" % pdir)
    verify("BOARD", os.path.join(gdir, "plant-monitor-jlc-board.zip"), os.path.join(pdir, "plant-monitor.kicad_pcb"))
    verify("PANEL 2-up", os.path.join(gdir, "plant-monitor-jlc-panel-2up.zip"), os.path.join(gdir, "panel", "plant-monitor-panel.kicad_pcb"), panel=True)
    print("\nRESULT: %s (%d FAIL)" % ("ALL CHECKS PASS" if not FAILS else "FAILURES", len(FAILS)))
    sys.exit(1 if FAILS else 0)

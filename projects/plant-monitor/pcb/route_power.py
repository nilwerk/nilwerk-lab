#!/usr/bin/env python3
"""Power-section router for 4.P2 slice 3 (Emil, PCB Designer).

Routes the power section of plant-monitor.kicad_pcb on a 0.1 mm grid: VBUS, VBAT, CELL_NEG, the protection nets (FET_MID, DW_*),
the rail caps of the LDO (3V3), the charger/LED nets (PROG, CHRG_N, STDBY_N, LED_*), the USB-C CC resistors and the battery-sense
divider node (BAT_SENS).  Signal nets (I2C, SOIL, IO, USB data), the 3V3 distribution to the module and sensors, and GND are NOT routed here
(GND stays on the unfilled bottom zone, as before).

Rules used (layout-brief.md section 5, design.py / gen_pcb.RULES): clearance 0.2 mm between copper of different nets, track
widths from the calculation in layout-4P2.md, via 0.3/0.7 mm, no via inside a pad (A-069), nothing inside the antenna keep-out (O2),
copper >= 0.5 mm from the board edge (O3).  The router only guarantees these with its own inflation; KiCad DRC checks them again.

Run from gen_pcb.py (route() is called there).  Pure geometry, no KiCad needed.
"""
from __future__ import annotations
import heapq, math
import numpy as np
import design as D
import gen_pcb as G

GRID = 0.1
EDGE = G.RULES["copper_edge"]
CLR = G.RULES["clearance"]
VIA_R = G.RULES["via_dia"] / 2
VIA_COST = 20           # one layer change = 2.0 mm of track, keeps routes on the top side when possible
NX = int(round(G.BOARD_W / GRID)) + 1
NY = int(round((G.BODY_L + G.TAIL_L) / GRID)) + 1

# (net, track width mm, parts to take pads from or None for all pads of the net)
ROUTE = [   # trunks first (VBAT/VBUS need the corridor around the TP4056 thermal vias), then the short nets
    ("VBAT", 0.5, None),          # charge + load path, 0.5 mm (layout-4P2.md width calc)
    ("VBUS", 0.4, None),          # USB 500 mA budget, 0.4 mm
    ("CELL_NEG", 0.5, None),      # cell return through the protection FETs
    ("3V3", 0.4, ["U2", "C13", "C14"]),   # LDO output and its rail caps only (distribution to the module/sensors: next slice)
    ("FET_MID", 0.5, None),
    ("CC1", 0.2, None), ("CC2", 0.2, None),
    ("DW_CS", 0.2, None), ("STDBY_N", 0.2, None), ("LED_STDBY_A", 0.2, None),
    ("PROG", 0.2, None), ("CHRG_N", 0.2, None), ("LED_CHRG_A", 0.2, None),
    ("DW_OD", 0.2, None), ("DW_OC", 0.2, None),
    ("BAT_SENS", 0.2, None),
]


def pads_abs():
    out = []
    for p in D.PARTS:
        if p.ref not in G.PLACE:
            continue
        x0, y0, r = G.PLACE[p.ref]
        pn = G.pad_nets(p)
        for pd in G.FOOT[p.footprint]["pads"]:
            dx, dy = G.rot(pd["x"], pd["y"], r)
            ang = (pd["ang"] + r) % 180
            w, h = (pd["h"], pd["w"]) if abs(ang - 90) < 1 else (pd["w"], pd["h"])
            out.append(dict(ref=p.ref, num=pd["num"], net=pn.get(pd["num"], "NC"), cx=x0 + dx, cy=y0 + dy, w=w, h=h,
                            back=any(l.startswith("B.") for l in pd["layers"]) or bool(pd["drill"]), front=any(l.startswith("F.") or l == "*.Cu" for l in pd["layers"]),
                            drill=bool(pd["drill"])))
    # the same copper pad can appear under two pin names (USB-C A4/B9, A9/B4, A1/B12): keep one
    seen, uniq = set(), []
    for q in out:
        key = (q["ref"], round(q["cx"], 3), round(q["cy"], 3), q["net"])
        if key not in seen:
            seen.add(key)
            uniq.append(q)
    return uniq


def board_region():
    """Copper may sit here: body and tail, EDGE mm inside the outline."""
    m = np.zeros((NX, NY), dtype=bool)
    xs = np.arange(NX) * GRID
    ys = np.arange(NY) * GRID
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    a = (X >= EDGE) & (X <= G.BOARD_W - EDGE) & (Y >= EDGE) & (Y <= G.BODY_L - EDGE)
    b = (X >= G.TAIL_X0 + EDGE) & (X <= G.TAIL_X0 + G.TAIL_W - EDGE) & (Y >= G.BODY_L - EDGE) & (Y <= G.BODY_L + G.TAIL_L - EDGE)
    return a | b, X, Y


REGION, GX, GY = board_region()


def stamp_rect(mask, x0, y0, x1, y1, r):
    i0, i1 = max(0, int(math.floor((x0 - r) / GRID))), min(NX - 1, int(math.ceil((x1 + r) / GRID)))
    j0, j1 = max(0, int(math.floor((y0 - r) / GRID))), min(NY - 1, int(math.ceil((y1 + r) / GRID)))
    if i0 > i1 or j0 > j1:
        return
    X, Y = GX[i0:i1 + 1, j0:j1 + 1], GY[i0:i1 + 1, j0:j1 + 1]
    dx = np.maximum(np.maximum(x0 - X, 0), X - x1)
    dy = np.maximum(np.maximum(y0 - Y, 0), Y - y1)
    mask[i0:i1 + 1, j0:j1 + 1] |= np.hypot(dx, dy) <= r + 1e-9


def stamp_seg(mask, x1, y1, x2, y2, r):
    stamp_rect(mask, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), r) if False else None
    i0, i1 = max(0, int(math.floor((min(x1, x2) - r) / GRID))), min(NX - 1, int(math.ceil((max(x1, x2) + r) / GRID)))
    j0, j1 = max(0, int(math.floor((min(y1, y2) - r) / GRID))), min(NY - 1, int(math.ceil((max(y1, y2) + r) / GRID)))
    if i0 > i1 or j0 > j1:
        return
    X, Y = GX[i0:i1 + 1, j0:j1 + 1], GY[i0:i1 + 1, j0:j1 + 1]
    vx, vy = x2 - x1, y2 - y1
    L2 = vx * vx + vy * vy
    t = np.clip(((X - x1) * vx + (Y - y1) * vy) / L2, 0, 1) if L2 > 0 else np.zeros_like(X)
    d = np.hypot(X - (x1 + t * vx), Y - (y1 + t * vy))
    mask[i0:i1 + 1, j0:j1 + 1] |= d <= r + 1e-9


class Obstacle:
    def __init__(self, net, layers, kind, geom, hw):
        self.net, self.layers, self.kind, self.geom, self.hw = net, layers, kind, geom, hw

    def stamp(self, masks, r, own_net):
        if self.net == own_net:
            return
        for l in self.layers:
            if self.kind == "rect":
                stamp_rect(masks[l], *self.geom, r + self.hw)
            else:
                stamp_seg(masks[l], *self.geom, r + self.hw)


def base_obstacles(pads):
    obs = []
    for p in pads:
        layers = ([0] if p["front"] else []) + ([1] if p["back"] else [])
        x0, y0, x1, y1 = p["cx"] - p["w"] / 2, p["cy"] - p["h"] / 2, p["cx"] + p["w"] / 2, p["cy"] + p["h"] / 2
        # hole clearance 0.25 mm (board rule) is larger than copper clearance 0.2 mm: drilled pads get the extra 0.05 mm
        obs.append(Obstacle(p["net"], layers, "rect", (x0, y0, x1, y1), 0.05 if p["drill"] else 0.0))
    for (x1, y1, x2, y2, w) in G.stub_tracks():
        obs.append(Obstacle("GND", [0], "seg", (x1, y1, x2, y2), w / 2))
    for (_, x, y) in G.via_list():
        obs.append(Obstacle("GND", [0, 1], "seg", (x, y, x, y), VIA_R))
    kx0, ky0, kx1, ky1 = G.ANT_KEEPOUT
    obs.append(Obstacle(None, [0, 1], "rect", (kx0, ky0, kx1, ky1), 0.0))   # antenna keep-out: nothing of any net
    return obs


def route_all():
    pads = pads_abs()
    obs = base_obstacles(pads)
    segs, vias, report = [], [], []
    for net, w, refs in ROUTE:
        tp = [p for p in pads if p["net"] == net and (refs is None or p["ref"] in refs)]
        if len(tp) < 2:
            report.append((net, "fewer than 2 pads", len(tp)))
            continue
        r_net = w / 2 + CLR
        # Masks: copper of this net may not come within r_net of foreign copper (CLR + half width of this track)
        masks = {0: np.zeros((NX, NY), dtype=bool), 1: np.zeros((NX, NY), dtype=bool)}
        for o in obs:
            o.stamp(masks, r_net, net)
        via_mask = np.zeros((NX, NY), dtype=bool)
        for o in obs:
            own_via = o.net == net and o.kind == "seg" and o.hw == VIA_R   # own vias: hole spacing only
            if o.net == net and not own_via:
                continue
            if own_via:
                stamp_seg(via_mask, *o.geom, VIA_R + 0.25 + o.hw)
            elif o.kind == "rect":
                stamp_rect(via_mask, *o.geom, VIA_R + CLR + o.hw)
            elif o.hw == VIA_R:   # another via: centre distance >= 0.7 + 0.25 mm (hole spacing rule)
                stamp_seg(via_mask, *o.geom, VIA_R + 0.26 + o.hw)
            else:
                stamp_seg(via_mask, *o.geom, VIA_R + CLR + o.hw)
        for p in pads:   # no via inside any pad (A-069), and not on pad copper of any net
            stamp_rect(via_mask, p["cx"] - p["w"] / 2, p["cy"] - p["h"] / 2, p["cx"] + p["w"] / 2, p["cy"] + p["h"] / 2, VIA_R + 0.05)
        ok_layer = {0: REGION & ~masks[0], 1: REGION & ~masks[1]}
        via_ok = REGION & ~via_mask

        def cell(p):
            return int(round(p["cx"] / GRID)), int(round(p["cy"] / GRID))

        # tree = set of (i, j, layer); start from the first pad
        first = tp[0]
        tree = {(*cell(first), 0)} if first["front"] else {(*cell(first), 1)}
        todo = tp[1:]
        net_segs = []
        net_vias = []
        while todo:
            # pick the pad closest to the tree
            def dist_tree(p):
                ci, cj = cell(p)
                return min(abs(ci - ti) + abs(cj - tj) for (ti, tj, _) in tree)
            todo.sort(key=dist_tree)
            tgt = todo.pop(0)
            si, sj = cell(tgt)
            start_layers = ([0] if tgt["front"] else []) + ([1] if tgt["back"] else [])
            # bounding box of search: pad + tree, plus margin
            ti = [t[0] for t in tree]; tj = [t[1] for t in tree]
            margin = 60
            bi0, bi1 = max(0, min(min(ti), si) - margin), min(NX - 1, max(max(ti), si) + margin)
            bj0, bj1 = max(0, min(min(tj), sj) - margin), min(NY - 1, max(max(tj), sj) + margin)
            dist = {}
            parent = {}
            pq = []
            for l in start_layers:
                s = (si, sj, l)
                dist[s] = 0
                parent[s] = None
                heapq.heappush(pq, (0, s))
            found = None
            while pq:
                d, node = heapq.heappop(pq)
                if dist.get(node, 1e18) < d:
                    continue
                if node in tree:
                    found = node
                    break
                i, j, l = node
                for ni, nj in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                    if not (bi0 <= ni <= bi1 and bj0 <= nj <= bj1):
                        continue
                    if not ok_layer[l][ni, nj] and (ni, nj, l) not in tree:
                        continue
                    nn = (ni, nj, l)
                    nd = d + 1
                    if nd < dist.get(nn, 1e18):
                        dist[nn] = nd
                        parent[nn] = node
                        heapq.heappush(pq, (nd, nn))
                # layer change through a via
                if via_ok[i, j] or (i, j, 1 - l) in tree:
                    nn = (i, j, 1 - l)
                    if (i, j) in ((si, sj),) and False:
                        pass
                    if via_ok[i, j]:
                        nd = d + VIA_COST
                        if nd < dist.get(nn, 1e18):
                            dist[nn] = nd
                            parent[nn] = node
                            heapq.heappush(pq, (nd, nn))
            if found is None:
                report.append((net, f"no route from {tgt['ref']}.{tgt['num']}", 0))
                continue
            # rebuild path: from found back to the pad
            path = []
            n = found
            while n is not None:
                path.append(n)
                n = parent[n]
            path.reverse()
            for node in path:
                tree.add(node)
            # convert to segments and vias
            pts = path
            k = 0
            while k < len(pts) - 1:
                a, b = pts[k], pts[k + 1]
                if a[2] != b[2]:
                    net_vias.append((a[0] * GRID, a[1] * GRID, net))
                    k += 1
                    continue
                # extend run while direction is constant and layer same
                dx, dy = b[0] - a[0], b[1] - a[1]
                e = k + 1
                while e + 1 < len(pts) and pts[e + 1][2] == a[2] and (pts[e + 1][0] - pts[e][0], pts[e + 1][1] - pts[e][1]) == (dx, dy):
                    e += 1
                net_segs.append((pts[k][0] * GRID, pts[k][1] * GRID, pts[e][0] * GRID, pts[e][1] * GRID, w, a[2], net))
                k = e
            # this connection is now an obstacle for the next connections of this net? no: same net is never an obstacle
            # but other nets must see it: add to obstacle list after the net is complete
        segs += net_segs
        vias += net_vias
        for (x1, y1, x2, y2, ww, l, nn) in net_segs:
            obs.append(Obstacle(net, [l], "seg", (x1, y1, x2, y2), ww / 2))
        for (x, y, _) in net_vias:
            obs.append(Obstacle(net, [0, 1], "seg", (x, y, x, y), VIA_R))
        report.append((net, "ok", len(net_segs), len(net_vias)))
    return segs, vias, report


if __name__ == "__main__":
    s, v, rep = route_all()
    for r in rep:
        print(r)
    print("segments", len(s), "vias", len(v))

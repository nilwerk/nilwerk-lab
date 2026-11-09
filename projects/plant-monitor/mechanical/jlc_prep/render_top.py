"""4.E3 JLC prep: 2D top view of the 4.P2 board source (outline, cell cavity, antenna, pads, vias).

Drawn from input/plant-monitor.kicad_pcb and input/plant-monitor-outline.dxf (no CAD needed for the parse).
Run: python3 render_top.py [out.png]   (needs matplotlib)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import board_step as bs  # noqa: E402
import fit_check as fc  # noqa: E402


def main(out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    b = bs.parse_board()
    loop = [bs.to_step_xy(p) for p in bs.outline_loop(b["edge"])]
    fig, ax = plt.subplots(figsize=(7.2, 8.4), dpi=150)
    ax.add_patch(Polygon(loop, closed=True, fc="#f6f4ef", ec="#15181d", lw=1.4, zorder=1))
    # cell cavity (DXF layer CELL_BAY_CAVITY) and module (MODULE_U1), antenna keep-out
    for layer, style in (("CELL_BAY_CAVITY", dict(fc="none", ec="#b8860b", ls="--")),
                         ("MODULE_U1", dict(fc="#d9e6e1", ec="#0f7a5c")),
                         ("ANT_KEEPOUT", dict(fc="#f3d9d4", ec="#a33b2b", hatch="//"))):
        pts = [(x, y) for (x, y) in _layer_pts(layer)]
        if pts:
            ax.add_patch(Polygon(pts, closed=True, lw=1.1, zorder=2, **style))
    for fp in b["footprints"]:
        for pd in fp["pads"]:
            gx, gy = bs.rot(pd["px"], pd["py"], fp["r"])
            cx, cy = bs.to_step_xy((fp["x"] + gx, fp["y"] + gy))
            poly = bs.pad_polygon(cx, cy, pd["w"], pd["h"], -(fp["r"] + pd["pr"]))
            ax.add_patch(Polygon(poly, closed=True, fc="#c9a24b", ec="none", zorder=3))
    for v in b["vias"]:
        x, y = bs.to_step_xy((v["x"], v["y"]))
        ax.add_patch(plt.Circle((x, y), v["dia"] / 2, fc="#8a8a8a", ec="none", zorder=4))
        ax.add_patch(plt.Circle((x, y), v["drill"] / 2, fc="#f6f4ef", ec="none", zorder=5))
    ax.set_aspect("equal")
    ax.set_xlim(-62, 38)
    ax.set_ylim(-72, 12)
    ax.axhline(0, color="#999", lw=0.5, ls=":")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm), antenna at top")
    ax.set_title("4.P2 board source, top view (no routing, placeholder pads)", fontsize=9)
    ax.text(-61, -70.5, "gold = placed pad copper, grey = vias, dashed = cell bay cavity (not copper), "
            "red hatch = antenna keep-out", fontsize=6.2)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)
    return out_png


def _layer_pts(layer):
    lines = [l.strip() for l in open(fc.DXF, encoding="utf-8").read().splitlines()]
    segs = []
    i = 0
    while i < len(lines) - 1:
        if lines[i] == "0" and lines[i + 1] == "LINE":
            rec = {}
            j = i + 2
            while j < len(lines) - 1 and lines[j] != "0":
                rec[lines[j]] = lines[j + 1]
                j += 2
            if rec.get("8") == layer:
                segs.append((float(rec["10"]), float(rec["20"])))
            i = j
        else:
            i += 1
    # the DXF LINE records of one closed polygon come in order: each start point is one vertex
    return segs


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "board-top-view.png")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    print(main(target))

"""PNG renders of enclosure v3 from the exported STL meshes (matplotlib painter's algorithm, like render.py). Run after build_v3.py."""
import pathlib, sys
import numpy as np, trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import params_v3 as P
import render as R
import board_src as B
import enclosure_v3 as E

OUT = pathlib.Path(__file__).resolve().parents[2] / "enclosure" / "v3"
REN = OUT / "renders"
AMBER = np.array([0.95, 0.65, 0.1]); GREEN = np.array([0.05, 0.45, 0.30]); WHITE = np.array([0.85, 0.85, 0.85])


def L(name):
    return trimesh.load(OUT / f"enclosure_v3_{name}.stl")


def mesh_from(wp):
    import cadquery as cq, tempfile, os
    f = os.path.join(tempfile.gettempdir(), "v3_tmp.stl"); cq.exporters.export(wp, f, tolerance=0.02, angularTolerance=0.15); return trimesh.load(f)


def main():
    REN.mkdir(parents=True, exist_ok=True)
    tray, lid, plug = L("tray"), L("lid"), L("tail_plug")
    board, cell = mesh_from(E.board_ghost()), mesh_from(E.cell_ghost())
    R.scene([(tray, R.GREY, 1), (plug, R.GREY * 0.8, 1), (lid, R.GREY * 1.1, 1)], REN / "v3_hero.png", "Enclosure v3 slice 2: assembled, front (lid) view, stake tail exits at the bottom", elev=48, azim=-70)
    lift = lambda m, dz: (m.copy().apply_translation((0, 0, dz)) or m)
    def moved(m, dz):
        c = m.copy(); c.apply_translation((0, 0, dz)); return c
    R.scene([(tray, R.GREY, 1), (moved(plug, 14), R.GREY * 0.8, 1), (cell, AMBER, 1), (moved(board, 7), GREEN, 1), (moved(lid, 28), R.GREY * 1.1, 1)],
            REN / "v3_exploded.png", "Exploded: tray, cell (amber), board with part boxes (green, heights ASSUMED), tail plug, lid", elev=40, azim=-62)
    # section through the board at the USB-C row (plane y = J1_Y) viewed along Y
    fig, ax = plt.subplots(figsize=(9, 3.4), dpi=150)
    y0 = P.J1_Y
    for m, col, nm in [(tray, "#555a60", "tray"), (lid, "#6c7278", "lid"), (board, "#0f7a5c", "board + parts [heights ASSUMED]")]:
        sec = m.section(plane_origin=(0, y0, 0), plane_normal=(0, 1, 0))
        if sec is None: continue
        p2, _ = sec.to_planar(to_2D=np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]))
        for ent in p2.entities:
            pts = p2.vertices[ent.points]; ax.plot(pts[:, 0], pts[:, 1], color=col, lw=1.0)
    ax.add_patch(Rectangle((P.CELL_X0 + 1.0, 0), (P.CELL_X1 - 1.0) - (P.CELL_X0 + 1.0), 6.3, fc=(0.95, 0.65, 0.1, 0.35), ec="#c98a00", lw=0.8))
    ax.set_aspect("equal"); ax.set_title(f"Section at y = {y0} (USB-C row): floor, cell (amber, 6.3 mm), board standoff 1.0, J1 window, 0.5 mm lid clearance at J2 height", fontsize=8)
    ax.set_xlabel("X mm"); ax.set_ylabel("Z mm"); ax.grid(alpha=0.2)
    fig.savefig(REN / "v3_section.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    # plan view: inner outline, cell cavity, board outline, part courtyards, bosses, features
    fig, ax = plt.subplots(figsize=(10, 6.6), dpi=150)
    ax.add_patch(Rectangle((P.OUT_X0, P.OUT_Y0), P.OUT_X1 - P.OUT_X0, P.OUT_Y1 - P.OUT_Y0, fc="#e6e8ea", ec="#333", lw=1.2))
    ax.add_patch(Rectangle((P.INNER_X0, P.INNER_Y0), P.INNER_X1 - P.INNER_X0, P.INNER_Y1 - P.INNER_Y0, fc="white", ec="#333", lw=0.8))
    ax.add_patch(Rectangle((P.CELL_X0, P.CELL_Y0), P.CELL_X1 - P.CELL_X0, P.CELL_Y1 - P.CELL_Y0, fc=(0.95, 0.65, 0.1, 0.35), ec="#c98a00"))
    ax.text((P.CELL_X0 + P.CELL_X1) / 2, (P.CELL_Y0 + P.CELL_Y1) / 2, "EEMB LP603449-PCM\ncavity 53.0 x 35.1 x 7.2", ha="center", fontsize=8)
    pts = [(0, 0), (P.BOARD_W, 0), (P.BOARD_W, -P.BODY_L), (P.TAIL_X0 + P.TAIL_W, -P.BODY_L), (P.TAIL_X0 + P.TAIL_W, -P.BODY_L - P.TAIL_L), (P.TAIL_X0, -P.BODY_L - P.TAIL_L), (P.TAIL_X0, -P.BODY_L), (0, -P.BODY_L), (0, 0)]
    ax.plot(*zip(*pts), color="#0f7a5c", lw=1.5)
    for ref, c in B.components().items():
        x0, y0b, x1, y1 = c["box"]; ax.add_patch(Rectangle((x0, y0b), x1 - x0, y1 - y0b, fc=(0.05, 0.45, 0.3, 0.18), ec="#0f7a5c", lw=0.3))
    for (x, y) in P.BOSS_XY:
        ax.add_patch(plt.Circle((x, y), P.BOSS_D / 2, fc="#999", ec="#333")); ax.add_patch(plt.Circle((x, y), P.INSERT_HOLE / 2, fc="white", ec="#333", lw=0.5))
    ax.add_patch(plt.Circle(P.U6, P.WIN_D / 2, fc="#ffd84d", ec="#333")); ax.annotate("light window d3.6", P.U6, (P.U6[0] + 3, P.U6[1] + 6), fontsize=7, arrowprops=dict(arrowstyle="-"))
    ax.annotate("AHT20 vents + baffle", P.U5, (P.U5[0] - 3, P.U5[1] + 7), fontsize=7, arrowprops=dict(arrowstyle="-"))
    ax.add_patch(plt.Circle(P.SW3, P.PIN_D / 2, fc="red")); ax.annotate("pinhole d1.8", P.SW3, (P.SW3[0] - 20, P.SW3[1] - 4), fontsize=7, arrowprops=dict(arrowstyle="-"))
    ax.annotate("USB-C window 9.6 x 3.9", (P.OUT_X1, P.J1_Y), (P.OUT_X1 - 20, P.J1_Y - 12), fontsize=7, arrowprops=dict(arrowstyle="-"))
    ax.annotate("tail seal plug\n(stake exits here)", (17.25, P.OUT_Y0), (-10, P.OUT_Y0 - 6), fontsize=7, arrowprops=dict(arrowstyle="-"))
    ax.set_xlim(P.OUT_X0 - 5, P.OUT_X1 + 5); ax.set_ylim(-70, P.OUT_Y1 + 4); ax.set_aspect("equal")
    ax.set_title(f"Enclosure v3 plan (lid off): outer {P.OUT_X1 - P.OUT_X0:.1f} x {P.OUT_Y1 - P.OUT_Y0:.1f} mm, inner {P.INNER_X1 - P.INNER_X0:.1f} x {P.INNER_Y1 - P.INNER_Y0:.1f} x {P.INNER_H:.1f} mm; board 34.5 x 67 outline green", fontsize=9)
    fig.savefig(REN / "v3_plan.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("renders in", REN)


if __name__ == "__main__":
    main()

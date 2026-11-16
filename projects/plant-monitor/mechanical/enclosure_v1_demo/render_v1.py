"""PNG renders of the v1 demo housing: hero and exploded via VTK z-buffer (vtk_scene.py, run: xvfb-run -a -s "-screen 0 1600x1200x24" python render_v1.py), section and plan via matplotlib. Run after build_v1.py. Not part of CI (needs vtk, networkx, a display)."""
import os, sys, pathlib, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import cadquery as cq
import params_v1 as P
import enclosure_v1 as E
import render as R           # mechanical/render.py: scene(), GREY

OUT = pathlib.Path(__file__).resolve().parents[2] / "enclosure" / "v1_demo_compact"
REN = OUT / "renders"
GREY = np.array([0.55, 0.57, 0.60])
AMBER = np.array([0.95, 0.65, 0.1]); GREEN = np.array([0.05, 0.45, 0.30]); BOARD = np.array([0.10, 0.35, 0.22])


def mesh_from(wp):
    f = os.path.join(tempfile.gettempdir(), f"v1r_{os.getpid()}.stl")
    cq.exporters.export(wp, f, tolerance=0.03, angularTolerance=0.2)
    m = trimesh.load(f)

    return m


def scene(meshes, path, title, elev=34, azim=-62):
    """VTK offscreen z-buffer render (vtk_scene.py, needs xvfb-run), title added with matplotlib."""
    import vtk_scene as V
    tmp = os.path.join(tempfile.gettempdir(), f"v1_scene_{os.getpid()}.png")
    V.render([(m, c, (0, 0, 0), 1.0) for m, c in meshes], tmp, azimuth=azim, elevation=elev)
    img = plt.imread(tmp)
    fig = plt.figure(figsize=(10, 6.9), dpi=150); ax = fig.add_axes([0, 0, 1, 0.93]); ax.imshow(img); ax.set_axis_off()
    fig.suptitle(title, fontsize=10, y=0.985)
    fig.savefig(path, facecolor="white"); plt.close(fig)


def moved(m, dz):
    c = m.copy(); c.apply_translation((0, 0, dz)); return c


def section(ax, meshes, y0, title):
    for m, col in meshes:
        sec = m.section(plane_origin=(0, y0, 0), plane_normal=(0, 1, 0))
        if sec is None:
            continue
        for seg in sec.discrete:
            ax.fill(seg[:, 0], seg[:, 2], color=col, lw=0.5, ec="k", alpha=0.95)
    ax.set_aspect("equal"); ax.set_title(title, fontsize=8); ax.set_ylabel("Z mm"); ax.grid(alpha=0.2)
    ax.axhline(P.Z_SPLIT, color="#c33", lw=0.6, ls="--")
    ax.text(P.OX1 - 1, P.Z_SPLIT + 0.4, "parting plane", fontsize=6, color="#c33", ha="right")


def main():
    REN.mkdir(parents=True, exist_ok=True)
    tray, lid = mesh_from(E.tray()), mesh_from(E.lid())
    pb, parts, cell = mesh_from(E.perfboard_ghost()), mesh_from(E.parts_ghost()), mesh_from(E.cell_ghost())
    dims = f"{P.OX1 - P.OX0:.1f} x {P.OY1 - P.OY0:.1f} x {P.Z_TOP + P.LID_T:.1f} mm"
    scene([(tray, GREY), (lid, GREY * 1.1)], REN / "v1_demo_hero.png",
            f"Plant Monitor v1 demo housing: base + lid, {dims} (PETG grey, left: two USB-C openings)", elev=38, azim=-62)
    scene([(tray, GREY), (cell, AMBER), (pb, BOARD), (parts, GREEN), (moved(lid, 34), GREY * 1.1)],
            REN / "v1_demo_exploded.png", "Exploded: base with cradle, LiPo under the board (amber), perfboard + part boxes (green, heights ASSUMED), lid with pin guides and collar", elev=30, azim=-62)
    fig, axs = plt.subplots(2, 1, figsize=(11, 6.2), dpi=150)
    for ax, ydoc, nm in ((axs[0], P.BH_XYDOC[1], "BH1750 / SuperMini USB-C row"), (axs[1], P.USB_TP_YDOC, "TP4056 USB-C / AHT20 vent row")):
        y0 = P.cy(ydoc)
        section(ax, [(tray, "#555a60"), (lid, "#7d848b"), (pb, "#0f7a5c"), (parts, "#7fc9a8")], y0, f"Section y = {y0:.1f} ({nm}); green = perfboard and part boxes (heights ASSUMED)")
    axs[1].set_xlabel("X mm")
    fig.savefig(REN / "v1_demo_section.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    # plan view
    fig, ax = plt.subplots(figsize=(11, 7.2), dpi=150)
    ax.add_patch(Rectangle((P.OX0, P.OY0), P.OX1 - P.OX0, P.OY1 - P.OY0, fc="#e6e8ea", ec="#333", lw=1.2))
    ax.add_patch(Rectangle((P.IX0, P.IY0), P.IX1 - P.IX0, P.IY1 - P.IY0, fc="white", ec="#333", lw=0.8))
    ax.add_patch(Rectangle((0, 0), P.PB_L, P.PB_W, fc="#dff0e8", ec="#0f7a5c", lw=1.5))
    for n, (x0, y0, x1, y1, h, s) in P.PARTS.items():
        ax.add_patch(Rectangle((x0, P.cy(y1)), x1 - x0, y1 - y0, fc=(0.05, 0.45, 0.3, 0.25), ec="#0f7a5c", lw=0.5))
        ax.text((x0 + x1) / 2, (P.cy(y0) + P.cy(y1)) / 2, n, fontsize=6, ha="center", va="center")
    kx0, ky0d, kx1, ky1d = P.ANT_KEEPOUT_DOC
    ax.add_patch(Rectangle((kx0, P.cy(ky1d)), kx1 - kx0, P.IY1 - P.cy(ky1d), fc=(0.9, 0.2, 0.2, 0.12), ec="#c33", ls="--", lw=0.8))
    ax.text((kx0 + kx1) / 2, P.cy(ky1d) - 3.0, "antenna keep-out\n(no metal, cell, wire)", fontsize=6, ha="center", va="top", color="#c33")
    ax.add_patch(Rectangle((P.CELL_X0, P.CELL_Y0), P.CELL_X1 - P.CELL_X0, P.CELL_Y1 - P.CELL_Y0, fc=(0.95, 0.65, 0.1, 0.35), ec="#c98a00", ls="-", lw=1.0))
    ax.text((P.CELL_X0 + P.CELL_X1) / 2, (P.CELL_Y0 + P.CELL_Y1) / 2, "LiPo EEMB LP603449 (UNDER the board)\n51 x 34.5 x 6.3, BRIEF size\nlead end at bottom stop", ha="center", fontsize=7)
    ax.add_patch(Rectangle((P.CAV_X0 - P.STOP_T, P.CAV_Y0 - P.STOP_T), P.CAV_X1 - P.CAV_X0 + 2 * P.STOP_T, P.CAV_Y1 - P.CAV_Y0 + 2 * P.STOP_T, fc="none", ec="#555", ls=":", lw=0.8))
    ax.add_patch(Rectangle((P.CAV_X0 - P.STOP_T, P.CAV_Y0 - P.STOP_T), P.STOP_T, P.CAV_Y1 - P.CAV_Y0 + 2 * P.STOP_T, fc="#999", ec="#333", lw=0.4))
    ax.text(P.CAV_X0 - P.STOP_T - 1, P.CAV_Y1 + 3, "cradle wall", fontsize=5.5, ha="right", color="#555")
    ax.add_patch(Rectangle((P.LEAD_NOTCH_X[0], P.CAV_Y0 - P.STOP_T), P.LEAD_NOTCH_X[1] - P.LEAD_NOTCH_X[0], P.STOP_T, fc="white", ec="#c33", lw=0.8))
    ax.annotate("lead notch", (P.LEAD_NOTCH_X[1], P.CAV_Y0 - P.STOP_T), (P.LEAD_NOTCH_X[1] + 3, -6), fontsize=6, arrowprops=dict(arrowstyle="-"))
    for x, y in P.SR_POSTS:
        ax.add_patch(Circle((x, y), P.POST_D / 2, fc="#555"))
    jx0, jx1, jy0, jy1 = P.JST_PARK
    ax.add_patch(Rectangle((jx0, jy0), jx1 - jx0, jy1 - jy0, fc="none", ec="#555", ls="--", lw=0.8))
    ax.text((jx0 + jx1) / 2, (jy0 + jy1) / 2, "JST-PH pair parking", fontsize=5.5, ha="center", va="center")
    for x, y in P.boss_xy():
        ax.add_patch(Circle((x, y), P.BOSS_D / 2, fc="#999", ec="#333")); ax.add_patch(Circle((x, y), P.INSERT_HOLE / 2, fc="white", ec="#333", lw=0.5))
    for x, y in E.btn_xy():
        ax.add_patch(Circle((x, y), P.BTN_HOLE_D / 2, fc="red"))
    ax.annotate("BOOT/RESET pin guides d2.2", E.btn_xy()[0], (-4, 57), fontsize=6, arrowprops=dict(arrowstyle="-"))
    bx, by = P.BH_XYDOC[0], P.cy(P.BH_XYDOC[1]); ax.add_patch(Circle((bx, by), P.BH_WIN_D / 2, fc="#ffd84d", ec="#333")); ax.annotate("BH1750 light window d5", (bx, by), (bx + 4, by + 10), fontsize=6, arrowprops=dict(arrowstyle="-"))
    ax_, ay_ = P.AHT_XYDOC[0], P.cy(P.AHT_XYDOC[1])
    for i in range(P.VENT_N):
        dx = (i - (P.VENT_N - 1) / 2) * P.VENT_PITCH
        ax.add_patch(Rectangle((ax_ + dx - P.VENT_W / 2, ay_ - P.VENT_L / 2), P.VENT_W, P.VENT_L, fc="#6aa", ec="#333", lw=0.3))
    ax.annotate("AHT20 vents 4 x 1.6 x 10", (ax_, ay_ - 5), (ax_ - 8, ay_ - 12), fontsize=6, arrowprops=dict(arrowstyle="-"))
    jx, jy = P.J1_XYDOC[0], P.cy(P.J1_XYDOC[1]); ax.add_patch(Rectangle((jx - P.HATCH[0] / 2, jy - P.HATCH[1] / 2), *P.HATCH, fc="none", ec="#a0a", lw=1)); ax.text(jx + 5, jy, "J1 hatch", fontsize=6, va="center", color="#a0a")
    lx, ly = P.LED_XYDOC[0], P.cy(P.LED_XYDOC[1]); ax.add_patch(Rectangle((lx - P.LED_WIN[0] / 2, ly - P.LED_WIN[1] / 2), *P.LED_WIN, fc="none", ec="#a50", lw=1)); ax.text(lx, ly - 4, "LED window (position OPEN)", fontsize=6, ha="center", color="#a50")
    for ydoc, nm in ((P.USB_SM_YDOC, "USB-C flash"), (P.USB_TP_YDOC, "USB-C charge")):
        yc = P.cy(ydoc); ax.add_patch(Rectangle((P.OX0 - 0.5, yc - P.PLUG_W / 2), 2.4, P.PLUG_W, fc="#ffd84d", ec="#333")); ax.text(P.OX0 - 1.5, yc, nm, fontsize=6, rotation=90, ha="right", va="center")
    ax.add_patch(Rectangle((P.J3_XYDOC[0] - P.CABLE_W / 2, P.OY0 - 0.5), P.CABLE_W, 2.4, fc="#ffd84d", ec="#333")); ax.text(P.J3_XYDOC[0], P.OY0 - 2.0, "soil cable exit", fontsize=6, ha="center", va="top")
    ax.set_xlim(P.OX0 - 8, P.OX1 + 3); ax.set_ylim(P.OY0 - 6, P.OY1 + 3); ax.set_aspect("equal")
    ax.set_title(f"v1 demo housing plan, round 2 compact (lid off): outer {P.OX1 - P.OX0:.1f} x {P.OY1 - P.OY0:.1f} mm, inner height {P.Z_TOP - P.Z_FLOOR:.1f} mm, lid shell {P.LID_SHELL_H:.1f} mm; perfboard 70 x 50 in green; part positions per WIRING.md (UNVERIFIED)", fontsize=8)
    fig.savefig(REN / "v1_demo_plan.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("renders in", REN)


if __name__ == "__main__":
    main()

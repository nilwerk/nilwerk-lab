"""Real renders from the exported STL meshes (matplotlib, painter's algorithm + Lambert shading).
Run after build.py: python render.py -> renders/<variant>_{hero,exploded,section}.png + compare_section.png"""
import pathlib
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import bay
import params as P

HERE = pathlib.Path(__file__).parent
OUT, REN = HERE / "out", HERE / "renders"
GREY = np.array([0.33, 0.35, 0.37])       # PETG grey
LIGHT = np.array([-0.4, -0.6, 0.8]); LIGHT /= np.linalg.norm(LIGHT)


def load(key, part, dz=0.0):
    m = trimesh.load(OUT / key / f"bay_{key}_{part}.stl")
    m.apply_translation((0, 0, dz))
    return m


def lid_assembled(key, rise=0.0):
    """Lid as assembled: plate bottom on the tray rim."""
    d = bay.dims(key)
    m = trimesh.load(OUT / key / f"bay_{key}_lid.stl")
    m.apply_translation((0, 0, d["tray_h"] + rise))
    return m


def cell_mesh(key):
    d = bay.dims(key)
    m = trimesh.creation.box((d["cell_l"], d["cell_w"], d["cell_h"]))
    m.apply_translation((0, 0, P.FLOOR + d["cell_h"] / 2))
    return m


def faces(mesh, color, alpha=1.0):
    n = mesh.face_normals
    shade = 0.35 + 0.65 * np.clip(n @ LIGHT, 0, 1)
    cols = np.clip(np.outer(shade, color), 0, 1)
    return mesh.triangles, np.hstack([cols, np.full((len(cols), 1), alpha)])


def scene(meshes, path, title, elev=28, azim=-52):
    fig = plt.figure(figsize=(8, 5.5), dpi=150)
    ax = fig.add_subplot(111, projection="3d")
    allv = np.vstack([m.vertices for m, _, _ in meshes])
    parts = [faces(m, c, a) for m, c, a in meshes]
    ax.add_collection3d(Poly3DCollection(np.concatenate([p[0] for p in parts]),
                        facecolors=np.concatenate([p[1] for p in parts]), edgecolors=(0, 0, 0, 0.08), linewidths=0.2))
    lo, hi = allv.min(0), allv.max(0)
    ctr, r = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(ctr[0] - r, ctr[0] + r); ax.set_ylim(ctr[1] - r, ctr[1] + r); ax.set_zlim(ctr[2] - r, ctr[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev, azim); ax.set_axis_off()
    fig.suptitle(title, fontsize=10)
    fig.savefig(path, bbox_inches="tight", facecolor="white"); plt.close(fig)


def section(ax, key, plane_normal, plane_origin, xlabel, hax, title):
    """2D cut of tray + lid + cell envelope; hax = index of horizontal axis in 3D."""
    d = bay.dims(key)
    for part, col in (("tray", "#555b61"), ("lid", "#7d848b")):
        m = load(key, "tray") if part == "tray" else lid_assembled(key)
        sec = m.section(plane_origin=plane_origin, plane_normal=plane_normal)
        for seg in sec.discrete:
            ax.fill(seg[:, hax], seg[:, 2], color=col, lw=0.6, ec="k")
    c = cell_mesh(key).bounds
    ax.fill([c[0][hax], c[1][hax], c[1][hax], c[0][hax]], [c[0][2], c[0][2], c[1][2], c[1][2]],
            color="#d9a441", alpha=0.85, ec="k", lw=0.6)
    ax.set_aspect("equal"); ax.set_title(title, fontsize=9); ax.set_xlabel(xlabel); ax.set_ylabel("Z (mm)")


def render_variant(key):
    d = bay.dims(key)
    tray, lid, cell = load(key, "tray"), lid_assembled(key), cell_mesh(key)
    t = d["name"]
    scene([(tray, GREY, 1), (lid, GREY * 1.15, 1)], REN / f"{key}_hero.png",
          f"{t}: assembled bay {d['out_l']:.1f} x {d['out_w']:.1f} x {d['out_h']:.1f} mm (PETG grey)", azim=-125)
    scene([(tray, GREY, 1), (cell, np.array([0.85, 0.65, 0.25]), 1), (lid_assembled(key, 14), GREY * 1.15, 1)],
          REN / f"{key}_exploded.png", f"{t}: exploded, cell envelope {d['cell_l']} x {d['cell_w']} x {d['cell_h']} mm", elev=32)
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 3.6), dpi=150, gridspec_kw={"width_ratios": [d["out_l"], d["out_w"]]})
    section(a, key, (0, 1, 0), (0, 0, 0), "X, length (mm)", 0, f"long section Y=0, cavity H {d['bay_h']:.1f}, cell {d['cell_h']}")
    section(b, key, (1, 0, 0), (0, 0, 0), "Y, width (mm)", 1, f"cross section X=0, cavity W {d['bay_w']:.1f}")
    fig.suptitle(f"{t}: section through the bay (cell envelope in amber)", fontsize=10)
    fig.savefig(REN / f"{key}_section.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


def render_compare():
    fig, axs = plt.subplots(2, 1, figsize=(8, 6), dpi=150, sharex=True)
    for ax, key in zip(axs, P.VARIANTS):
        d = bay.dims(key)
        section(ax, key, (0, 1, 0), (0, 0, 0), "X, length (mm)", 0,
                f"{d['name']}: outer {d['out_l']:.1f} x {d['out_w']:.1f} x {d['out_h']:.1f}, cavity H {d['bay_h']:.1f}")
    fig.savefig(REN / "compare_section.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    REN.mkdir(exist_ok=True)
    for k in P.VARIANTS:
        render_variant(k)
    render_compare()
    print("rendered to", REN)

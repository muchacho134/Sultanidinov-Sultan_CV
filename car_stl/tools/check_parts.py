import sys, json, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from overlay import load, mesh
from shade import render_sheet, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh'); P = json.load(open("parts.json"))
GAP = {"front": 12.0, "rear": 8.0}
# ---- 1) sections with CAD outlines
fig, ax = plt.subplots(2, 2, figsize=(18, 11))
t = np.linspace(0, 2 * np.pi, 300)
for row, lab in enumerate(("front", "rear")):
    w = P[lab]
    a = ax[row, 0]
    for y, col in ((800, 'k'), (700, 'tab:blue'), (950, 'tab:orange')):
        s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
        for e in s.discrete:
            if (np.abs(e[:, 0] - w["x"]) < 700).any(): a.plot(e[:, 0], e[:, 2], '-', color=col, lw=.9, label=f"mesh y={y}" if e is s.discrete[0] else None)
    a.plot(w["x"] + w["r"] * np.cos(t), w["z"] + w["r"] * np.sin(t), 'r-', lw=2, label=f"CAD tyre r {w['r']:.0f}")
    rw = w["r"] + GAP[lab]
    a.plot(w["x"] + rw * np.cos(t[:150]), w["z"] + rw * np.sin(t[:150]), 'm--', lw=1.5, label=f"well r {rw:.0f}")
    xs = np.array([w["x"] - 700, w["x"] + 700]); a.plot(xs, P["floor"]["z0"] + P["floor"]["kx"] * xs, 'g-', lw=2, label="CAD floor")
    a.set_xlim(w["x"] - 700, w["x"] + 700); a.set_ylim(-20, 1000); a.set_aspect('equal'); a.grid(alpha=.3); a.legend(fontsize=8)
    a.set_title(f"{lab}: side sections vs CAD")
    a = ax[row, 1]
    for dx, col in ((0, 'k'), (-200, 'tab:blue'), (200, 'tab:orange')):
        s = m.section(plane_origin=[w["x"] + dx, 0, 0], plane_normal=[1, 0, 0])
        for e in s.discrete: a.plot(e[:, 1], e[:, 2], '-', color=col, lw=.9, label=f"mesh x={w['x'] + dx:.0f}" if e is s.discrete[0] else None)
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * w["y_in"], sgn * w["y_out"]))
        a.plot([y0, y1, y1, y0, y0], [w["z"] - w["r"], w["z"] - w["r"], w["z"] + w["r"], w["z"] + w["r"], w["z"] - w["r"]], 'r-', lw=2)
        a.plot([sgn * w["wall"]] * 2, [0, w["z"] + rw], 'm--', lw=1.5)
    a.plot([-1100, 1100], [P["floor"]["z0"] + P["floor"]["kx"] * w["x"]] * 2, 'g-', lw=2)
    a.set_xlim(-1100, 1100); a.set_ylim(-20, 1000); a.set_aspect('equal'); a.grid(alpha=.3); a.legend(fontsize=8)
    a.set_title(f"{lab}: cross sections through the axle (red = CAD wheels, magenta = well wall, green = floor)")
fig.tight_layout(); fig.savefig("parts_sections.png", dpi=70)
# ---- 2) 3D: mesh faces inside the wheel regions in red, CAD wheels dark, floor seen from below
V, F = np.asarray(m.vertices, float), np.asarray(m.faces)
c = m.triangles_center; inside = np.zeros(len(F), bool)
for lab in ("front", "rear"):
    w = P[lab]; rw = w["r"] + GAP[lab]
    inw = (np.abs(c[:, 1]) > w["wall"]) & ((np.hypot(c[:, 0] - w["x"], c[:, 2] - w["z"]) < rw) |
                                           ((np.abs(c[:, 0] - w["x"]) < rw) & (c[:, 2] < w["z"])))
    inside |= inw
C = np.tile([0.86, 0.87, 0.89], (len(F), 1)); C[inside] = (0.92, 0.25, 0.2)
Vs, Fs, Cs = [V], [F], [C]; off = len(V)
for k in json.load(open("part_names.json")):
    if not k.startswith("Wheel_"): continue
    v, f = mesh(load(f"part_{k}.brep"), 2.0)
    Vs.append(v); Fs.append(f + off); Cs.append(np.tile([0.12, 0.12, 0.14], (len(f), 1))); off += len(v)
V2, F2, C2 = np.vstack(Vs), np.vstack(Fs), np.vstack(Cs)
render_sheet(V2, F2, C2, "parts_3d.png", N=vertex_normals(V2, F2))

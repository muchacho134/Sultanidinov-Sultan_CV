"""Wireframe over the faint mesh: side, from below, front, and a 3/4 view from below."""
import sys, json, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
m = trimesh.load(sys.argv[1], force='mesh'); W = {k: np.array(v) for k, v in json.load(open(sys.argv[2])).items()}; out = sys.argv[3]
V, F, fn, fc = m.vertices, m.faces, m.face_normals, m.triangles_center
half = fc[:, 1] <= 5
COL = lambda k: 'red' if k.startswith("outer") else ('blue' if k == "centreline" else ('black' if "opening" in k else ('tab:green' if k.startswith("long") else 'tab:orange')))
R = lambda yaw, pitch: (np.array([[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]]) @
                        np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]]))
views = (("SIDE", lambda X: X[:, [0, 2]], half & (fn[:, 1] < 0)),
         ("FROM BELOW", lambda X: X[:, [0, 1]] * [1, -1], half & (fn[:, 2] < 0)),
         ("FRONT", lambda X: X[:, [1, 2]], half & (fn[:, 0] < 0)),
         ("3/4 FROM BELOW", lambda X: (X @ R(np.radians(30), np.radians(-120)).T)[:, :2], half & (fn[:, 2] < 0)))
fig = plt.figure(figsize=(22, 15)); gs = fig.add_gridspec(3, 2, height_ratios=[0.8, 1, 1.2])
axs = [fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, :]), fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1])]
for a, (title, pr, sel) in zip(axs, views):
    T = np.stack([pr(V[F[sel]][:, k]) for k in range(3)], 1)
    a.add_collection(PolyCollection(T, facecolors=(0.9, 0.9, 0.92), edgecolors=(0.82, 0.82, 0.85), lw=0.2))
    for k, w in W.items():
        q = pr(w); a.plot(q[:, 0], q[:, 1], '-', color=COL(k), lw=2.2 if not (k.startswith("long") or k.startswith("cross")) else 1.4)
    a.autoscale(); a.set_aspect('equal'); a.set_title(title, fontsize=14); a.grid(alpha=.2)
axs[0].plot([], [], 'r-', label='outer edge'); axs[0].plot([], [], 'b-', label='centreline'); axs[0].plot([], [], 'k-', label='wheel openings')
axs[0].plot([], [], '-', color='tab:green', label='lengthwise'); axs[0].plot([], [], '-', color='tab:orange', label='crosswise'); axs[0].legend(loc='upper left')
fig.tight_layout(); fig.savefig(out, dpi=60)

"""Curated curve network over the STL: side, top, nose, tail, with every curve labelled."""
import sys, json, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
m = trimesh.load(sys.argv[1], force='mesh'); C = {k: np.array(v) for k, v in json.load(open(sys.argv[2])).items()}; out = sys.argv[3]
V, F = m.vertices, m.faces; fc = m.triangles_center; fn = m.face_normals; half = fc[:, 1] <= 5
L = np.array([0.35, -0.55, 0.75]); L /= np.linalg.norm(L)
fig = plt.figure(figsize=(22, 17)); gs = fig.add_gridspec(3, 2)
axs = [fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, :]), fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1])]
views = (("SIDE", 0, 2, half & (fn[:, 1] < 0), None), ("TOP", 0, 1, half & (fn[:, 2] > 0), None),
         ("NOSE (from front)", 1, 2, half & (fn[:, 0] < -0.05) & (fc[:, 0] < -1500), lambda Q: Q[:, 0].min() < -1500),
         ("TAIL (from rear)", 1, 2, half & (fn[:, 0] > 0.05) & (fc[:, 0] > 1700), lambda Q: Q[:, 0].max() > 1700))
cm_ = plt.cm.tab20
for a, (title, i, j, sel, keep) in zip(axs, views):
    T = V[F[sel]][:, :, [i, j]]; sh = 0.4 + 0.55 * np.clip(np.abs(fn[sel] @ L), 0, 1)
    a.add_collection(PolyCollection(T, facecolors=plt.cm.gray(sh), edgecolors='none'))
    for n_, (k, Q) in enumerate(C.items()):
        if keep and not keep(Q): continue
        a.plot(Q[:, i], Q[:, j], '-', lw=2.6, color=cm_(n_ % 20))
        q = Q[len(Q) // 2]; a.text(q[i], q[j], k, fontsize=9, weight='bold', color=cm_(n_ % 20))
    a.autoscale(); a.set_aspect('equal'); a.set_title(title, fontsize=14); a.grid(alpha=.2)
fig.tight_layout(); fig.savefig(out, dpi=60)

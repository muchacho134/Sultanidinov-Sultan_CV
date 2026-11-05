"""Close views of the nose and tail faces (y-z), and the side (x-z), with selected curves labelled."""
import sys, json, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
m = trimesh.load(sys.argv[1], force='mesh'); C = json.load(open(sys.argv[2])); out = sys.argv[3]
V, F = m.vertices, m.faces; fc = m.triangles_center; fn = m.face_normals; half = fc[:, 1] <= 5
L = np.array([0.35, -0.55, 0.75]); L /= np.linalg.norm(L)
def shade(sel, i, j, a):
    T = V[F[sel]][:, :, [i, j]]; sh = 0.35 + 0.6 * np.clip(np.abs(fn[sel] @ L), 0, 1)
    a.add_collection(PolyCollection(T, facecolors=plt.cm.gray(sh), edgecolors='none'))
fig, ax = plt.subplots(1, 3, figsize=(24, 9), gridspec_kw={'width_ratios': [1, 1, 1.4]})
cm_ = plt.cm.tab20
for a, (title, sel, i, j, keep) in zip(ax, (
        ("NOSE (from -x), x < -1700", half & (fn[:, 0] < -0.05) & (fc[:, 0] < -1700), 1, 2, lambda P: P[:, 0].mean() < -1600),
        ("TAIL (from +x), x > 1800", half & (fn[:, 0] > 0.05) & (fc[:, 0] > 1800), 1, 2, lambda P: P[:, 0].mean() > 1800),
        ("TAIL corner, side view x > 1500", half & (fn[:, 1] < 0) & (fc[:, 0] > 1500), 0, 2, lambda P: P[:, 0].max() > 1700))):
    shade(sel, i, j, a)
    for n_, (k, v) in enumerate(C.items()):
        P = np.array(v["points"])
        if not keep(P): continue
        a.plot(P[:, i], P[:, j], '-', lw=2.5, color=cm_(n_ % 20)); q = P[len(P) // 2]
        a.text(q[i], q[j], k, fontsize=11, weight='bold', color=cm_(n_ % 20))
    a.autoscale(); a.set_aspect('equal'); a.set_title(title); a.grid(alpha=.25)
fig.tight_layout(); fig.savefig(out, dpi=60)

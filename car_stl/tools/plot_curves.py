import sys, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m = trimesh.load(sys.argv[1], force='mesh'); C = np.load(sys.argv[2]); out = sys.argv[3]
V = m.vertices; F = m.faces; fc = m.triangles_center; half = fc[:, 1] <= 5
curves = [C[k] for k in sorted(C.files, key=lambda s: int(s.split('_')[1]))]
fig, ax = plt.subplots(3, 1, figsize=(18, 17), gridspec_kw={'height_ratios': [1.2, 1.9, 1.2]})
views = (("side (from -y)", 0, 2, lambda f: m.face_normals[f, 1] < 0), ("top", 0, 1, lambda f: m.face_normals[f, 2] > 0),
         ("rear (from +x)", 1, 2, lambda f: m.face_normals[f, 0] > 0))
cmap = plt.cm.tab20
for a, (title, i, j, facing) in zip(ax, views):
    sel = half & facing(np.arange(len(F)))
    T = V[F[sel]][:, :, [i, j]]
    from matplotlib.collections import PolyCollection
    a.add_collection(PolyCollection(T, facecolors=(0.85, 0.86, 0.88), edgecolors='none'))
    for k, Q in enumerate(curves):
        a.plot(Q[:, i], Q[:, j], '-', color=cmap(k % 20), lw=2.2)
        p = Q[len(Q) // 2]; a.text(p[i], p[j], str(k), fontsize=9, weight='bold')
    a.autoscale(); a.set_aspect('equal'); a.set_title(title); a.grid(alpha=.25)
fig.tight_layout(); fig.savefig(out, dpi=65)

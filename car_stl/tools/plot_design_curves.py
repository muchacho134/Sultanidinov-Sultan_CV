import sys, json, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
m = trimesh.load(sys.argv[1], force='mesh'); C = json.load(open(sys.argv[2])); out = sys.argv[3]
V, F = m.vertices, m.faces; fc = m.triangles_center; fn = m.face_normals; half = fc[:, 1] <= 5
fig = plt.figure(figsize=(20, 15)); gs = fig.add_gridspec(3, 2, width_ratios=[2.6, 1])
axs = [fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, :]), fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1])]
views = (("SIDE (from -y)", 0, 2, fn[:, 1] < 0), ("TOP", 0, 1, fn[:, 2] > 0), ("SECTIONS (y-z) every 200 mm", None, None, None),
         ("REAR (from +x)", 1, 2, fn[:, 0] > 0))
cmap = plt.cm.tab10
names = [k for k in C]
for a, (title, i, j, facing) in zip(axs, views):
    if i is not None:
        sel = half & facing
        T = V[F[sel]][:, :, [i, j]]
        sh = np.clip(0.55 + 0.45 * np.abs(fn[sel] @ np.array([0.3, -0.6, 0.75])), 0, 1)
        a.add_collection(PolyCollection(T, facecolors=plt.cm.gray(0.35 + 0.6 * sh), edgecolors='none'))
        for n_, k in enumerate(names):
            P = np.array(C[k]["points"]); ax_ = C[k].get("axis", -1)
            col = 'r' if k == "centre_profile" else ('b' if k == "plan_outline" else {0: 'tab:orange', 1: 'tab:green', 2: 'tab:purple'}[ax_])
            a.plot(P[:, i], P[:, j], '-', color=col, lw=2.4)
            q = P[len(P) // 2]
            if k not in ("centre_profile", "plan_outline"): a.text(q[i], q[j], k, fontsize=8, weight='bold', color=col)
        a.autoscale(); a.set_aspect('equal'); a.set_title(title); a.grid(alpha=.2)
    else:
        for x in np.arange(-2100, 2200, 200.0):
            sec = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
            if sec is None: continue
            for p in sec.discrete:
                q = p[p[:, 1] <= 2]
                if len(q): a.plot(q[:, 1], q[:, 2], '.', ms=0.6, color=plt.cm.viridis((x + 2300) / 4600))
        for n_, k in enumerate(names):
            if C[k].get("axis") != 0: continue
            P = np.array(C[k]["points"]); a.plot(P[:, 1], P[:, 2], '-', lw=1.6, color=cmap(n_ % 10))
        a.set_aspect('equal'); a.set_title(title); a.grid(alpha=.2)
fig.tight_layout(); fig.savefig(out, dpi=60)

import sys, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m = trimesh.load(sys.argv[1], force='mesh'); V = m.vertices
# wheels: outward faces near |y| max and below z 800
for s, name in ((1, "+Y"), (-1, "-Y")):
    sel = (V[:, 1] * s > 960) & (V[:, 2] < 800)
    P = V[sel]
    for xs, lab in ((P[:, 0] < 0, "front"), (P[:, 0] > 0, "rear")):
        Q = P[xs]
        A = np.c_[2 * Q[:, 0], 2 * Q[:, 2], np.ones(len(Q))]; b = (Q[:, [0, 2]] ** 2).sum(1)
        cx, cz, c = np.linalg.lstsq(A, b, rcond=None)[0]; r = np.sqrt(c + cx * cx + cz * cz)
        print("wheel %s %s: centre x %.0f z %.0f  outer r %.0f  face |y| %.0f..%.0f  pts %d" %
              (name, lab, cx, cz, r, np.abs(Q[:, 1]).min(), np.abs(Q[:, 1]).max(), len(Q)))
fig, ax = plt.subplots(2, 1, figsize=(16, 11))
# side silhouette + centreline section
sec = m.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
for e in sec.discrete: ax[0].plot(e[:, 0], e[:, 2], 'k-', lw=1)
for y, col in ((450, 'tab:blue'), (800, 'tab:orange'), (960, 'tab:green')):
    s_ = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s_ is not None:
        for e in s_.discrete: ax[0].plot(e[:, 0], e[:, 2], '-', color=col, lw=.8)
ax[0].set_title("Longitudinal sections at y = 0 (black), 450, 800, 960 mm"); ax[0].set_aspect('equal'); ax[0].grid(alpha=.3)
# cross sections
xs = [-2150, -1700, -1200, -600, 0, 600, 1100, 1600, 2000, 2200]
cmap = plt.cm.viridis
for i, x in enumerate(xs):
    s_ = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
    if s_ is None: continue
    for e in s_.discrete: ax[1].plot(e[:, 1], e[:, 2], '-', color=cmap(i / len(xs)), lw=1, label=str(x) if e is s_.discrete[0] else None)
ax[1].legend(fontsize=8, ncol=5); ax[1].set_aspect('equal'); ax[1].grid(alpha=.3)
ax[1].set_title("Cross sections at x (mm, - = nose, + = tail)")
fig.tight_layout(); fig.savefig("sections.png", dpi=80)

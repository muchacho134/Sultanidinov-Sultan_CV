import sys, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m = trimesh.load(sys.argv[1], force='mesh')
fig, ax = plt.subplots(1, 2, figsize=(18, 7))
for a, (lab, x0, z0) in zip(ax, (("front", -1297.0, 391.0), ("rear", 1356.0, 400.0))):
    for th, col in ((90, 'k'), (45, 'tab:blue'), (135, 'tab:orange'), (20, 'tab:green'), (160, 'tab:red')):
        t = np.radians(th)
        u = np.array([np.cos(t), 0, np.sin(t)])          # radial direction in x-z (0 deg = towards tail)
        nrm = np.cross(u, [0, 1, 0])                      # plane contains the axle (Y) and u
        s = m.section(plane_origin=[x0, 0, z0], plane_normal=nrm)
        if s is None: continue
        for e in s.discrete:
            r = (e - [x0, 0, z0]) @ u
            sel = (r > 150) & (np.abs(e[:, 1]) > 450)
            if sel.sum() > 2:
                rr, yy = np.where(sel, r, np.nan), np.where(sel, np.abs(e[:, 1]), np.nan)
                a.plot(yy, rr, '-', color=col, lw=1, label=f"{th} deg" if e is s.discrete[0] else None)
    a.axhline(0, color='gray', lw=.5); a.set_xlim(450, 1060); a.set_ylim(150, 700); a.set_aspect('equal'); a.grid(alpha=.3)
    a.set_xlabel("|y| (mm)"); a.set_ylabel("distance from axle (mm)"); a.legend(fontsize=8)
    a.set_title(f"{lab} wheel: radial slices through the axle (angle from horizontal-rearward)")
fig.tight_layout(); fig.savefig("wheel_radial.png", dpi=75)

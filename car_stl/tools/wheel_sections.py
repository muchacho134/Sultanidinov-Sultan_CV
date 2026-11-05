import sys, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m = trimesh.load(sys.argv[1], force='mesh')
fig, ax = plt.subplots(2, 3, figsize=(20, 12))
for row, (xc, lab) in enumerate(((-1297, "front"), (1356, "rear"))):
    # cross section through the axle (y-z)
    a = ax[row, 0]
    for dx, col in ((0, 'k'), (-150, 'tab:blue'), (150, 'tab:orange'), (-300, 'tab:green'), (300, 'tab:red')):
        s = m.section(plane_origin=[xc + dx, 0, 0], plane_normal=[1, 0, 0])
        if s is None: continue
        for e in s.discrete: a.plot(e[:, 1], e[:, 2], '-', color=col, lw=1, label=f"x={xc+dx}" if e is s.discrete[0] else None)
    a.set_xlim(300, 1060); a.set_ylim(-20, 900); a.set_aspect('equal'); a.grid(alpha=.3); a.legend(fontsize=8)
    a.set_title(f"{lab} wheel: cross sections (y-z)")
    # longitudinal sections at several y (x-z)
    a = ax[row, 1]
    for y, col in ((1000, 'k'), (980, 'tab:purple'), (940, 'tab:blue'), (880, 'tab:green'), (760, 'tab:orange'), (650, 'tab:red'), (580, 'tab:brown')):
        s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
        if s is None: continue
        for e in s.discrete:
            sel = np.abs(e[:, 0] - xc) < 650
            if sel.any(): a.plot(e[:, 0], e[:, 2], '-', color=col, lw=1, label=f"y={y}" if e is s.discrete[0] else None)
    a.set_xlim(xc - 650, xc + 650); a.set_ylim(-20, 1000); a.set_aspect('equal'); a.grid(alpha=.3); a.legend(fontsize=8)
    a.set_title(f"{lab} wheel: longitudinal sections (x-z)")
    # horizontal sections at several z (x-y), positive y side
    a = ax[row, 2]
    for z, col in ((150, 'tab:blue'), (400, 'k'), (600, 'tab:orange'), (720, 'tab:red')):
        s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if s is None: continue
        for e in s.discrete:
            sel = (np.abs(e[:, 0] - xc) < 650) & (e[:, 1] > 300)
            if sel.any(): a.plot(e[:, 0], e[:, 1], '-', color=col, lw=1, label=f"z={z}" if e is s.discrete[0] else None)
    a.set_xlim(xc - 650, xc + 650); a.set_ylim(300, 1060); a.set_aspect('equal'); a.grid(alpha=.3); a.legend(fontsize=8)
    a.set_title(f"{lab} wheel: plan sections (x-y), +y side")
fig.tight_layout(); fig.savefig("wheel_sections.png", dpi=70)

"""Find candidate single-face regions on the half car (y <= 0).

Faces with low curvature (radius > R_CALM) are grown into regions across edges whose
dihedral angle is below ANG; large regions are candidate CAD faces, everything else
(tight bands, creases, recess walls) becomes blends / features.
"""
import sys, json, numpy as np, trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
R_CALM, ANG, MIN_AREA = float(sys.argv[2]), float(sys.argv[3]), 0.02e6
m = trimesh.load(sys.argv[1], force='mesh')
H = (np.load(sys.argv[6]) if len(sys.argv) > 6 else
     trimesh.curvature.discrete_mean_curvature_measure(m, m.vertices, 40.0) / (np.pi * 1600.0))
F = m.faces; fc = m.triangles_center
half = fc[:, 1] <= 5.0
calm = half & (np.abs(H[F].mean(1)) < 1.0 / R_CALM)
adj = m.face_adjacency; ang = np.degrees(m.face_adjacency_angles)
CONE = float(sys.argv[5]) if len(sys.argv) > 5 else 180.0
fn = m.face_normals; area0 = m.area_faces
nbrs = [[] for _ in range(len(F))]
for (a, b), t in zip(adj, ang):
    if t < ANG and calm[a] and calm[b]:
        nbrs[a].append(b); nbrs[b].append(a)
# region growing with a normal cone: a face joins only if its normal stays within CONE
# degrees of the region's area-weighted mean normal
lab = np.full(len(F), -1)
order = np.argsort(np.abs(H[F].mean(1)))          # flattest seeds first
cos_c = np.cos(np.radians(CONE)); k = 0
from collections import deque
for seed in order:
    if not calm[seed] or lab[seed] >= 0:
        continue
    lab[seed] = k; nsum = fn[seed] * area0[seed]; q = deque([seed])
    while q:
        f = q.popleft()
        for g in nbrs[f]:
            if lab[g] < 0:
                mean = nsum / np.linalg.norm(nsum)
                # stay within the cone of both the running mean and the seed (no drift)
                if fn[g] @ mean >= cos_c and fn[g] @ fn[seed] >= cos_c:
                    lab[g] = k; nsum = nsum + fn[g] * area0[g]; q.append(g)
    k += 1
area = m.area_faces
regs = []
for k in np.unique(lab[lab >= 0]):
    sel = lab == k
    A = area[sel].sum()
    if A < MIN_AREA:
        lab[sel] = -1; continue
    P = fc[sel]; c = np.average(P, axis=0, weights=area[sel])
    # plane test: RMS distance to the best-fit plane
    U, S, Vt = np.linalg.svd(P - c, full_matrices=False); nrm = Vt[-1]
    rms = np.sqrt(np.mean(((P - c) @ nrm) ** 2))
    regs.append(dict(id=int(k), area_m2=A / 1e6, centroid=c.round(0).tolist(), normal=nrm.round(2).tolist(),
                     plane_rms=float(rms), bbox=[P.min(0).round(0).tolist(), P.max(0).round(0).tolist()]))
regs.sort(key=lambda r: -r["area_m2"])
for i, r in enumerate(regs):
    r["n"] = i + 1
    kind = "PLANE" if r["plane_rms"] < 3 else "B-spline"
    print("%2d  %5.2f m2  %-8s  plane rms %6.1f mm  centroid %s  x %s..%s" %
          (r["n"], r["area_m2"], kind, r["plane_rms"], r["centroid"], r["bbox"][0][0], r["bbox"][1][0]))
tot = sum(r["area_m2"] for r in regs); half_area = area[half].sum() / 1e6
print("regions %d cover %.2f of %.2f m2 of the half (%.0f %%)" % (len(regs), tot, half_area, 100 * tot / half_area))
json.dump(regs, open("regions.json", "w"), indent=1)
np.save("region_labels.npy", lab)
# colour image: regions in distinct colours, blends grey, other half hidden
rng = np.random.default_rng(3)
pal = np.array([[0.90, 0.30, 0.25], [0.25, 0.55, 0.90], [0.30, 0.75, 0.40], [0.95, 0.70, 0.20], [0.60, 0.40, 0.85],
                [0.20, 0.75, 0.75], [0.95, 0.50, 0.70], [0.55, 0.65, 0.25], [0.85, 0.55, 0.30], [0.35, 0.35, 0.80],
                [0.75, 0.25, 0.55], [0.40, 0.80, 0.90], [0.80, 0.80, 0.35], [0.50, 0.30, 0.20], [0.30, 0.50, 0.40]])
C = np.tile([0.62, 0.63, 0.66], (len(F), 1))
for r in regs:
    C[lab == r["id"]] = pal[(r["n"] - 1) % len(pal)] if r["n"] <= len(pal) else rng.uniform(0.3, 0.95, 3)
keep = half
V = np.asarray(m.vertices, float); Fh = F[keep]
render_sheet(V, Fh, C[keep], sys.argv[4], N=vertex_normals(V, F))

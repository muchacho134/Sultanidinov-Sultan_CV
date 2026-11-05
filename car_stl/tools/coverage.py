"""Coverage check: distance from every half-car mesh vertex to the nearest CAD face (patches +
finished faces). Reports uncovered clusters (> GAP mm) with their location and owning patch."""
import sys, json, numpy as np, trimesh
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from overlay import load, mesh
from build_car import faces as occ_faces
m = trimesh.load(sys.argv[1], force='mesh'); lab = np.load(sys.argv[2]); GAP = float(sys.argv[5])
pts = []
for path in (sys.argv[3], sys.argv[4]):
    for f in occ_faces(load(path)):
        v, t = mesh(f, 0.5)
        if len(t):
            tm = trimesh.Trimesh(np.asarray(v, float), np.asarray(t), process=False)
            pts.append(tm.sample(max(int(tm.area / 25.0), 50)))       # ~1 point per 5x5 mm
            pts.append(tm.vertices)
tree = cKDTree(np.vstack(pts))
V = m.vertices; half = V[:, 1] <= -2
d, _ = tree.query(V[half]); idx = np.where(half)[0]
far = idx[d > GAP]
print("half-car vertices %d  uncovered (> %.0f mm) %d (%.1f %%)" % (half.sum(), GAP, len(far), 100 * len(far) / half.sum()))
if len(far):
    g = trimesh.graph.connected_components(m.edges_unique[np.isin(m.edges_unique, far).all(1)], nodes=far, min_len=1)
    vlab = np.full(len(V), -1)
    for fi, l in enumerate(lab):
        if l >= 0: vlab[m.faces[fi]] = l
    for comp in sorted(g, key=len, reverse=True)[:12]:
        P = V[comp]
        print("  cluster %4d verts  centre (%5.0f %5.0f %4.0f)  x %5.0f..%5.0f  patch labels %s" %
              (len(comp), *P.mean(0), P[:, 0].min(), P[:, 0].max(), np.unique(vlab[comp])))
np.save("uncovered.npy", far)

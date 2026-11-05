"""Split the half body into regions by surface direction, so neighbouring regions share borders.

labels: 0 bottom (-z), 1 back (+x), 2 front (-x), 3 top (+z), 4 side (-y), 5 wheel well
- normals smoothed over the mesh (removes wrap noise) before deciding
- each face goes to the direction it faces most; wheel-well faces are set aside
- labels cleaned: majority filter over neighbours, small islands merged into their surroundings
"""
import sys, json, numpy as np, trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh'); P = json.load(open(sys.argv[2])); OUT = sys.argv[3]
F, c, A = m.faces, m.triangles_center, m.area_faces
half = c[:, 1] <= 5
adj = m.face_adjacency
nF = len(F)
G = coo_matrix((np.ones(2 * len(adj)), (np.r_[adj[:, 0], adj[:, 1]], np.r_[adj[:, 1], adj[:, 0]])), shape=(nF, nF)).tocsr()
G = G + coo_matrix((np.ones(nF), (np.arange(nF), np.arange(nF))), shape=(nF, nF)).tocsr()
N = m.face_normals * A[:, None]
for _ in range(int(sys.argv[4]) if len(sys.argv) > 4 else 6):          # smooth normals
    N = G @ N
N /= np.linalg.norm(N, axis=1)[:, None] + 1e-12
DIRS = np.array([[0, 0, -1], [1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, -1, 0]], float)
W_ = np.array([1.15, 1.0, 1.0, 1.0, 1.0])                          # slight preference for the bottom
lab = np.argmax((N @ DIRS.T) * W_, axis=1)
# wheel wells: faces on/inside the well cylinders, inboard of the arch lip
for k, gap in (("front", 12.0), ("rear", 8.0)):
    w = P[k]; rw = w["r"] + gap
    d = np.hypot(c[:, 0] - w["x"], c[:, 2] - w["z"])
    well = (d < rw + 25) & (np.abs(c[:, 1]) > w["wall"] - 8) & (np.abs(c[:, 1]) < 1100) & (c[:, 2] > 60)
    lab[well & half] = 5
# majority filter (3 passes)
for _ in range(3):
    votes = np.zeros((nF, 6))
    for L in range(6):
        votes[:, L] = G @ ((lab == L) * A)
    keep5 = lab == 5
    lab = np.where(keep5, 5, np.argmax(votes[:, :5], axis=1))
# merge small islands
for _ in range(4):
    changed = False
    same = lab[adj[:, 0]] == lab[adj[:, 1]]
    g2 = coo_matrix((np.ones(same.sum()), (adj[same, 0], adj[same, 1])), shape=(nF, nF))
    nc, comp = connected_components(g2, directed=False)
    area = np.bincount(comp, weights=A * half, minlength=nc)
    for cc in np.where((area > 0) & (area < 0.012e6))[0]:
        idx = np.where(comp == cc)[0]
        e = np.isin(adj[:, 0], idx) ^ np.isin(adj[:, 1], idx)
        nb = np.where(np.isin(adj[e, 0], idx), lab[adj[e, 1]], lab[adj[e, 0]])
        nb = nb[nb != 5] if (nb != 5).any() else nb
        if len(nb):
            lab[idx] = np.bincount(nb, minlength=6).argmax(); changed = True
    if not changed: break
lab[~half] = -1
np.save(OUT, lab)
NAMES = ["bottom", "back", "front", "top", "side", "wheel well"]
for L in range(6):
    print("%-10s %.2f m2" % (NAMES[L], A[lab == L].sum() / 1e6))
COL = np.array([[0.35, 0.45, 0.95], [0.95, 0.35, 0.3], [0.3, 0.8, 0.45], [0.95, 0.8, 0.3], [0.75, 0.5, 0.9], [0.4, 0.4, 0.42]])
V = np.asarray(m.vertices, float)
render_sheet(V, F[half], COL[lab[half]], OUT.replace(".npy", ".png"), N=vertex_normals(V, F))

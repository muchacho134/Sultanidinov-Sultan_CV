"""Clean panel borders: subdivide the half body, carry the panel labels over, then fair every border
by diffusing the panel indicator fields over the surface (curve-shortening: jagged steps vanish,
long borders become smooth curves / straight lines). Borders drawn as crisp dark lines."""
import sys, numpy as np, trimesh
from scipy.sparse import coo_matrix, diags
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh'); lab = np.load(sys.argv[2], allow_pickle=True); OUT = sys.argv[3]
EDGE, ITERS = float(sys.argv[4]), int(sys.argv[5])
keep = m.triangles_center[:, 1] <= 5
h = m.submesh([np.where(keep)[0]], append=True)
hl = lab[keep]
V, F = trimesh.remesh.subdivide_to_size(h.vertices, h.faces, max_edge=EDGE)
s = trimesh.Trimesh(V, F, process=False)
_, fi = h.nearest.on_surface(s.triangles_center) if False else (None, None)
# label transfer: nearest original face centre
from scipy.spatial import cKDTree
_, j = cKDTree(h.triangles_center).query(s.triangles_center)
L0 = hl[j]
names = sorted(set(L0)); idx = {n: i for i, n in enumerate(names)}
li = np.array([idx[n] for n in L0])
nF, nV, K = len(F), len(V), len(names)
# face -> vertex averaging and back (area weighted)
A = s.area_faces
rows = np.repeat(np.arange(nF), 3); cols = F.ravel()
FV = coo_matrix((np.repeat(A, 3), (cols, rows)), shape=(nV, nF)).tocsr()
FV = diags(1 / np.asarray(FV.sum(1)).ravel()) @ FV                  # vertex = area-weighted mean of its faces
VF = coo_matrix((np.full(3 * nF, 1 / 3), (rows, cols)), shape=(nF, nV)).tocsr()
Ph = np.zeros((nF, K)); Ph[np.arange(nF), li] = 1.0
PINNED = [idx[n] for n in names if n in ("wheel well",)]            # wheel wells keep their exact (cylinder) border
for _ in range(ITERS):
    Ph = VF @ (FV @ Ph)
lab2 = np.argmax(Ph, axis=1)
for p in PINNED:
    lab2[li == p] = p; lab2[(lab2 == p) & (li != p)] = li[(lab2 == p) & (li != p)]
np.save(OUT.replace(".png", "_labels.npy"), np.array(names, dtype=object)[lab2])
PAL = {"floor": (0.3, 0.45, 0.85), "front undertray": (0.45, 0.55, 0.95), "rear diffuser": (0.25, 0.35, 0.7),
       "wheel well": (0.35, 0.35, 0.38), "front fascia": (0.35, 0.75, 0.45), "tail panel": (0.9, 0.4, 0.35),
       "hood": (0.95, 0.75, 0.25), "windshield": (0.2, 0.25, 0.32), "roof": (0.5, 0.55, 0.62), "side glass": (0.3, 0.38, 0.48),
       "engine cover / fastback": (0.85, 0.6, 0.2), "front fender": (0.6, 0.85, 0.35), "body side": (0.75, 0.55, 0.9),
       "rear quarter": (0.95, 0.55, 0.65), "sill": (0.55, 0.4, 0.75), "front bumper corner": (0.3, 0.65, 0.55),
       "rear bumper corner": (0.8, 0.3, 0.45), "side intake": (0.08, 0.08, 0.1), "front corner intake": (0.1, 0.1, 0.12),
       "tail light recess": (0.75, 0.1, 0.1), "diffuser opening": (0.12, 0.12, 0.14), "recess (other)": (0.5, 0.5, 0.5)}
C = np.array([PAL.get(names[k], (1, 0, 1)) for k in lab2])
# crisp border lines: faces touching a different label get darkened
adj = s.face_adjacency
b = lab2[adj[:, 0]] != lab2[adj[:, 1]]
edge_faces = np.unique(adj[b].ravel()); C[edge_faces] *= 0.25
render_sheet(np.asarray(V, float), F, C, OUT, N=vertex_normals(np.asarray(V, float), F))
print("faces", nF, "panels", K)

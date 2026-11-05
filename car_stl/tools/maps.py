import sys, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.cm as cm
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh'); V, F = np.asarray(m.vertices, float), np.asarray(m.faces)
H, d = np.load("H.npy"), np.load("mirror_d.npy")
N = vertex_normals(V, F)
def face(v): return v[F].mean(1)
# 1) curvature: blue = flat / large radius, red = tight convex, purple = concave
h = face(H)
t = np.clip(np.abs(h) * 150, 0, 1)            # 1/150mm radius saturates
C = np.where((h < 0)[:, None], cm.cool(t)[:, :3], cm.YlOrRd(0.15 + 0.85 * t)[:, :3])
C[t < 0.12] = (0.55, 0.72, 0.95)              # near-flat
render_sheet(V, F, C, "map_curvature.png", N=N)
# 2) creases: faces touching an edge sharper than 25 deg
ang = np.degrees(m.face_adjacency_angles); sharp = m.face_adjacency[ang > 25].ravel()
C = np.tile([0.85, 0.86, 0.88], (len(F), 1)); C[sharp] = (0.9, 0.1, 0.1)
render_sheet(V, F, C, "map_creases.png", N=N)
# 3) asymmetry: distance to the mirrored surface
t = np.clip(face(d) / 60.0, 0, 1)
render_sheet(V, F, cm.viridis(t)[:, :3], "map_asymmetry.png", N=N)

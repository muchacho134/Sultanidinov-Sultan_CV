"""Close-ups of each wheel well on the half car: from below and from a low 3/4 angle."""
import sys, json, numpy as np, trimesh
from PIL import Image
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import raster, rot, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh'); lab = np.load(sys.argv[2]); P = json.load(open(sys.argv[3]))
pal = np.array([[0.30, 0.55, 0.95], [0.55, 0.35, 0.90]] + [[0.30, 0.80, 0.45], [0.95, 0.55, 0.20], [0.95, 0.80, 0.25], [0.95, 0.80, 0.25]] * 2)
V = np.asarray(m.vertices, float); F = m.faces; c = m.triangles_center
C = np.where((lab >= 0)[:, None], pal[np.maximum(lab, 0)], [0.86, 0.87, 0.89])
N = vertex_normals(V, F)
tiles = []
for w in (P["front"], P["rear"]):
    near = (np.abs(c[:, 0] - w["x"]) < 750) & (c[:, 1] <= 5) & (c[:, 1] > -1100)
    Fs = F[near]; used = np.unique(Fs); idx = np.full(len(V), -1); idx[used] = np.arange(len(used))
    Vs, Fs2, Ns = V[used], idx[Fs], N[used]
    for R in (rot(0, np.pi), rot(np.radians(-25), -np.radians(110)), rot(np.radians(25), -np.radians(110))):
        tiles.append(raster(Vs, Fs2, C[near], R, 700, 520, N=Ns))
rows = [np.concatenate(tiles[i:i + 3], 1) for i in (0, 3)]
Image.fromarray(np.concatenate(rows, 0)).save(sys.argv[4])

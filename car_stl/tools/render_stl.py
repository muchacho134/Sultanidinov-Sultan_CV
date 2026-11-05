import sys, numpy as np, trimesh
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh')
V, F = np.asarray(m.vertices, float), np.asarray(m.faces)
C = np.tile([0.88, 0.89, 0.91], (len(F), 1))
if len(sys.argv) > 3:            # optional per-face colour file (.npy)
    C = np.load(sys.argv[3])
render_sheet(V, F, C, sys.argv[2], N=vertex_normals(V, F))

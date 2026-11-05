import sys, numpy as np, trimesh
from scipy.spatial import cKDTree
m = trimesh.load(sys.argv[1], force='mesh')
V, F = m.vertices, m.faces
# --- symmetry about y = 0
t = cKDTree(V); Vm = V * [1, -1, 1]
d, _ = t.query(Vm)
print("mirror y=0 distance: median %.1f  p90 %.1f  p99 %.1f  max %.1f mm" % tuple(np.percentile(d, [50, 90, 99, 100])))
# --- sharp edges: dihedral angle between adjacent faces
ang = np.degrees(m.face_adjacency_angles)
print("dihedral angle: p50 %.1f p90 %.1f p99 %.1f max %.1f deg" % tuple(np.percentile(ang, [50, 90, 99, 100])))
for th in (20, 30, 45, 60):
    print("  edges sharper than %d deg: %d" % (th, (ang > th).sum()))
# --- curvature (discrete mean curvature at vertices, ball radius 40 mm)
r = 40.0
H = trimesh.curvature.discrete_mean_curvature_measure(m, V, r) / (np.pi * r * r)   # ~1/mm
K = trimesh.curvature.discrete_gaussian_curvature_measure(m, V, r) / (np.pi * r * r)
np.save("H.npy", H); np.save("K.npy", K); np.save("mirror_d.npy", d)
print("mean curvature radius |1/H| percentiles (mm):", (1 / np.maximum(np.abs(np.percentile(np.abs(H), [10, 50, 90])), 1e-9)).round(0))
# --- near-planar areas: face normals cluster
fn = m.face_normals; area = m.area_faces
for name, n in (("floor (-Z)", [0, 0, -1]), ("rear face (+X)", [1, 0, 0]), ("front face (-X)", [-1, 0, 0]),
                ("left side (+Y)", [0, 1, 0]), ("right side (-Y)", [0, -1, 0]), ("top (+Z)", [0, 0, 1])):
    sel = fn @ np.array(n) > 0.985
    print("faces within 10 deg of %-16s area %.2f m2" % (name, area[sel].sum() / 1e6))

import sys, numpy as np, trimesh
src, out_mm, out_raw = sys.argv[1:4]
s = trimesh.load(src); m = trimesh.util.concatenate(s.dump())

def health(t, tag):
    u, c = np.unique(t.edges_sorted, axis=0, return_counts=True)
    print(f"{tag}: faces {len(t.faces)} open edges {(c == 1).sum()} non-manifold edges {(c > 2).sum()} watertight {t.is_watertight}", flush=True)

raw = trimesh.Trimesh(m.vertices.copy(), m.faces.copy(), process=True)     # weld seams split by UVs
health(raw, "welded")
raw.update_faces(raw.nondegenerate_faces()); raw.remove_unreferenced_vertices()
health(raw, "degenerates removed")
trimesh.repair.fix_winding(raw)
health(raw, "winding fixed")
raw.export(out_raw)
# mm: Z-up, X = front(0) -> rear, Y = car's right, ground at Z=0, length 5360 mm (proper rotation, no mirroring)
v = raw.vertices
k = 5360.0 / np.ptp(v[:, 2])
car = trimesh.Trimesh(np.c_[-v[:, 2], -v[:, 0], v[:, 1]] * k, raw.faces.copy(), process=False)
car.apply_translation([-car.bounds[0][0], -car.bounds.mean(0)[1], -car.bounds[0][2]])
print("mm bounds", car.bounds.round(1).tolist(), "scale", round(k, 2))
car.export(out_mm)

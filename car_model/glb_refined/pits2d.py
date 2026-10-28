"""Surface pits / holes seen from five straight-on views. For each view's height map (toward the
viewer), a flat grey closing with an 80 mm disc fills any dip narrower than 80 mm; the filled
depth is the pit depth. Regions deeper than 3 mm are reported with location and size."""
import sys, json, numpy as np, trimesh
from scipy import ndimage
sys.path.insert(0, '.')
from depthmap import depth_map

src, out = sys.argv[1], sys.argv[2]
P = 4.0; RAD = 40.0; MIN_DEPTH = 3.0
L = 5360.0
m = trimesh.load(src); m.merge_vertices()
disk = (np.hypot(*np.mgrid[-10:11, -10:11]) <= RAD / P)

def permuted(order):
    return trimesh.Trimesh(m.vertices[:, order], m.faces, process=False)

views = []
# (name, mesh, axis_dir, range a, range b, x_ref, labels of the two grid axes, world mapping)
views.append(("top", permuted([2, 0, 1]), -1, (0, L), (-1000, 1000), 1800.0, ("x", "y")))
views.append(("left side", permuted([1, 0, 2]), 1, (0, L), (0, 1600), -1200.0, ("x", "z")))
views.append(("right side", permuted([1, 0, 2]), -1, (0, L), (0, 1600), 1200.0, ("x", "z")))
views.append(("front", m, 1, (-1000, 1000), (0, 1600), -100.0, ("y", "z")))
views.append(("rear", m, -1, (-1000, 1000), (0, 1600), L + 100.0, ("y", "z")))

report = []
maps = {}
for name, mesh, d, ra, rb, xr, axes in views:
    A, B, D = depth_map(mesh, d, ra, rb, P, xr)
    h = -D                                                   # height toward the viewer
    valid = np.isfinite(h)
    hf = np.where(valid, h, np.nanmin(h) - 500)             # misses are far away (never "fill" a silhouette)
    closed = ndimage.grey_closing(hf, footprint=disk)
    pit = np.where(valid, closed - hf, 0.0)
    # ignore the outline band (closing bridges across silhouette notches) and very steep cells
    inner = ndimage.binary_erosion(valid, iterations=int(RAD / P) + 1)
    gy, gx = np.gradient(np.nan_to_num(h, nan=0.0), P)
    steep = np.hypot(gx, gy) > 2.0
    mask = (pit > MIN_DEPTH) & inner & ~steep
    lab, n = ndimage.label(mask)
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        reg = lab[sl] == i
        cnt = int(reg.sum())
        if cnt < 3:
            continue
        idx = np.argwhere(reg) + np.array([s.start for s in sl])
        a = A[idx[:, 1]]; b = B[idx[:, 0]]
        dep = float(pit[sl][reg].max())
        surf = float(np.nanmean(D[sl][reg]))
        report.append(dict(view=name, axes=axes, a=(round(a.min()), round(a.max())), b=(round(b.min()), round(b.max())),
                           depth=round(dep, 1), area_cm2=round(cnt * P * P / 100, 1), surf_depth=round(surf, 0)))
    maps[name] = (A, B, D, pit, mask)
    print(name, "regions", n, flush=True)

report.sort(key=lambda r: -(r['depth'] * r['area_cm2'] ** 0.5))
json.dump(report, open(out, "w"), indent=1)
np.savez_compressed(out.replace('.json', '_maps.npz'), **{f"{k}_{j}": v for k, t in maps.items() for j, v in zip("ABDpm", t)})
print("total", len(report))
for r in report:
    print("  %-10s %s %5d..%5d  %s %5d..%5d  depth %5.1f mm  area %6.1f cm2" % (r['view'], r['axes'][0], *r['a'], r['axes'][1], *r['b'], r['depth'], r['area_cm2']))

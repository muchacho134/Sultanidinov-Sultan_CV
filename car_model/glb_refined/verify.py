"""Checks for the refined body: windscreen / boot-lid pits, flat underside without holes, closed files."""
import sys, json, subprocess, numpy as np, trimesh
from scipy import ndimage
sys.path.insert(0, '.')
from depthmap import depth_map

body = sys.argv[1]
subprocess.run([sys.executable, "-I", "-W", "ignore", "pits2d.py", body, "out/pits_verify.json"], check=True, stdout=subprocess.DEVNULL)
rep = json.load(open("out/pits_verify.json"))
def zone(r):
    am = 0.5 * sum(r['a']); bm = 0.5 * sum(r['b'])
    if r['view'] == 'top' and 1650 <= am <= 2500 and abs(bm) < 650: return 'windscreen'
    if r['view'] == 'top' and 4550 <= am <= 5360 and abs(bm) < 600: return 'boot lid'
    if r['view'] == 'rear' and bm > 1000 and abs(am) < 600: return 'boot lid edge'
    return None
hits = [(zone(r), r) for r in rep if zone(r)]
print("windscreen / boot-lid pits:", len(hits))
for z, r in hits:
    print("   %-14s a %s b %s depth %.1f area %.1f" % (z, r['a'], r['b'], r['depth'], r['area_cm2']))

m = trimesh.load(body)
mb = trimesh.Trimesh(m.vertices[:, [2, 0, 1]], m.faces, process=False)
xs, ys, Db = depth_map(mb, 1, (0, 5360), (-1000, 1000), 4.0, -200.0)
zb = Db - 200.0
valid = np.isfinite(zb)
X, Y = np.meshgrid(xs, ys)
wells = np.zeros_like(valid)
for xc in (903, 4155):
    wells |= (np.hypot(X - xc, 0) < 425) & (np.abs(Y) > 585)
floor = valid & ~wells
inner = ndimage.binary_erosion(floor, iterations=3)
flat = inner & (np.abs(zb - 190.0) < 1.0)
print("underside: %.1f %% of the floor (outside the wheel wells) is at z = 190 +-1 mm; max deviation %.1f mm"
      % (100 * flat.sum() / max(inner.sum(), 1), np.nanmax(np.abs(np.where(inner, zb, 190.0) - 190.0))))
# holes / pits seen from below
h = -zb; hf = np.where(valid, h, np.nanmin(h) - 500)
disk = np.hypot(*np.mgrid[-12:13, -12:13]) <= 12.5
pit = np.where(valid, ndimage.grey_closing(hf, footprint=disk) - hf, 0)
lab, n = ndimage.label((pit > 1.0) & inner)
print("underside pits/holes outside the wheel wells:", n)
for i, sl in enumerate(ndimage.find_objects(lab), 1):
    reg = lab[sl] == i; idx = np.argwhere(reg) + np.array([s.start for s in sl])
    print("   x %d..%d y %d..%d depth %.1f" % (xs[idx[:, 1]].min(), xs[idx[:, 1]].max(), ys[idx[:, 0]].min(), ys[idx[:, 0]].max(), pit[sl][reg].max()))
for p in sys.argv[2:]:
    chk = trimesh.load(p); chk.merge_vertices(); pr = chk.split(only_watertight=False)
    u, c = np.unique(chk.edges_sorted, axis=0, return_counts=True)
    print("FILE", p, "parts", len(pr), "all watertight", all(x.is_watertight for x in pr), "open", int((c == 1).sum()), "non-manifold", int((c > 2).sum()), "bounds", chk.bounds.round(0).tolist())

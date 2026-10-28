"""Fill every surface pit narrower than 100 mm on a closed body, seen from five straight-on views.
For each pit a smooth filler solid is made (local implicit field: below the filled-in surface and
above the existing surface minus 4 mm, contoured with marching cubes) and fused onto the body."""
import sys, time, numpy as np, trimesh, manifold3d as mf
from scipy import ndimage
from scipy.interpolate import RegularGridInterpolator
from skimage import measure
sys.path.insert(0, '.')
from depthmap import depth_map
from glb_ends import to_manifold, from_manifold

L = 5360.0
P = 4.0; FINE = 2.0
DISK = np.hypot(*np.mgrid[-12:13, -12:13]) <= 12.5          # 100 mm

# view: (name, column order so that col0 is the depth axis, depth sign, grid ranges, x_ref)
VIEWS = [("top", [2, 0, 1], -1, (0, L), (-1000, 1000), 1800.0),
         ("bottom", [2, 0, 1], 1, (0, L), (-1000, 1000), -200.0)]
MAX_DEPTH = 30.0; MAX_AREA_CM2 = 150.0                    # only small, shallow pits are filled

def fillers_for_view(mesh, order, sign, ra, rb, xref, min_depth=0.6):
    mv = trimesh.Trimesh(mesh.vertices[:, order], mesh.faces, process=False)
    A, B, D = depth_map(mv, sign, ra, rb, P, xref)
    h = -D                                           # height toward the viewer
    valid = np.isfinite(h)
    idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    hn = np.where(valid, h, h[tuple(idx)] if valid.any() else 0)
    closed = ndimage.grey_closing(hn, footprint=DISK)
    pit = np.where(valid, closed - h, 0.0)
    gy, gx = np.gradient(np.where(valid, h, 0.0), P)
    steep = np.hypot(gx, gy) > 0.6                   # only surfaces this view sees head-on
    inner = ndimage.binary_erosion(valid, iterations=3)
    mask = (pit > min_depth) & inner & ~steep
    mask = ndimage.binary_dilation(mask, iterations=2) & valid
    lab, n = ndimage.label(mask)
    out = []
    Hc = RegularGridInterpolator((B, A), closed, bounds_error=False, fill_value=None)
    Hs = RegularGridInterpolator((B, A), np.where(valid, h, closed), bounds_error=False, fill_value=None)
    M = RegularGridInterpolator((B, A), mask.astype(float), bounds_error=False, fill_value=0.0)
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        reg = lab[sl] == i
        if reg.sum() < 2 or reg.sum() * P * P / 100 > MAX_AREA_CM2 or pit[sl][reg].max() > MAX_DEPTH:
            continue
        b0, b1 = B[sl[0].start] - 6, B[sl[0].stop - 1] + 6
        a0, a1 = A[sl[1].start] - 6, A[sl[1].stop - 1] + 6
        aa = np.arange(a0, a1 + FINE, FINE); bb = np.arange(b0, b1 + FINE, FINE)
        BB, AA = np.meshgrid(bb, aa, indexing='ij')
        pts = np.c_[BB.ravel(), AA.ravel()]
        top = Hc(pts).reshape(BB.shape); bot = Hs(pts).reshape(BB.shape) - 4.0
        inside = M(pts).reshape(BB.shape) > 0.5
        lo, hi = np.nanmin(bot) - 4, np.nanmax(top) + 4
        hh = np.arange(lo, hi + FINE, FINE)
        phi = np.minimum(top[..., None] - hh[None, None, :], hh[None, None, :] - bot[..., None])
        phi = np.where(inside[..., None], phi, -5.0).astype(np.float32)
        if (phi > 0).sum() < 4:
            continue
        vol = np.pad(phi, 1, constant_values=-5.0)
        v, f, _, _ = measure.marching_cubes(vol, 0.05)
        v = (v - 1) * FINE + np.array([bb[0], aa[0], hh[0]])          # (b, a, height)
        # back to world: grid axes (a, b) are mesh columns 1, 2 of the permuted mesh; height = -depth
        depth = -v[:, 2]
        world_perm = np.c_[xref + sign * depth, v[:, 1], v[:, 0]]       # permuted coords: (depth axis, col1, col2)
        world = np.empty_like(world_perm)
        world[:, order] = world_perm
        fm = trimesh.Trimesh(world, f, process=True)
        if fm.volume < 0:
            fm.invert()
        if fm.is_watertight and abs(fm.volume) > 1.0:
            out.append(fm)
    return out, int(n)

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    T = time.time()
    body = trimesh.load(src); body.merge_vertices()
    Mb = to_manifold(body)
    for name, order, sign, ra, rb, xref in VIEWS:
        cur = from_manifold(Mb)
        fills, n = fillers_for_view(cur, order, sign, ra, rb, xref)
        kept = 0
        for f in fills:
            F_ = to_manifold(f)
            if (Mb ^ F_).volume() > 0.3 * abs(f.volume):      # at least 30 % of it is inside the body
                Mb = Mb + F_; kept += 1
        fills = fills[:kept] if kept else []
        print(f"{name:6s} pit regions {n:4d}  fillers {len(fills):4d}  ({time.time() - T:.0f} s)", flush=True)
    out = from_manifold(Mb)
    out.merge_vertices()
    print("filled body", len(out.faces), "watertight", out.is_watertight, "volume", round(out.volume / 1e9, 3))
    out.export(dst)

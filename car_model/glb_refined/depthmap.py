import numpy as np

def depth_map(mesh, axis_dir, y_range, z_range, step, x_ref, normals=False):
    """Orthographic depth along X (axis_dir=+1 looking toward +X from x_ref, -1 looking toward -X).
    Returns D[z_i, y_i] = distance from x_ref to the first surface (nan where nothing is hit)."""
    v = mesh.vertices; f = mesh.faces
    ys = np.arange(y_range[0], y_range[1] + 1e-9, step); zs = np.arange(z_range[0], z_range[1] + 1e-9, step)
    W, H = len(ys), len(zs)
    px = np.c_[(v[:, 1] - ys[0]) / step, (v[:, 2] - zs[0]) / step]
    dep = (v[:, 0] - x_ref) * axis_dir
    D = np.full((H, W), np.inf)
    FI = np.full((H, W), -1, np.int64)
    tri = px[f]; dz = dep[f]
    lo = np.floor(tri.min(1)).astype(int); hi = np.ceil(tri.max(1)).astype(int)
    keep = (hi[:, 0] >= 0) & (lo[:, 0] < W) & (hi[:, 1] >= 0) & (lo[:, 1] < H) & (dz.min(1) > -1e6)
    for fi, t, z, l, h in zip(np.nonzero(keep)[0], tri[keep], dz[keep], lo[keep], hi[keep]):
        x0, y0 = max(l[0], 0), max(l[1], 0); x1, y1 = min(h[0], W - 1), min(h[1], H - 1)
        if x1 < x0 or y1 < y0: continue
        d = (t[1, 0] - t[0, 0]) * (t[2, 1] - t[0, 1]) - (t[2, 0] - t[0, 0]) * (t[1, 1] - t[0, 1])
        if abs(d) < 1e-12: continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        w1 = ((X - t[0, 0]) * (t[2, 1] - t[0, 1]) - (t[2, 0] - t[0, 0]) * (Y - t[0, 1])) / d
        w2 = ((t[1, 0] - t[0, 0]) * (Y - t[0, 1]) - (X - t[0, 0]) * (t[1, 1] - t[0, 1])) / d
        w0 = 1 - w1 - w2; msk = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not msk.any(): continue
        zz = w0 * z[0] + w1 * z[1] + w2 * z[2]
        sub = D[y0:y1 + 1, x0:x1 + 1]
        msk &= zz < sub
        sub[msk] = zz[msk]
        FI[y0:y1 + 1, x0:x1 + 1][msk] = fi
    D[np.isinf(D)] = np.nan
    if not normals:
        return ys, zs, D
    n = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    nx = np.abs(n[:, 0]) / (np.linalg.norm(n, axis=1) + 1e-12)       # facing-ness toward the view axis
    NX = np.where(FI >= 0, nx[np.maximum(FI, 0)], np.nan)
    return ys, zs, D, NX
